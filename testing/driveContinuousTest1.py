"""
Common functions for the SPIKE Prime robot
"""

from hub import port, light_matrix, motion_sensor, sound, button
import hub
import motor
import runloop, motor_pair, sys, math, asyncio

# GLOBALS
degrees_to_turn = 0 # Yaw angle reading that indicates the robot needs to stop
stop_angle = 0
TRACK = 11.2 # distance between wheels. cm - please measure your own robot.
# cm, this is a constant for your robot
WHEEL_CIRCUMFERENCE = 17.5
# input must be in the same unit as WHEEL_CIRCUMFERENCE
SPIN_CIRCUMFERENCE = TRACK * math.pi
PIVOT_CIRCUMFERENCE = 2 * TRACK * math.pi

# --- NEW: P-Controller Gain ---
# This is the "magic number" for your drive_straight function.
# You will need to "tune" this value.
# - If your robot is "lazy" and drifts a lot, make this number BIGGER.
# - If your robot "wiggles" or "oscillates" too much, make this number SMALLER.
# Start with a value around 3.0
KP_GAIN = 3.0 
# --- End new global ---

# --- NEW: Continuous / Manual Drive Globals ---
_manual_drive_active = False
_manual_speed = 0
_manual_steering = 0
_manual_distance = 0.0
# --- End Manual Drive Globals ---

# ARM ROTATION TRACKING
_left_arm_start_angle = 0
_right_arm_start_angle = 0
_center_arm_start_angle = 0

async def setupMotors():
    motor_pair.pair(motor_pair.PAIR_1, port.A, port.B)
    motion_sensor.reset_yaw(0)
    await runloop.until(motion_sensor.stable)

    # Store the initial position of each arm motor
    global _left_arm_start_angle, _right_arm_start_angle, _center_arm_start_angle
    _left_arm_start_angle = motor.relative_position(port.C)
    _right_arm_start_angle = motor.relative_position(port.D)
    _center_arm_start_angle = motor.relative_position(port.D) # Assuming right and center arm use the same motor for now

async def resetYaw():
    motion_sensor.reset_yaw(0)
    await runloop.until(motion_sensor.stable)

def degreesForDistance(distance_cm):
    # Add multiplier for gear ratio if needed
    return int((distance_cm/WHEEL_CIRCUMFERENCE) * 360)

async def drive(distance, speed):
    """
    Original simple drive function.
    Moves for a distance with no yaw correction. Good for speed, bad for accuracy.
    """
    await motor_pair.move_for_degrees(motor_pair.PAIR_1, degreesForDistance(distance), 0, velocity=speed, stop=motor.BRAKE, acceleration=1000, deceleration=1000)

# --- UPDATED: Yaw-Corrected Drive Function with Easing ---
async def drive_straight(distance_cm, speed, min_speed=50, ramp_degrees=180, stop=True):
    """
    Drives in a straight line using a P-controller and velocity easing.
    - distance_cm: Distance to travel in cm (negative for backward).
    - speed: Max motor velocity (always positive).
    - min_speed: The speed to start and end at (always positive). A lower value (e.g., 50) gives a gentler start.
    - ramp_degrees: Motor degrees over which to accelerate/decelerate.
    """
    global KP_GAIN
    await resetYaw() # Start from a known "straight" angle (0)

    # --- 1. Setup Speed Parameters ---
    max_speed_abs = abs(speed)
    min_speed_abs = max(0, abs(min_speed)) # Ensure min_speed is positive
    
    if max_speed_abs < min_speed_abs:
        min_speed_abs = max_speed_abs # Can't have min speed > max speed

    speed_range = max_speed_abs - min_speed_abs
    
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
        steering = KP_GAIN * error
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
    if (stop):
        motor_pair.stop(motor_pair.PAIR_1, stop=motor.BRAKE)

# --- End new function ---

# --- NEW: Manual / Continuous Drive Functions ---

def set_drive_params(speed, steering):
    """
    Updates the parameters for the drive loop immediately.
    speed: -100 to 100
    steering: -100 to 100 (negative is left, positive is right)
    """
    global _manual_speed, _manual_steering
    _manual_speed = speed
    _manual_steering = steering

def stop_drive_loop():
    """Stops the continuous driving task."""
    global _manual_drive_active
    _manual_drive_active = False

def get_distance_traveled():
    """Returns total distance traveled in cm since the loop started."""
    global _manual_distance
    return _manual_distance

