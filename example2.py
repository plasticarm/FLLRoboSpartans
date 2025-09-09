"""
Available functions in the common library:

setupMotors()
resetYaw()
degreesForDistance(distance_cm)
drive(distance, speed)
rotateRightArm(degrees, speed)
rotateLeftArm(degrees, speed)
rotateCenterArm(degrees, speed)
resetArmRotation()
turn_done()
rotateDegrees(degrees, speed)
spin_turn(robot_degrees, motor_speed)
pivot_turn(robot_degrees, motor_speed)
all_done()
beep(frequency, duration)
"""

# Importing the common library functions
from common import *
import runloop

# DO NOT MODIFY CODE ABOVE THIS LINE!!!

# Your code here
async def main():
    # Initialize the motor pair for wheels and save motor positions. Do this every time.
    await init()
    # Your other code here


runloop.run(main())