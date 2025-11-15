
# This code was automatically generated for mission: Mainmission
# It assumes a library named '*' with asynchronous commands for movement and rotation.

from common import *
import runloop

async def mission_08_silo () :
    # Drive to silo
    await accurateDrive(40.50, 500)
    # Hit the lever 4 times (down, up)
    for i in range(4):
        await rotateRightArm(90, 1000)
        await rotateRightArm(-90, 500)
    await accurateDrive(-40.50, 500)

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

    # reset the arms before finishing so they are ready to go again.
    await resetArmRotation()

runloop.run(main())
