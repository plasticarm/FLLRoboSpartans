
# This code was automatically generated for mission: Mainmission
# It assumes a library named '*' with asynchronous commands for movement and rotation.

from common import *
import runloop

async def mission_08_silo () :
    # Drive to silo
    await accurateDrive(40.50, 500)
    for i in range(4):
        await rotateRightArm(70, 500)
        await rotateRightArm(-70, 500)
    

async def mission_06_forge () :
    # Drive to the 3 rocks
    await accurateDrive(16.0, 400)
    # Change direction to the right
    await accurateRotateDegrees(23.00, 500)
    # Drive closer to the rocks
    await accurateDrive(10.00, 400)
    # Hit the lever to release the rocks
    await rotateDegrees(-10.00, 500)
    # Rotate back to the right to reposition
    await accurateRotateDegrees (30,500)

async def mission_05_who_lived_here () :
    # Reverse from the rocks
    await accurateDrive(-12.5, 400)
    # Drive forward a little so that rotation works
    #await drive (2, 20)
    # Rotate to the left to align with the lever
    await accurateRotateDegrees (-38.00, 500)
    # Drive up to the lever
    await accurateDrive (15.5, 500)
    # Hit the lever
    await rotateDegrees (-24, 300)
    await rotateDegrees (6, 300)
    # Drive back away from the structure
    await accurateDrive (-11.5,500)

async def mission_10_tip_the_scales () :
    # Rotate to the left to prepare to drive to the scales
    await accurateRotateDegrees(-40,500)
    # Drive towards the scales
    await accurateDrive(32, 500)
    # Rotate to the left to get in front of the scales
    await accurateRotateDegrees(-108,500)
    # Drive right up to the scales
    await accurateDrive (16, 200)
    # Slowly swing arm down to hit the scales
    await rotateRightArm(70,200)
    # Bring the arm back up
    await rotateRightArm (-80, 350)

async def drive_home () :
    # Back away from the scales
    await accurateDrive (-12, 300)
    # Rotate left
    await accurateRotateDegrees (-70, 500)
    # Drive forward
    await accurateDrive (20, 1000)
    # Rotate right
    await rotateDegrees (25, 600)
    #Drive towards home
    #reset arms and drive at same time.
    a = resetArmRotation()
    b = accurateDrive (60, 1000)
    # run the functions together
    runloop.run(*[a,b])
    # Rotate right
    #await accurateRotateDegrees (20, 300)

async def main():
    # Starting mission: Mainmission
    # Initial Position: 75.92, -44.72 cm
    # Initial Angle: 0.00 degrees
    # Initialize the motor pair for wheels and save motor positions. Do this every time.

    # This mission performs the 4 missions on the right side of the table

    await init()
    await setSpeedFactor(2)
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
