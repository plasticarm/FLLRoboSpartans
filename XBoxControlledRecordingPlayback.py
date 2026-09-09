from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Button, Color
from pybricks.robotics import DriveBase
from pybricks.iodevices import XboxController
from pybricks.tools import wait, StopWatch

hub = PrimeHub()

# 1. IMU Initialization
# Wait briefly to ensure the robot is completely still on the mat, then reset the gyro heading
print("Calibrating Gyro - Keep robot still!")
wait(500)
hub.imu.reset_heading(0)

# Hardware Initialization & Acceleration Ramping
left_motor = Motor(Port.B, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.F)
drive_base = DriveBase(left_motor, right_motor, wheel_diameter=88, axle_track=107)
drive_base.settings(straight_speed=500, straight_acceleration=500, turn_rate=300, turn_acceleration=300)

# 2. Enable Active Yaw Correction
# Links the hub's internal gyroscope to the DriveBase to automatically correct drift
drive_base.use_gyro(True)

motor_a = Motor(Port.A)
motor_b = Motor(Port.E)

# File Handling for Persistent Memory
def load_recording():
    loaded_moves = []
    try:
        with open("path_data.txt", "r") as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) == 5:
                    loaded_moves.append((int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])))
    except OSError:
        pass
    return loaded_moves

def save_recording(moves):
    try:
        with open("path_data.txt", "w") as file:
            for t, d_speed, d_turn, a_duty, b_duty in moves:
                file.write(f"{t},{d_speed},{d_turn},{a_duty},{b_duty}\n")
    except Exception:
        pass

# Input Scaling & Deadzone
def apply_deadzone(stick, threshold=7):
    if -threshold <= stick <= threshold:
        return 0.0
    elif stick > threshold:
        return ((stick - threshold) / (100.0 - threshold)) * 100.0
    else:
        return ((stick + threshold) / (100.0 - threshold)) * 100.0

def exp_scale(value, max_output):
    return (value / 100.0) * abs(value / 100.0) * max_output

# Connect Xbox Controller
hub.light.on(Color.RED)
controller = XboxController()
hub.light.on(Color.GREEN)

# State Variables
recorded_moves = load_recording()
python_script_output = []
is_recording = False
is_playing = False
playback_index = 0
playback_clock = 0

recorded_time = 0
prev_inputs = (0, 0, 0, 0)
prev_record, prev_play, prev_hub_left, prev_hub_right = False, False, False, False

# Telemetry Tracking Variables
TelemetryDisplayTime = 6000 
telemetry_timer = StopWatch()
is_displaying_telemetry = False

moving_y = False
start_dist = 0
last_d_speed = 0

moving_x = False
start_angle = 0
last_d_turn = 0

moving_a = False
start_a = 0
last_a_duty = 0

moving_b = False
start_b = 0
last_b_duty = 0

