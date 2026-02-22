cmake_minimum_required(VERSION 3.10)
project(sumo_test)

find_package(Webots REQUIRED)

add_executable(sumo_test sumo_test.cpp)
target_link_libraries(sumo_test ${WEBOTS_LIBRARIES})
