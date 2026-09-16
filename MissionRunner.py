from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Button, Color
from pybricks.robotics import DriveBase
from pybricks.tools import wait

hub = PrimeHub()

# 1. IMU & Hardware Initialization
print("Calibrating Gyro - Keep robot still!")
wait(500)
hub.imu.reset_heading(0)

left_motor = Motor(Port.B, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.F)
drive_base = DriveBase(left_motor, right_motor, wheel_diameter=56, axle_track=112)
drive_base.settings(straight_speed=500, straight_acceleration=500, turn_rate=300, turn_acceleration=300)

motor_a = Motor(Port.A)
motor_b = Motor(Port.E, Direction.COUNTERCLOCKWISE)

# 2. Autonomous Wrapper Functions
# These functions translate your controller's generated code into physical movements[cite: 2].

def Drive(speed, distance_cm):
    drive_base.settings(straight_speed=abs(speed))
    drive_base.straight(distance_cm * 10) 

def Rotate(speed, angle_deg):
    drive_base.settings(turn_rate=abs(speed))
    drive_base.turn(angle_deg)

def LeftAttachmentRotate(speed, angle_deg):
    # Multiplies the 0-100 duty value by 10 to convert to degrees per second[cite: 2]
    motor_a.run_angle(abs(speed) * 10, angle_deg, wait=True)

def RightAttachmentRotate(speed, angle_deg):
    motor_b.run_angle(abs(speed) * 10, angle_deg, wait=True)

def ToggleYawCorrection(state):
    drive_base.use_gyro(state)

def Stop():
    drive_base.stop()
    left_motor.hold()
    right_motor.hold()

# 3. Mission Slot Definitions
# Paste the generated python commands from your controller terminal directly into these functions.

def run_slot_1():
    hub.display.char("1")
    # --- PASTE RECORDING 1 BELOW THIS LINE ---
    ToggleYawCorrection(True)
    Drive(120, 35)
    Rotate(40, 90)
    LeftAttachmentRotate(100, 180)
    # -----------------------------------------
    Stop()

def run_slot_2():
    hub.display.char("2")
    # --- PASTE RECORDING 2 BELOW THIS LINE ---
    
    # -----------------------------------------
    Stop()

def run_slot_3():
    hub.display.char("3")
    # --- PASTE RECORDING 3 BELOW THIS LINE ---
    
    # -----------------------------------------
    Stop()

# Map the functions to a dictionary for the menu
missions = {
    1: run_slot_1,
    2: run_slot_2,
    3: run_slot_3
}

# 4. Hub Menu Interface
selected_slot = 1
hub.display.number(selected_slot)

prev_hub_left = False
prev_hub_right = False
prev_hub_center = False

print("\n>>> Master Program Ready. Select a slot and press Center to run.")

while True:
    hub_pressed = hub.buttons.pressed()
    hub_left_pressed = Button.LEFT in hub_pressed
    hub_right_pressed = Button.RIGHT in hub_pressed
    hub_center_pressed = Button.CENTER in hub_pressed

    # Cycle Next Slot
    if hub_right_pressed and not prev_hub_right:
        selected_slot = (selected_slot % len(missions)) + 1
        hub.display.number(selected_slot)
        hub.speaker.beep(400, 100)

    # Cycle Previous Slot
    if hub_left_pressed and not prev_hub_left:
        selected_slot = len(missions) if selected_slot == 1 else selected_slot - 1
        hub.display.number(selected_slot)
        hub.speaker.beep(400, 100)

    # Execute Selected Slot
    if hub_center_pressed and not prev_hub_center:
        hub.speaker.beep(800, 200)
        print(f">>> Executing Slot {selected_slot}...")
        
        # Reset IMU to ensure perfect tracking at the start of every run
        hub.imu.reset_heading(0) 
        wait(100)
        
        # Run the specific mission function
        if selected_slot in missions:
            missions[selected_slot]()
            
        print(f">>> Slot {selected_slot} Finished.")
        hub.speaker.beep(600, 200)
        hub.display.number(selected_slot)

    # Debouncing
    prev_hub_left = hub_left_pressed
    prev_hub_right = hub_right_pressed
    prev_hub_center = hub_center_pressed

    wait(50)