#include "PQPlanarity.h"
#include "utils/Logging.h"

class UpdateGraphReg : public GraphObserver {
	NodeArray<node>* node_reg;
	EdgeArray<edge>* edge_reg;

public:
	UpdateGraphReg(const Graph* g, NodeArray<node>* nodeReg, EdgeArray<edge>* edgeReg)
		: GraphObserver(g), node_reg(nodeReg), edge_reg(edgeReg) {
		nodeReg->init(*g, nullptr);
		edgeReg->init(*g, nullptr);
		for (node n : g->nodes) {
			(*node_reg)[n] = n;
		}
		for (edge e : g->edges) {
			(*edge_reg)[e] = e;
		}
	}

	~UpdateGraphReg() override {
		node_reg->init();
		edge_reg->init();
	}

	void nodeDeleted(node v) override { (*node_reg)[v] = nullptr; }

	void nodeAdded(node v) override { (*node_reg)[v] = v; }

	void edgeDeleted(edge e) override { (*edge_reg)[e] = nullptr; }

	void edgeAdded(edge e) override { (*edge_reg)[e] = e; }

	void reInit() override { }

	void cleared() override { }
};

node PQPlanarity::nodeFromIndex(int idx) const {
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
	return node_reg[idx];
#pragma GCC diagnostic pop
}

edge PQPlanarity::edgeFromIndex(int idx) const {
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
	return edge_reg[idx];
#pragma GCC diagnostic pop
}

void PQPlanarity::thawPipeBijection(node u, node v, const FrozenPipeBij& in, PipeBij& out) const {
	for (const FrozenPipeBijPair& pair : in) {
		out.emplaceBack(edgeFromIndex(pair.first)->getAdj(u), edgeFromIndex(pair.second)->getAdj(v));
	}
}

bool PQPlanarity::verifyPipeBijection(node u, node v, const FrozenPipeBij& bij) const {
	PipeBij thawed_bij;
	thawPipeBijection(u, v, bij, thawed_bij);

	PipeBij new_bij;
	matchings.getIncidentEdgeBijection(u, new_bij);

	const PipeBijCmp& cmp = PipeBijCmp();
	thawed_bij.quicksort(cmp);
	new_bij.quicksort(cmp);
	bool bijection_broke = thawed_bij != new_bij;
	if (bijection_broke) {
		log.lout(Logger::Level::Alarm) << "old_bij: " << printBijection(thawed_bij) << std::endl;
		log.lout(Logger::Level::Alarm) << "new_bij: " << printBijection(new_bij) << std::endl;
	}
	OGDF_ASSERT(!bijection_broke);
	return !bijection_broke;
}

void PQPlanarity::embed() {
	OGDF_ASSERT(G->representsCombEmbedding());

	PQ_PROFILE_START("embed")
	int undo_cnt = undo_stack.size();
	log.lout(Logger::Level::High) << undo_cnt << " Operations to undo" << std::endl;
	UpdateGraphReg updater(G, &node_reg, &edge_reg);
	OGDF_ASSERT(matchings.isReduced());
	matchings.setPipeQueue(nullptr);
	while (!undo_stack.empty()) {
		PQ_PROFILE_START("embed-step")
		UndoOperation* op = undo_stack.popBackRet();
		log.lout(Logger::Level::High) << (undo_cnt - undo_stack.size())
#ifdef OGDF_DEBUG
									  << " (" << op->consistency_nr << ")"
#endif
									  << ": " << *op << std::endl;

#ifdef PQ_OPSTATS
		std::chrono::time_point<std::chrono::high_resolution_clock> start = tpc::now();
#endif
		op->undo(*this);
#ifdef PQ_OPSTATS
		stats_out << (stats_first_in_array ? "" : ",") << "{\"op\":\"embed-" << op->name() << "\""
				  << ",\"op_time_ns\":" << dur_ns(tpc::now() - start) << "}";
		stats_first_in_array = false;
#endif

#ifdef OGDF_DEBUG
		if (consistency.doWriteOut) {
			stringstream ss;
			ss << "undoOp" << op->consistency_nr;
			consistency.writeOut(ss.str(), false, false);
		}
#endif
		delete op;
		OGDF_ASSERT(G->representsCombEmbedding());
		PQ_PROFILE_STOP("embed-step")
	}
	PQ_PROFILE_STOP("embed")
}