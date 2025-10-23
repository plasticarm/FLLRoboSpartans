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
    await motor_pair.move_for_degrees(motor_pair.PAIR_1, degreesForDistance(distance), 0, velocity=speed, stop=motor.BRAKE, acceleration=1000, deceleration=1000)

async def rotateRightArm(degrees, speed):
    # Calculate Compound Gear Ratios :
    # 20/8 = 2.5
    await motor.run_for_degrees(port.D, -degrees * 2.5, speed)

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
