# ------------------------------------------------------------------------------
# PID Controller for LEGO Spike Prime (MicroPython)
# ------------------------------------------------------------------------------
# This file provides a robust PID (Proportional-Integral-Derivative) controller
# class designed to stabilize robot motion, target specific angles, or maintain
# desired sensor readings (like distance or color reflection).
#
# NOTE: In a real Spike Prime environment, replace 'time.time()' with an
# appropriate timer/time tracking mechanism available in the MicroPython runtime.
# ------------------------------------------------------------------------------

import time
# You would typically import spike modules here, e.g.:
# from spike import PrimeHub, Motor, MotorPair
# from spike.control import wait_for_seconds

class PIDController:
    """
    A Proportional-Integral-Derivative (PID) Controller implementation.
    The output is the adjustment needed to reach the setpoint.
    """

    def __init__(self, Kp, Ki, Kd, setpoint, output_limits=(-100, 100), integral_max=1000):
        """
        Initializes the PID controller with coefficients and limits.

        Args:
            Kp (float): Proportional gain.
            Ki (float): Integral gain.
            Kd (float): Derivative gain.
            setpoint (float): The target value the system should achieve.
            output_limits (tuple): Min and Max bounds for the controller output.
            integral_max (float): Maximum value for the integral error accumulator
                                  (anti-windup).
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        self.integral_max = integral_max

        # Error storage
        self.last_error = 0.0
        self.integral = 0.0

        # Time tracking
        self.previous_time = time.time()

    def set_setpoint(self, new_setpoint):
        """Allows dynamic changes to the target value."""
        self.setpoint = new_setpoint
        # Reset integral when changing setpoint to prevent large initial swings
        self.integral = 0.0

    def calculate(self, current_value):
        """
        Calculates the required control output based on the current state.

        Args:
            current_value (float): The system's current measured value (e.g., motor angle, color intensity).

        Returns:
            float: The calculated control output (e.g., motor power/speed).
        """
        current_time = time.time()
        dt = current_time - self.previous_time
        
        # Avoid division by zero and ensure positive time step
        if dt <= 0:
            dt = 0.001 

        # 1. Proportional Term (P)
        error = self.setpoint - current_value
        P_term = self.Kp * error

        # 2. Integral Term (I)
        self.integral += error * dt
        
        # Integral Windup Prevention (Clamping)
        if self.integral > self.integral_max:
            self.integral = self.integral_max
        elif self.integral < -self.integral_max:
            self.integral = -self.integral_max

        I_term = self.Ki * self.integral

        # 3. Derivative Term (D)
        derivative = (error - self.last_error) / dt
        D_term = self.Kd * derivative

        # Total Output
        output = P_term + I_term + D_term

        # Clamp output to defined limits (e.g., -100 to 100 for motor power)
        output = max(min(output, self.output_limits[1]), self.output_limits[0])

        # Update internal state for the next calculation
        self.last_error = error
        self.previous_time = current_time

        return output

# ------------------------------------------------------------------------------
# MOCK USAGE EXAMPLE (Adapt for your specific motors/sensors)
# ------------------------------------------------------------------------------

def run_pid_example():
    """
    Simulates a motor-target control loop.
    In a real application, you would replace the simulated values with
    actual sensor readings and motor commands.
    """
    print("--- Starting PID Control Simulation ---")

    # Define PID constants (These require tuning for your specific robot!)
    # Start small and increase Kp first, then Ki, then Kd.
    KP = 2.0
    KI = 0.001
    KD = 0.5
    TARGET_ANGLE = 90.0  # Target motor angle in degrees

    # Initialize the controller
    pid = PIDController(
        Kp=KP, 
        Ki=KI, 
        Kd=KD, 
        setpoint=TARGET_ANGLE,
        output_limits=(-50, 50) # Max motor speed/power for this example
    )

    # Mock variables for simulation (replace with actual Spike Prime code)
    # mock_motor = Motor('A') 
    mock_current_angle = 0.0 
    loop_count = 0
    
    # Simple loop to simulate the robot attempting to reach the target angle
    while abs(pid.last_error) > 1.0 or loop_count < 10:
        if loop_count > 200: # Safety break for simulation
            break

        # 1. Get current value (REPLACE WITH: mock_current_angle = motor.get_position())
        # mock_current_angle = mock_motor.get_position() 
        
        # Simulate a slow system response for the mock
        if loop_count < 100:
             mock_current_angle += (100 - mock_current_angle) / 50 
        else: # Simulate it getting closer to the target
             mock_current_angle += (TARGET_ANGLE - mock_current_angle) * 0.1 

        
        # 2. Calculate the control output
        motor_power = pid.calculate(mock_current_angle)
        
        # 3. Apply the output (REPLACE WITH: motor.start_at_power(motor_power))
        # mock_motor.start_at_power(motor_power)

        print(f"Loop: {loop_count:3} | Angle: {mock_current_angle:6.2f} | Error: {pid.last_error:6.2f} | Power: {motor_power:6.2f}")

        # Wait a short duration (Essential for control loops)
        time.sleep(0.02) # Use wait_for_seconds(0.02) in Spike Prime

        loop_count += 1
        
    # Final stop command (REPLACE WITH: motor.stop())
    # mock_motor.stop()
    print("\n--- PID Control Finished ---")
    print(f"Final Angle: {mock_current_angle:.2f}, Target: {TARGET_ANGLE:.2f}")

# Uncomment the line below to run the simulation within a standard Python interpreter
# if __name__ == "__main__":
#    run_pid_example()
#
# In Spike Prime, you would integrate the PID loop directly into your main program
# and define your motors and sensors outside this function.
