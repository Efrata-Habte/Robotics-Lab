"""
Drive forward and turn on the spot, away from obstacles reported on /obstacle.

The node starts switched off; switch it on with the /turn_away_enable service:
    ros2 service call /turn_away_enable std_srvs/srv/SetBool "{data: true}"
"""

from geometry_msgs.msg import Twist
from lab_interfaces.msg import ObstacleInfo
from my_robot_interfaces.msg import RobotStatus
from my_robot_interfaces.srv import SetTurnSpeed
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_srvs.srv import SetBool

FORWARD = 'forward'
TURNING = 'turning'
STOPPED = 'stopped'


def choose_motion(obstacle, forward_speed, turn_speed):
    """Return the state and the velocity for one obstacle message."""
    twist = Twist()
    if not obstacle.too_close:
        twist.linear.x = forward_speed
        return FORWARD, twist
    # A positive angle means the obstacle is on the left, so turn right (negative z)
    twist.angular.z = -turn_speed if obstacle.angle > 0.0 else turn_speed
    return TURNING, twist


class TurnAway(Node):

    def __init__(self):
        super().__init__('turn_away')
        self.declare_parameter('forward_speed', 0.2)
        self.declare_parameter('turn_speed', 0.5)
        self.declare_parameter('max_turn_speed', 1.5)

        self.enabled = False

        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.status_pub = self.create_publisher(RobotStatus, 'robot_status', 10)
        self.create_subscription(ObstacleInfo, 'obstacle', self.on_obstacle, 10)
        self.create_service(SetBool, 'turn_away_enable', self.on_enable)
        self.create_service(SetTurnSpeed, 'set_turn_speed', self.on_set_turn_speed)

        self.get_logger().info('turn_away ready, switched off')

    def on_obstacle(self, obstacle):
        if self.enabled:
            # Read on every message, so ros2 param set takes effect at once
            forward_speed = self.get_parameter('forward_speed').value
            turn_speed = self.get_parameter('turn_speed').value
            state, twist = choose_motion(obstacle, forward_speed, turn_speed)
            self.cmd_vel_pub.publish(twist)
        else:
            # While off, publish no velocity so other nodes can drive the robot
            state = STOPPED

        status = RobotStatus()
        status.state = state
        status.obstacle_distance = obstacle.distance
        self.status_pub.publish(status)

    def on_enable(self, request, response):
        if request.data:
            self.enabled = True
            response.message = 'turn_away switched on'
        else:
            if self.enabled:
                # One zero velocity, so the robot does not keep its last command
                self.cmd_vel_pub.publish(Twist())
            self.enabled = False
            response.message = 'turn_away switched off'
        response.success = True
        self.get_logger().info(response.message)
        return response

    def on_set_turn_speed(self, request, response):
        max_turn_speed = self.get_parameter('max_turn_speed').value
        speed = request.turn_speed
        if 0.0 < speed <= max_turn_speed:
            self.set_parameters([Parameter('turn_speed', value=float(speed))])
            response.success = True
            response.message = f'turn speed set to {speed:.2f} rad/s'
        else:
            response.success = False
            response.message = (
                f'rejected {speed:.2f} rad/s: must be above 0 and at most '
                f'{max_turn_speed:.2f} rad/s')
        self.get_logger().info(response.message)
        return response


def main():
    rclpy.init()
    node = TurnAway()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
