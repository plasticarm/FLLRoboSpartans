from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Button, Color
from pybricks.robotics import DriveBase
from pybricks.iodevices import XboxController
from pybricks.tools import wait

hub = PrimeHub()

# IMU Initialization
print("\n>>> Calibrating Gyro - Keep robot still!")
wait(500)
hub.imu.reset_heading(0)

# Hardware Initialization
left_motor = Motor(Port.B, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.F)
drive_base = DriveBase(left_motor, right_motor, wheel_diameter=88, axle_track=107)
drive_base.settings(straight_speed=500, straight_acceleration=500, turn_rate=300, turn_acceleration=300)

motor_a = Motor(Port.A)
motor_b = Motor(Port.E, Direction.COUNTERCLOCKWISE)

# Input Scaling & Deadzone
DRIVE_MAX_SPEED = 220
PRECISION_TURN_RATE = 25
TURN_RATE = 90

def apply_deadzone(stick, threshold=10):
    if -threshold <= stick <= threshold:
        return 0.0
    elif stick > threshold:
        return ((stick - threshold) / (100.0 - threshold)) * 100.0
    else:
        return ((stick + threshold) / (100.0 - threshold)) * 100.0

def exp_scale(value, max_output):
    return (value / 100.0) * abs(value / 100.0) * max_output

# Connect Xbox Controller
has_controller = False
try:
    hub.light.on(Color.RED)
    controller = XboxController()
    hub.light.on(Color.GREEN)
    has_controller = True
    print(">>> Xbox Controller Connected!")
except Exception:
    hub.light.on(Color.BLUE)
    print(">>> Running in Hub-Only Competition Mode")

# State Variables
is_recording = False

use_gyro_global = True
drive_base.use_gyro(use_gyro_global)

prev_record = False
prev_dpad_right, prev_dpad_down, prev_dpad_left = False, False, False
prev_y = False

moving_y, start_dist, max_d_speed = False, 0, 0
moving_x, last_heading, accumulated_turn, max_d_turn = False, 0, 0, 0
moving_a, start_a, max_a_duty = False, 0, 0
moving_b, start_b, max_b_duty = False, 0, 0
record_start_a, record_start_b = 0, 0
suppress_drive_until_stop = False

def heading_delta(current_heading, previous_heading):
    delta = current_heading - previous_heading
    if delta > 180:
        delta -= 360
    elif delta < -180:
        delta += 360
    return delta

def emit_command(cmd):
    if is_recording:
        print(cmd)

def finish_active_commands():
    global moving_y, moving_x, moving_a, moving_b, accumulated_turn, last_heading, suppress_drive_until_stop

    if moving_y:
        moving_y = False
        dist_cm = round((drive_base.distance() - start_dist) / 10.0)
        if abs(dist_cm) >= 1:
            emit_command(f"Drive({round(max_d_speed)}, {dist_cm})")

    if moving_x:
        current_heading = hub.imu.heading()
        accumulated_turn += heading_delta(current_heading, last_heading)
        last_heading = current_heading
        moving_x = False
        rot_deg = round(accumulated_turn)
        if abs(rot_deg) > 2:
            emit_command(f"Rotate({round(max_d_turn)}, {rot_deg})")
        accumulated_turn = 0
        suppress_drive_until_stop = True

    if moving_a:
        moving_a = False
        a_deg = round(motor_a.angle() - start_a)
        if abs(a_deg) > 2:
            emit_command(f"LeftAttachmentRotate({round(max_a_duty)}, {a_deg})")

    if moving_b:
        moving_b = False
        b_deg = round(motor_b.angle() - start_b)
        if abs(b_deg) > 2:
            emit_command(f"RightAttachmentRotate({round(max_b_duty)}, {b_deg})")

print("\n>>> System Ready. Waiting for input...")

