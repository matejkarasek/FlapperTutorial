import logging
import time
import matplotlib.pyplot as plt
from pynput import keyboard

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

# Change the URI to match your Crazyflie's setup
URI = uri_helper.uri_from_env(default='radio://0/04/2M/FD00')

logging.basicConfig(level=logging.ERROR)

# Global variables for control
vx, vy, vz, yaw_rate = 0.0, 0.0, 0.0, 0.0
SPEED = 0.5
YAW_SPEED = 45.0

# Lists to store logged data for plotting
z_estimates = []
baro_pressures = []
timestamps = []
start_time = None


def log_data_callback(timestamp, data, logconf):
    """Callback function triggered whenever new log data arrives."""
    global start_time
    if start_time is None:
        start_time = timestamp
    
    # Store the data
    timestamps.append((timestamp - start_time) / 1000.0)  # Convert to seconds
    z_estimates.append(data['stateEstimate.z'])
    baro_pressures.append(data['baro.pressure'])


def on_press(key):
    global vx, vy, vz, yaw_rate
    try:
        if key.char == 'w':      vx = SPEED
        elif key.char == 's':    vx = -SPEED
        elif key.char == 'a':    vy = SPEED
        elif key.char == 'd':    vy = -SPEED
        elif key.char == 'i':    vz = SPEED
        elif key.char == 'k':    vz = -SPEED
        elif key.char == 'j':    yaw_rate = YAW_SPEED
        elif key.char == 'l':    yaw_rate = -YAW_SPEED
    except AttributeError:
        pass


def on_release(key):
    global vx, vy, vz, yaw_rate
    try:
        if key.char in ['w', 's']:   vx = 0.0
        elif key.char in ['a', 'd']: vy = 0.0
        elif key.char in ['i', 'k']: vz = 0.0
        elif key.char in ['j', 'l']: yaw_rate = 0.0
    except AttributeError:
        if key == keyboard.Key.esc:
            print("Escape pressed. Landing...")
            return False


def plot_data():
    """Generates the plots after landing."""
    if not z_estimates:
        print("No data collected to plot.")
        return

    print("Generating plots...")
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Plot State Estimate Z on the left Y-axis
    color = 'tab:blue'
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('State Estimate Z (m)', color=color)
    ax1.plot(timestamps, z_estimates, color=color, label='Z Estimate')
    ax1.tick_params(axis='y', labelcolor=color)

    # Create a secondary Y-axis to plot Barometric Pressure
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Baro Pressure (hPa)', color=color)
    ax2.plot(timestamps, baro_pressures, color=color, linestyle='--', label='Baro Pressure')
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title('Flapper Height vs Barometric Pressure Over Time')
    fig.tight_layout()
    plt.show()


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    print("Connecting to Flapper...")
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        
        # 1. Set up the Log Configuration
        log_config = LogConfig(name='AltitudeBaro', period_in_ms=100) # 10Hz logging
        log_config.add_variable('stateEstimate.z', 'float')
        log_config.add_variable('baro.pressure', 'float')
        
        # 2. Register the callback and start logging
        scf.cf.log.add_config(log_config)
        log_config.data_received_cb.add_callback(log_data_callback)
        log_config.start()
        
        # 3. Enter flight control loop
        with MotionCommander(scf, default_height=0.4) as mc:
            print("\n--- Controls ---")
            print("  W/S : Forward / Backward")
            print("  A/D : Left / Right")
            print("  I/K : Up / Down")
            print("  J/L : Turn Left / Turn Right")
            print("  ESC : Land and Exit")
            print("----------------")

            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.start()

            while listener.running:
                mc.start_linear_motion(vx, vy, vz, yaw_rate)
                time.sleep(0.1)

            print("Control loop finished. Clean landing initiated...")
        
        # 4. Stop logging after landing
        log_config.stop()

    # 5. Plot the data after the communication blocks are closed and drone is safe
    plot_data()