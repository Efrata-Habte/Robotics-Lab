cmake_minimum_required(VERSION 3.10)
project(my_robot_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# Each step adds its file to this list:
#   Step 4: "msg/RobotStatus.msg"
#   Step 5: "srv/SetTurnSpeed.srv"
#   Step 6: "action/Rotate.action"
# rosidl_generate_interfaces(${PROJECT_NAME}
# )

ament_export_dependencies(rosidl_default_runtime)
ament_package()
