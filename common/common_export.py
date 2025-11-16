"""
In SP3, you can import a text-based Python file (.py) that is present in the hub root.
We will write a second program that exports the first program’s library functions 
to a file called “customlib.py” in the SP root folder (“/flash”). 
Use a slot that you don’t use for missions. We used slot 18. 
It will first create a string that contains all the library functions. 
Test code is excluded. It then writes the string out to a file in the SPIKE hub root. 
It does not itself import or use the library. It is simply an exporter utility. 
TIP:  You can also create multiple libraries by exporting chunks of code to different .py files in the root

Library code string using python multiline quotes. 
Do not include test code, only the functions you want to reuse and the imports they need.
"""

commonCode: str = """

#Common functions for the SPIKE Prime robot

from hub import port, light_matrix, motion_sensor, sound, button
import hub
import motor
import runloop, motor_pair, sys, math

# GLOBALS
degrees_to_turn = 0 # Yaw angle reading that indicates the robot needs to stop
stop_angle = 0
TRACK = 11.2 # distance between wheels. cm - please measure your own robot.
# cm, this is a constant for your robot
WHEEL_CIRCUMFERENCE = 17.5
# input must be in the same unit as WHEEL_CIRCUMFERENCE
SPIN_CIRCUMFERENCE = TRACK * math.pi
PIVOT_CIRCUMFERENCE = 2 * TRACK * math.pi
# --- GYRO TURNING CONSTANTS ---
# 1. Proportional Gain (Kp)
# - This is the "secret sauce".
# - If your robot is too SLOW to turn or STOPS before the target: Make Kp LARGER (e.g., 0.8)
# - If your robot is SHAKY or OVERSHOOTS a lot: Make Kp SMALLER (e.g., 0.4)
# - Start with 0.6 and adjust.
# We set this so that at 180 degrees, the speed is near the top of
# your 300-600 range (180 * 3.3 = 594).
KP_GAIN = 5.3
DRIVE_KP_GAIN = 0.1

# 2. Minimum Move Speed (MIN_MOVE_SPEED)
# - This is the lowest speed that will make your robot's motors move (overcomes friction).
# - If your robot stops just short of the target: Make MIN_MOVE_SPEED slightly HIGHER (e.g., 20)
# - If your robot is jittery and can't stop on the target: Make MIN_MOVE_SPEED LOWER (e.g., 10)
MIN_MOVE_SPEED = 20

# 3. Target Tolerance
# - How close is "good enough"? (in degrees)
# - 1 degree is usually fine for most applications.
TOLERANCE = 1

# ARM ROTATION TRACKING
_left_arm_start_angle = 0
_right_arm_start_angle = 0
_center_arm_start_angle = 0

async def setupMotors():
    light_matrix.show_image(light_matrix.IMAGE_ASLEEP)
    motor_pair.pair(motor_pair.PAIR_1, port.A, port.B)
    motion_sensor.reset_yaw(0)
    await runloop.until(motion_sensor.stable)

    # Store the initial position of each arm motor
    global _left_arm_start_angle, _right_arm_start_angle, _center_arm_start_angle
    _left_arm_start_angle = motor.relative_position(port.C)
    _right_arm_start_angle = motor.relative_position(port.D)
    _center_arm_start_angle = motor.relative_position(port.D) # Assuming right and center arm use the same motor for now
    light_matrix.show_image(light_matrix.IMAGE_HAPPY)

async def resetYaw():
    motion_sensor.reset_yaw(0)
    light_matrix.write("Y")
    await runloop.until(motion_sensor.stable)
    light_matrix.show_image(light_matrix.IMAGE_HAPPY)

def degreesForDistance(distance_cm):
    # Add multiplier for gear ratio if needed
    return int((distance_cm/WHEEL_CIRCUMFERENCE) * 360)

async def drive(distance, speed):
    if distance > 0:
        light_matrix.show_image(light_matrix.IMAGE_ARROW_N)
    else:
        light_matrix.show_image(light_matrix.IMAGE_ARROW_S)    
    await motor_pair.move_for_degrees(motor_pair.PAIR_1, degreesForDistance(distance), 0, velocity=speed, stop=motor.BRAKE, acceleration=1000, deceleration=1000)

async def drive_straight(distance_cm, speed, min_speed=150, ramp_degrees=720):    
    #Drives in a straight line using a P-controller and velocity easing.
    #- distance_cm: Distance to travel in cm (negative for backward).
    #- speed: Max motor velocity (always positive).
    #- min_speed: The speed to start and end at (always positive).
    #- ramp_degrees: Motor degrees over which to accelerate/decelerate.

    global DRIVE_KP_GAIN
    motion_sensor.reset_yaw(0) # Start from a known "straight" angle (0)

    # --- 1. Setup Speed Parameters ---
    max_speed_abs = abs(speed)
    min_speed_abs = max(0, abs(min_speed)) # Ensure min_speed is positive

    if max_speed_abs < min_speed_abs:
        min_speed_abs = max_speed_abs # Can't have min speed > max speed

    speed_range = max_speed_abs - min_speed_abs

    if distance > 0:
        light_matrix.show_image(light_matrix.IMAGE_ARROW_N)
    else:
        light_matrix.show_image(light_matrix.IMAGE_ARROW_S)

    direction = 1
    if distance_cm < 0:
        direction = -1 # Drive backward

    # --- 2. Setup Distance Parameters ---
    target_motor_degrees = degreesForDistance(abs(distance_cm))
    if target_motor_degrees == 0:
        return # Nothing to move

    start_position = motor.relative_position(port.A)

    # --- 3. Setup Easing Parameters ---
    # Handle moves shorter than two ramps
    accel_ramp = ramp_degrees
    decel_ramp = ramp_degrees

    if target_motor_degrees < (ramp_degrees * 2):
        # Short move: ramp up for half the distance, down for the other half
        accel_ramp = target_motor_degrees / 2
        decel_ramp = target_motor_degrees / 2

    decel_start_degrees = target_motor_degrees - decel_ramp

    # --- 4. P-Controller Loop ---
    current_degrees_moved = 0

    while current_degrees_moved < target_motor_degrees:
        # --- P-Controller (Yaw Correction) ---
        yaw_angle = motion_sensor.tilt_angles()[0] * -0.1
        error = yaw_angle # We want the yaw to be 0
        steering = DRIVE_KP_GAIN * error
        steering = max(-100, min(100, steering))

        # --- Easing (Velocity Control) ---
        current_speed_abs = 0

        if accel_ramp > 0 and current_degrees_moved < accel_ramp:
            # --- Acceleration Phase ---
            progress = current_degrees_moved / accel_ramp # 0.0 to 1.0
            current_speed_abs = min_speed_abs + (progress * speed_range)

        elif decel_ramp > 0 and current_degrees_moved >= decel_start_degrees:
            # --- Deceleration Phase ---
            degrees_left = target_motor_degrees - current_degrees_moved
            progress = degrees_left / decel_ramp # 1.0 down to 0.0
            progress = max(0.0, progress) # Clamp at 0
            current_speed_abs = min_speed_abs + (progress * speed_range)

        else:
            # --- Coasting Phase ---
            current_speed_abs = max_speed_abs

        # Ensure speed is at least min_speed
        if current_speed_abs < min_speed_abs:
            current_speed_abs = min_speed_abs

        if current_speed_abs > max_speed_abs:
            current_speed_abs = max_speed_abs

        # --- Apply motor movement ---
        current_speed_with_direction = int(current_speed_abs * direction)
        motor_pair.move(motor_pair.PAIR_1, int(steering), velocity=current_speed_with_direction)

        # Update how far we've gone
        current_degrees_moved = abs(motor.relative_position(port.A) - start_position)

        await runloop.sleep_ms(10) # 10ms loop for smooth easing

    # --- End of Loop ---
    # We've reached our target distance, so stop.
    motor_pair.stop(motor_pair.PAIR_1, stop=motor.BRAKE)

async def accurateDrive(distance_cm, speed):
    await drive_straight(distance_cm, speed)

# --- End Accurate Drive ---
async def rotateRightArm(degrees, speed):
    # Calculate Compound Gear Ratios :
    # 20/8 = 2.5
    await motor.run_for_degrees(port.D, math.floor(-degrees * 2.5), speed)
    light_matrix.show_image(light_matrix.IMAGE_ARROW_E)    

async def rotateLeftArm(degrees, speed):
    # Calculate Compound Gear Ratios :
    # 36/12 = 3
    await motor.run_for_degrees(port.C, degrees * 3, speed)
    light_matrix.show_image(light_matrix.IMAGE_ARROW_W)

async def rotateCenterArm(degrees, speed):
    # Calculate Compound Gear Ratios :
    # 36/12 * 20/12 = 5
    await motor.run_for_degrees(port.D, degrees * math.ceil(4.9), speed)
    light_matrix.show_image(light_matrix.IMAGE_ARROW_N) 

async def resetArmRotation():
    global _left_arm_start_angle, _right_arm_start_angle, _center_arm_start_angle
    a = motor.run_to_relative_position(port.C, _left_arm_start_angle, 660)
    b = motor.run_to_relative_position(port.D, _right_arm_start_angle, 660)
    runloop.run(*[a,b])
    light_matrix.show_image(light_matrix.IMAGE_TARGET) 

# Function that returns true when the yaw has turned past stop angle
def turn_done():
    global degrees_to_turn, stop_angle
    # convert tuple decidegree into the same format as in app and blocks
    yaw_angle = motion_sensor.tilt_angles()[0] * -0.1
    
    # if we need to turn less than 180 degrees, check the absolute values
    if (abs(degrees_to_turn) < 180):
        # FIX: Check for >= (greater than or equal)
        return abs(yaw_angle) >= stop_angle
        
    # If we need to turn more than 180 degrees, compute the yaw angle we need to stop at.
    if degrees_to_turn >= 0:
        # moving clockwise # The adjusted yaw angle is positive until we cross 180. # Then, we are negative numbers counting up.
        # FIX: Check for >= stop_angle
        return yaw_angle < 0 and yaw_angle >= stop_angle
    else: 
        # moving counter-clockwise # The adjusted yaw angle is negative until we cross 180 # Then, we are positive numbers counting down.
        # FIX: Check for <= stop_angle
        return yaw_angle > 0 and yaw_angle <= stop_angle

# basic rotation of robot with accuracy as priority
async def rotateDegrees(degrees, speed):
    if degrees > 0:
        light_matrix.show_image(light_matrix.IMAGE_ARROW_E)
    else:
        light_matrix.show_image(light_matrix.IMAGE_ARROW_W)

    global degrees_to_turn, stop_angle
    if abs(degrees) > 355:
        print ("Out of range. Do not rotateDegrees for more than 355.")
        return
    # reset the yaw    
    await resetYaw()
    degrees_to_turn = degrees
    if (abs(degrees) < 180):
        stop_angle = abs(degrees_to_turn)
    else:
        stop_angle = (360 - abs(degrees)) if degrees < 0 else (abs(degrees) - 360)
    # set the steering laue based on turn direction
    steering_val = 100 if degrees >= 0 else -100
    motor_pair.move(motor_pair.PAIR_1, steering_val, velocity=speed)
    await runloop.until(turn_done)
    motor_pair.stop(motor_pair.PAIR_1)
    # reset degrees_to_turn and stop_angle
    degrees_to_turn = 0
    stop_angle = 0

async def spin_turn(robot_degrees, motor_speed):
    # Add a multiplier for gear ratios if you’re using gears
    motor_degrees = int((SPIN_CIRCUMFERENCE/WHEEL_CIRCUMFERENCE) * abs(robot_degrees))
    if robot_degrees > 0:
        # spin clockwise
        await motor_pair.move_for_degrees(motor_pair.PAIR_1, motor_degrees, 100, velocity=motor_speed)
    else:
        #spin counter clockwise
        await motor_pair.move_for_degrees(motor_pair.PAIR_1, motor_degrees, -100, velocity=motor_speed)

async def pivot_turn(robot_degrees, motor_speed):
    # Add a multiplier for gear ratios if you’re using gears
    motor_degrees = int((PIVOT_CIRCUMFERENCE/WHEEL_CIRCUMFERENCE) * abs(robot_degrees))
    if robot_degrees > 0:
        # pivot clockwise
        await motor_pair.move_for_degrees(motor_pair.PAIR_1, motor_degrees, 50, velocity=motor_speed)
    else:
        #pivot counter clockwise
        await motor_pair.move_for_degrees(motor_pair.PAIR_1, motor_degrees, -50, velocity=motor_speed)

# --- GYRO-BASED PRECISE ROTATION FUNCTION ---
async def gyro_turn(target_angle, max_speed):
    # Reset the gyro's yaw angle to 0 before we start.
    # This sets the robot's current heading as the "zero" point.
    await resetYaw()

    # Get the current angle (which should be 0)
    current_angle = motion_sensor.tilt_angles()[0] * -0.1
    # Calculate the error (how far we are from the target)
    error = target_angle - current_angle

    if target_angle > 0:
        light_matrix.show_image(light_matrix.IMAGE_ARROW_E)
    else:
        light_matrix.show_image(light_matrix.IMAGE_ARROW_W)

    # Loop until the error is within our tolerance
    while abs(error) > TOLERANCE:
        # Get the latest angle
        current_angle = motion_sensor.tilt_angles()[0] * -0.1

        # Recalculate the error
        error = target_angle - current_angle

        # --- P-Controller ---
        # Calculate the speed based on the error and our gain
        speed = error * KP_GAIN
        # 1. Apply Maximum Speed
        # Cap the speed at the max_speed
        if speed > max_speed:
            speed = max_speed
        elif speed < -max_speed:
            speed = -max_speed

        # 2. Apply Minimum *Movement* Speed
        # If we are not at the target, but the calculated speed is too low
        # to overcome friction, set it to the minimum speed to keep moving.
        if abs(error) > TOLERANCE and abs(speed) < MIN_MOVE_SPEED:
            if speed > 0:
                speed = MIN_MOVE_SPEED# Force minimum speed turning right
            else:
                speed = -MIN_MOVE_SPEED # Force minimum speed turning left

        # --- End P-Controller ---

        # For a "spin turn", we run the motors in opposite directions.
        # We cast to int() because the motor commands require whole numbers.
        left_speed = int(speed)
        right_speed = int(-speed)

        # Start the motors
        motor_pair.move_tank(motor_pair.PAIR_1, left_speed, right_speed)

        # You MUST await a small delay in an async while-loop.
        # Without this, your loop blocks all other code from running.
        # This also gives the gyro time to get a new reading.
        await asyncio.sleep_ms(10)
    # Stop the motors when done. SMART_BRAKE seems to work better to stop more accurately.
    motor_pair.stop(motor_pair.PAIR_1, stop=motor.SMART_BRAKE)

async def accurateRotateDegrees(degrees, speed):
    await gyro_turn(degrees, speed)
    # brief pause to ensure robot has stopped
    await asyncio.sleep_ms(100)
    # final stop to ensure no movement. This uses HOLD to prevent any further movement.
    motor_pair.stop(motor_pair.PAIR_1, stop=motor.HOLD)

def all_done():
    return (motor.velocity(port.C) == 0 and motor.velocity(port.D) == 0)

async def init():
    # Initialize the motor pair for wheels and save motor positions. Do this every time.
    await setupMotors()
    await sound.beep(400, 250)

async def reset():
    await resetArmRotation()

async def beep(frequency, duration):
    await sound.beep(frequency, duration)

# --- Music ---

# --- Note table (common ones used in theme) ---
NOTES = {
    # --- Octave 3 ---
    "C3": 131,"C#3": 139,"Db3": 139,
    "D3": 147,"D#3": 156,"Eb3": 156,
    "E3": 165,"F3": 175,"F#3": 185,"Gb3": 185,
    "G3": 196,"G#3": 208,"Ab3": 208,
    "A3": 220,"A#3": 233,"Bb3": 233,
    "B3": 247,

    # --- Octave 4 ---
    "C4": 262,"C#4": 277,"Db4": 277,
    "D4": 294,"D#4": 311,"Eb4": 311,
    "E4": 330,"F4": 349,"F#4": 370,"Gb4": 370,
    "G4": 392,"G#4": 415,"Ab4": 415,
    "A4": 440,"A#4": 466,"Bb4": 466,
    "B4": 494,

    # --- Octave 5 ---
    "C5": 523,"C#5": 554,"Db5": 554,
    "D5": 587,"D#5": 622,"Eb5": 622,
    "E5": 659,"F5": 698,"F#5": 740,"Gb5": 740,
    "G5": 784,"G#5": 831,"Ab5": 831,
    "A5": 880,"A#5": 932,"Bb5": 932,
    "B5": 988
}

# --- Timing setup ---
BPM = 112
QUARTER = int(60000 / BPM)# ms for quarter note
SIXTEENTH = QUARTER // 4
EIGHTH = QUARTER // 2
DOTTED_QUARTER = QUARTER + EIGHTH
HALF = QUARTER * 2

# --- Song definitions ---
RAIDERS = [
    ("E3", EIGHTH), ("F3", EIGHTH), 
    ("G3", EIGHTH), ("C4", HALF), ("D3", EIGHTH), ("E3", EIGHTH), 
    ("F3", HALF), ("G3", EIGHTH), ("A3", EIGHTH),
    ("B4", EIGHTH), ("F4", HALF), ("A3", EIGHTH), ("B4", EIGHTH),
    ("C4", QUARTER), ("D4", QUARTER), ("E4", QUARTER), ("F4", EIGHTH), ("E3", EIGHTH),
    ("G2", EIGHTH),("C3", EIGHTH), ("D3", EIGHTH), ("E3", EIGHTH),     
    ("F4", HALF), ("G3", EIGHTH), ("G3", EIGHTH), 
    ("E4", QUARTER), ("D4", EIGHTH), ("G3", EIGHTH), ("E4", QUARTER), ("D4", EIGHTH),("G3", EIGHTH),
    ("E4", QUARTER), ("D4", EIGHTH), ("G3", EIGHTH), ("E4", QUARTER), ("D4", EIGHTH),("G3", EIGHTH)
]
EMPIREMARCH = [
    ("A4", QUARTER), ("A4", QUARTER), ("A4", QUARTER), ("F3", EIGHTH), ("C4", EIGHTH), ("A4", QUARTER), ("F3", EIGHTH), ("C4", EIGHTH), ("A4", HALF),
    ("E4", QUARTER), ("E4", QUARTER), ("E4", QUARTER), ("F4", EIGHTH), ("C4", EIGHTH), ("A3", QUARTER), ("F3", EIGHTH), ("C4", EIGHTH), ("A4", HALF),
    ("A4", QUARTER), ("A4", QUARTER), ("A4", QUARTER), ("F3", EIGHTH), ("C4", EIGHTH), ("A4", QUARTER), ("F3", EIGHTH), ("C4", EIGHTH), ("A4", HALF),
    ("E4", QUARTER), ("E4", QUARTER), ("E4", QUARTER), ("F4", EIGHTH), ("C4", EIGHTH), ("A3", QUARTER), ("F3", EIGHTH), ("C4", EIGHTH), ("A4", HALF),
    ("C5", QUARTER), ("C5", QUARTER), ("C5", QUARTER), ("A4", EIGHTH), ("F4", EIGHTH), ("F4", DOTTED_QUARTER), ("E4", EIGHTH), ("D4", EIGHTH), ("B3", HALF),
    ("A4", QUARTER), ("A4", QUARTER), ("A4", QUARTER), ("F3", EIGHTH), ("C4", EIGHTH), ("A4", QUARTER), ("F3", EIGHTH), ("C4", EIGHTH), ("A4", HALF),
    ("E4", QUARTER), ("E4", QUARTER), ("E4", QUARTER), ("F4", EIGHTH), ("C4", EIGHTH), ("A3", QUARTER), ("F3", EIGHTH), ("C4", EIGHTH), ("A4", HALF)]

SONGCHOICE = RAIDERS
PLAY_SONG = False
# --- END MUSIC ---

# --- Async Tasks ---

async def button_listener():
    # Monitors buttons and sets song choice.
    global SONGCHOICE, PLAY_SONG

    while True:
        if button.pressed(button.LEFT):
            PLAY_SONG = False# stop any current song
            SONGCHOICE = RAIDERS
            PLAY_SONG = True

            # Wait until button released
            while button.pressed(button.LEFT):
                await runloop.sleep_ms(50)

        elif button.pressed(button.RIGHT):
            PLAY_SONG = False
            SONGCHOICE = EMPIREMARCH
            PLAY_SONG = True

            while button.pressed(button.RIGHT):
                await runloop.sleep_ms(50)

        await runloop.sleep_ms(50)

async def play_music():
    # Plays whichever song is selected.
    global SONGCHOICE, PLAY_SONG

    while True:
        if PLAY_SONG and SONGCHOICE:
            for note, dur in SONGCHOICE:
                if not PLAY_SONG:
                    break
                freq = NOTES.get(note, 440)
                await sound.beep(freq, dur)
                await runloop.sleep_ms(30)
            # loop the song
        await runloop.sleep_ms(50)
        
# --- End Async Tasks ---

"""

# WRITE TO SLOT 18
def exportProgram():
    import os
    global code
    os.chdir('/flash')  # change directory to root
    try:
        os.remove('common.py')  # remove any existing library file of the same name
    except:
        pass
    with open('common.py', 'w+') as f:  # Create a new file common.py in the SPIKE hub root
        f.write(commonCode)  # Write out the library code string to the common.py file

exportProgram()  # Runs the export function
