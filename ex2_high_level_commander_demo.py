"""
EXAMPLE 2 - position commander demo

The script allows you to control the Flapper's XYZ and yaw states using the High-level Commander (cflib.crazyflie.high_level_commander)

The high-level commander is documented here:
https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/api/cflib/crazyflie/high_level_commander/
"""


'''
Usage of the High Level Commander:
--------------------------------------

Taking off and landing vertically from the current position to the given height:

  takeoff(absolute_height_m, duration_s, yaw=0.0)
  land(absolute_height_m, duration_s, yaw=0.0)
          
    Where:
      absolute_height_m: Absolute (m)
      duration_s: Time it should take until target height is reached (s)
      yaw: Yaw (rad). Use current yaw if set to None.

Going to an XYZ position with a specified yaw angle
  go_to(x, y, z, yaw, duration_s, relative=False, linear=False)
        
      Warning! Avoid overlapping go_to commands. When a command is sent to a
      Crazyflie when another one is currently executed, the generated polynomial
      can take unexpected routes and have high peaks.

      x: X (m)
      y: Y (m)
      z: Z (m)
      yaw: Yaw (radians)
      duration_s: Time it should take to reach the position (s)
      relative: True if x, y, z is relative to the current position
      linear: True to use linear interpolation instead of a smooth polynomial

Follow a spiral-like segment (spline approximation of a spiral/arc for <= 90-degree segments)
  spiral(angle, r0, rF, ascent, duration_s, sideways=False, clockwise=False):
      
      angle: spiral angle (rad), limited to +/- 2pi
      r0: initial radius (m), must be positive
      rF: final radius (m), must be positive
      ascent: altitude gain (m), positive to climb, negative to descent
      duration_s: time it should take to reach the end of the spiral (s)
      sideways: true if crazyflie should spiral sideways instead of forward
      clockwise: true if crazyflie should spiral clockwise instead of counter-clockwise

Stop the motors
  stop()
      
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


# Function to set an RGB color of the onboard LEDs and fade into it within the specified time
# -------------------------------------------------------------------------------------------
# - r: red component <0, 255> 
# - g: green component <0, 255> 
# - b: blue component <0, 255> 
# - intensity <0.0, 1.0>
# - time: fade effect duration in seconds

def set_RGB_color(scf, r, g, b, intensity, time):
    r *= intensity
    g *= intensity
    b *= intensity

    # set parameter "ring.fadeTime", expects a string as input
    scf.cf.param.set_value('ring.fadeTime', str(time))
  
    # use bit shift operations to get color in hexadecimal format 0xRRGGBB
    color = (int(r) << 16) | (int(g) << 8) | int(b)
    
    # set the color of the new RGB color 
    scf.param.set_value('ring.fadeColor', str(color))

def run_sequence(scf):
    commander = scf.cf.high_level_commander
    
    # We set onboard RGB leds to Blue, the fade effect will take 2 seconds
    set_RGB_color(scf, 0, 0, 255, 1, 2)
    
    # We wait for 2 seconds
    time.sleep(2.0)
    
    # We take off from the current position to a height of 1m, taking 2 seconds to reach the target height
    takeoff_yaw = 0.0
    commander.takeoff(1.0, 2.0, yaw=takeoff_yaw)
    time.sleep(3.0)
    
    # We go to absulute position [1, 0, 1] in 2 seconds
    commander.go_to(1.0, 0.0, 1.0, 0.0, 2)
    time.sleep(3.0)

    # We go back, but this time with a constant velocity 
    commander.go_to(0.0, 0.0, 1.0, 0.0, 2, linear = True)
    time.sleep(3.0)

    # We turn 90 degrees
    commander.go_to(0.0, 0.0, 0.0, pi/2, 2, relative = True)
    time.sleep(3.0)
    
    # We make a circle with radius 0.5 m (composed of four 90-deg segments, each taking 1 second)
    for i in range(4):
      commander.spiral(pi/2, 0.5, 0.5, 0, 1, sideways=False, clockwise=False)
      time.sleep(1.0)
    
    # We make a spiral with a 0.5 m start radius and 0.75 m end radius, while climbing 0.5 m. The drone will fly sideways
    commander.spiral(2*pi, 0.5, 0.75, 0.5, 4, sideways=True, clockwise=False)
    time.sleep(2.0)
    
    # We go to [0, 0, 1] position and 0 deg yaw angle
    commander.go_to(0.0, 0.0, 1.0, 0.0, 2)
    time.sleep(3.0)
    
    # We land
    commander.land(0.0, 4.0)
    time.sleep(4.0)
    
    # Stop the motors just to be safe
    commander.stop()


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
                
        reset_estimator(scf.cf)
        run_sequence(scf)
