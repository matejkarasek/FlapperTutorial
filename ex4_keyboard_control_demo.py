import logging
import sys
import termios
import tty
import time
import select
import matplotlib.pyplot as plt

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

# Change the URI to match your Crazyflie's setup
URI = uri_helper.uri_from_env(default='radio://0/08/2M/FD17')

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
    
    timestamps.append((timestamp - start_time) / 1000.0)  # Convert to seconds
    z_estimates.append(data['stateEstimate.z'])
    baro_pressures.append(data['baro.pressure'])


def get_key(settings):
    """Reads a single keypress from the terminal without blocking."""
    tty.setraw(sys.stdin.fileno())
    # Wait up to 0.05 seconds for input
    rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def plot_data():
    """Generates the plots after landing."""
    if not z_estimates:
        print("No data collected to plot.")
        return

    print("\nGenerating plots...")
    fig, ax1 = plt.subplots(figsize=(10, 5))

    color = 'tab:blue'
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('State Estimate Z (m)', color=color)
    ax1.plot(timestamps, z_estimates, color=color, label='Z Estimate')
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Baro Pressure (hPa)', color=color)
    ax2.plot(timestamps, baro_pressures, color=color, linestyle='--', label='Baro Pressure')
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title('Crazyflie Altitude vs Barometric Pressure Over Time')
    fig.tight_layout()
    plt.show()


if __name__ == '__main__':
    # Save the original terminal settings so we can restore them later
    old_settings = termios.tcgetattr(sys.stdin)
    
    cflib.crtp.init_drivers()

    print("Connecting to Flapper...")
    try:
        with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
            
            # Set up the Log Configuration
            log_config = LogConfig(name='AltitudeBaro', period_in_ms=100)
            log_config.add_variable('stateEstimate.z', 'float')
            log_config.add_variable('baro.pressure', 'float')
            
            scf.cf.log.add_config(log_config)
            log_config.data_received_cb.add_callback(log_data_callback)
            log_config.start()
            
            with MotionCommander(scf, default_height=0.4) as mc:
                print("\n--- Controls (VNC/SSH Compatible) ---")
                print("  W/S : Forward / Backward")
                print("  A/D : Left / Right")
                print("  I/K : Up / Down")
                print("  J/L : Turn Left / Turn Right")
                print("  SPACE: Stop / Hover")
                print("  Q   : Land and Exit")
                print("-------------------------------------")

                running = True
                while running:
                    # Capture the key inside the active loop
                    key = get_key(old_settings)
                    
                    if key == 'w':      vx, vy, vz, yaw_rate = SPEED, 0.0, 0.0, 0.0
                    elif key == 's':    vx, vy, vz, yaw_rate = -SPEED, 0.0, 0.0, 0.0
                    elif key == 'a':    vx, vy, vz, yaw_rate = 0.0, SPEED, 0.0, 0.0
                    elif key == 'd':    vx, vy, vz, yaw_rate = 0.0, -SPEED, 0.0, 0.0
                    elif key == 'i':    vx, vy, vz, yaw_rate = 0.0, 0.0, SPEED, 0.0
                    elif key == 'k':    vx, vy, vz, yaw_rate = 0.0, 0.0, -SPEED, 0.0
                    elif key == 'j':    vx, vy, vz, yaw_rate = 0.0, 0.0, 0.0, YAW_SPEED
                    elif key == 'l':    vx, vy, vz, yaw_rate = 0.0, 0.0, 0.0, -YAW_SPEED
                    elif key == ' ':    vx, vy, vz, yaw_rate = 0.0, 0.0, 0.0, 0.0 # Spacebar to hover
                    elif key == 'q':    # 'q' key to land safely
                        print("\nLanding initiated...")
                        running = False

                    mc.start_linear_motion(vx, vy, vz, yaw_rate)
                    time.sleep(0.1)  # 10Hz control cycle

                log_config.stop()

        # Show the plot once the drone is landed and disconnected
        plot_data()

    finally:
        # Always restore original terminal settings even if the script crashes
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)