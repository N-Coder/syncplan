#include "solve/BlockEmbedding.h"

#include "utils/GraphUtils.h"

void BlockEmbedding::init(Graph& G, PQPlanarityComponents& components, node bc,
		EdgeArray<edge>& Ge_to_subgraph, EdgeArray<BlockEmbedding*>& Ge_to_block) {
	OGDF_ASSERT(!components.isCutComponent(bc));
	subgraph_to_Ge.init(subgraph, nullptr);

	for (node w : components.nodesInBiconnectedComponent(bc)) {
		OGDF_ASSERT(w != nullptr);
		OGDF_ASSERT(w->graphOf() == &G);
		node n = subgraph.newNode();
		Gn_to_subgraph(w, this) = n;

		for (adjEntry adj : w->adjEntries) {
			edge e = adj->theEdge();
			if (Ge_to_block[e] != nullptr) {
				continue;
			}

			node Gs, Gt;
			if (adj->isSource()) {
				Gs = n;
				if (!Gn_to_subgraph.contains(e->target(), this)) {
					continue;
				}
				Gt = Gn_to_subgraph(e->target(), this);
			} else {
				Gt = n;
				if (!Gn_to_subgraph.contains(e->source(), this)) {
					continue;
				}
				Gs = Gn_to_subgraph(e->source(), this);
			}
			OGDF_ASSERT(Gs != nullptr);
			OGDF_ASSERT(Gt != nullptr);

			edge se = Ge_to_subgraph[e] = subgraph.newEdge(Gs, Gt);
			Ge_to_block[e] = this;
			subgraph_to_Ge[se] = e;
		}
	}

	if (subgraph.numberOfNodes() > 3) {
		spqr = new StaticPlanarSPQRTree(subgraph, false);
		rigid_vars.init(spqr->tree(), TwoSAT_Var_Undefined);
	}
}

bool BlockEmbedding::addQVertex(node q, EdgeArray<edge>& Ge_to_subgraph, TwoSAT& sat,
		twosat_var part_var) {
	q_vertices.pushBack(q);

	node rigid = nullptr;
	const Skeleton* rigid_skel = nullptr;
	node q_in_rigid = nullptr;

	int cnt_s = 0, cnt_r = 0, cnt_p = 0;
	node subgr_q = Gn_to_subgraph(q, this);
	for (adjEntry adj : q->adjEntries) {
		const Skeleton& skel = spqr->skeletonOfReal(Ge_to_subgraph[adj->theEdge()]);
		edge skel_edge = spqr->copyOfReal(Ge_to_subgraph[adj->theEdge()]);
		OGDF_ASSERT(skel_edge->graphOf() == &skel.getGraph());
		if (spqr->typeOf(skel.treeNode()) == SPQRTree::NodeType::SNode) {
			cnt_s++;
		} else if (rigid == nullptr) {
			rigid = skel.treeNode();
			rigid_skel = &skel;
			if (skel.original(skel_edge->source()) == subgr_q) {
				q_in_rigid = skel_edge->source();
			} else {
				q_in_rigid = skel_edge->target();
			}
			OGDF_ASSERT(skel.original(q_in_rigid) == subgr_q);
			if (spqr->typeOf(rigid) == SPQRTree::NodeType::PNode) {
				OGDF_ASSERT(spqr->skeleton(rigid).getGraph().firstNode()->degree() == 3);
				cnt_p++;
			} else {
				OGDF_ASSERT(spqr->typeOf(rigid) == SPQRTree::NodeType::RNode);
				cnt_r++;
			}
			OGDF_ASSERT(spqr->numberOfNodeEmbeddings(rigid) == 2);
		} else {
			OGDF_ASSERT(skel.treeNode() == rigid);
		}
	}
	OGDF_ASSERT(rigid != nullptr);
	OGDF_ASSERT(rigid_skel != nullptr);
	OGDF_ASSERT(q_in_rigid != nullptr);

	twosat_var& rigid_var = rigid_vars[rigid];
	if (rigid_var == TwoSAT_Var_Undefined) {
		rigid_var = sat.newVariable();
	}

	List<adjEntry> q_adjs_rigid_order;
	for (adjEntry adj : q_in_rigid->adjEntries) {
		edge real_edge = rigid_skel->realEdge(adj->theEdge());
		if (real_edge == nullptr) { // the edge is virtual
			node twin_spqr = rigid_skel->twinTreeNode(adj->theEdge());
			edge twin_edge = rigid_skel->twinEdge(adj->theEdge());
			OGDF_ASSERT(spqr->typeOf(twin_spqr) == SPQRTree::NodeType::SNode);
			const Skeleton& twin_skel = spqr->skeleton(twin_spqr);
			node q_in_twin;
			if (twin_skel.original(twin_edge->source()) == subgr_q) {
				q_in_twin = twin_edge->source();
			} else {
				q_in_twin = twin_edge->target();
			}
			OGDF_ASSERT(twin_skel.original(q_in_twin) == subgr_q);
			OGDF_ASSERT(q_in_twin->degree() == 2);
			edge other_edge = twin_edge->getAdj(q_in_twin)->cyclicSucc()->theEdge();
			OGDF_ASSERT(other_edge != twin_edge);
			real_edge = twin_skel.realEdge(other_edge);
			OGDF_ASSERT(real_edge != nullptr);
		}
		q_adjs_rigid_order.pushBack(subgraph_to_Ge[real_edge]->getAdj(q));
	}
	OrderComp comp = compareCyclicOrder(q, q_adjs_rigid_order, true);
	if (comp == REVERSED) {
		sat.newClause(part_var, true, rigid_var, true);
		sat.newClause(part_var, false, rigid_var, false);
	} else if (comp == SAME) {
		sat.newClause(part_var, true, rigid_var, false);
		sat.newClause(part_var, false, rigid_var, true);
	} else {
		return false;
	}
	return true;
}
