
# This code was automatically generated for mission: Mainmission
# It assumes a library named '*' with asynchronous commands for movement and rotation.

from common import *
import runloop

async def mission_08_silo () :
    # Drive to silo
    await drive(40.50, 500)

async def mission_06_forge () :
    # Drive to the 3 rocks
    await drive(18.50, 1000)
    # Change direction to the right
    await rotateDegrees(23.00, 500)
    # Drive closer to the rocks
    await drive(10.00, 1000)
    # Hit the lever to release the rocks
    await rotateDegrees(-20.00, 500)
    # Rotate back to the right to reposition
    await rotateDegrees (40,500)

async def mission_05_who_lived_here () :
    # Reverse from the rocks
    await drive(-15.00, 1000)
    # Drive forward a little so that rotation works
    await drive (2, 20)
    # Rotate to the left to align with the lever
    await rotateDegrees (-38.00, 500)
    # Drive up to the lever
    await drive (13, 500)
    # Hit the lever
    await rotateDegrees (-26, 500)
    await rotateDegrees (6, 300)
    # Drive back away from the structure
    await drive (-10,500)

async def mission_10_tip_the_scales () :
    # Rotate to the left to prepare to drive to the scales
    await rotateDegrees(-40,500)
    # Drive towards the scales
    await drive(31, 500)
    # Rotate to the left to get in front of the scales
    await rotateDegrees(-87,500)
    # Drive right up to the scales
    await drive (2, 200)
    # Slowly swing arm down to hit the scales
    await rotateRightArm(70,200)
    # Bring the arm back up
    await rotateRightArm (-80, 350)

async def drive_home () :
    # Back away from the scales
    await drive (-8, 300)
    # Rotate left
    await rotateDegrees (-70, 500)
    # Drive forward
    await drive (20, 500)
    # Rotate right
    await rotateDegrees (40, 600)
    #Drive towards home
    #reset arms and drive at same time.
    a = resetArmRotation()
    b = drive (70, 500)
    # run the functions together
    runloop.run(*[a,b])
    # Rotate right
    await rotateDegrees (20, 300)

async def main():
    # Starting mission: Mainmission
    # Initial Position: 75.92, -44.72 cm
    # Initial Angle: 0.00 degrees
    # Initialize the motor pair for wheels and save motor positions. Do this every time.

    # This mission performs the 4 missions on the right side of the table

    await init()
    await rotateRightArm (-45, 500)
    await rotateLeftArm (-90, 500)
    await mission_08_silo ()
    await mission_06_forge ()
    await mission_05_who_lived_here ()
    await mission_10_tip_the_scales ()
    await drive_home()

    # reset the arms before finishing so they are ready to go again.
    await resetArmRotation()

runloop.run(main())
