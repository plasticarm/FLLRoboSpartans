
# This code was automatically generated for mission: Mainmission
# It assumes a library named '*' with asynchronous commands for movement and rotation.

from common import *
import runloop

async def mission_09_whats_on_sale_wares () :
    # Drive forward a bit to move away from table wall
    await drive (3, 300)
    # Turn left to face middle of table
    await rotateDegrees (-55, 300)
    # Drive towards the roof lever
    await drive (43, 500)
    # Rotate to face the lever
    await rotateDegrees (95, 300)
    # Drive forward a bit to the lever
    await drive (3, 600)
    # Lower the arm to go on top of the lever
    await rotateLeftArm (49, 300)
    # Drive back to pull the lever down
    await drive (-9.5, 350)

async def mission_09_whats_on_sale_roof_raise () :
    # Turn left towards the roof
    await rotateDegrees (-8, 400)
    await drive (8, 300)
    await rotateDegrees (-7, 100)
    await drive (2.5, 200)
    # Raise left arm to raise roof
    await rotateLeftArm (-30, 700)
    await rotateDegrees (15, 400)
    await rotateDegrees (-30, 400)
    await drive (-5, 400)
    await rotateLeftArm (49, 400)


    # Turn right to full raise roof

    # Turn left to go back to original position

    # Drive back to get ready for next mission
    

async def mission_10_tip_the_scales_scale_pan () :
    # Raise the arm
    await rotateLeftArm (-50, 300)
    # Turn to the left to face the scale pan ring
    await rotateDegrees (-25, 300)
    # Lower the arm partially into the ring
    await rotateLeftArm (38, 300)
    # Drive forward to position the arm above the ring
    await drive (6, 100)
    # Fully lower the arm into the ring
    await rotateLeftArm(25, 200)
    # Pull the ring out
    await drive (-9, 300)
    # Rotate to face back of the bot towards home
    await accurateRotateDegrees (-70, 300)
    # Drive home
    await drive (-70, 300)

async def main():
    # Starting mission: Second mission starting from home left, second line
    # Initial Position: 75.92, -44.72 cm,
    # Initial Angle: 0.00 degrees
    # Initialize the motor pair for wheels and save motor positions. Do this every time.

    # This mission performs the 2 easy missions on the right center side of the table

    await init()
    await mission_09_whats_on_sale_wares()
    await mission_09_whats_on_sale_roof_raise()
    await mission_10_tip_the_scales_scale_pan()

    # reset the arms before finishing so they are ready to go again.
    await resetArmRotation()

runloop.run(main())