while True:
    # 1. Controller Reading
    if has_controller:
        pressed = controller.buttons.pressed()
        triggers = controller.triggers()
        left_stick = controller.joystick_left()
        right_stick = controller.joystick_right()
    else:
        pressed, triggers, left_stick, right_stick = [], (0, 0), (0, 0), (0, 0)

    record_pressed = Button.VIEW in pressed 
    dpad_right_pressed = Button.RIGHT in pressed
    dpad_down_pressed = Button.DOWN in pressed
    dpad_left_pressed = Button.LEFT in pressed
    
    x_held = Button.X in pressed
    y_held = Button.Y in pressed
    a_held = Button.A in pressed
    b_held = Button.B in pressed
    lb_pressed = Button.LB in pressed
    rb_pressed = Button.RB in pressed

    # Global Gyro Toggle (D-Pad Right)
    if dpad_right_pressed and not prev_dpad_right:
        finish_active_commands()
        use_gyro_global = not use_gyro_global
        drive_base.use_gyro(use_gyro_global)
        emit_command(f"ToggleYawCorrection({use_gyro_global})")
        if use_gyro_global: hub.speaker.beep(600, 100) 
        else: hub.speaker.beep(200, 100) 

    # Active Brake Toggle (Y Button)
    if y_held and not prev_y:
        finish_active_commands()
        emit_command("Stop()")

    # Attachment Reset (D-Pad Down)
    if dpad_down_pressed:
        motor_a.run_target(500, record_start_a, wait=False)
        motor_b.run_target(500, record_start_b, wait=True)
        motor_a.run_target(500, record_start_a, wait=True) 

    if motor_a.stalled() or motor_b.stalled():
        if has_controller: controller.rumble(100)
    else:
        if has_controller: controller.rumble(0)

    speed_mult = 1.0
    if a_held: speed_mult = 2.0  
    elif b_held: speed_mult = 0.4  

    # Toggle Recording (Xbox VIEW)
    if record_pressed and not prev_record:
        if is_recording:
            finish_active_commands()
            is_recording = False
            hub.speaker.beep(500, 300)
            print("# ----------------------------------------------------")
            print(">>> RECORDING STOPPED. Copy the commands above into MissionRunner.py.")
        else:
            drive_base.stop()
            wait(100)
            hub.imu.reset_heading(0)

            record_start_a = motor_a.angle()
            record_start_b = motor_b.angle()
            moving_y, moving_x, moving_a, moving_b = False, False, False, False
            accumulated_turn = 0
            suppress_drive_until_stop = False

            is_recording = True
            print("\n# --- GENERATED PYTHON SCRIPT ---")
            hub.speaker.beep(1000, 300)

    if has_controller:
        # Manual Teleoperation
        left_x = apply_deadzone(left_stick[0])
        left_y = apply_deadzone(left_stick[1])
        right_x = apply_deadzone(right_stick[0])
        left_trigger = apply_deadzone(triggers[0])
        right_trigger = apply_deadzone(triggers[1])

        d_speed_base = exp_scale(left_y, DRIVE_MAX_SPEED) 
        left_turn_base = exp_scale(left_x, PRECISION_TURN_RATE) if x_held else 0
        right_turn_base = exp_scale(right_x, TURN_RATE)
        
        d_turn_base = left_turn_base + right_turn_base
        
        a_duty_base = exp_scale(right_trigger, 50) - (50 if rb_pressed else 0)
        b_duty_base = (50 if lb_pressed else 0) - exp_scale(left_trigger, 50)

        d_speed = d_speed_base * speed_mult
        d_turn = d_turn_base * speed_mult
        a_duty = max(min(a_duty_base * speed_mult, 100), -100)
        b_duty = max(min(b_duty_base * speed_mult, 100), -100)

        if y_held:
            left_motor.hold()
            right_motor.hold()
            d_speed = 0
            d_turn = 0
        elif not dpad_down_pressed:
            drive_base.drive(d_speed, d_turn)

        motor_a.dc(a_duty)
        motor_b.dc(b_duty)

        # 1. Autonomous Command Generation: Rotation
        if d_turn != 0 and not moving_x:
            if moving_y:
                moving_y = False
                dist_cm = round((drive_base.distance() - start_dist) / 10.0)
                if abs(dist_cm) >= 1:
                    emit_command(f"Drive({round(max_d_speed)}, {dist_cm})")
            moving_x = True
            last_heading = hub.imu.heading()
            accumulated_turn = 0
            max_d_turn = abs(d_turn)
        elif d_turn != 0 and moving_x:
            current_heading = hub.imu.heading()
            accumulated_turn += heading_delta(current_heading, last_heading)
            last_heading = current_heading
            max_d_turn = max(max_d_turn, abs(d_turn))
        elif d_turn == 0 and moving_x:
            current_heading = hub.imu.heading()
            accumulated_turn += heading_delta(current_heading, last_heading)
            last_heading = current_heading
            moving_x = False
            rot_deg = round(accumulated_turn)
            if abs(rot_deg) > 2:
                emit_command(f"Rotate({round(max_d_turn)}, {rot_deg})")
            accumulated_turn = 0
            suppress_drive_until_stop = True

        # 2. Autonomous Command Generation: Distance
        if d_speed == 0:
            suppress_drive_until_stop = False

        if d_turn != 0 or suppress_drive_until_stop:
            if moving_y:
                moving_y = False
                dist_cm = round((drive_base.distance() - start_dist) / 10.0)
                if abs(dist_cm) >= 1:
                    emit_command(f"Drive({round(max_d_speed)}, {dist_cm})")
        elif d_speed != 0 and not moving_y:
            moving_y = True
            start_dist = drive_base.distance()
            max_d_speed = abs(d_speed)
        elif d_speed != 0 and moving_y:
            max_d_speed = max(max_d_speed, abs(d_speed))
        elif d_speed == 0 and moving_y:
            moving_y = False
            dist_cm = round((drive_base.distance() - start_dist) / 10.0)
            if abs(dist_cm) >= 1:
                emit_command(f"Drive({round(max_d_speed)}, {dist_cm})")

        # 3. Autonomous Command Generation: Motor A
        if a_duty != 0 and not moving_a:
            moving_a = True
            start_a = motor_a.angle()
            max_a_duty = abs(a_duty)
        elif a_duty != 0 and moving_a:
            max_a_duty = max(max_a_duty, abs(a_duty))
        elif a_duty == 0 and moving_a:
            moving_a = False
            a_deg = round(motor_a.angle() - start_a)
            if abs(a_deg) > 2:
                emit_command(f"LeftAttachmentRotate({round(max_a_duty)}, {a_deg})")

        # 4. Autonomous Command Generation: Motor B
        if b_duty != 0 and not moving_b:
            moving_b = True
            start_b = motor_b.angle()
            max_b_duty = abs(b_duty)
        elif b_duty != 0 and moving_b:
            max_b_duty = max(max_b_duty, abs(b_duty))
        elif b_duty == 0 and moving_b:
            moving_b = False
            b_deg = round(motor_b.angle() - start_b)
            if abs(b_deg) > 2:
                emit_command(f"RightAttachmentRotate({round(max_b_duty)}, {b_deg})")

    # Debouncing Updates
    prev_record = record_pressed
    prev_dpad_right = dpad_right_pressed
    prev_dpad_down = dpad_down_pressed
    prev_dpad_left = dpad_left_pressed
    prev_y = y_held

    wait(50)