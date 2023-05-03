#pragma once

#include <ogdf/basic/PriorityQueue.h>

#include "PMatching.h"

// using PipeCmp = std::function<bool(const Pipe *, const Pipe *)>;

template<typename PipeCmp>
struct PipeCmpPtr {
	const PipeCmp* cmp;

	PipeCmpPtr() = delete;

	PipeCmpPtr(const PipeCmp* queue) : cmp(queue) {};

	bool operator()(const Pipe* x, const Pipe* y) const {
		if (x == nullptr) {
			return y != nullptr; // true
		} else if (y == nullptr) {
			return false;
		} else if (x->pipe_priority != y->pipe_priority) {
			return x->pipe_priority > y->pipe_priority;
		} else {
			return cmp->comparePipes(x, y);
		}
	}

	bool checkOrder(const Pipe* first, const Pipe* second) const {
		return first == second || !(*this)(second, first);
	}
};

template<typename PipeCmp>
class SimplePipeQueue : public PipeQueue {
public:
	using PipesHeap = PriorityQueue<Pipe*, PipeCmpPtr<PipeCmp>>;
	using PipesHeapHandle = typename PipesHeap::handle;

protected:
	std::unique_ptr<PipesHeap> pipes_heap;

public:
	SimplePipeQueue() = default;

	SimplePipeQueue(const SimplePipeQueue& copy) = delete;

	SimplePipeQueue(SimplePipeQueue&& move) = delete;

	SimplePipeQueue& operator=(const SimplePipeQueue& copy) = delete;

	SimplePipeQueue& operator=(SimplePipeQueue&& move) = delete;

	bool empty() override { return pipes_heap->empty(); }

	int size() override { return pipes_heap->size(); }

	Pipe* getTop() override { return pipes_heap->top(); }

	void addPipe(Pipe* p) override {
#ifdef OGDF_DEBUG
		OGDF_ASSERT(p->node1->degree() == p->node2->degree());
		p->dbg_degree = p->node1->degree();
#endif
		p->heap_entry = pipes_heap->push(p);
	}

	void removePipe(Pipe* pipe) override {
		OGDF_ASSERT(pipes_heap->value((PipesHeapHandle)pipe->heap_entry) == pipe);
		pipes_heap->decrease((PipesHeapHandle)pipe->heap_entry, nullptr);
		OGDF_ASSERT(pipes_heap->top() == nullptr);
		pipes_heap->pop();
		OGDF_ASSERT(pipes_heap->empty() || pipes_heap->top() != nullptr);
	}

	void rebuild(List<Pipe>& pipes_list) override {
		clear();
		for (Pipe& p : pipes_list) {
			addPipe(&p);
		}
	}

	void clear() override {
#ifdef OGDF_DEBUG
		Pipe* top = nullptr;
		while (!pipes_heap->empty()) {
			// OGDF_ASSERT(checkOrder(top, pipes_heap->top()));
			top = pipes_heap->top();
			pipes_heap->pop();
		}
#else
		pipes_heap->clear();
#endif
	}
};

struct PipeQueueByDegree : public SimplePipeQueue<PipeQueueByDegree> {
	bool invert_degree;

	explicit PipeQueueByDegree(bool invert = false) : invert_degree(invert) {
		pipes_heap = std::make_unique<PipesHeap>(this);
	};

	bool comparePipes(const Pipe* x, const Pipe* y) const {
		if (invert_degree) {
			return x->degree() < y->degree();
		} else {
			return x->degree() > y->degree();
		}
	}
};

struct PipeQueueRandom : public SimplePipeQueue<PipeQueueRandom> {
	using engine = std::minstd_rand;
	mutable engine gen;

	explicit PipeQueueRandom() { pipes_heap = std::make_unique<PipesHeap>(this); };

	engine::result_type hash(const Pipe* p) const {
		gen.seed(max(p->node1->index(), p->node2->index()));
		gen.discard(5 + p->degree() % 20);
		return gen();
	}

	bool comparePipes(const Pipe* x, const Pipe* y) const {
		if (x == nullptr) {
			return true;
		} else if (y == nullptr) {
			return false;
		}
		return hash(x) > hash(y);
	}
};

template<typename PipeCmp1, typename PipeCmp2>
class DoublePipeQueue : public SimplePipeQueue<PipeCmp1> {
public:
	using PipesHeap2 = PriorityQueue<Pipe*, PipeCmpPtr<PipeCmp2>>;
	using PipesHeapHandle2 = typename PipesHeap2::handle;
	using Base = SimplePipeQueue<PipeCmp1>;

protected:
	using Base::pipes_heap;
	std::unique_ptr<PipesHeap2> pipes_heap2;

	virtual bool isQueue1(Pipe* p) const = 0;

public:
	bool empty() override { return Base::empty() && pipes_heap2->empty(); }

	int size() override { return Base::size() + pipes_heap2->size(); }

	Pipe* getTop() override {
		while (!Base::empty()) {
			Pipe* p = Base::getTop();
			if (isQueue1(p)) {
				return p;
			} else {
				removePipe(p);
				addPipe(p);
			}
		}
		OGDF_ASSERT(!pipes_heap2->empty());
		return pipes_heap2->top();
	}

	void addPipe(Pipe* p) override {
#ifdef OGDF_DEBUG
		OGDF_ASSERT(p->node1->degree() == p->node2->degree());
		p->dbg_degree = p->node1->degree();
#endif
		if (isQueue1(p)) {
			p->heap_data = 1;
			p->heap_entry = pipes_heap->push(p);
		} else {
			p->heap_data = 2;
			p->heap_entry = pipes_heap2->push(p);
		}
	}

	void removePipe(Pipe* pipe) override {
		if (pipe->heap_data == 2) {
			OGDF_ASSERT(pipes_heap2->value((PipesHeapHandle2)pipe->heap_entry) == pipe);
			pipes_heap2->decrease((PipesHeapHandle2)pipe->heap_entry, nullptr);
			OGDF_ASSERT(pipes_heap2->top() == nullptr);
			pipes_heap2->pop();
			OGDF_ASSERT(pipes_heap2->empty() || pipes_heap2->top() != nullptr);
		} else {
			Base::removePipe(pipe);
		}
	}

	void clear() override {
#ifdef OGDF_DEBUG
		Pipe* top = nullptr;
		while (!pipes_heap->empty()) {
			// OGDF_ASSERT(checkOrder(top, pipes_heap->top()));
			top = pipes_heap->top();
			pipes_heap->pop();
		}
		while (!pipes_heap2->empty()) {
			// OGDF_ASSERT(checkOrder(top, pipes_heap2->top()));
			top = pipes_heap2->top();
			pipes_heap2->pop();
		}
#else
		pipes_heap->clear();
		pipes_heap2->clear();
#endif
	}
};

class PQPlanarity;

struct PipeQueueByDegreePreferContract
	: public DoublePipeQueue<PipeQueueByDegreePreferContract, PipeQueueByDegreePreferContract> {
	PQPlanarity* PQ;
	bool invert_degree, invert_contract;

	explicit PipeQueueByDegreePreferContract(PQPlanarity* pq, bool invertDegree = false,
			bool invertContract = false)
		: PQ(pq), invert_degree(invertDegree), invert_contract(invertContract) {
		pipes_heap = std::make_unique<PipesHeap>(this);
		pipes_heap2 = std::make_unique<PipesHeap2>(this);
	}

	bool comparePipes(const Pipe* x, const Pipe* y) const;

	bool isQueue1(Pipe* p) const override;
};
