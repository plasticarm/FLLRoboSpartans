"""
Common functions for the SPIKE Prime robot
"""

from hub import port, light_matrix, motion_sensor, sound
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
    await motor.run_for_degrees(port.C, degrees * 3, speed)

async def rotateLeftArm(degrees, speed):
    await motor.run_for_degrees(port.D, degrees * 3, speed)

async def rotateCenterArm(degrees, speed):
    await motor.run_for_degrees(port.C, degrees * math.ceil(4.9), speed)

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
        return abs(yaw_angle) > stop_angle
    # If we need to turn more than 180 degrees, compute the yaw angle we need to stop at.
    if degrees_to_turn >= 0:
        # moving clockwise # The adjusted yaw angle is positive until we cross 180. # Then, we are negative numbers counting up.
        return yaw_angle < 0 and yaw_angle > stop_angle
    else: # The adjusted yaw angle is negative until we cross 180 # Then, we are positive numbers counting down.
        return yaw_angle > 0 and yaw_angle < stop_angle

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
