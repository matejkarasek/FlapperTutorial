import logging
import sys
import time
import select
import threading
import matplotlib.pyplot as plt

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

IS_WINDOWS = sys.platform.startswith('win')

if IS_WINDOWS:
    import msvcrt
else:
    import termios
    import tty

# Change the URI to match your Crazyflie's setup
URI = uri_helper.uri_from_env(default='radio://0/04/2M/FD00')

logging.basicConfig(level=logging.ERROR)

# Global variables for thread control and velocities
vx, vy, vz, yaw_rate = 0.0, 0.0, 0.0, 0.0
SPEED = 0.5
YAW_SPEED = 45.0
running = True

# Lists to store logged data for plotting
z_estimates = []
baro_pressures = []
timestamps = []
start_time = None


def log_data_callback(timestamp, data, logconf):
    global start_time
    if start_time is None:
        start_time = timestamp
    
    timestamps.append((timestamp - start_time) / 1000.0)
    z_estimates.append(data['stateEstimate.z'])
    baro_pressures.append(data['baro.pressure'])


def keyboard_listener_thread(linux_settings):
    """Dedicated thread to capture keys instantly without losing them."""
    global vx, vy, vz, yaw_rate, running
    
    while running:
        key = ''
        if IS_WINDOWS:
            if msvcrt.kbhit():
                try:
                    key = msvcrt.getch().decode('utf-8').lower()
                except UnicodeDecodeError:
                    pass
        else:
            # Linux / Pi VNC Input capture
            tty.setraw(sys.stdin.fileno())
            rlist, _, _ = select.select([sys.stdin], [], [], 0.02) # Fast polling
            if rlist:
                key = sys.stdin.read(1).lower()
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, linux_settings)

        if key:
            if key == 'w':      vx, vy, vz, yaw_rate = SPEED, 0.0, 0.0, 0.0
            elif key == 's':    vx, vy, vz, yaw_rate = -SPEED, 0.0, 0.0, 0.0
            elif key == 'a':    vx, vy, vz, yaw_rate = 0.0, SPEED, 0.0, 0.0
            elif key == 'd':    vx, vy, vz, yaw_rate = 0.0, -SPEED, 0.0, 0.0
            elif key == 'i':    vx, vy, vz, yaw_rate = 0.0, 0.0, SPEED, 0.0
            elif key == 'k':    vx, vy, vz, yaw_rate = 0.0, 0.0, -SPEED, 0.0
            elif key == 'j':    vx, vy, vz, yaw_rate = 0.0, 0.0, 0.0, YAW_SPEED
            elif key == 'l':    vx, vy, vz, yaw_rate = 0.0, 0.0, 0.0, -YAW_SPEED
            elif key == ' ':    vx, vy, vz, yaw_rate = 0.0, 0.0, 0.0, 0.0
            elif key == 'q':
                print("\nLanding initiated...")
                running = False
        
        time.sleep(0.01) # Keep the CPU happy


def plot_data():
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
    old_settings = None
    if not IS_WINDOWS:
        old_settings = termios.tcgetattr(sys.stdin)
    
    cflib.crtp.init_drivers()

    print("Connecting to Crazyflie...")
    try:
        with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
            
            log_config = LogConfig(name='AltitudeBaro', period_in_ms=100)
            log_config.add_variable('stateEstimate.z', 'float')
            log_config.add_variable('baro.pressure', 'float')
            
            scf.cf.log.add_config(log_config)
            log_config.data_received_cb.add_callback(log_data_callback)
            log_config.start()
            
            with MotionCommander(scf, default_height=0.4) as mc:
                print(f"\n--- Controls ({'Windows' if IS_WINDOWS else 'VNC/SSH'} Mode) ---")
                print("  W/S : Forward / Backward")
                print("  A/D : Left / Right")
                print("  I/K : Up / Down")
                print("  J/L : Turn Left / Turn Right")
                print("  SPACE: Stop / Hover")
                print("  Q   : Land and Exit")
                print("-------------------------------------")

                # Start the background keyboard grabber thread
                input_thread = threading.Thread(target=keyboard_listener_thread, args=(old_settings,))
                input_thread.daemon = True
                input_thread.start()

                # Main thread handles the strict 10Hz heartbeat to the Crazyflie
                while running:
                    mc.start_linear_motion(vx, vy, vz, yaw_rate)
                    time.sleep(0.1)

                log_config.stop()

        plot_data()

    finally:
        if not IS_WINDOWS and old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)