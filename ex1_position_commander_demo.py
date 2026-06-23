"""
EXAMPLE 1 - position commander demo

The script allows you to control the Flapper in XYZ directions using the Position Commander (cflib.positioning.position_hl_commander)
The example is based on this script: 
https://github.com/bitcraze/crazyflie-demos/blob/main/demos/scripts/cflib/autonomy/position_commander_demo/position_commander_demo.py
And uses the position HL commander documented here:
https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/api/cflib/positioning/position_hl_commander/
"""


"""
Basic usage of the Position Commander:
--------------------------------------

Going left, right, forward, back, up and down (relative to the latest setpoint):
  pc.left(distance_m, velocity=DEFAULT):
  pc.right(distance_m, velocity=DEFAULT):
  pc.forward(distance_m, velocity=DEFAULT):
  pc.back(distance_m, velocity=DEFAULT):
  pc.up(distance_m, velocity=DEFAULT):
  pc.down(distance_m, velocity=DEFAULT):

  Where:
    distance_m: The distance to travel (meters)
    velocity: The velocity of the motion (meters/second). If not given, the default velocity is used. 
  
Moving in a straight line (relative to the latest setpoint):
  pc.move_distance(distance_x_m, distance_y_m, distance_z_m, velocity=DEFAULT):

  Where:
    distance_x_m: The distance to travel along the X-axis (meters)
    distance_y_m: The distance to travel along the Y-axis (meters)
    distance_z_m: The distance to travel along the Z-axis (meters)
    velocity: The velocity of the motion (meters/second)

Going to an absolute position:
  pc.go_to(x, y, z=DEFAULT, velocity=DEFAULT):

  Where:
    x: X coordinate
    y: Y coordinate
    z: Z coordinate
    velocity: The velocity (meters/second)

The default velocity can be set using:
  pc.set_default_velocity(velocity)

  Where:
    velocity: The default velocity (meters/second)

The default height can be set using:
  pc.set_default_height(height)

  Where:
    height: The default height (meters)

"""

# Libraries we need
import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.utils import uri_helper

# URI (Uniform Resource Identifier) of the Flapper in the format "radio://[radio_dongle_ID]/[radio_channel]/[bitrate]/[address]"
uri = 'radio://0/04/2M/FD00'


def slightly_more_complex_usage():
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        time.sleep(1.0)

        with PositionHlCommander(
                scf,
                x=0.0, y=0.0, z=0.0,
                default_velocity=0.3,
                default_height=0.5,
                controller=PositionHlCommander.CONTROLLER_PID) as pc:
            
            # Go to a xyz coordinate
            pc.go_to(1.0, 1.0, 1.0)

            # Move relative to the current position
            pc.right(1.0)

            # Go to a coordinate and use default height
            pc.go_to(0.0, 0.0)

            # Go slowly to a coordinate
            pc.go_to(1.0, 1.0, velocity=0.2)

            # Set new default velocity and height
            pc.set_default_velocity(0.3)
            pc.set_default_height(1.0)
            pc.go_to(0.0, 0.0)

            # Use a for loop to got back and forth twice
            for i in range(2):
                pc.forward(1.0)
                time.sleep(1.0)
                pc.back(1.0)
                time.sleep(1.0)
            
            # Set a low velocity for a smoother landing
            pc.set_default_velocity(0.3)
            # The flapper will land when the position commander exits


def simple_sequence():
    # We create a synchronous Crazyflie instance for the Flapper with the specified URI
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        time.sleep(1.0)

        # In this example, position high-level commander is used
        with PositionHlCommander(scf, controller=PositionHlCommander.CONTROLLER_PID) as pc:
            # The flapper will take off once the position commander is initialized
            
            # We can add a pause to let the flapper hover for 2 seconds before starting the sequence
            time.sleep(2) 

            # Move the flapper in a square pattern  
            pc.forward(1)
            pc.left(1)
            pc.back(1)
            pc.right(1)
            
            time.sleep(2)
            
            # Climb up 1 meter
            pc.up(1.0)

            time.sleep(2)
            
            # Set a low velocity for a smoother landing
            pc.set_default_velocity(0.3) 
            
            # The flapper will land when the position commander exits


if __name__ == '__main__':
    # initialize the communication drivers
    cflib.crtp.init_drivers()

    # run the example sequence
    simple_sequence()
    # slightly_more_complex_usage()
