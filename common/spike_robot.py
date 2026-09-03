# spike_robot.py
# Class for common Spike Prime robot functions

from hub import port, light_matrix, motion_sensor, sound, button
import hub
import motor
import runloop, motor_pair, sys, math, asyncio

WHEEL_CIRCUMFERENCE = 35.0  # Wheel circumference in cm
STABILIZATION_DELAY = 0.2  # Delay in seconds after movements
TURN_COMPENSATION = 5  # Degrees to add to compensate for motor stopping early
DEFAULT_DRIVE_SPEED = 300  # Default speed for driving movements
DEFAULT_ACCESSORY_SPEED = 200  # Default speed for accessory motor movements

class SpikeRobot:
    # Initialize the robot with motor ports (default: B=left, F=right, D=accessory1)
    def __init__(self, left_motor_port=port.B, right_motor_port=port.F, accessory1_port=port.D):
        self.left_motor_port = left_motor_port
        self.right_motor_port = right_motor_port
        self.accessory1_port = accessory1_port
        self.motor_pair_id = motor_pair.PAIR_1

    # Setup motors and reset sensors - call this first before using the robot
    async def setup(self):
        motor_pair.pair(self.motor_pair_id, self.left_motor_port, self.right_motor_port)
        motion_sensor.reset_yaw(0)
        await runloop.until(motion_sensor.stable)

    # Convert distance in cm to motor degrees based on wheel circumference
    def degreesForDistance(self, distance_cm):
        return int((distance_cm / WHEEL_CIRCUMFERENCE) * 360)

    # Reset yaw sensor to 0 for accurate measurements
    async def resetYaw(self):
        motion_sensor.reset_yaw(0)
        await runloop.sleep_ms(50)  # Brief pause for sensor to stabilize

    # Drive straight for a given distance (cm) at specified speed
    # Positive distance = forward, negative = backward
    # Uses acceleration and deceleration to maintain alignment
    async def drive(self, distance, speed):
        # Reset motor positions to ensure synchronized start
        motor.reset_relative_position(self.left_motor_port, 0)
        motor.reset_relative_position(self.right_motor_port, 0)
        await runloop.sleep_ms(10)  # Brief pause for motors to sync
        
        await motor_pair.move_for_degrees(
            self.motor_pair_id, 
            -self.degreesForDistance(distance), 
            0, 
            velocity=speed,
            stop=motor.SMART_BRAKE,
            acceleration=400,
            deceleration=400
        )
        await runloop.sleep_ms(int(STABILIZATION_DELAY * 1000))
        # Wait for hub to be completely stable before returning
        await runloop.until(motion_sensor.stable, timeout=300)
        await self.resetYaw()
        # Extra wait after reset for sensor to stabilize
        await runloop.sleep_ms(50)

    # Drive forward by specified distance (cm) at specified speed
    async def drive_forward(self, distance, speed=None):
        light_matrix.show_image(light_matrix.IMAGE_ARROW_E)
        if speed is None:
            speed = DEFAULT_DRIVE_SPEED
        await self.drive(distance, speed)
    
    # Drive backward by specified distance (cm) at specified speed
    async def drive_backward(self, distance, speed=None):
        light_matrix.show_image(light_matrix.IMAGE_ARROW_W)
        if speed is None:
            speed = DEFAULT_DRIVE_SPEED
        await self.drive(-distance, speed)

    # Turn the robot by a specific angle (degrees) using gyro sensor
    # Positive angle = turn right, negative = turn left
    # Always uses speed 100 for consistent, accurate turns
    async def turn(self, angle):
        # Reset yaw to 0 before each turn for consistent measurements
        await self.resetYaw()
        
        # Wait for sensor to fully stabilize after reset
        await runloop.until(motion_sensor.stable, timeout=100)
        
        # Add compensation to slightly overshoot (motors stop early when braking)
        target_yaw = angle + (TURN_COMPENSATION if angle > 0 else -TURN_COMPENSATION)
        turn_speed = 100  # Fixed speed for accuracy
        correction_speed = 20  # Very slow speed for fine adjustments
        
        # Turn at full speed to target angle with compensation
        if angle > 0:
            motor_pair.move_tank(self.motor_pair_id, turn_speed, -turn_speed)
            while (motion_sensor.tilt_angles()[0] * -0.1) < target_yaw:
                await runloop.sleep_ms(1)
        else:
            motor_pair.move_tank(self.motor_pair_id, -turn_speed, turn_speed)
            while (motion_sensor.tilt_angles()[0] * -0.1) > target_yaw:
                await runloop.sleep_ms(1)
        
        motor_pair.stop(self.motor_pair_id, stop=motor.SMART_BRAKE)
        
        # Wait for hub to stabilize
        await runloop.sleep_ms(int(STABILIZATION_DELAY * 1000))
        await runloop.until(motion_sensor.stable, timeout=200)
        
        # Perform correction phase to reach exact angle
        current_yaw = motion_sensor.tilt_angles()[0] * -0.1
        error = angle - current_yaw
        
        # Only correct if error is significant (> 2 degrees)
        if abs(error) > 2:
            if error > 0:
                # Under-rotated - need to turn more to the right
                correction_target = angle - 2
                motor_pair.move_tank(self.motor_pair_id, correction_speed, -correction_speed)
                while (motion_sensor.tilt_angles()[0] * -0.1) < correction_target:
                    await runloop.sleep_ms(1)
                motor_pair.stop(self.motor_pair_id, stop=motor.SMART_BRAKE)
                await runloop.sleep_ms(150)
                await runloop.until(motion_sensor.stable, timeout=150)
            else:
                # Over-rotated - need to turn back to the left
                correction_target = angle + 2
                motor_pair.move_tank(self.motor_pair_id, -correction_speed, correction_speed)
                while (motion_sensor.tilt_angles()[0] * -0.1) > correction_target:
                    await runloop.sleep_ms(1)
                motor_pair.stop(self.motor_pair_id, stop=motor.SMART_BRAKE)
                await runloop.sleep_ms(150)
                await runloop.until(motion_sensor.stable, timeout=150)

    # Turn right by specified degrees
    async def turn_right(self, angle):
        light_matrix.show_image(light_matrix.IMAGE_ARROW_S)
        await self.turn(angle)
    
    # Turn left by specified degrees
    async def turn_left(self, angle):
        light_matrix.show_image(light_matrix.IMAGE_ARROW_N)
        await self.turn(-angle)

    # Drive in an arc with steering (-100 to 100)
    # steering: -100=sharp left, 0=straight, 100=sharp right
    async def arc(self, distance, speed, steering):
        await motor_pair.move_for_degrees(
            self.motor_pair_id, 
            -self.degreesForDistance(distance), 
            steering, 
            velocity=speed,
            stop=motor.SMART_BRAKE
        )
        await runloop.sleep_ms(int(STABILIZATION_DELAY * 1000))
        await self.resetYaw()

    # Stop all motors immediately
    def stop(self):
        motor_pair.stop(self.motor_pair_id)
        motor.stop(self.accessory1_port)

    # Rotate accessory 1 to the left (counter-clockwise) by specified degrees at given speed
    async def acc1_rotate_left(self, degrees, speed=None):
        light_matrix.write("A1")
        if speed is None:
            speed = DEFAULT_ACCESSORY_SPEED
        await motor.run_for_degrees(self.accessory1_port, -degrees, speed)
    
    # Rotate accessory 1 to the right (clockwise) by specified degrees at given speed
    async def acc1_rotate_right(self, degrees, speed=None):
        light_matrix.write("A1")
        if speed is None:
            speed = DEFAULT_ACCESSORY_SPEED
        await motor.run_for_degrees(self.accessory1_port, degrees, speed)
