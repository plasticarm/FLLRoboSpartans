from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Button, Color
from pybricks.robotics import DriveBase
from pybricks.iodevices import XboxController
from pybricks.tools import wait, StopWatch
import ustruct

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
SLOT_COUNT = 10
SLOT_SIZE = 51
MAX_MOVES_PER_SLOT = 5
recorded_moves = []
recording_slots = [[] for _ in range(SLOT_COUNT)]
selected_slot = 1
python_script_output = []
is_recording = False
is_playing = False
playback_index = 0
playback_clock = 0

use_gyro_global = True
drive_base.use_gyro(use_gyro_global)

recorded_time = 0
prev_inputs = (0, 0, 0, 0, 0, 1) 
prev_record, prev_play = False, False
prev_hub_left, prev_hub_right, prev_hub_center = False, False, False
prev_dpad_right, prev_dpad_down, prev_dpad_left = False, False, False
prev_y = False

# Telemetry Tracking Variables
TelemetryDisplayTime = 6000 
telemetry_timer = StopWatch()
is_displaying_telemetry = False

moving_y, start_dist, max_d_speed = False, 0, 0
moving_x, start_angle, max_d_turn = False, 0, 0
moving_a, start_a, max_a_duty = False, 0, 0
moving_b, start_b, max_b_duty = False, 0, 0
record_start_a, record_start_b = 0, 0


def load_recording_slots():
    slots = []
    for slot_index in range(SLOT_COUNT):
        try:
            data = hub.system.storage(slot_index * SLOT_SIZE, read=SLOT_SIZE)
            move_count = data[0]
            if move_count > MAX_MOVES_PER_SLOT:
                move_count = 0
            moves = []
            for move_index in range(move_count):
                offset = 1 + move_index * 10
                move = ustruct.unpack("<HhhbbB", data[offset:offset + 9])
                moves.append((move[0], move[1], move[2], move[3], move[4], move[5] & 1, (move[5] >> 1) & 1))
            slots.append(moves)
        except Exception:
            slots.append([])
    return slots


def save_recording_slot(slot_index, moves):
    if len(moves) > MAX_MOVES_PER_SLOT:
        return False

    data = bytearray(SLOT_SIZE)
    data[0] = len(moves)
    for move_index, move in enumerate(moves):
        timestamp, speed, turn, a_duty, b_duty, play_brake, play_gyro = move
        offset = 1 + move_index * 10
        data[offset:offset + 9] = ustruct.pack(
            "<HhhbbB",
            max(0, min(65535, round(timestamp))),
            max(-32768, min(32767, round(speed))),
            max(-32768, min(32767, round(turn))),
            max(-128, min(127, round(a_duty))),
            max(-128, min(127, round(b_duty))),
            int(play_brake) | (int(play_gyro) << 1),
        )
    try:
        hub.system.storage(slot_index * SLOT_SIZE, write=bytes(data))
        return True
    except Exception as error:
        print(f">>> ERROR: Could not save slot {slot_index + 1}: {error}")
        return False


recording_slots = load_recording_slots()

print("\n>>> System Ready. Waiting for input...")
hub.display.number(selected_slot)

