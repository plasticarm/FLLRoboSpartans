
# This code was automatically generated for mission: Mainmission
# It assumes a library named '*' with asynchronous commands for movement and rotation.

from common import *
import runloop

async def mission_02_map_reveal () :
    # Raise the arm up

    # Drive Foward 60cm

    # Lower Arm 135%

    # Drive Foward 5cm

    # Turn Left 10%

    # Raise Arm 45%

    # Turn Right 45%

    # Lower arm 45 degrees

    # Drive forward 5cm

    # Raise arm 45

    # Drive back 15cm

    # Turn right 45 deg

    # Drive foward 4cm

    # Turn Left 10%

    # Drive Foward 4cm

    # Raise Arm 60%

    # Turn Right 90%

    # Drive Foward 30cm

    # Lower Arm 70%

    # Drive back 30cm

    # Raise Arm 60%

    # Turn Right 60%

    #Drive Foward 60cm (Home)



    # await drive (3, 300)
    # await rotateDegrees (-55, 300)
    # await rotateLeftArm (49, 300)
    # Beep to finish the mission
    await beep (500, 1000)

async def main():
    # Starting mission: Second mission starting from home left, second line
    # Initial Position: 75.92, -44.72 cm,
    # Initial Angle: 0.00 degrees
    # Initialize the motor pair for wheels and save motor positions. Do this every time.

    # This mission performs the tripple action of a map reveal

    await init()
    await mission_02_map_reveal()

    # reset the arms before finishing so they are ready to go again.
    await resetArmRotation()

runloop.run(main())
