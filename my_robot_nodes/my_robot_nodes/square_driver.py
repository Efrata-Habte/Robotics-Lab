"""
Drive the robot around a square with two action servers.

Each side is a /drive_distance goal, followed by a /rotate goal of a quarter turn to
the left. Each goal is sent only when the one before it has finished. Usage:
    ros2 run my_robot_nodes square_driver --ros-args -p side_length:=0.8
"""

import math

from action_msgs.msg import GoalStatus
from lab_interfaces.action import DriveDistance
from my_robot_interfaces.action import Rotate
from nav_msgs.msg import Odometry
import rclpy
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

SIDES = 4
QUARTER_TURN = math.pi / 2.0

STATUS_NAMES = {
    GoalStatus.STATUS_SUCCEEDED: 'succeeded',
    GoalStatus.STATUS_ABORTED: 'aborted',
    GoalStatus.STATUS_CANCELED: 'canceled',
}


class SquareDriver(Node):

    def __init__(self):
        super().__init__('square_driver')
        self.declare_parameter('side_length', 0.5)

        self.drive_client = ActionClient(self, DriveDistance, 'drive_distance')
        self.rotate_client = ActionClient(self, Rotate, 'rotate')

        self.have_odom = False
        self.create_subscription(Odometry, 'odom', self.on_odom, 10)

    def on_odom(self, msg):
        self.have_odom = True

    def wait_until_ready(self):
        """Wait for both action servers and for odometry, which they need too."""
        for name, client in (('drive_distance', self.drive_client),
                             ('rotate', self.rotate_client)):
            while not client.wait_for_server(timeout_sec=2.0):
                self.get_logger().info(f'Waiting for the /{name} action server...')
        while not self.have_odom:
            self.get_logger().info('Waiting for odometry...', throttle_duration_sec=2.0)
            rclpy.spin_once(self, timeout_sec=0.5)

    def plan(self, side_length):
        """List the goals for the whole square: a drive, then a turn, four times."""
        legs = []
        for side in range(1, SIDES + 1):
            drive = DriveDistance.Goal()
            drive.distance = side_length
            legs.append((side, f'drive {side_length:.2f} m', self.drive_client, drive))

            turn = Rotate.Goal()
            turn.angle = QUARTER_TURN
            legs.append((side, 'turn left 90 deg', self.rotate_client, turn))
        return legs

    def run_goal(self, client, goal):
        """Send one goal and block until it ends. Return its status."""
        send_future = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()
        if not goal_handle.accepted:
            return None

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        return result_future.result().status

    def drive_square(self):
        """Run every leg in turn. Return True if the whole square was driven."""
        side_length = self.get_parameter('side_length').value
        self.get_logger().info(f'Driving a square of {side_length:.2f} m a side')

        for side, label, client, goal in self.plan(side_length):
            self.get_logger().info(f'Side {side}/{SIDES}: {label}')
            status = self.run_goal(client, goal)
            if status != GoalStatus.STATUS_SUCCEEDED:
                outcome = 'rejected' if status is None else STATUS_NAMES.get(status, 'failed')
                self.get_logger().error(
                    f'Stopped on side {side}/{SIDES}: "{label}" was {outcome}')
                return False

        self.get_logger().info('Square complete')
        return True


def main():
    rclpy.init()
    node = SquareDriver()
    try:
        node.wait_until_ready()
        node.drive_square()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
