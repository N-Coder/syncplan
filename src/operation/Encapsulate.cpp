#include "operation/Encapsulate.h"

#include "PQPlanarity.h"
#include "utils/GraphUtils.h"
#include "utils/Logging.h"

std::ostream& operator<<(std::ostream& os, const EncapsulatedBlock& block) {
	os << "EncapsulatedBlock(bicon=" << block.bicon << ", bicon_rep=" << block.bicon_rep
	   << ", star_rep=" << block.star_rep << ", bij=" << printBijection(block.bij) << ")";
	return os;
}

class UndoEncapsulate : public PQPlanarity::UndoOperation {
public:
	List<std::pair<int, int>> ray_pipes;

	explicit UndoEncapsulate(const List<EncapsulatedBlock>& cut_list) {
		for (const EncapsulatedBlock& cut : cut_list) {
			ray_pipes.emplaceBack(cut.star_rep->index(), cut.bicon_rep->index());
		}
	}

	void undo(PQPlanarity& pq) override {
		PQ_PROFILE_START("undo-encapsulate")
		pq.log.lout(Logger::Level::High)
				<< "UNDO ENCAPSULATE CUT for " << ray_pipes.size() << " blocks." << std::endl;
		Logger::Indent _(&pq.log);
		for (const std::pair<int, int>& pipe : ray_pipes) {
			node u = pq.nodeFromIndex(pipe.first);
			node v = pq.nodeFromIndex(pipe.second);
			pq.log.lout() << "Joining pipe matching " << pq.fmtPQNode(u, false) << " with "
						  << pq.fmtPQNode(v, false) << "." << std::endl;
			Logger::Indent _(&pq.log);
			pq.log.lout(Logger::Level::Medium) << pq.matchings.printBijection(u) << std::endl;
			PipeBij bij;
			pq.matchings.getIncidentEdgeBijection(u, bij);
			pq.matchings.removeMatching(u, v);
			join(*pq.G, u, v, bij);
			pq.log.lout(Logger::Level::Medium) << printEdges(bij) << std::endl;
		}
		PQ_PROFILE_STOP("undo-encapsulate")
	}

	ostream& print(ostream& os) const override {
		os << "UndoEncapsulate([";
		bool first = true;
		for (const auto& p : ray_pipes) {
			if (first) {
				first = false;
			} else {
				os << ", ";
			}
			os << "(" << p.first << ", " << p.second << ")";
		}
		return os << "])";
	}
};

PQPlanarity::Result PQPlanarity::encapsulate(node g_cut) {
	// get some properties of the original cut vertex
	if (!components.isCutVertex(g_cut)) {
		return Result::NOT_APPLICABLE;
	}
	PQ_PROFILE_START("encapsulate")
	node bc_cut = components.biconnectedComponent(g_cut);
	int old_conn_count = components.connectedCount(), block_count = bc_cut->degree(),
		degree = g_cut->degree();
	log.lout(Logger::Level::High) << "ENCAPSULATE CUT " << fmtPQNode(g_cut) << " in component "
								  << components.fmtBCNode(bc_cut) << "." << std::endl;
	Logger::Indent _(&log);
	List<EncapsulatedBlock> block_list;
	NodeArray<EncapsulatedBlock*> block_map(components.bcTree(), nullptr);

	for (adjEntry g_adj : g_cut->adjEntries) {
		node bc_adj_n = components.biconnectedComponent(g_adj->twinNode());
		if (components.isCutComponent(bc_adj_n)) {
			bc_adj_n = components.findCommonBiconComp(bc_cut, bc_adj_n);
		}
		if (block_map[bc_adj_n] == nullptr) {
			block_map[bc_adj_n] = &(*block_list.emplaceBack(bc_adj_n));
		}
		block_map[bc_adj_n]->bij.emplaceBack(g_adj, nullptr);
	}

	for (EncapsulatedBlock& block : block_list) {
		log.lout(Logger::Level::Medium)
				<< "Encapsulating Block " << components.fmtBCNode(block.bicon) << std::endl;
		Logger::Indent _(&log);
		log.lout(Logger::Level::Minor) << printBijection(block.bij) << std::endl;
		std::pair<node, node> pair = split(*G, block.bij);
		block.star_rep = pair.first;
		block.bicon_rep = pair.second;

		components.postSplitOffEncapsulatedBlock(g_cut, block);

		matchings.matchNodes(block.star_rep, block.bicon_rep);
		log.lout(Logger::Level::Minor) << matchings.printBijection(block.star_rep) << std::endl;
#ifdef OGDF_DEBUG
		PipeBij actual_edges;
		matchings.getIncidentEdgeBijection(pair.first, actual_edges);
		for (PipeBijPair& pair : actual_edges) {
			pair.first = pair.first->twin();
			pair.second = pair.second->twin();
		}
		OGDF_ASSERT(block.bij == actual_edges);
#endif

		formatNode(block.star_rep);
		formatNode(block.bicon_rep);
		if (GA != nullptr) {
			std::ostringstream ss;
			ss << "StarRep " << block.star_rep->index() << " of {" << block.bicon->index()
			   << "} around [" << g_cut->index() << "]";
			GA->label(block.star_rep) = ss.str();
			ss.str("");
			ss << "BicRep " << block.bicon_rep->index() << " for [" << g_cut->index() << "] in {"
			   << block.bicon->index() << "}";
			GA->label(block.bicon_rep) = ss.str();
		}
		log.lout(Logger::Level::Medium) << "Matched " << fmtPQNode(block.star_rep) << " with "
										<< fmtPQNode(block.bicon_rep) << std::endl;
	}


#ifdef OGDF_DEBUG
	OGDF_ASSERT(components.connectedCount() == old_conn_count + block_count);
	OGDF_ASSERT(g_cut->degree() == degree);
	OGDF_ASSERT(bc_cut->degree() == block_count);
	int ray_count = 0;
	for (node bicon : FilteringBFS(components.bcTree(), {bc_cut})) {
		OGDF_ASSERT(components.bcConnectedId(bicon) == components.bcConnectedId(bc_cut));
		if (bicon != bc_cut) {
			OGDF_ASSERT(bicon->degree() == 1);
			OGDF_ASSERT(bicon->adjEntries.head()->twinNode() == bc_cut);
			++ray_count;
		}
	}
	OGDF_ASSERT(bc_cut->degree() == ray_count);
#endif

	pushUndoOperationAndCheck(new UndoEncapsulate(block_list));
	PQ_PROFILE_STOP("encapsulate")
	return Result::SUCCESS;
}