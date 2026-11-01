"""
Start diffdrive_bot in Gazebo with its nodes, plus rotate_server and square_driver.

Usage:
    ros2 launch my_robot_nodes square.launch.py side_length:=0.8
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    robot_launch = os.path.join(
        get_package_share_directory('diffdrive_bot'), 'launch', 'control.launch.py')

    side_length_arg = DeclareLaunchArgument(
        'side_length', default_value='0.5', description='Length of a side of the square, in m')
    side_length = ParameterValue(LaunchConfiguration('side_length'), value_type=float)

    # Gazebo, the bridge, RViz, and the obstacle detector, drive controller and
    # drive_distance action server
    robot = IncludeLaunchDescription(PythonLaunchDescriptionSource(robot_launch))

    rotate_server = Node(
        package='my_robot_nodes',
        executable='rotate_server',
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    square_driver = Node(
        package='my_robot_nodes',
        executable='square_driver',
        parameters=[{'side_length': side_length, 'use_sim_time': True}],
        output='screen',
    )

    return LaunchDescription([
        side_length_arg,
        robot,
        rotate_server,
        square_driver,
    ])
