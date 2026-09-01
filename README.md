# Montour Robospartans Spike Prime Robot Control

This project provides Python code to control a LEGO Spike Prime robot. It includes a main script and a separate class for common robot functions such as driving and turning.

## Project Structure
```
montour-robospartans/
├── main.py                      # Main robot program (upload to hub)
├── export_common.py             # Generated export script (upload to hub)
├── common/
│   ├── spike_robot.py          # SpikeRobot class source (edit this)
│   ├── generate_export.py      # Helper to generate export_common.py
│   ├── export_common.py        # Export script template (not used)
│   └── test_spike_robot.py     # Unit tests for local testing
└── README.md
```

## Requirements
- **On your computer:** Python 3.x
- **On the hub:** LEGO Spike Prime with Python firmware

## Development Workflow

### 1. Edit Robot Code
Edit `common/spike_robot.py` to add or modify robot functions like drive, turn, etc.

### 2. Generate Export Script
Run this on your computer to regenerate `export_common.py` from your latest changes:
```bash
python3 common/generate_export.py
```

### 3. Upload to Hub
Using the LEGO SPIKE app, upload these two files to the hub:
1. `export_common.py` (generated from step 2)
2. `main.py`

### 4. Run on Hub
In the LEGO SPIKE app:
1. **First time only:** Run `export_common.py` to create `common.py` on the hub
2. Run `main.py` to execute your robot program

### 5. Update Code
Whenever you modify `common/spike_robot.py`:
- Repeat steps 2-4 to sync changes to the hub

## Testing Locally
Run unit tests on your computer (not on the hub):
```bash
python3 common/test_spike_robot.py
```

## SpikeRobot API

### Configuration Constants
- `WHEEL_CIRCUMFERENCE = 35.0` - Wheel circumference in cm
- `STABILIZATION_DELAY = 0.2` - Delay after movements (200ms)
- `TURN_COMPENSATION = 5` - Degrees to compensate for turn undershoot

### Methods
The `SpikeRobot` class provides these methods:

**Initialization:**
- `__init__(left_motor_port=port.B, right_motor_port=port.F, accessory1_port=port.D)` - Initialize robot with motor ports

**Setup:**
- `async setup()` - Initialize motor pair and reset sensors (call first!)

**Movement:**
- `async drive(distance, speed)` - Drive straight for distance (cm) at speed (positive=forward, negative=backward)
- `async drive_forward(distance, speed)` - Drive forward by distance (cm)
- `async drive_backward(distance, speed)` - Drive backward by distance (cm)
- `async arc(distance, speed, steering)` - Drive in an arc (steering: -100=sharp left, 0=straight, 100=sharp right)

**Turning:**
- `async turn(angle)` - Turn by angle with gyro sensor (positive=right, negative=left)
- `async turn_right(angle)` - Turn right by angle (degrees)
- `async turn_left(angle)` - Turn left by angle (degrees)

**Accessory Control:**
- `async rotate_left(degrees, speed)` - Rotate accessory motor 1 counter-clockwise
- `async rotate_right(degrees, speed)` - Rotate accessory motor 1 clockwise

**Control:**
- `stop()` - Stop all motors immediately

**Utilities:**
- `degreesForDistance(distance)` - Convert cm to motor degrees
- `async resetYaw()` - Reset motion sensor yaw to 0

All async methods should be called with `await` or using `runloop.run()`.

## Notes
- The hub uses MicroPython and does not support subdirectories for imports
- Common code must be exported to `common.py` in the hub's root directory
- Edit source in `common/spike_robot.py`, not in `export_common.py`

## Recent Improvements
- **Accurate Turning:** Uses gyro sensor with turn compensation and correction phase for precise angles
- **Synchronized Driving:** Motor position resets before each drive ensure wheels stay aligned
- **Smart Braking:** Uses `motor.SMART_BRAKE` to compensate for momentum and improve stopping accuracy
- **Stabilization:** Checks for sensor stability after movements to ensure accurate readings
- **Accessory Motor:** Support for additional motor on port D with rotate functions
- **Optimized Parameters:** Acceleration/deceleration set to 400 deg/s² for smooth synchronized movement
