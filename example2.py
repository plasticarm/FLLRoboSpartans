"""
Available functions in the common library:

setupMotors()
resetYaw()
degreesForDistance(distance_cm)
drive(distance, speed)
rotateDegrees(degrees, speed)
accurateRotateDegrees(degrees, speed)
spin_turn(robot_degrees, motor_speed)
pivot_turn(robot_degrees, motor_speed)
turn_done()
rotateRightArm(degrees, speed)
rotateLeftArm(degrees, speed)
rotateCenterArm(degrees, speed)
resetArmRotation()
reset()
all_done()
beep(frequency, duration)
"""

# Importing the common library functions
from common import *
import runloop

# DO NOT MODIFY CODE ABOVE THIS LINE!!!

# Your code here
async def missionA():
    # Example mission code. For doing multiple missions break missions into separate functions.
    await drive(30, 50)  # Drive forward 30 cm at speed 50
    await rotateDegrees(90, 50)  # Rotate right 90 degrees at speed 50
    await drive(20, 50)  # Drive forward 20 cm at speed 50
    await rotateDegrees(-90, 50)  # Rotate left 90 degrees at speed 50
    await drive(10, 50)  # Drive forward 10 cm at speed 50
    await rotateRightArm(90, 50)  # Rotate right arm 90 degrees at speed 50
    await rotateLeftArm(90, 50)  # Rotate left arm 90 degrees
    await beep(1000, 500)  # Beep at frequency 1000 Hz for 500 ms

# Your code here
async def missionB():
    # Example mission code. For doing multiple missions break missions into separate functions.
    await drive(30, 50)  # Drive forward 30 cm at speed 50
    await accurateRotateDegrees(90, 50)  # Rotate right 90 degrees at speed 50
    await drive(20, 50)  # Drive forward 20 cm at speed 50
    await accurateRotateDegrees(-90, 50)  # Rotate left 90 degrees at speed 50
    await drive(10, 50)  # Drive forward 10 cm at speed 50
    await rotateRightArm(90, 50)  # Rotate right arm 90 degrees at speed 50
    await rotateLeftArm(90, 50)  # Rotate left arm 90 degrees
    await beep(1000, 500)  # Beep at frequency 1000 Hz for 500 ms

async def missions():
    # For doing multiple missions break missions into separate functions.
    await missionA()
    await missionB()
    # Add more missions as needed

async def main():
    
    # Initialize the motor pair for wheels and save motor positions. Do this every time.
    await init()
    # Your other code here
    """ Optional example of running multiple tasks concurrently and playing music
    a = button_listener()
    b = play_music()
    c = missions()
    runloop.run(*[a, b, c])
    """
    await missions()
    # Reset arm rotations at end so they are ready for the next run. Do this every time.
    await resetArmRotation()

runloop.run(main())