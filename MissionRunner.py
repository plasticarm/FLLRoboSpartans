from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait

hub = PrimeHub()

# 1. IMU & Hardware Initialization
print("Calibrating Gyro - Keep robot still!")
wait(500)
hub.imu.reset_heading(0)

left_motor = Motor(Port.B, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.F)
drive_base = DriveBase(left_motor, right_motor, wheel_diameter=88, axle_track=107)
drive_base.settings(straight_speed=500, straight_acceleration=500, turn_rate=300, turn_acceleration=300)
drive_base.use_gyro(True)
yaw_correction_enabled = True

motor_a = Motor(Port.A)
motor_b = Motor(Port.E, Direction.COUNTERCLOCKWISE)

TURN_KP = 4.0
TURN_MIN_RATE = 35
TURN_TOLERANCE = 1

# 2. Autonomous Wrapper Functions
# These functions translate your controller's generated code into physical movements[cite: 2].

def Drive(speed, distance_cm):
    drive_base.settings(straight_speed=abs(speed))
    drive_base.straight(distance_cm * 10) 

def Rotate(speed, angle_deg):
    drive_base.stop()
    left_motor.hold()
    right_motor.hold()
    wait(100)

    drive_base.use_gyro(False)
    wait(100)
    hub.imu.reset_heading(0)
    wait(100)

    max_rate = abs(speed)
    min_rate = min(TURN_MIN_RATE, max_rate)
    while True:
        error = angle_deg - hub.imu.heading()
        if abs(error) <= TURN_TOLERANCE:
            break

        turn_rate = error * TURN_KP
        turn_rate = max(min(turn_rate, max_rate), -max_rate)

        if abs(turn_rate) < min_rate:
            turn_rate = min_rate if turn_rate > 0 else -min_rate

        drive_base.drive(0, turn_rate)
        wait(10)

    drive_base.stop()
    left_motor.hold()
    right_motor.hold()
    drive_base.use_gyro(yaw_correction_enabled)
    wait(100)

def LeftAttachmentRotate(speed, angle_deg):
    # Multiplies the 0-100 duty value by 10 to convert to degrees per second[cite: 2]
    motor_a.run_angle(abs(speed) * 10, angle_deg, wait=True)

def RightAttachmentRotate(speed, angle_deg):
    motor_b.run_angle(abs(speed) * 10, angle_deg, wait=True)

def ToggleYawCorrection(state):
    global yaw_correction_enabled
    yaw_correction_enabled = state
    drive_base.use_gyro(state)

def Stop():
    drive_base.stop()
    left_motor.hold()
    right_motor.hold()
    motor_a.stop()
    motor_b.stop()

# 3. Paste the generated python commands from your controller terminal here.

def run_recording():
    # --- PASTE RECORDING BELOW THIS LINE ---
    # ---------------------------------------
    Stop()

# 4. Run once when this program is started from its physical hub slot.
print("\n>>> Running recording...")
hub.imu.reset_heading(0)
wait(100)

run_recording()

print(">>> Recording finished.")
