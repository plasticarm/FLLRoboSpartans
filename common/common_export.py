"""
In SP3, you can import a text-based Python file (.py) that is present in the hub root.
We will write a second program that exports the first program’s library functions 
to a file called “customlib.py” in the SP root folder (“/flash”). 
Use a slot that you don’t use for missions. We used slot 18. 
It will first create a string that contains all the library functions. 
Test code is excluded. It then writes the string out to a file in the SPIKE hub root. 
It does not itself import or use the library. It is simply an exporter utility. 
TIP:  You can also create multiple libraries by exporting chunks of code to different .py files in the root

Library code string using python multiline quotes. 
Do not include test code, only the functions you want to reuse and the imports they need.
"""

commonCode: str = """
TODO: Paste all code from common.py here
"""

# WRITE TO SLOT 18
def exportProgram():
    import os
    global code
    os.chdir('/flash')  # change directory to root
    try:
        os.remove('common.py')  # remove any existing library file of the same name
    except:
        pass
    with open('common.py', 'w+') as f:  # Create a new file common.py in the SPIKE hub root
        f.write(commonCode)  # Write out the library code string to the common.py file

exportProgram()  # Runs the export function
