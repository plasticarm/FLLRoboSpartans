
# This code was automatically generated for mission: Mainmission
# It assumes a library named '*' with asynchronous commands for movement and rotation.

from common import *
import runloop

async def lift_statue () :
    await drive (46, 400)
    await accurateRotateDegrees (-33, 400)
    await drive (43, 400)
    await accurateRotateDegrees (-75, 400)
    await drive (45, 400)
    await accurateRotateDegrees (-44, 200)
    await drive (5.5, 400)
    # Hit 1
    await rotateRightArm (120, 800)
    await drive(-1, 100)
    await rotateRightArm(-100, 400)
    # Hit 2
    await rotateRightArm(120, 800)
    await drive (-1, 300)
    # dont hit tail
    await rotateRightArm (-80, 400)
    await drive (-8, 300)
    await rotateDegrees (94, 400)
    # lower left arm 
    await rotateLeftArm (45, 400)
    await drive (27, 400)
    # lift thing
    await rotateLeftArm (-90, 660)
    await drive (-7, 400)
    await accurateRotateDegrees (-50, 400)
    await drive (62, 400)
    await accurateRotateDegrees (-60, 400)
    await drive (65, 550)


async def main():
    # Starting mission: Second mission starting from home left, second line
    # Initial Position: 75.92, -44.72 cm,
    # Initial Angle: 0.00 degrees
    # Initialize the motor pair for wheels and save motor positions. Do this every time.
    await init()
    await lift_statue()

    # reset the arms before finishing so they are ready to go again.
    await resetArmRotation()

runloop.run(main())
