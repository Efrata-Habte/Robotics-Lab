"""
Action server /rotate: turn the robot on the spot through a given angle.

The angle is measured with the yaw from /odom. Try it with:
    ros2 action send_goal --feedback /rotate my_robot_interfaces/action/Rotate "{angle: 1.57}"
"""

import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

from my_robot_interfaces.action import Rotate

# How often the goal loop checks progress, in Hz
LOOP_RATE = 20.0


def yaw_of(q):
    """Heading in rad, about the z axis, of a quaternion."""
    siny = 2.0 * (q.w * q.z + q.x * q.y)
    cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny, cosy)


def wrap(angle):
    """Wrap an angle to [-pi, pi]."""
    return math.remainder(angle, 2.0 * math.pi)


class RotateServer(Node):

    def __init__(self):
        super().__init__('rotate_server')
        self.declare_parameter('turn_speed', 0.5)

        # Total angle the robot has turned since the node started, in rad. Each odometry
        # message adds the small change in yaw, so the jump from pi to -pi never shows up.
        self.total_turned = 0.0
        self.last_yaw = None
        self.busy = False

        # The goal loop blocks its thread, so odometry must be able to run in another
        # thread at the same time: a reentrant group with a MultiThreadedExecutor
        group = ReentrantCallbackGroup()
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_subscription(Odometry, 'odom', self.on_odom, 10, callback_group=group)
        self.server = ActionServer(
            self, Rotate, 'rotate',
            execute_callback=self.execute,
            goal_callback=self.on_goal,
            cancel_callback=self.on_cancel,
            callback_group=group,
        )
        self.get_logger().info('rotate_server ready')

    def on_odom(self, msg):
        yaw = yaw_of(msg.pose.pose.orientation)
        if self.last_yaw is not None:
            self.total_turned += wrap(yaw - self.last_yaw)
        self.last_yaw = yaw

    def on_goal(self, goal):
        if goal.angle == 0.0:
            self.get_logger().warn('Rejected: the angle must not be zero')
            return GoalResponse.REJECT
        if self.last_yaw is None:
            self.get_logger().warn('Rejected: no odometry received yet')
            return GoalResponse.REJECT
        if self.busy:
            self.get_logger().warn('Rejected: already turning')
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def on_cancel(self, goal_handle):
        return CancelResponse.ACCEPT

    def execute(self, goal_handle):
        self.busy = True
        try:
            return self.turn(goal_handle)
        finally:
            self.cmd_vel_pub.publish(Twist())
            self.busy = False

    def turn(self, goal_handle):
        target = goal_handle.request.angle
        direction = 1.0 if target > 0.0 else -1.0
        start = self.total_turned
        self.get_logger().info(f'Turning {target:.2f} rad')

        twist = Twist()
        feedback = Rotate.Feedback()
        result = Rotate.Result()
        rate = self.create_rate(LOOP_RATE)
        try:
            while rclpy.ok():
                turned = self.total_turned - start
                result.turned = turned

                if goal_handle.is_cancel_requested:
                    self.cmd_vel_pub.publish(Twist())
                    goal_handle.canceled()
                    self.get_logger().info(f'Canceled after {turned:.2f} rad')
                    return result
                if abs(turned) >= abs(target):
                    break

                # Read every loop, so ros2 param set takes effect during a turn
                twist.angular.z = direction * self.get_parameter('turn_speed').value
                self.cmd_vel_pub.publish(twist)
                feedback.turned = turned
                goal_handle.publish_feedback(feedback)
                rate.sleep()
        finally:
            self.destroy_rate(rate)

        self.cmd_vel_pub.publish(Twist())
        goal_handle.succeed()
        self.get_logger().info(f'Done, turned {result.turned:.2f} rad')
        return result


def main():
    rclpy.init()
    node = RotateServer()
    try:
        rclpy.spin(node, executor=MultiThreadedExecutor())
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
