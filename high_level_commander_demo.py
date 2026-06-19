"""
Simple example that connects to one crazyflie (check the address at the top
and update it to your crazyflie address) and uses the high level commander
to send setpoints and trajectory to fly a figure 8.

This example is intended to work with any positioning system (including LPS).
It aims at documenting how to set the Crazyflie in position control mode
and how to send setpoints using the high level commander.
"""

'''
Vertical takeoff from current x-y position to given height

takeoff(absolute_height_m, duration_s, yaw=0.0)
        
  Where:
    absolute_height_m: Absolute (m)
    duration_s: Time it should take until target height is reached (s)
    yaw: Yaw (rad). Use current yaw if set to None.
        
land(self, absolute_height_m, duration_s, group_mask=ALL_GROUPS,
             yaw=0.0):
        """
        vertical land from current x-y position to given height

        :param absolute_height_m: Absolute (m)
        :param duration_s: Time it should take until target height is
                           reached (s)
        :param group_mask: Mask for which CFs this should apply to
        :param yaw: Yaw (rad). Use current yaw if set to None.
        """
        target_yaw = yaw
        useCurrentYaw = False
        if yaw is None:
            target_yaw = 0.0
            useCurrentYaw = True

        self._send_packet(struct.pack('<BBff?f',
                                      self.COMMAND_LAND_2,
                                      group_mask,
                                      absolute_height_m,
                                      target_yaw,
                                      useCurrentYaw,
                                      duration_s))

    def stop(self, group_mask=ALL_GROUPS):
        """
        stops the current trajectory (turns off the motors)

        :param group_mask: Mask for which CFs this should apply to
        :return:
        """
        self._send_packet(struct.pack('<BB',
                                      self.COMMAND_STOP,
                                      group_mask))

    def go_to(self, x, y, z, yaw, duration_s, relative=False, linear=False,
              group_mask=ALL_GROUPS):
        """
        Go to an absolute or relative position.

        The path is designed to transition smoothly from the current
        state to the target position, gradually decelerating at the
        goal with minimal overshoot. When the system is at hover, the
        path will be a straight line, but if there is any initial
        velocity, the path will be a smooth curve.

        The trajectory is derived by solving for a unique 7th-degree
        polynomial that satisfies the initial conditions of position,
        velocity, and acceleration, and ends at the goal with zero
        velocity and acceleration. Additionally, the jerk (derivative
        of acceleration) is constrained to be zero at both the starting
        and ending points.

        Warning! Avoid overlapping go_to commands. When a command is sent to a
        Crazyflie when another one is currently executed, the generated polynomial
        can take unexpected routes and have high peaks.

        :param x: X (m)
        :param y: Y (m)
        :param z: Z (m)
        :param yaw: Yaw (radians)
        :param duration_s: Time it should take to reach the position (s)
        :param relative: True if x, y, z is relative to the current position
        :param linear: True to use linear interpolation instead of a smooth polynomial
        :param group_mask: Mask for which CFs this should apply to
        """
        if self._cf.platform.get_protocol_version() < 8:
            if linear:
                print('Warning: Linear mode not supported in protocol version < 8, update your crazyflie\'s firmware')
            self._send_packet(struct.pack('<BBBfffff',
                                          self.COMMAND_GO_TO,
                                          group_mask,
                                          relative,
                                          x, y, z,
                                          yaw,
                                          duration_s))
        else:
            self._send_packet(struct.pack('<BBBBfffff',
                                          self.COMMAND_GO_TO_2,
                                          group_mask,
                                          relative,
                                          linear,
                                          x, y, z,
                                          yaw,
                                          duration_s))

    def spiral(self, angle, r0, rF, ascent, duration_s, sideways=False, clockwise=False,
               group_mask=ALL_GROUPS):
        """
        Follow a spiral-like segment (spline approximation of a spiral/arc for <= 90-degree segments)

        :param angle: spiral angle (rad), limited to +/- 2pi
        :param r0: initial radius (m), must be positive
        :param rF: final radius (m), must be positive
        :param ascent: altitude gain (m), positive to climb, negative to descent
        :param duration_s: time it should take to reach the end of the spiral (s)
        :param sideways: true if crazyflie should spiral sideways instead of forward
        :param clockwise: true if crazyflie should spiral clockwise instead of counter-clockwise
        :param group_mask: Mask for which CFs this should apply to
        """
        if self._cf.platform.get_protocol_version() < 8:
            print('Warning: Spiral command is not supported in protocol version < 8, update your crazyflie\'s firmware')
        else:
            if angle > 2*math.pi:
                angle = 2*math.pi
                print('Warning: Spiral angle saturated at 2pi as it was too large')
            elif angle < -2*math.pi:
                angle = -2*math.pi
                print('Warning: Spiral angle saturated at -2pi as it was too small')
            if r0 < 0:
                r0 = 0
                print('Warning: Initial radius set to 0 as it cannot be negative')
            if rF < 0:
                rF = 0
                print('Warning: Final radius set to 0 as it cannot be negative')
            self._send_packet(struct.pack('<BBBBfffff',
                                          self.COMMAND_SPIRAL,
                                          group_mask,
                                          sideways,
                                          clockwise,
                                          angle,
                                          r0, rF,
                                          ascent,
                                          duration_s))
            
'''
            
import argparse
import sys
import time
from math import pi

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.mem import MemoryElement
from cflib.crazyflie.mem import Poly4D
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper
from cflib.utils.reset_estimator import reset_estimator

# URI to the Crazyflie to connect to
# uri = uri_helper.uri_from_env(default='radio://0/04/2M/FD04')
uri = 'radio://0/04/2M/FD04'

def run_sequence(scf):
    commander = scf.cf.high_level_commander
    
    
    takeoff_yaw = 0.0
    commander.takeoff(1.0, 2.0, yaw=takeoff_yaw)
    time.sleep(3.0)
    commander.go_to(1.0, 0.0, 1.0, 0.0, 2)
    time.sleep(3.0)
    commander.go_to(0.0, 0.0, 1.0, 0.0, 2, linear = True)
    time.sleep(3.0)
    commander.go_to(0.0, 0.0, 1.0, pi/2, 2, linear = True)
    time.sleep(3.0)
    commander.spiral(pi/2, 0.5, 1, -0.3, 1, sideways=False, clockwise=False)
    time.sleep(2.0)
    commander.spiral(pi/2, 0.5, 1, 0, 1, sideways=True, clockwise=False)
    time.sleep(2.0)
    commander.go_to(0.0, 0.0, 1.0, 0.0, 2)
    time.sleep(3.0)
    commander.land(0.0, 4.0)
    time.sleep(4.0)
    commander.stop()


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
                
        reset_estimator(scf.cf)
        run_sequence(scf)
