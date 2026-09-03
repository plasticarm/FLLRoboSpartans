import tkinter as tk
from tkinter import ttk, filedialog
import re

class CommandBlockGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Command Block Creator")

        # Menu
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Output Python", command=self.output_python)
        file_menu.add_command(label="Open Python", command=self.open_python)

        # Main Frame
        self.main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Frames for Buttons and Commands
        self.button_frame = tk.Frame(self.main_frame, bg="white")
        self.button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.main_frame.add(self.button_frame, weight=1)

        self.command_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.command_frame, weight=1)

        # Canvas and Scrollbar in Command Frame
        self.canvas = tk.Canvas(self.command_frame)
        self.scrollbar = ttk.Scrollbar(self.command_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Preview Frame
        self.preview_frame = tk.Frame(self.main_frame, bg="white", relief=tk.SUNKEN, bd=2)
        self.main_frame.add(self.preview_frame, weight=1)

        self.preview_label = tk.Label(self.preview_frame, text="Output Preview", bg="white", font=("Arial", 14))
        self.preview_label.pack(anchor="n", pady=5)

        self.preview_text = tk.Text(self.preview_frame, wrap=tk.WORD, state=tk.DISABLED, bg="white", font=("Courier", 12))
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.copy_button = tk.Button(self.preview_frame, text="Copy to Clipboard", command=self.copy_preview, bg="blue", fg="white")
        self.copy_button.pack(anchor="s", pady=5)

        # Add Command Buttons
        self.add_drive_button = tk.Button(self.button_frame, text="Add Drive Command", command=self.add_drive_block, bg="blue", fg="white")
        self.add_drive_button.pack(pady=5, anchor="w")

        self.add_turn_button = tk.Button(self.button_frame, text="Add TurnDegrees Command", command=self.add_turn_block, bg="red", fg="white")
        self.add_turn_button.pack(pady=5, anchor="w")

        self.add_rotate_button = tk.Button(self.button_frame, text="Add Rotate Command", command=self.add_rotate_block, bg="red", fg="white")
        self.add_rotate_button.pack(pady=5, anchor="w")

        self.add_left_arm_button = tk.Button(self.button_frame, text="Add LeftArmRotation Command", command=self.add_left_arm_block, bg="green", fg="white")
        self.add_left_arm_button.pack(pady=5, anchor="w")

        self.add_right_arm_button = tk.Button(self.button_frame, text="Add RightArmRotation Command", command=self.add_right_arm_block, bg="green", fg="white")
        self.add_right_arm_button.pack(pady=5, anchor="w")

        self.blocks = []
        self.dragging_block = None
        self.drag_start_y = 0
        self.dragging_index = None

    def add_drive_block(self):
        self._add_block("drive", ["Distance", "Speed"])

    def add_turn_block(self):
        self._add_block("turnDegrees", ["Direction", "Degrees", "Speed"])

    def add_rotate_block(self):
        self._add_block("rotate", ["Direction", "Degrees", "Speed"])

    def add_left_arm_block(self):
        self._add_block("leftArmRotation", ["Degrees", "Speed"])

    def add_right_arm_block(self):
        self._add_block("rightArmRotation", ["Degrees", "Speed"])

    def _add_block(self, command_name, parameters):
        block_frame = ttk.LabelFrame(self.scrollable_frame, text=command_name)
        block_frame.pack(pady=5, padx=5, fill=tk.X, anchor="w")
        self.blocks.append((command_name, block_frame, parameters))

        entries = []
        for param in parameters:
            param_label = ttk.Label(block_frame, text=f"{param}:")
            param_label.pack(side=tk.LEFT, padx=5)

            param_entry = ttk.Entry(block_frame)
            param_entry.pack(side=tk.LEFT, padx=5)
            entries.append(param_entry)

        remove_button = ttk.Button(block_frame, text="Remove", command=lambda: self._remove_block(block_frame))
        remove_button.pack(side=tk.RIGHT, padx=5)

        block_frame.bind("<Button-1>", lambda event: self._start_drag(block_frame, event))
        block_frame.bind("<B1-Motion>", lambda event: self._drag_block(block_frame, event))
        block_frame.bind("<ButtonRelease-1>", lambda event: self._end_drag(block_frame))

        self.blocks[-1] = (command_name, entries, block_frame)
        self.update_preview()

    def _remove_block(self, block_frame):
        self.blocks = [block for block in self.blocks if block[2] != block_frame]
        block_frame.destroy()
        self.update_preview()

    def _start_drag(self, block_frame, event):
        self.dragging_block = block_frame
        self.drag_start_y = event.y_root
        self.dragging_index = next((i for i, block in enumerate(self.blocks) if block[2] == block_frame), -1)

    def _drag_block(self, block_frame, event):
        if self.dragging_block and self.dragging_index is not None:
            delta_y = event.y_root - self.drag_start_y

            # Determine if the block should move up or down
            if delta_y < -20 and self.dragging_index > 0:  # Move up
                self._swap_blocks(self.dragging_index, self.dragging_index - 1)
                self.dragging_index -= 1
                self.drag_start_y = event.y_root

            elif delta_y > 20 and self.dragging_index < len(self.blocks) - 1:  # Move down
                self._swap_blocks(self.dragging_index, self.dragging_index + 1)
                self.dragging_index += 1
                self.drag_start_y = event.y_root

    def _swap_blocks(self, index1, index2):
        # Swap positions in the list
        self.blocks[index1], self.blocks[index2] = self.blocks[index2], self.blocks[index1]

        # Repack the frames in the new order
        for _, _, block_frame in self.blocks:
            block_frame.pack_forget()
            block_frame.pack(pady=5, padx=5, fill=tk.X, anchor="w")
        self.update_preview()

    def _end_drag(self, block_frame):
        self.dragging_block = None
        self.dragging_index = None

    def output_python(self):
        commands = []
        for command_name, entries, _ in self.blocks:
            params = [entry.get() for entry in entries]
            params_str = ", ".join(f"'{p}'" if not p.isdigit() else p for p in params)
            commands.append(f"{command_name}({params_str})")

        script_content = """def main():
"""
        script_content += "\n".join(f"    {cmd}" for cmd in commands)
        script_content += "\n\nrunloop.run(main())\n"

        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python files", "*.py")])
        if file_path:
            with open(file_path, "w") as file:
                file.write(script_content)

    def open_python(self):
        file_path = filedialog.askopenfilename(defaultextension=".py", filetypes=[("Python files", "*.py")])
        if not file_path:
            return

        with open(file_path, "r") as file:
            content = file.read()

        match = re.search(r"def main\(\):\n(.*?)\n\nrunloop.run\(main\(\)\)", content, re.S)
        if match:
            commands = match.group(1).strip().split("\n")
            self.blocks = []

            for command in commands:
                match_cmd = re.match(r"(\w+)\((.*?)\)", command)
                if match_cmd:
                    command_name = match_cmd.group(1)
                    params = [param.strip().strip("'") for param in match_cmd.group(2).split(",")]

                    if command_name == "drive":
                        self._add_block("drive", ["Distance", "Speed"])
                    elif command_name == "turnDegrees":
                        self._add_block("turnDegrees", ["Direction", "Degrees", "Speed"])
                    elif command_name == "rotate":
                        self._add_block("rotate", ["Direction", "Degrees", "Speed"])
                    elif command_name == "leftArmRotation":
                        self._add_block("leftArmRotation", ["Degrees", "Speed"])
                    elif command_name == "rightArmRotation":
                        self._add_block("rightArmRotation", ["Degrees", "Speed"])

                    for i, param in enumerate(params):
                        if i < len(self.blocks[-1][1]):
                            self.blocks[-1][1][i].delete(0, tk.END)
                            self.blocks[-1][1][i].insert(0, param)
            self.update_preview()

    def update_preview(self):
        commands = []
        for command_name, entries, _ in self.blocks:
            params = [entry.get() for entry in entries]
            params_str = ", ".join(f"'{p}'" if not p.isdigit() else p for p in params)
            commands.append(f"{command_name}({params_str})")

        script_content = """def main():
"""
        script_content += "\n".join(f"    {cmd}" for cmd in commands)
        script_content += "\n\nrunloop.run(main())\n"

        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, script_content)
        self.preview_text.config(state=tk.DISABLED)

    def copy_preview(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.preview_text.get(1.0, tk.END))
        self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = CommandBlockGUI(root)
    root.mainloop()
