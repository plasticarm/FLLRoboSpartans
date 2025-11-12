
# This code was automatically generated for mission: Mainmission
# It assumes a library named '*' with asynchronous commands for movement and rotation.

from common import *
import runloop

async def surface_brush():
    await accurateDrive (47, 800)
    await rotateLeftArm (37, 300)
    await accurateDrive (5, 800)
    await accurateDrive (-7, 800)
    await accurateDrive (1, 500)
    await accurateDrive (-24, 500)
    await accurateRotateDegrees(70,100)
    await accurateDrive(37,500)
    # drop surface brush
    await rotateLeftArm (-70, 200)
    await rotateLeftArm (70, 200)
    await accurateRotateDegrees(20,100)    
    await rotateLeftArm (-70, 200)
    await accurateDrive(2,300)
    # raise statue
    await rotateLeftArm (-70, 200)
    """
    # drive back home
    await drive(-30,300)
    await accurateRotateDegrees(-90,300)
    await drive(-30,500)
    """

    await resetArmRotation()
    # drive to map mission    
    await drive(-20,300)
    await accurateRotateDegrees(-90,300)   
    
    await accurateDrive(43,500)
    await accurateRotateDegrees(-45,300)
    # lower arm to push
    await rotateLeftArm(40, 200)
    await accurateDrive(10,500)    
    #push 1st part
    await accurateDrive (15,300)
    #back up and set up to do 2nd part
    await rotateLeftArm(-60, 200)
    await accurateDrive (-15,300)    
    await accurateRotateDegrees(20, 300)
    await accurateDrive (8,300)
    #lower arm to push
    await rotateLeftArm(60, 200)
    #drive forward and push 2nd part
    await accurateDrive (12,300)
    #raise arm back up
    await rotateLeftArm(-60, 200)
    await accurateDrive (-10,300)
    await accurateRotateDegrees(20, 300)
    # lower arm to hook onto loop
    await rotateLeftArm(-30, 200)
    # drive forward to insert arm into loop
    await accurateDrive (5,300)
    # raise arm to securely hold part3
    await rotateLeftArm(60, 200)
    # back up and rotate to arena
    await accurateDrive (-5,300)
    await accurateRotateDegrees(120, 300)
    await accurateDrive (10,300)
    #drop part 3
    await rotateLeftArm(-70, 200)
    await accurateDrive (-10,300)


    """
    #await rotateRightArm (60, 200)
    #drive in mission
    await drive (22,300)
    await rotateRightArm ()
    await rotateDegrees (10,300)
    await rotateDegrees (-10,300)
    """
    

async def main():

    await init()
    await surface_brush()
    await resetArmRotation()

runloop.run(main())
