#pragma once

#include <ogdf/basic/extended_graph_alg.h>
#include <ogdf/basic/simple_graph_alg.h>
#include <ogdf/graphalg/Triconnectivity.h>

#include <NodePCRotation.h>

#include "../utils/Macros.h"
#include "../utils/OverlappingGraphCopies.h"

using namespace ogdf;
using namespace std;

ostream& operator<<(ostream& os, Triconnectivity::CompType t);

namespace spqr_utils {
inline bool isSNode(const Graph& skel) {
	return skel.numberOfNodes() > 2 && skel.numberOfNodes() == skel.numberOfEdges();
}

inline bool isPNode(const Graph& skel) { return skel.numberOfNodes() == 2; }

inline bool isRNode(const Graph& skel) { return !isSNode(skel) && !isPNode(skel); }

inline adjEntry getAdjInSkel(const OverlappingGraphCopy* skel, adjEntry GC_adj) {
	return skel->copy(GC_adj->theEdge())->getAdj(skel->copy(GC_adj->theNode()));
}

inline adjEntry getAdjInOrig(const OverlappingGraphCopy* skel, adjEntry skel_adj) {
	return skel->original(skel_adj->theEdge())->getAdj(skel->original(skel_adj->theNode()));
}
}

struct SimpleSPQRTree {
	using Comp = Triconnectivity::CompStruct;
	static Logger log;
	OverlappingGraphCopy GC;
	OverlappingGraphCopies GC_skels;
	EdgeArray<SList<edge>> par_replacement;
	EdgeArray<OverlappingGraphCopy*> skels;
	EdgeArray<OverlappingGraphCopy*> twins;
	vector<OverlappingGraphCopy*> skel_array;
	bool planar = true;

	NO_COPY(SimpleSPQRTree)

	NO_MOVE(SimpleSPQRTree)

	SimpleSPQRTree(OverlappingGraphCopies& OGC_base) : GC(OGC_base), GC_skels(GC) {};

	~SimpleSPQRTree() {
		for (auto ptr : skel_array) {
			ptr->breakLinkForMasterDeconstruction();
			delete ptr;
		}
	}

	void init();

	OverlappingGraphCopy* getNonSSkel(node GC_n) const;

	OverlappingGraphCopy* getTwinSkel(OverlappingGraphCopy* skel, edge skel_e) const;

	OverlappingGraphCopy* getTwinSkel_GC(OverlappingGraphCopy* skel, edge GC_e) const;
};

class NodeSSPQRRotation : public pc_tree::NodePCRotation {
	const SimpleSPQRTree& spqr;

	pc_tree::PCNode* process(adjEntry skel_adj, OverlappingGraphCopy& skel,
			pc_tree::PCNode* parent = nullptr);

	void getIncidentRealEdgesInSubtree(adjEntry skel_adj, OverlappingGraphCopy& skel,
			List<edge>& out);

public:
	NO_COPY(NodeSSPQRRotation)

	NO_MOVE(NodeSSPQRRotation)

	NodeSSPQRRotation(const SimpleSPQRTree& spqr, node n);

	void mapPartnerEdges();
};
