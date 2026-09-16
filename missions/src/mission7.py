
# This code was automatically generated for mission: Mainmission
# It assumes a library named '*' with asynchronous commands for movement and rotation.

from common import *
import runloop

async def lift_sand () :
    # Drive forward away from the wall
    await accurateDrive (3, 300)
    # Rotate to go to the sand lever
    await accurateRotateDegrees (90, 500)
    # Drive forward
    await accurateDrive (39.5, 500)
    # Rotate right arm to drag lever
    await rotateRightArm(60, 400)
    # back away from lever
    await accurateDrive(-15, 700)
    await rotateRightArm(-20, 100)
    # turn and drive around
    await accurateRotateDegrees(-90,400)
    await accurateDrive(10.5, 500)
    await accurateRotateDegrees(90,400)
    await accurateDrive(45, 1000)
    await drive(-70,400)
    await accurateRotateDegrees(90, 400)
    await drive(40,400)



    #Drive towards home
    #reset arms and drive at same time.
    """""
    a = resetArmRotation()
    b = accurateDrive (-60, 1000)
    # run the functions together
    runloop.run(*[a,b])
    """""
    # Rotate right
    #await accurateRotateDegrees (20, 300)

async def main():
    # Starting mission: Mainmission
    # Initial Position: 75.92, -44.72 cm
    # Initial Angle: 0.00 degrees
    # Initialize the motor pair for wheels and save motor positions. Do this every time.

    # This mission performs the 4 missions on the right side of the table

    await init()
    await setSpeedFactor(1)
    await lift_sand()

    # reset the arms before finishing so they are ready to go again.
    await resetArmRotation()

runloop.run(main())