async def drive_forever_loop():
    """
    Async task that continuously drives the robot based on global params.
    Tracks distance traveled using wheel circumference.
    """
    global _manual_drive_active, _manual_speed, _manual_steering, _manual_distance
    
    _manual_drive_active = True
    _manual_distance = 0.0
    _manual_speed = 0
    _manual_steering = 0
    
    # Use Port A for distance tracking
    last_position = motor.relative_position(port.A)
    
    print("Starting Continuous Drive Loop...")

    while _manual_drive_active:
        # Apply current parameters to motors
        motor_pair.move(motor_pair.PAIR_1, int(_manual_steering), velocity=int(_manual_speed))
        
        # --- Calculate Distance ---
        current_position = motor.relative_position(port.A)
        
        # Calculate how much the wheel turned since last check
        diff_degrees = current_position - last_position
        
        # Convert degrees to cm: (degrees / 360) * Circumference
        # We take the absolute value so driving backward also adds to "Total Distance Traveled"
        # If you want "Net Displacement" (so backing up subtracts), remove the abs()
        distance_change = (abs(diff_degrees) / 360.0) * WHEEL_CIRCUMFERENCE
        
        _manual_distance += distance_change
        last_position = current_position
        
        # Sleep briefly to let other tasks run and prevent CPU hogging
        await runloop.sleep_ms(50)
    
    # Stop motors when loop exits
    motor_pair.stop(motor_pair.PAIR_1)
    print("Continuous Drive Loop Stopped.")

async def turn_moving(target_degrees, speed, steering_sharpness=30):
    """
    Turns the robot while moving by a specific number of degrees.
    This blocks until the turn is complete, but keeps the motors running via drive_forever_loop.
    
    target_degrees: Positive for Clockwise (Right), Negative for Counter-Clockwise (Left).
    speed: Forward speed.
    steering_sharpness: How tight the turn is (0-100). Higher = Sharper.
    """
    
    # Determine direction and steering sign
    if target_degrees > 0:
        actual_steering = abs(steering_sharpness) # Right
    else:
        actual_steering = -abs(steering_sharpness) # Left
        
    start_yaw = motion_sensor.tilt_angles()[0] * -0.1
    
    # Start moving/turning
    set_drive_params(speed, actual_steering)
    
    # Wait until turn is complete
    while True:
        current_yaw = motion_sensor.tilt_angles()[0] * -0.1
        diff = current_yaw - start_yaw
        
        # Handle wrap-around (e.g. crossing from 179 to -179)
        if diff < -180: diff += 360
        if diff > 180: diff -= 360
            
        # Check completion
        # We check if we have turned AT LEAST the target amount
        if abs(diff) >= abs(target_degrees):
            break
        
        await runloop.sleep_ms(10)

# --- End Manual Drive Functions ---

async def rotateRightArm(degrees, speed):
    await motor.run_for_degrees(port.D, -degrees * 3, speed)

async def rotateLeftArm(degrees, speed):
    await motor.run_for_degrees(port.C, degrees * 3, speed)

async def rotateCenterArm(degrees, speed):
    await motor.run_for_degrees(port.D, degrees * math.ceil(4.9), speed)

async def resetArmRotation():
    global _left_arm_start_angle, _right_arm_start_angle, _center_arm_start_angle
    a = motor.run_to_relative_position(port.C, _left_arm_start_angle, 660)
    b = motor.run_to_relative_position(port.D, _right_arm_start_angle, 660)
    runloop.run(*[a,b])

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
async def rotateDegrees(degrees, speed, stop=True):
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
    if (stop):
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

def all_done():
    return (motor.velocity(port.C) == 0 and motor.velocity(port.D) == 0)

async def init():
    # Initialize the motor pair for wheels and save motor positions. Do this every time.
    await setupMotors()
    await sound.beep(400, 250)

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
    """Monitors buttons and sets song choice."""
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
    """Plays whichever song is selected."""
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

# --- EXAMPLE: Square Drive Demo ---
async def drive_square_demo():
    """
    Demo function: Drives in a square using manual/continuous drive controls.
    Does not stop the motors between sides, resulting in fluid movement.
    """
 
    async def _square_logic():
        side_length_cm = 20
        drive_speed = 800
        
        # Give the drive loop a moment to spin up
        await runloop.sleep_ms(100)
        
        for i in range(4):
            print("Side", i+1)
            # 1. Drive Straight
            # Store starting distance to measure 30cm relative to NOW
            start_dist = get_distance_traveled()
            
            # Ensure we are driving straight
            set_drive_params(speed=drive_speed, steering=0)
            
            # Wait until we've traveled the side length
            while (get_distance_traveled() - start_dist) < side_length_cm:
                await runloop.sleep_ms(50)
       
            # 2. Turn 90 Degrees using new helper
            print("Turning 90...")
            await turn_moving(90, drive_speed, steering_sharpness=30)
                
        # Stop everything
        set_drive_params(0, 0)
        stop_drive_loop()

    a = drive_forever_loop()
    b = _square_logic()
    runloop.run(*[a,b])

    # Run the continuous drive loop AND our logic at the same time
async def main():
    # Starting mission: Mainmission
    # Initial Position: 75.92, -44.72 cm
    # Initial Angle: 0.00 degrees
    # Initialize the motor pair for wheels and save motor positions. Do this every time.

    # This mission performs the 4 missions on the right side of the table

    await init()

    await drive_square_demo()
    # reset the arms before finishing so they are ready to go again.
    await resetArmRotation()


runloop.run(main())