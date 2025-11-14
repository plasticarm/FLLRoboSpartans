
# This code was automatically generated for mission: Mainmission
# It assumes a library named '*' with asynchronous commands for movement and rotation.

from common import *
import runloop

async def mission3 () :
    await rotateRightArm(-45, 300)
    await accurateDrive(3, 300)
    await accurateRotateDegrees(-5, 400)
    await accurateDrive (53, 600)
    await accurateRotateDegrees (-38, 400)
    await accurateDrive (23, 600)
    await accurateRotateDegrees(-34, 400)
    await rotateLeftArm(30, 300)
    await accurateDrive (69, 600)
    await accurateRotateDegrees(2.5, 400)
    # Hit car lever up
    await rotateLeftArm(-75, 600)
    await accurateDrive (-14, 600)
    await accurateRotateDegrees(75, 600)
    await accurateDrive (-50, 600)
    await accurateRotateDegrees(-32, 600)
    await rotateLeftArm(83, 600)
    await accurateDrive (10, 400)
    await rotateLeftArm (-90, 600)



async def main():
    # Starting mission: Second mission starting from home left, second line
    # Initial Position: 75.92, -44.72 cm,
    # Initial Angle: 0.00 degrees
    # Initialize the motor pair for wheels and save motor positions. Do this every time.
    await init()
    await mission3()

    # reset the arms before finishing so they are ready to go again.
    await resetArmRotation()

runloop.run(main())
