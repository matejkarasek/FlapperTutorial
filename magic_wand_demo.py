'''
Example of a swarm sharing data and performing a leader-follower scenario
using the motion commander.

The swarm takes off and the drones hover until the follower's local coordinate
system is aligned with the global one. Then, the leader performs its own
trajectory based on commands from the motion commander. The follower is
constantly commanded to keep a defined distance from the leader, meaning that
it is moving towards the leader when their current distance is larger than the
defined one and away from the leader in the opposite scenario.
All movements refer to the local coordinate system of each drone.

This example is intended to work with an absolute positioning system, it has
been tested with the lighthouse positioning system.

This example aims at documenting how to use the collected data to define new
trajectories in real-time. It also indicates how to use the swarm class to
feed the Crazyflies completely different asynchronized trajectories in parallel.

The example is based on the following script:
https://github.com/bitcraze/crazyflie-demos/blob/main/demos/scripts/cflib/swarm/leader_follower/leader_follower.py
'''
import math
import time

import cflib.crtp
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm
from cflib.positioning.motion_commander import MotionCommander

import matplotlib.pyplot as plt

# Change uris according to your setup, both need to be on the same radio channel and datarate
URI_Flapper = 'radio://0/04/2M/FD04'  # Flapper
URI_Magic_Wand = 'radio://0/04/2M/CF00'  # Magic Wand

flight_duration = 40

DEFAULT_HEIGHT = 0.5
DEFAULT_VELOCITY = 0.5
xF = []
yF = []
zF = []
rollF = []
pitchF = []
yawF = []
timeF = []

xMW = []
yMW = []
zMW = []
rollMW = []
pitchMW = []
yawMW = []
timeMW = []

# List of URIs
uris = {
    URI_Flapper,
    URI_Magic_Wand,
}

global time_start

def pose_callback(uri, data):
    if timeMW == [] and timeF == []:
        global time_start
        time_start = time.time()
    if uri == URI_Flapper:  # Flapper
        xF.append(data['stateEstimate.x'])
        yF.append(data['stateEstimate.y'])
        zF.append(data['stateEstimate.z'])
        rollF.append(data['stateEstimate.roll'])
        pitchF.append(data['stateEstimate.pitch'])
        yawF.append(data['stateEstimate.yaw'])
        timeF.append(time.time()-time_start)
    elif uri == URI_Magic_Wand:  # Magic_Wand
        xMW.append(data['stateEstimate.x'])
        yMW.append(data['stateEstimate.y'])
        zMW.append(data['stateEstimate.z'])
        rollMW.append(data['stateEstimate.roll'])
        pitchMW.append(data['stateEstimate.pitch'])
        yawMW.append(data['stateEstimate.yaw'])
        timeMW.append(time.time()-time_start)


def start_pose_logging(scf):
    log_conf1 = LogConfig(name='Pose', period_in_ms=20)
    log_conf1.add_variable('stateEstimate.x', 'float')
    log_conf1.add_variable('stateEstimate.y', 'float')
    log_conf1.add_variable('stateEstimate.z', 'float')
    log_conf1.add_variable('stateEstimate.roll', 'float')
    log_conf1.add_variable('stateEstimate.pitch', 'float')
    log_conf1.add_variable('stateEstimate.yaw', 'float')
    scf.cf.log.add_config(log_conf1)
    log_conf1.data_received_cb.add_callback(lambda _timestamp, data, _logconf: pose_callback(scf.cf.link_uri, data))
    log_conf1.start()


def follow(scf):
    uri = scf.__dict__['_link_uri']

    if uri == URI_Flapper:
        
        # Get initial offset between the Magic_Wand and the Flapper
        dx = xF[-1] - xMW[-1]
        dy = yF[-1] - yMW[-1]
        dz = zF[-1] - zMW[-1]

        print("Initial offset for Flapper: ", dx, dy, dz)
        
        # We will control the Flapper with Motion Commander
        with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
            end_time = time.time() + flight_duration

            while time.time() < end_time:
                # Desired position = latest Magic_Wand position + offset
                x_desired = xMW[-1] + dx
                y_desired = yMW[-1] + dy
                z_desired = max(zMW[-1] + dz, DEFAULT_HEIGHT) # assures minimal flight height at least 0.5 m

                # Position error = latest Flapper position - desired position
                error_x = x_desired - xF[-1]
                error_y = y_desired - yF[-1]
                error_z = z_desired - zF[-1]

                # Proportional gain: 1m error ==> 2 m/s desired velocity
                Kp = 2 # control loop will get unstable if too high

                # Desired velocity in world coordinates
                v_world_x = error_x * Kp
                v_world_y = error_y * Kp
                v_world_z = error_z * Kp

                # Keep the velocity within bounds <-max_vel, max_vel>
                max_vel = 2
                v_world_x = max(-max_vel, min(max_vel, v_world_x))
                v_world_y = max(-max_vel, min(max_vel, v_world_y))
                v_world_z = max(-max_vel, min(max_vel, v_world_z))

                # Transform into body coordinates
                current_yaw = yawF[-1]
                cos_yaw = math.cos(math.radians(current_yaw))
                sin_yaw = math.sin(math.radians(current_yaw))
                
                v_body_x = v_world_x * cos_yaw + v_world_y * sin_yaw
                v_body_y = -v_world_x * sin_yaw + v_world_y * cos_yaw
                v_body_z = v_world_z  # no change here

                mc.start_linear_motion(v_body_x, v_body_y, v_body_z)
                
                time.sleep(0.02)  # loop at 50 Hz
            
            mc.stop()
            mc.land()

    elif uri == URI_Magic_Wand:
        # Magic_Wand is handheld, so we only need to keep the loop active
        end_time = time.time() + flight_duration
        while time.time() < end_time:
            time.sleep(0.1)
        print("Magic_Wand loop finished.")

def plot_data():
  fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 6), sharex=True)

  ax1.plot(timeF, xF, label='Flapper', color='blue')
  ax1.plot(timeMW, xMW, label='Magic_Wand', color='orange')
  ax1.legend()
  ax1.set_ylabel('X Position (m)')
  
  ax2.plot(timeF, yF, color='blue')
  ax2.plot(timeMW, yMW, color='orange')
  ax2.set_ylabel('Y Position (m)')

  ax3.plot(timeF, zF, color='blue')
  ax3.plot(timeMW, zMW, color='orange')
  ax3.set_ylabel('Z Position (m)')

  ax3.set_xlabel('Time (s)')
  
  plt.show()

if __name__ == '__main__':
    cflib.crtp.init_drivers()

    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:

        swarm.reset_estimators()

        swarm.parallel_safe(start_pose_logging)
        time.sleep(1)

        swarm.parallel_safe(follow)
        time.sleep(1)

    plot_data()
    