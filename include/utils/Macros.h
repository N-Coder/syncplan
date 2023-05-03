#pragma once

#define NO_COPY(cls)               \
	cls(const cls& copy) = delete; \
	cls& operator=(const cls& copy) = delete;

#define NO_MOVE(cls)          \
	cls(cls&& move) = delete; \
	cls& operator=(cls&& move) = delete;

#define DEFAULT_COPY(cls)           \
	cls(const cls& copy) = default; \
	cls& operator=(const cls& copy) = default;

#define DEFAULT_MOVE(cls)      \
	cls(cls&& move) = default; \
	cls& operator=(cls&& move) = default;

#define NO_RT_COPY(cls)                                                              \
	cls(const cls& copy) { throw std::runtime_error("class cls is not copyable"); }; \
	cls& operator=(const cls& copy) { throw std::runtime_error("class cls is not copyable"); };

#define NO_RT_MOVE(cls)                                                        \
	cls(cls&& move) { throw std::runtime_error("class cls is not movable"); }; \
	cls& operator=(cls&& move) { throw std::runtime_error("class cls is not movable"); };

#define COPY_CONSTR(cls) cls(const cls& copy)
#define COPY_OP(cls) cls& operator=(const cls& copy)
#define MOVE_CONSTR(cls) cls(cls&& move) noexcept : cls()
#define MOVE_OP(cls) cls& operator=(cls&& move) noexcept
#define SWAP_OP(cls) friend void swap(cls& first, cls& second) noexcept


#define COPY_MOVE_BY_SWAP(cls)          \
	cls& operator=(cls copy_by_value) { \
		using std::swap;                \
		swap(*this, copy_by_value);     \
	}                                   \
	MOVE_CONSTR(cls) {                  \
		using std::swap;                \
		swap(*this, move);              \
	}                                   \
	MOVE_OP(cls) {                      \
		using std::swap;                \
		swap(*this, move);              \
	}
