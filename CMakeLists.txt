cmake_minimum_required(VERSION 3.15)
project(cplanarity)
set(CMAKE_CXX_STANDARD 17)

#set(CMAKE_CXX_FLAGS_DEBUG "-Og -g -Werror=uninitialized -Wall")
set(CMAKE_CXX_FLAGS_DEBUG "-Og -g")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -g -DNDEBUG -march=native -mtune=native")
#set(CMAKE_CXX_FLAGS_DEBUG "--coverage")
#set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")

message("CMAKE_BUILD_TYPE is ${CMAKE_BUILD_TYPE}")
message("CMAKE_CXX_FLAGS_DEBUG is ${CMAKE_CXX_FLAGS_DEBUG}")
message("CMAKE_CXX_FLAGS_RELEASE is ${CMAKE_CXX_FLAGS_RELEASE}")
message("CMAKE_CXX_FLAGS is ${CMAKE_CXX_FLAGS}")

if (NOT CMAKE_BUILD_TYPE)
    message(FATAL_ERROR "No CMAKE_BUILD_TYPE set!")
endif ()

#set(OGDF_DIR /home/user/OGDF/build-default)
find_package(OGDF REQUIRED)
#set(PCTree_DIR /home/user/PCTree/cmake-build-default)
find_package(PCTree REQUIRED)

file(GLOB SOURCE_FILES
        ${PROJECT_SOURCE_DIR}/src/*.cpp
        ${PROJECT_SOURCE_DIR}/src/operation/*.cpp
        ${PROJECT_SOURCE_DIR}/src/solve/*.cpp
        ${PROJECT_SOURCE_DIR}/src/utils/*.cpp)
#message("SOURCE_FILES are ${SOURCE_FILES}")

add_executable(profile-cplan src/exec/profile-cplan.cpp ${SOURCE_FILES})
target_include_directories(profile-cplan PRIVATE include lib)
target_link_libraries(profile-cplan PCTree OGDF bigInt)

add_executable(profile-pqplan src/exec/profile-pqplan.cpp ${SOURCE_FILES})
target_include_directories(profile-pqplan PRIVATE include lib)
target_link_libraries(profile-pqplan PCTree OGDF bigInt)

if (LIKWID_PERFMON)
    #set(likwid_DIR /home/user/likwid/install/share/likwid)
    if (TARGET likwid-library)
        message("LIKWID already loaded")
    else()
        message("Including LIKWID")
        find_package(likwid REQUIRED)
    endif()

    add_executable(profile-cplan-likwid src/exec/profile-cplan.cpp ${SOURCE_FILES})
    target_include_directories(profile-cplan-likwid PRIVATE include lib ${LIKWID_INCLUDE_DIR})
    target_compile_definitions(profile-cplan-likwid PUBLIC LIKWID_PERFMON=ON)
    target_link_libraries(profile-cplan-likwid PCTree OGDF bigInt likwid-library)
endif ()

add_executable(random-cplan src/exec/random-cplan.cpp ${SOURCE_FILES})
target_include_directories(random-cplan PRIVATE include lib)
target_link_libraries(random-cplan PCTree OGDF bigInt)

add_executable(random-pqplan src/exec/random-pqplan.cpp ${SOURCE_FILES})
target_include_directories(random-pqplan PRIVATE include lib)
target_link_libraries(random-pqplan PCTree OGDF bigInt)

add_executable(preprocess-cplan src/exec/preprocess-cplan.cpp ${SOURCE_FILES})
target_include_directories(preprocess-cplan PRIVATE include lib)
target_link_libraries(preprocess-cplan PCTree OGDF bigInt)

add_executable(make-cluster-index src/exec/make-cluster-index.cpp ${SOURCE_FILES})
target_include_directories(make-cluster-index PRIVATE include lib)
target_link_libraries(make-cluster-index PCTree OGDF bigInt)

add_executable(make-pq-index src/exec/make-pq-index.cpp ${SOURCE_FILES})
target_include_directories(make-pq-index PRIVATE include lib)
target_link_libraries(make-pq-index PCTree OGDF bigInt)

add_executable(pqplan src/exec/pqplan.cpp ${SOURCE_FILES})
target_include_directories(pqplan PRIVATE ${OGDF_DIR}/../src/) # help CLion to find the sources
target_include_directories(pqplan PRIVATE ${PCTree_DIR}/../src/) # help CLion to find the sources
target_include_directories(pqplan PRIVATE include lib)
target_link_libraries(pqplan PCTree OGDF bigInt)

add_executable(cplan src/exec/cplan.cpp ${SOURCE_FILES})
target_include_directories(cplan PRIVATE include lib)
target_link_libraries(cplan PCTree OGDF bigInt)
