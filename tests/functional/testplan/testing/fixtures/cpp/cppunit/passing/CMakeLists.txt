cmake_minimum_required(VERSION 2.6)

LIST(APPEND CMAKE_MODULE_PATH ".")

# Locate Cppunit
find_package(Cppunit REQUIRED)
include_directories(${CPPUNIT_INCLUDE_DIRS})

# Link runTests with what we want to test and the GTest and pthread library
add_executable(runTests tests.cpp)
target_link_libraries(runTests ${CPPUNIT_LIBRARIES} pthread)
