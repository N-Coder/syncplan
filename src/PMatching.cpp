#include "PQPlanarity.h"
#include "utils/Logging.h"

using namespace ogdf;

Pipe::Pipe(node node1, node node2)
	: node1(node1)
	, node2(node2)
#ifdef OGDF_DEBUG
	, dbg_degree(node1->degree())
#endif
{
}

int Pipe::degree() const {
	OGDF_ASSERT(dbg_degree == node1->degree());
	OGDF_ASSERT(dbg_degree == node2->degree());
	return node1->degree();
}

node Pipe::getTwin(node n) const {
	if (n == node1) {
		return node2;
	} else {
		OGDF_ASSERT(n == node2);
		return node1;
	}
}

std::ostream& operator<<(std::ostream& os, const Pipe& pipe) {
	os << "(°" << pipe.degree() << " #" << pipe.node1->index() << " = #" << pipe.node2->index()
	   << ")";
	return os;
}

bool PMatching::isMatchedPVertex(node n) const {
	OGDF_ASSERT(n != nullptr);
	return nodes[n] != nullptr;
}

const Pipe* PMatching::getPipe(node n) const {
	OGDF_ASSERT(n != nullptr);
	return nodes[n];
}

node PMatching::getTwin(node n) const {
	OGDF_ASSERT(n != nullptr);
	Pipe* pipe = nodes[n];
	OGDF_ASSERT(pipe != nullptr);
	node twin = pipe->getTwin(n);
	OGDF_ASSERT(nodes[twin] == pipe);
	OGDF_ASSERT(twin->degree() == n->degree());
	return twin;
}

node PMatching::getTwinOrNull(node n) const {
	OGDF_ASSERT(n != nullptr);
	Pipe* pipe = nodes[n];
	if (pipe == nullptr) {
		return nullptr;
	}
	node twin = pipe->getTwin(n);
	OGDF_ASSERT(nodes[twin] == pipe);
	OGDF_ASSERT(twin->degree() == n->degree());
	return twin;
}

const Pipe& PMatching::getTopPipe() const {
	OGDF_ASSERT(queue);
	return *(queue->getTop());
}

void PMatching::matchNodes(node f, node s) {
	OGDF_ASSERT(!isMatchedPVertex(f));
	OGDF_ASSERT(!isMatchedPVertex(s));
	OGDF_ASSERT(f->degree() == s->degree());
	List<Pipe>::iterator it = pipes_list.emplaceBack(f, s);
	(*it).list_entry = it;
	if (queue) {
		queue->addPipe(&(*it));
	}
	nodes[f] = nodes[s] = &(*it);
}

node PMatching::removeMatching(node n, node t) {
	OGDF_ASSERT(n != nullptr);
	Pipe* pipe = nodes[n];
	OGDF_ASSERT(pipe != nullptr);
	if (pipe->pipe_priority >= 0) {
		priority_pipes--;
	}
	node twin = pipe->getTwin(n);
	OGDF_ASSERT(t == nullptr || t == twin);
	nodes[n] = nodes[twin] = nullptr;
	if (queue) {
		queue->removePipe(pipe);
	}
	pipes_list.del(pipe->list_entry);
	return twin;
}

void PMatching::makePriority(node n) {
	Pipe* p = nodes[n];
	bool incr = p->pipe_priority < 0;
	if (queue) {
		p->pipe_priority = queue->getTop()->pipe_priority + 1;
		queue->removePipe(p);
		queue->addPipe(p);
	} else {
		p->pipe_priority = priority_pipes;
	}
	if (incr) {
		priority_pipes++;
	}
}

void PMatching::rebuildHeap() {
	if (queue) {
		queue->rebuild(pipes_list);
	}
}

void PMatching::nodeDeleted(node v) { OGDF_ASSERT(!isMatchedPVertex(v)); }

List<Pipe>::const_iterator PMatching::begin() const { return pipes_list.begin(); }

List<Pipe>::const_iterator PMatching::end() const { return pipes_list.end(); }

const List<Pipe>& PMatching::getPipes() const { return pipes_list; }

int PMatching::getPipeCount() const { return pipes_list.size(); }

bool PMatching::isReduced() const { return pipes_list.empty(); }

PipeBijIterator PMatching::getIncidentEdgeBijection(node u) const {
	return getPipeBijection(u, getTwin(u));
}

void PMatching::getIncidentEdgeBijection(node u, PipeBij& out) const {
	getPipeBijection(u, getTwin(u), out);
}

void PMatching::getIncidentEdgeBijection(node u, AdjEntryArray<adjEntry>& out) const {
	getPipeBijection(u, getTwin(u), out);
}

void PMatching::getIncidentEdgeBijection(node u, EdgeArray<edge>& out) const {
	getPipeBijection(u, getTwin(u), out);
}

adjEntry PMatching::translateIncidentEdge(adjEntry e) const {
	node u = e->theNode();
	node v = getTwin(u);
	auto ve = v->adjEntries.rbegin();
	for (auto ue : u->adjEntries) {
		if (ue == e) {
			return (*ve);
		} else {
			ve++;
		}
		OGDF_ASSERT(ve != v->adjEntries.rend());
	}
	OGDF_ASSERT(false);
	return nullptr;
}

std::function<std::ostream&(std::ostream&)> PMatching::printBijection(node u) const {
	node v = getTwin(u);
	const auto bij = getIncidentEdgeBijection(u);
	return [u, v, bij](std::ostream& ss) -> std::ostream& {
		return ss << "u" << u->index() << " = v" << v->index() << ": " << ::printBijection(bij);
	};
}
