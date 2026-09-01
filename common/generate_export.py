#!/usr/bin/env python3
# generate_export.py
# Helper script to generate export_common.py from spike_robot.py
# Run this on your computer whenever you update spike_robot.py

import os

# Read the source code from spike_robot.py (in same directory)
with open('common/spike_robot.py', 'r') as src:
    spike_robot_code = src.read()

# Generate export_common.py with the embedded code
export_script = f'''commonCode = """{spike_robot_code}"""

import os
os.chdir('/flash')
try:
    os.remove('common.py')
except OSError:
    pass
with open('common.py', 'w+') as f:
    f.write(commonCode)
print('Exported code to common.py')
'''

# Write the generated script to export_common.py in root
with open('export_common.py', 'w') as f:
    f.write(export_script)

print('✓ Generated export_common.py from common/spike_robot.py')
print('  Upload export_common.py to the hub and run it to create common.py')
