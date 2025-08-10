
from hub import port, light_matrix, motion_sensor
import hub
import motor
import runloop, motor_pair, sys, math, asyncio

# GLOBALS
# Set from -355 to 355. Positive numbers are clockwise.
degrees_to_turn = 0 # Yaw angle reading that indicates the robot needs to stop
stop_angle = 0

TRACK = 11.2 # distance between wheels. cm - please measure your own robot.
# cm, this is a constant for your robot
WHEEL_CIRCUMFERENCE = 17.5
# input must be in the same unit as WHEEL_CIRCUMFERENCE
SPIN_CIRCUMFERENCE = TRACK * math.pi
PIVOT_CIRCUMFERENCE = 2 * TRACK * math.pi   

async def setupMotors():
    motor_pair.pair(motor_pair.PAIR_1, port.A, port.B)
    motion_sensor.reset_yaw(0)
    await runloop.until(motion_sensor.stable)

async def resetYaw():
    motion_sensor.reset_yaw(0)
    await runloop.until(motion_sensor.stable)

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

def degreesForDistance(distance_cm):
    # Add multiplier for gear ratio if needed
    return int((distance_cm/WHEEL_CIRCUMFERENCE) * 360)

async def drive(distance, speed):
    #motor_pair.pair(motor_pair.PAIR_1, port.A, port.B)
    await motor_pair.move_for_degrees(motor_pair.PAIR_1, degreesForDistance(distance), 0, velocity=speed, stop=motor.BRAKE, acceleration=1000, deceleration=1000)

async def rotateRightArm(degrees, speed):
    await motor.run_for_degrees(port.D, degrees * 3, speed)

async def rotateLeftArm(degrees, speed):
    await motor.run_for_degrees(port.C, degrees * 3, speed)

async def rotateCenterArm(degrees, speed):
    await motor.run_for_degrees(port.D, degrees * math.ceil(4.9), speed)

async def rotateDegrees(degrees, speed):  
    global degrees_to_turn, stop_angle  
    if abs(degrees) > 355:
        print ("Out of range")
        return
    #await setupMotors()
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
    return (motor.velocity(port.C) is 0 and motor.velocity(port.D) is 0)

async def main():
    await setupMotors()
    
        
    while True:
        await drive(15, 660)
        await drive(-15, 660)
        await rotateLeftArm(360, 660)
        await rotateRightArm(360, 660)
        await asyncio.sleep(1)
        await rotateDegrees(180, 300)
        await rotateCenterArm(360, 660)
        #await spin_turn(360, 400)
        a = rotateLeftArm(180, 660)
        b = rotateRightArm(180, 660)
        # run both the functions together
        runloop.run(*[a,b])
        #await runloop.until(all_done)
        await rotateDegrees(-180, 300)
        #await spin_turn(360, 400)
        # wait until both motors have stopped
        await runloop.until(all_done)
        await rotateDegrees(180, 300)
        #await rotateDegrees(180, 300)

        a = rotateLeftArm(180, 660)
        b = rotateRightArm(180, 660)
        c = rotateDegrees(-180, 300)
        # run both the functions together
        runloop.run(*[a,b, c])
        #await asyncio.gather(rotateLeftArm(90, 660), rotateRightArm(90, 660))
        #await spin_turn(720, 400)
        #await pivot_turn(720, 400)

runloop.run(main())