while True:
    # 1. Hub Button Reading
    hub_pressed = hub.buttons.pressed()
    hub_left_pressed = Button.LEFT in hub_pressed
    hub_right_pressed = Button.RIGHT in hub_pressed
    hub_center_pressed = Button.CENTER in hub_pressed

    # 2. Controller Reading
    if has_controller:
        pressed = controller.buttons.pressed()
        triggers = controller.triggers()
        left_stick = controller.joystick_left()
        right_stick = controller.joystick_right()
    else:
        pressed, triggers, left_stick, right_stick = [], (0, 0), (0, 0), (0, 0)

    record_pressed = Button.VIEW in pressed 
    play_pressed = Button.MENU in pressed
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
        use_gyro_global = not use_gyro_global
        drive_base.use_gyro(use_gyro_global)
        cmd = f"ToggleYawCorrection({use_gyro_global})"
        print(cmd)
        if is_recording: python_script_output.append(cmd)
        if use_gyro_global: hub.speaker.beep(600, 100) 
        else: hub.speaker.beep(200, 100) 

    # Active Brake Toggle (Y Button)
    if y_held and not prev_y:
        cmd = "Stop()"
        print(cmd)
        if is_recording: python_script_output.append(cmd)

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

    if not is_recording and not is_playing:
        if hub_right_pressed and not prev_hub_right:
            selected_slot = (selected_slot % SLOT_COUNT) + 1
            hub.display.number(selected_slot)
            hub.speaker.beep(400, 100)
            print(f">>> Selected recording slot {selected_slot}.")
        elif hub_left_pressed and not prev_hub_left:
            selected_slot = SLOT_COUNT if selected_slot == 1 else selected_slot - 1
            hub.display.number(selected_slot)
            hub.speaker.beep(400, 100)
            print(f">>> Selected recording slot {selected_slot}.")

    # Toggle Recording (Xbox VIEW)
    if record_pressed and not prev_record:
        if not is_playing:
            is_recording = not is_recording
            if is_recording:
                drive_base.stop()
                wait(100)
                hub.imu.reset_heading(0)
                
                recorded_moves = []
                python_script_output.clear()
                recorded_time = 0
                prev_inputs = (0, 0, 0, 0, 0, 1)
                
                record_start_a = motor_a.angle()
                record_start_b = motor_b.angle()
                
                hub.display.char("R")
                is_displaying_telemetry = False
                print(f"\n========================================")
                print(f">>> RECORDING STARTED <<<")
                print(f"========================================")
                hub.speaker.beep(1000, 300)
            else:
                if save_recording_slot(selected_slot - 1, recorded_moves):
                    recording_slots[selected_slot - 1] = recorded_moves[:]
                    save_message = f">>> Saved {len(recorded_moves)} moves to persistent slot {selected_slot}."
                else:
                    save_message = f">>> ERROR: Slot {selected_slot} holds at most {MAX_MOVES_PER_SLOT} recorded moves."
                hub.display.char("-")
                print(f"\n========================================")
                print(f">>> RECORDING STOPPED.")
                print(save_message)
                print(f"========================================")
                print("\n# --- GENERATED PYTHON SCRIPT ---")
                for command in python_script_output:
                    print(command)
                print("# ----------------------------------------------------\n")

    # Toggle Playback (Controller MENU or Hub CENTER)
    if (play_pressed and not prev_play) or (hub_center_pressed and not prev_hub_center):
        if is_recording:
            print("\n>>> ERROR: Cannot start playback while recording is active.")
        elif len(recording_slots[selected_slot - 1]) == 0:
            print(f"\n>>> ERROR: Playback failed. Slot {selected_slot} is empty.")
            hub.speaker.beep(100, 200)
        else:
            recorded_moves = recording_slots[selected_slot - 1]
            is_playing = not is_playing
            if is_playing:
                print(f"\n========================================")
                print(f">>> STARTING PLAYBACK: Slot {selected_slot}, executing {len(recorded_moves)} commands.")
                print(f"========================================")
                hub.speaker.beep(600, 100)
                hub.speaker.beep(800, 200)
                drive_base.stop()
                wait(100)
                hub.imu.reset_heading(0)
                
                playback_clock = 0
                playback_index = 0
                hub.display.char("P")
                is_displaying_telemetry = False
            else:
                print("\n>>> PLAYBACK CANCELLED manually.")
                drive_base.stop()
                motor_a.stop()
                motor_b.stop()
                hub.display.char("-")

    # Execution Loops
    if is_playing:
        playback_clock += (50 * speed_mult)
        if playback_index < len(recorded_moves):
            t, d_speed, d_turn, a_duty, b_duty, play_brake, play_gyro = recorded_moves[playback_index]
            
            if playback_clock >= t:
                play_d_speed = d_speed * speed_mult
                play_d_turn = d_turn * speed_mult
                play_a_duty = max(min(a_duty * speed_mult, 100), -100)
                play_b_duty = max(min(b_duty * speed_mult, 100), -100)

                drive_base.use_gyro(bool(play_gyro))

                if play_brake:
                    left_motor.hold()
                    right_motor.hold()
                else:
                    drive_base.drive(play_d_speed, play_d_turn)

                motor_a.dc(play_a_duty)
                motor_b.dc(play_b_duty)
                playback_index += 1
        else:
            is_playing = False
            print("\n>>> PLAYBACK FINISHED successfully.")
            drive_base.stop()
            motor_a.stop()
            motor_b.stop()
            hub.display.char("-")
            
    elif has_controller:
        # Manual Teleoperation
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

        if is_recording:
            current_inputs = (d_speed, d_turn, a_duty, b_duty, int(y_held), int(use_gyro_global))
            if current_inputs != (0, 0, 0, 0, 0, 1) or prev_inputs != (0, 0, 0, 0, 0, 1):
                recorded_time += 50
                recorded_moves.append((recorded_time, d_speed, d_turn, a_duty, b_duty, int(y_held), int(use_gyro_global)))
            prev_inputs = current_inputs

        # 1. Autonomous Command Generation: Distance
        if d_speed != 0 and not moving_y:
            moving_y = True
            start_dist = drive_base.distance()
            max_d_speed = abs(d_speed)
        elif d_speed != 0 and moving_y:
            max_d_speed = max(max_d_speed, abs(d_speed))
        elif d_speed == 0 and moving_y:
            moving_y = False
            dist_cm = round((drive_base.distance() - start_dist) / 10.0)
            if abs(dist_cm) >= 1:
                hub.display.number(abs(dist_cm))
                cmd = f"Drive({round(max_d_speed)}, {dist_cm})"
                print(cmd)
                if is_recording: python_script_output.append(cmd)
            telemetry_timer.reset()
            is_displaying_telemetry = True

        # 2. Autonomous Command Generation: Rotation
        if d_turn != 0 and not moving_x:
            moving_x = True
            start_angle = drive_base.angle()
            max_d_turn = abs(d_turn)
        elif d_turn != 0 and moving_x:
            max_d_turn = max(max_d_turn, abs(d_turn))
        elif d_turn == 0 and moving_x:
            moving_x = False
            rot_deg = round(drive_base.angle() - start_angle)
            if abs(rot_deg) > 2:
                hub.display.number(abs(rot_deg))
                cmd = f"Rotate({round(max_d_turn)}, {rot_deg})"
                print(cmd)
                if is_recording: python_script_output.append(cmd)
            telemetry_timer.reset()
            is_displaying_telemetry = True

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
                hub.display.number(abs(a_deg))
                cmd = f"LeftAttachmentRotate({round(max_a_duty)}, {a_deg})"
                print(cmd)
                if is_recording: python_script_output.append(cmd)
            telemetry_timer.reset()
            is_displaying_telemetry = True

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
                hub.display.number(abs(b_deg))
                cmd = f"RightAttachmentRotate({round(max_b_duty)}, {b_deg})"
                print(cmd)
                if is_recording: python_script_output.append(cmd)
            telemetry_timer.reset()
            is_displaying_telemetry = True

    if is_displaying_telemetry and telemetry_timer.time() > TelemetryDisplayTime:
        hub.display.off()
        is_displaying_telemetry = False

    # Debouncing Updates
    prev_record = record_pressed
    prev_play = play_pressed
    prev_hub_left = hub_left_pressed
    prev_hub_right = hub_right_pressed
    prev_hub_center = hub_center_pressed
    prev_dpad_right = dpad_right_pressed
    prev_dpad_down = dpad_down_pressed
    prev_dpad_left = dpad_left_pressed
    prev_y = y_held

    wait(50)