while True:
    pressed = controller.buttons.pressed()
    triggers = controller.triggers()
    left_stick = controller.joystick_left()
    right_stick = controller.joystick_right()
    hub_pressed = hub.buttons.pressed()

    record_pressed = Button.VIEW in pressed 
    play_pressed = Button.MENU in pressed
    
    x_held = Button.X in pressed
    a_held = Button.A in pressed
    b_held = Button.B in pressed
    lb_pressed = Button.LB in pressed
    rb_pressed = Button.RB in pressed
    hub_left_pressed = Button.LEFT in hub_pressed
    hub_right_pressed = Button.RIGHT in hub_pressed

    if Button.UP in pressed:
        hub.speaker.beep(400, 100) 

    # Haptic Feedback based on Motor Resistance
    if motor_a.stalled() or motor_b.stalled():
        controller.rumble(100)
    else:
        controller.rumble(0)

    speed_mult = 1.0
    if a_held:
        speed_mult = 2.0  
    elif b_held:
        speed_mult = 0.4  

    # Toggle Recording 
    if (record_pressed and not prev_record) or (hub_left_pressed and not prev_hub_left):
        if not is_playing:
            is_recording = not is_recording
            if is_recording:
                # Reset the IMU heading when recording starts for a fresh zero-point
                hub.imu.reset_heading(0)

                recorded_moves.clear()
                python_script_output.clear()
                recorded_time = 0
                prev_inputs = (0, 0, 0, 0)
                hub.display.char("R")
                is_displaying_telemetry = False
                print("\n--- RECORDING STARTED ---")
            else:
                hub.display.char("-")
                save_recording(recorded_moves)
                
                print("\n# --- GENERATED PYTHON SCRIPT ---")
                for command in python_script_output:
                    print(command)
                print("# -------------------------------\n")

    # Toggle Playback 
    if (play_pressed and not prev_play) or (hub_right_pressed and not prev_hub_right):
        if not is_recording and len(recorded_moves) > 0:
            is_playing = not is_playing
            if is_playing:
                # Reset the IMU heading when playback starts to match recording conditions
                hub.imu.reset_heading(0)

                playback_clock = 0
                playback_index = 0
                hub.display.char("P")
                is_displaying_telemetry = False
            else:
                drive_base.stop()
                motor_a.stop()
                motor_b.stop()
                hub.display.char("-")

    if is_playing:
        playback_clock += (50 * speed_mult)
        if playback_index < len(recorded_moves):
            t, d_speed, d_turn, a_duty, b_duty = recorded_moves[playback_index]
            
            if playback_clock >= t:
                play_d_speed = d_speed * speed_mult
                play_d_turn = d_turn * speed_mult
                play_a_duty = max(min(a_duty * speed_mult, 100), -100)
                play_b_duty = max(min(b_duty * speed_mult, 100), -100)

                drive_base.drive(play_d_speed, play_d_turn)
                motor_a.dc(play_a_duty)
                motor_b.dc(play_b_duty)
                playback_index += 1
        else:
            is_playing = False
            drive_base.stop()
            motor_a.stop()
            motor_b.stop()
            hub.display.char("-")
            
    else:
        left_x = apply_deadzone(left_stick[0])
        left_y = apply_deadzone(left_stick[1])
        right_x = apply_deadzone(right_stick[0])
        left_trigger = apply_deadzone(triggers[0])
        right_trigger = apply_deadzone(triggers[1])

        d_speed_base = exp_scale(left_y, 250) 
        left_turn_base = exp_scale(left_x, 37.5) if x_held else 0
        right_turn_base = exp_scale(right_x, 150)
        
        d_turn_base = left_turn_base + right_turn_base
        
        a_duty_base = exp_scale(right_trigger, 50) - (50 if rb_pressed else 0)
        b_duty_base = exp_scale(left_trigger, 50) - (50 if lb_pressed else 0)

        d_speed = d_speed_base * speed_mult
        d_turn = d_turn_base * speed_mult
        a_duty = max(min(a_duty_base * speed_mult, 100), -100)
        b_duty = max(min(b_duty_base * speed_mult, 100), -100)

        drive_base.drive(d_speed, d_turn)
        motor_a.dc(a_duty)
        motor_b.dc(b_duty)

        if is_recording:
            current_inputs = (d_speed, d_turn, a_duty, b_duty)
            if current_inputs != (0, 0, 0, 0) or prev_inputs != (0, 0, 0, 0):
                recorded_time += 50
                recorded_moves.append((recorded_time, d_speed, d_turn, a_duty, b_duty))
            prev_inputs = current_inputs

        # 1. Python Code Translation: Distance
        if d_speed != 0 and not moving_y:
            moving_y = True
            start_dist = drive_base.distance()
            last_d_speed = d_speed
        elif d_speed == 0 and moving_y:
            moving_y = False
            dist_cm = round((drive_base.distance() - start_dist) / 10.0)
            hub.display.number(dist_cm)
            
            cmd = f"Drive({round(last_d_speed)}, {dist_cm})"
            print(cmd)
            if is_recording:
                python_script_output.append(cmd)
                
            telemetry_timer.reset()
            is_displaying_telemetry = True

        # 2. Python Code Translation: Rotation
        if d_turn != 0 and not moving_x:
            moving_x = True
            start_angle = drive_base.angle()
            last_d_turn = d_turn
        elif d_turn == 0 and moving_x:
            moving_x = False
            rot_deg = round(drive_base.angle() - start_angle)
            hub.display.number(rot_deg)
            
            cmd = f"Rotate({round(last_d_turn)}, {rot_deg})"
            print(cmd)
            if is_recording:
                python_script_output.append(cmd)
                
            telemetry_timer.reset()
            is_displaying_telemetry = True

        # 3. Python Code Translation: Motor A
        if a_duty != 0 and not moving_a:
            moving_a = True
            start_a = motor_a.angle()
            last_a_duty = a_duty
        elif a_duty == 0 and moving_a:
            moving_a = False
            a_deg = round(motor_a.angle() - start_a)
            hub.display.number(a_deg)
            
            cmd = f"LeftAttachmentRotate({round(last_a_duty)}, {a_deg})"
            print(cmd)
            if is_recording:
                python_script_output.append(cmd)
                
            telemetry_timer.reset()
            is_displaying_telemetry = True

        # 4. Python Code Translation: Motor B
        if b_duty != 0 and not moving_b:
            moving_b = True
            start_b = motor_b.angle()
            last_b_duty = b_duty
        elif b_duty == 0 and moving_b:
            moving_b = False
            b_deg = round(motor_b.angle() - start_b)
            hub.display.number(b_deg)
            
            cmd = f"RightAttachmentRotate({round(last_b_duty)}, {b_deg})"
            print(cmd)
            if is_recording:
                python_script_output.append(cmd)
                
            telemetry_timer.reset()
            is_displaying_telemetry = True

    if is_displaying_telemetry and telemetry_timer.time() > TelemetryDisplayTime:
        hub.display.off()
        is_displaying_telemetry = False

    prev_record = record_pressed
    prev_play = play_pressed
    prev_hub_left = hub_left_pressed
    prev_hub_right = hub_right_pressed

    wait(50)