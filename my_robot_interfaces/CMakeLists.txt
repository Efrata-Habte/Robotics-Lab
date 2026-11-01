cmake_minimum_required(VERSION 3.10)
project(my_robot_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# Step 6 adds "action/Rotate.action" to this list
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/RobotStatus.msg"
  "srv/SetTurnSpeed.srv"
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
