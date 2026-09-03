# main.py
# Entry point for controlling the Spike Prime robot

from common import SpikeRobot
import runloop

robot = SpikeRobot()

async def main():
    await robot.setup()
    
    # Run 10 laps
    for i in range(10):
        await robot.drive_forward(50)
        await robot.acc1_rotate_left(90)
        await robot.acc1_rotate_right(90)
        await robot.turn_right(90)
        await robot.drive_forward(20)
        await robot.turn_right(90)
    
    robot.stop()

runloop.run(main())
