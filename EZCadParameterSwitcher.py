import tkinter as tk
import tkinter.messagebox as mb
from tkinter import font as tkfont
import pyautogui
import threading
import time
import xlrd
import keyboard
import cv2
import numpy as np
import os
import sys
from PIL import Image, ImageTk


##################################################
# Initialization and GUI Setup
##################################################

class LaserParameterChanger:
    def __init__(self, master):
        self.master = master
        master.title("Laser Parameter Changer")

        # Create a bold font based on the default font size
        default_font = tkfont.nametofont("TkDefaultFont")
        bold_font = default_font.copy()
        bold_font.config(weight="bold")

        # Settings Section
        self.settings_frame = tk.Frame(master)  # Renamed to "Settings Section"
        self.settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20, side=tk.LEFT)

        # Coordinates Column
        tk.Label(self.settings_frame, text="Settings", font=bold_font).grid(row=0, column=0, padx=(15, 10))
        self.save_coordinates_button = tk.Button(self.settings_frame, text="Save Settings", command=self.save_coordinates, width=15)
        self.save_coordinates_button.grid(row=1, column=0)
        self.load_coordinates_button = tk.Button(self.settings_frame, text="Load Settings", command=self.load_coordinates, width=15)
        self.load_coordinates_button.grid(row=2, column=0)

        # Tools Column
        tk.Label(self.settings_frame, text="Tools", font=bold_font).grid(row=0, column=2, padx=(10, 0))
        self.coordinate_reader_button = tk.Button(self.settings_frame, text="Coordinate Reader", command=self.coordinate_reader, width=15)
        self.coordinate_reader_button.grid(row=1, column=2)
        self.pen_allocation_button = tk.Button(self.settings_frame, text="Pen Allocation", command=self.pen_allocation, width=15)
        self.pen_allocation_button.grid(row=2, column=2)
        self.focus_root_button = tk.Button(self.settings_frame, text="Focus Window", command=self.focus_root_window, width=15)
        self.focus_root_button.grid(row=3, column=2)
        self.setup_wizard_button = tk.Button(self.settings_frame, text="Setup Wizard", command=self.setup_wizard, width=15)
        self.setup_wizard_button.grid(row=4, column=2)
        self.array_calculator_button = tk.Button(self.settings_frame, text="Array Calculator", command=self.open_array_calculator, width=15)
        self.array_calculator_button.grid(row=5, column=2)

        # Initialize attributes for array outputs
        self.array_number_label_b = None
        self.array_number_entry_b = None
        self.array_spacing_label_b = None
        self.array_spacing_entry_b = None
        self.array_type_label_b = None
        self.array_type_entry_b = None

        # Location Settings Section
        self.coord_settings_frame = tk.Frame(master)
        self.coord_settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(self.coord_settings_frame, text="Location Name", font=bold_font).grid(row=0, column=0)
        tk.Label(self.coord_settings_frame, text="X Coordinates", font=bold_font).grid(row=0, column=1)
        tk.Label(self.coord_settings_frame, text="Y Coordinates", font=bold_font).grid(row=0, column=2)
        tk.Label(self.coord_settings_frame, text="Enable", font=bold_font).grid(row=0, column=5)

        self.locations = ["Pen Window", "Default Parameter Tickbox", "Loops", "Speed", "Power", "Frequency", "Hatch Setting", "Apply Button", "Select All", "Target RGB Start", "Target RGB Stop", "Clear Selection", "Object List"]
        self.location_entries = []
        self.location_coordinates = {}
        self.create_location_entries()

        # Change Parameters Button
        self.change_parameters_button = tk.Button(master, text="Change Parameters", command=self.confirm_change_parameters)
        self.change_parameters_button.pack(pady=5)

        # Delay entry
        self.delay_label = tk.Label(self.coord_settings_frame, text="Delay (seconds):")
        self.delay_label.grid(row=len(self.locations) + 1, column=0)
        self.delay_entry = tk.Entry(self.coord_settings_frame)
        self.delay_entry.grid(row=len(self.locations) + 1, column=1)

        # RGB entry
        self.rgb_label = tk.Label(self.coord_settings_frame, text="Target RGB:")
        self.rgb_label.grid(row=len(self.locations) + 2, column=0)
        self.rgb_r_entry = tk.Entry(self.coord_settings_frame, width=10)
        self.rgb_g_entry = tk.Entry(self.coord_settings_frame, width=10)
        self.rgb_b_entry = tk.Entry(self.coord_settings_frame, width=10)
        self.rgb_r_entry.grid(row=len(self.locations) + 2, column=1)
        self.rgb_g_entry.grid(row=len(self.locations) + 2, column=2)
        self.rgb_b_entry.grid(row=len(self.locations) + 2, column=3)

        # Add color picker button next to the RGB entry fields
        self.rgb_picker_button = tk.Button(self.coord_settings_frame, text="Pick", command=self.open_color_picker)
        self.rgb_picker_button.grid(row=len(self.locations) + 2, column=4)

        # Add checkbox to rows
        self.select_all_enable_var = tk.BooleanVar(value=True)
        select_all_enable_checkbox = tk.Checkbutton(self.coord_settings_frame, variable=self.select_all_enable_var)
        select_all_enable_checkbox.grid(row=self.locations.index("Select All") + 1, column=5)

        # Bind the key combinations
        keyboard.add_hotkey('ctrl+a', self.click_clear_selection)

        # Tooltips
        self.add_tooltip(self.rgb_label, "RGB value of the currently selected Pen, coloured blue.")
        self.add_tooltip(self.delay_label, "Delay in seconds between each action.")

        self.load_coordinates()  # Load saved settings
        self.parameter_data = []  # Initialise parameter data
        self.stop_script = False # Flag to stop script
        self.escape_pressed = False # Initialise the Escape flag
        keyboard.on_press_key("esc", self.stop_actions)

##################################################
# Event Handling and Key Bindings
##################################################

    def click_clear_selection(self, event=None):
        original_x, original_y = pyautogui.position()
        if self.select_all_enable_var.get():
            try:
                x = int(self.location_entries[self.locations.index("Select All")][0].get())
                y = int(self.location_entries[self.locations.index("Select All")][1].get())
                pyautogui.moveTo(x, y)
                pyautogui.click()
                print(f"Clicked 'Select All' at ({x}, {y})")
                pyautogui.moveTo(original_x, original_y)  # Return to the original position
                print(f"Returned to original position at ({original_x}, {original_y})")
            except ValueError:
                print("Invalid coordinates for 'Select All'. Please check the input.")

    def open_color_picker(self):
        self.color_picker_popup = tk.Toplevel(self.master)
        self.color_picker_popup.title("Pick a Color")
        self.color_picker_popup.geometry("+0+0")  # Position at the top left corner
        self.color_picker_popup.grab_set()  # Ensure the popup grabs focus
        self.color_picker_popup.focus_set()  # Ensure the popup gets focus

        # Instruction label
        instruction_label = tk.Label(self.color_picker_popup, text="Move the mouse cursor to a location and pick a pixel colour by pressing A.")
        instruction_label.pack(padx=20, pady=10)

        # Dynamic RGB value readout
        self.rgb_value_label = tk.Label(self.color_picker_popup, text="RGB: (0, 0, 0)", font=("Helvetica", 16))
        self.rgb_value_label.pack(padx=20, pady=10)

        # Bind key press event to pick color
        self.color_picker_popup.bind("<KeyPress>", self.pick_color)

        # Update RGB value in real-time
        self.update_rgb_value()

        # Close the popup when done
        self.color_picker_popup.protocol("WM_DELETE_WINDOW", self.close_color_picker_popup)

    def pick_color(self, event):
        if event.char.lower() == 'a':
            x, y = pyautogui.position()
            r, g, b = pyautogui.screenshot().getpixel((x, y))
            self.rgb_r_entry.delete(0, tk.END)
            self.rgb_r_entry.insert(0, str(r))
            self.rgb_g_entry.delete(0, tk.END)
            self.rgb_g_entry.insert(0, str(g))
            self.rgb_b_entry.delete(0, tk.END)
            self.rgb_b_entry.insert(0, str(b))
            self.color_picker_popup.destroy()

    def update_rgb_value(self):
        if hasattr(self, 'color_picker_popup') and self.color_picker_popup.winfo_exists():
            x, y = pyautogui.position()
            r, g, b = pyautogui.screenshot().getpixel((x, y))
            self.rgb_value_label.config(text=f"RGB: ({r}, {g}, {b})")
            self.color_picker_popup.after(100, self.update_rgb_value)

    def close_color_picker_popup(self):
        if hasattr(self, 'color_picker_popup'):
            self.color_picker_popup.destroy()
            del self.color_picker_popup

    def stop_actions(self, event=None):
        if hasattr(self, 'popup_window') and self.popup_window.winfo_exists():
            self.stop_script = True
            self.escape_pressed = True
            print("Script stopped by pressing escape.")
            self.close_script_running_popup()
            self.show_escape_pressed_popup()
        else:
            self.escape_pressed = False  # Ensure escape flag is reset if no actions are running

    def show_escape_pressed_popup(self):
        if hasattr(self, 'escape_popup'):
            self.close_escape_pressed_popup()

        self.escape_popup = tk.Toplevel(self.master)
        self.escape_popup.title("Script Halted")
        self.escape_popup.geometry("+0+0")  # Position at the top left corner

        # Set your desired RGB color here
        background_color = "#ffff00"
        self.escape_popup.configure(bg=background_color)

        self.escape_popup_label = tk.Label(self.escape_popup, text="", bg=background_color, wraplength=300, font=("Helvetica", 16, "bold"))
        self.escape_popup_label.pack(padx=20, pady=20)

        close_button = tk.Button(self.escape_popup, text="Close", command=self.close_escape_pressed_popup)
        close_button.pack(pady=0)
        close_button.focus_set()  # Set focus on the close button

        self.escape_popup.protocol("WM_DELETE_WINDOW", self.close_escape_pressed_popup)

        # Start the countdown
        self.countdown_and_close_escape_popup(8)

    def countdown_and_close_escape_popup(self, countdown):
        if hasattr(self, 'escape_popup') and self.escape_popup.winfo_exists():
            self.escape_popup_label.config(text=f"Escape key pressed, actions halted.\nScript will complete current action sequence.\nWindow will close in {countdown} seconds.")
            if countdown > 0:
                self.master.after(1000, self.countdown_and_close_escape_popup, countdown - 1)
            else:
                self.close_escape_pressed_popup()

    def close_escape_pressed_popup(self):
        if hasattr(self, 'escape_popup'):
            self.escape_popup.destroy()
            del self.escape_popup

    def show_actions_completed_popup(self):
        # Only show the popup if the script was not halted by pressing Escape
        if not self.escape_pressed:
            if hasattr(self, 'completed_popup'):
                self.close_actions_completed_popup()

            self.completed_popup = tk.Toplevel(self.master)
            self.completed_popup.title("Actions Completed")
            self.completed_popup.geometry("+0+0")  # Position at the top left corner

            # Set your desired RGB color here
            background_color = "#57eb72"
            self.completed_popup.configure(bg=background_color)

            message = "Actions performed."
            tk.Label(self.completed_popup, text=message, bg=background_color, wraplength=300, font=("Helvetica", 16, "bold")).pack(padx=20, pady=20)

            close_button = tk.Button(self.completed_popup, text="Close", command=self.close_actions_completed_popup)
            close_button.pack(pady=0)
            close_button.focus_set()  # Set focus on the close button

            self.completed_popup.protocol("WM_DELETE_WINDOW", self.close_actions_completed_popup)

    def close_actions_completed_popup(self):
        if hasattr(self, 'completed_popup'):
            self.completed_popup.destroy()
            del self.completed_popup

##################################################
# Wizard and Default Parameter Checking
##################################################

    def run_setup_wizard(self):
        self.show_resolution_selector()

    def show_resolution_selector(self):
        self.resolution_popup = tk.Toplevel(self.master)
        self.resolution_popup.title("Run Setup Wizard")
        self.resolution_popup.geometry("+0+0")  # Position at the top left corner

        # Create a font for the bold, underlined, and larger text
        bold_underline_font = tkfont.Font(family="Helvetica", size=12, weight="bold", underline=True)

        # Create labels with the desired font styles
        tk.Label(self.resolution_popup, text="This tool will automatically detect the appropriate coordinates for the point of interest locations.",
                 wraplength=300).pack(padx=20, pady=(10, 0))

        tk.Label(self.resolution_popup, text="Some setup is required:", wraplength=300, font=bold_underline_font).pack(padx=20, pady=(10, 0))

        tk.Label(self.resolution_popup, text="Draw a shape in the laser marking software, hatch this shape with Pen 0.",
                 wraplength=300).pack(padx=20, pady=(10, 0))

        tk.Label(self.resolution_popup, text="Ensure Pen 0 is selected and the default parameter checkbox is ticked.",
                 wraplength=300).pack(padx=20, pady=(10, 0))

        tk.Label(self.resolution_popup, text="Select the correct resolution of the monitor in the drop down menu.",
                 wraplength=300).pack(padx=20, pady=(10, 0))

        self.resolution_var = tk.StringVar(value="2560x1440")
        resolution_menu = tk.OptionMenu(self.resolution_popup, self.resolution_var, "2560x1440", "1920x1080", "Custom")
        resolution_menu.pack(padx=20, pady=10)

        self.custom_resolution_frame = tk.Frame(self.resolution_popup)
        self.custom_resolution_frame.pack(padx=20, pady=10)
        self.custom_width_entry = tk.Entry(self.custom_resolution_frame, width=10)
        self.custom_height_entry = tk.Entry(self.custom_resolution_frame, width=10)
        tk.Label(self.custom_resolution_frame, text="Width:").pack(side=tk.LEFT)
        self.custom_width_entry.pack(side=tk.LEFT)
        tk.Label(self.custom_resolution_frame, text="Height:").pack(side=tk.LEFT)
        self.custom_height_entry.pack(side=tk.LEFT)
        self.custom_resolution_frame.pack_forget()

        self.resolution_var.trace("w", self.toggle_custom_resolution)

        run_button = tk.Button(self.resolution_popup, text="Run", command=self.run_image_detection)
        run_button.pack(padx=20, pady=10)

    def toggle_custom_resolution(self, *args):
        if self.resolution_var.get() == "Custom":
            self.custom_resolution_frame.pack(padx=20, pady=10)
        else:
            self.custom_resolution_frame.pack_forget()

    def run_image_detection(self):
        if self.resolution_var.get() == "Custom":
            width = self.custom_width_entry.get()
            height = self.custom_height_entry.get()
            try:
                width = int(width)
                height = int(height)
            except ValueError:
                mb.showerror("Error", "Please enter valid width and height values.")
                return
        else:
            width, height = map(int, self.resolution_var.get().split("x"))

        self.selected_resolution = (width, height)  # Store the selected resolution
        self.resolution_popup.destroy()
        self.find_images_on_screen()

    def calculate_scaling_factor(self):
        width, height = self.selected_resolution
        if width == 2560 and height == 1440:
            return 1.0
        elif width == 1920 and height == 1080:
            return 0.75
        else:
            return (width / 2560) * 1.0  # Custom scaling based on width

    def find_images_on_screen(self):
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        image_folder = os.path.join(base_path, 'SetupHelper')

        # Define the explicit search order
        image_search_order = ["PenWindow2.png", "DefaultCheckbox.png", "ObjectListTop.png"] + [
            f for f in os.listdir(image_folder)
            if os.path.isfile(os.path.join(image_folder, f)) and f not in ["PenWindow2.png", "DefaultCheckbox.png", "ObjectListTop.png"]
        ]

        screen = pyautogui.screenshot()
        screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

        pen_window2_coords = None

        for image_file in image_search_order:
            print(f"Looking for '{image_file}'")
            image_path = os.path.join(image_folder, image_file)
            template = cv2.imread(image_path, cv2.IMREAD_COLOR)

            if template is None:
                print(f"Could not read image: {image_path}")
                continue

            found = False
            max_val = 0
            best_loc = (0, 0)

            search_area = screen
            if image_file == "DefaultCheckbox.png" and pen_window2_coords:
                x, y = pen_window2_coords
                x_start = max(0, x - 200)
                y_start = max(0, y - 200)
                x_end = min(screen.shape[1], x + 200)
                y_end = min(screen.shape[0], y + 200)
                search_area = screen[y_start:y_end, x_start:x_end]

            for method in [cv2.TM_CCOEFF, cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR, cv2.TM_CCORR_NORMED, cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                result = cv2.matchTemplate(search_area, template, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                    if min_val < max_val:
                        max_val = min_val
                        best_loc = min_loc
                else:
                    if max_val > min_val:
                        max_val = max_val
                        best_loc = max_loc

            threshold = 0.8 if method not in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED] else 0.2
            if (method not in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED] and max_val >= threshold) or (method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED] and max_val <= threshold):
                if image_file == "DefaultCheckbox.png" and pen_window2_coords:
                    center_x = best_loc[0] + x_start + template.shape[1] // 2
                    center_y = best_loc[1] + y_start + template.shape[0] // 2
                else:
                    center_x = best_loc[0] + template.shape[1] // 2
                    center_y = best_loc[1] + template.shape[0] // 2
                print(f"'{image_file}' coordinates: ({center_x}, {center_y})")
                self.update_coordinates_from_image(image_file, center_x, center_y)
                found = True

                if image_file == "PenWindow2.png":
                    pen_window2_coords = (center_x, center_y)

            if not found:
                print(f"'{image_file}' not found")

    def update_coordinates_from_image(self, image_file, x, y):
        scaling_factor = self.calculate_scaling_factor()
        additional_x = 0
        if image_file in ["Loops.png", "Speed.png", "Power.png", "Frequency.png"]:
            additional_x = 80 * scaling_factor
            x += int(additional_x)

        if image_file in ["Apply1.png", "Apply2.png"]:
            self.location_entries[self.locations.index("Apply Button")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Apply Button")][0].insert(0, x)
            self.location_entries[self.locations.index("Apply Button")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Apply Button")][1].insert(0, y)
        elif image_file == "DefaultCheckbox.png":
            self.location_entries[self.locations.index("Default Parameter Tickbox")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Default Parameter Tickbox")][0].insert(0, x)
            self.location_entries[self.locations.index("Default Parameter Tickbox")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Default Parameter Tickbox")][1].insert(0, y)
        elif image_file == "Frequency.png":
            self.location_entries[self.locations.index("Frequency")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Frequency")][0].insert(0, x)
            self.location_entries[self.locations.index("Frequency")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Frequency")][1].insert(0, y)
        elif image_file == "Hatch.png":
            self.location_entries[self.locations.index("Hatch Setting")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Hatch Setting")][0].insert(0, x)
            self.location_entries[self.locations.index("Hatch Setting")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Hatch Setting")][1].insert(0, y)
        elif image_file == "Loops.png":
            self.location_entries[self.locations.index("Loops")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Loops")][0].insert(0, x)
            self.location_entries[self.locations.index("Loops")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Loops")][1].insert(0, y)
        elif image_file == "PenWindow1.png":
            self.location_entries[self.locations.index("Pen Window")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Pen Window")][0].insert(0, x)
            self.location_entries[self.locations.index("Pen Window")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Pen Window")][1].insert(0, y)
            self.location_entries[self.locations.index("Target RGB Start")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Target RGB Start")][0].insert(0, x)
            self.location_entries[self.locations.index("Target RGB Start")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Target RGB Start")][1].insert(0, y)

            # Add coordinates for Clear Selection
            additional_y = int(700 * scaling_factor)
            clear_selection_y = y + additional_y
            self.location_entries[self.locations.index("Clear Selection")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Clear Selection")][0].insert(0, x)
            self.location_entries[self.locations.index("Clear Selection")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Clear Selection")][1].insert(0, clear_selection_y)
        elif image_file == "PenWindow2.png":
            self.location_entries[self.locations.index("Target RGB Stop")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Target RGB Stop")][0].insert(0, x)
            self.location_entries[self.locations.index("Target RGB Stop")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Target RGB Stop")][1].insert(0, y)
        elif image_file == "Power.png":
            self.location_entries[self.locations.index("Power")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Power")][0].insert(0, x)
            self.location_entries[self.locations.index("Power")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Power")][1].insert(0, y)
        elif image_file == "SelectAll.png":
            self.location_entries[self.locations.index("Select All")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Select All")][0].insert(0, x)
            self.location_entries[self.locations.index("Select All")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Select All")][1].insert(0, y)
        elif image_file == "Speed.png":
            self.location_entries[self.locations.index("Speed")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Speed")][0].insert(0, x)
            self.location_entries[self.locations.index("Speed")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Speed")][1].insert(0, y)
        elif image_file == "ObjectListTop.png":
            x_object_list_start = int(self.location_entries[self.locations.index("Object List")][0].get())
            self.location_entries[self.locations.index("Object List")][0].delete(0, tk.END)
            self.location_entries[self.locations.index("Object List")][0].insert(0, x)
            self.location_entries[self.locations.index("Object List")][1].delete(0, tk.END)
            self.location_entries[self.locations.index("Object List")][1].insert(0, y)

    def setup_wizard(self):
        self.setup_popup = tk.Toplevel(self.master)
        self.setup_popup.title("Setup Wizard")
        self.setup_popup.geometry("+0+0")  # Position at the top left corner

        # Get the default font for the application
        default_font = tkfont.nametofont("TkDefaultFont")
        bold_font = default_font.copy()
        bold_font.config(weight="bold")

        # Create a Text widget for better text wrapping and formatting
        text_widget = tk.Text(self.setup_popup, wrap="word", width=45, height=15, borderwidth=0, background=self.setup_popup.cget("background"), font=default_font)
        text_widget.pack(padx=20, pady=20)

        # Configure tags for bold text
        text_widget.tag_configure("bold", font=bold_font)

        # Insert text into the Text widget
        text_widget.insert("1.0", "These tools will help align the point of interest coordinates in the laser marking software window.\n\n")

        # Insert formatted text using tags
        text_widget.insert("end", "Default Parameter Check ", "bold")
        text_widget.insert("end", "will check the coordinates of the tickbox.\n\n")

        text_widget.insert("end", "Show Apply, Hatch and Select All Locations ", "bold")
        text_widget.insert("end", "will show coordinates of where the Apply button, Hatch Dropdown, and Select All button should be.\n\n")

        text_widget.insert("end", "Run Setup Wizard ", "bold")
        text_widget.insert("end", "will open a tool to detect coordinates for the point of interest locations.\n\n")

        text_widget.insert("end", "Always check the individual coordinates before performing actions.")

        # Make the Text widget read-only
        text_widget.config(state="disabled")

        self.default_parameter_check_button = tk.Button(self.setup_popup, text="Default Parameter Check", command=self.default_parameter_check)
        self.default_parameter_check_button.pack(pady=10)

        self.show_apply_hatch_var = tk.IntVar()
        self.show_apply_hatch_checkbox = tk.Checkbutton(self.setup_popup, text="Show Apply, Hatch and Select All Locations", variable=self.show_apply_hatch_var, command=self.toggle_apply_hatch_boxes)
        self.show_apply_hatch_checkbox.pack(pady=10)

        self.run_setup_wizard_button = tk.Button(self.setup_popup, text="Run Setup Wizard", command=self.run_setup_wizard)
        self.run_setup_wizard_button.pack(pady=10)

        self.setup_popup.protocol("WM_DELETE_WINDOW", self.on_setup_wizard_close)

    def toggle_apply_hatch_boxes(self):
        if self.show_apply_hatch_var.get():
            self.show_apply_hatch_locations()
        else:
            self.hide_apply_hatch_locations()

    def on_setup_wizard_close(self):
        self.hide_apply_hatch_locations()
        self.setup_popup.destroy()

    def default_parameter_check(self):
        print("Starting Default Parameter Check")

        # Move to Clear Selection coordinates and perform three clicks with a 0.1 second delay between each click
        clear_selection_x = int(self.location_entries[self.locations.index("Clear Selection")][0].get())
        clear_selection_y = int(self.location_entries[self.locations.index("Clear Selection")][1].get())

        pyautogui.moveTo(clear_selection_x, clear_selection_y)
        for _ in range(3):
            pyautogui.click()
            time.sleep(0.1)

        print(f"Clicked clear selection at ({clear_selection_x}, {clear_selection_y})")

        # Press the Escape key
        pyautogui.press('esc')
        print("Pressed ESC key")

        # Change to pen number 255
        self.change_pen_number(255)
        time.sleep(0.5)  # Wait for the pen number change to take effect

        # Look for the target RGB value and click on it
        target_color = (
            int(self.rgb_r_entry.get()),
            int(self.rgb_g_entry.get()),
            int(self.rgb_b_entry.get())
        )
        start_x = int(self.location_entries[self.locations.index("Target RGB Start")][0].get())
        start_y = int(self.location_entries[self.locations.index("Target RGB Start")][1].get())
        end_x = int(self.location_entries[self.locations.index("Target RGB Stop")][0].get())
        end_y = int(self.location_entries[self.locations.index("Target RGB Stop")][1].get())
        step = 5  # Step size for iteration

        print(f"Target color for pen selection: {target_color}")
        print(f"Searching for target color for pen selection from ({start_x}, {start_y}) to ({end_x}, {end_y})")

        found_target_color = False
        for x in range(start_x, end_x + 1, step):
            for y in range(start_y, end_y + 1, step):
                pixel_color = pyautogui.pixel(x, y)
                if pixel_color == target_color:
                    print(f"Found target color for pen selection at ({x}, {y})")
                    pyautogui.click(x, y)  # Click the center of the found pixel
                    found_target_color = True
                    break  # Exit the loop once the target color is found
            if found_target_color:
                break

        if not found_target_color:
            print("Target color for pen selection not found within the specified range.")
            self.show_default_parameter_popup(False)
            return  # Exit the function if the target color is not found
        time.sleep(0.5)  # Add a delay to let it catch up..

        # Check the coordinates of the Default Parameter Tickbox
        x, y = self.location_coordinates["Default Parameter Tickbox"]
        pixel_color = pyautogui.pixel(x, y)
        print(f"Checking Default Parameter Tickbox at ({x}, {y}), pixel color: {pixel_color}")

        if pixel_color == (0, 0, 0):
            print("Default Parameter Tickbox coordinates correct.")
            self.show_default_parameter_popup(True)
        else:
            print("Default Parameter Tickbox coordinates incorrect.")
            self.show_default_parameter_popup(False)

    def show_default_parameter_popup(self, is_correct):
        popup = tk.Toplevel(self.master)
        popup.geometry("+0+0")  # Position at the top left corner

        if is_correct:
            popup.title("Coordinates Correct")
            popup.configure(bg="#57eb72")  # Light Green color
            message = "Default Parameter Tickbox coordinates correct."
        else:
            popup.title("Coordinates Incorrect")
            popup.configure(bg="#ff0000")  # Red color
            message = "Default Parameter Tickbox coordinates incorrect."

        tk.Label(popup, text=message, bg=popup.cget("bg"), wraplength=300, font=("Helvetica", 16, "bold")).pack(padx=20, pady=20)
        tk.Button(popup, text="Close", command=popup.destroy).pack(pady=10)

    def show_apply_hatch_locations(self):
        # Read coordinates from the textboxes
        apply_x = int(self.location_entries[self.locations.index("Apply Button")][0].get())
        apply_y = int(self.location_entries[self.locations.index("Apply Button")][1].get())
        hatch_x = int(self.location_entries[self.locations.index("Hatch Setting")][0].get())
        hatch_y = int(self.location_entries[self.locations.index("Hatch Setting")][1].get())
        select_all_x = int(self.location_entries[self.locations.index("Select All")][0].get())
        select_all_y = int(self.location_entries[self.locations.index("Select All")][1].get())

        # Draw red box at Apply Button coordinates
        self.apply_box = self.draw_flashing_box(apply_x, apply_y)
        print(f"Drew flashing box at Apply Button coordinates: ({apply_x}, {apply_y})")

        # Draw red box at Hatch Setting coordinates
        self.hatch_box = self.draw_flashing_box(hatch_x, hatch_y)
        print(f"Drew flashing box at Hatch Setting coordinates: ({hatch_x}, {hatch_y})")

        # Draw red box at Select All coordinates
        self.select_all_box = self.draw_flashing_box(select_all_x, select_all_y)
        print(f"Drew flashing box at Select All coordinates: ({select_all_x}, {select_all_y})")

    def hide_apply_hatch_locations(self):
        if hasattr(self, 'apply_box') and self.apply_box:
            self.apply_box.destroy()
            self.apply_box = None
            print("Destroyed flashing box at Apply Button coordinates")

        if hasattr(self, 'hatch_box') and self.hatch_box:
            self.hatch_box.destroy()
            self.hatch_box = None
            print("Destroyed flashing box at Hatch Setting coordinates")

        if hasattr(self, 'select_all_box') and self.select_all_box:
            self.select_all_box.destroy()
            self.select_all_box = None
            print("Destroyed flashing box at Select All coordinates")

    def draw_flashing_box_at_coordinates(self, x, y):
        overlay = tk.Toplevel(self.master)
        overlay.overrideredirect(True)
        overlay.geometry(f"5x5+{x - 2}+{y - 2}")
        overlay.attributes("-topmost", True)  # Ensure the box is always on top

        def flash_box(color_index=0):
            colors = ["red", "yellow"]
            if overlay.winfo_exists():
                overlay.configure(bg=colors[color_index])
                next_color_index = (color_index + 1) % len(colors)
                overlay.after(500, flash_box, next_color_index)

        flash_box()

        def remove_box():
            if overlay.winfo_exists():
                overlay.destroy()

        overlay.after(4000, remove_box)  # Keep the box for 2 seconds

    def handle_move_button(self, idx):
        x = int(self.location_entries[idx][0].get())
        y = int(self.location_entries[idx][1].get())

        # Call the method to draw the flashing box at the specified coordinates
        self.draw_flashing_box_at_coordinates(x, y)

        # Call the original move_to_coordinates method
        self.move_to_coordinates(idx, draw_box=False)  # Pass draw_box as False to avoid drawing the box again

    def draw_flashing_box(self, x, y, size=5):
        overlay = tk.Toplevel(self.master)
        overlay.overrideredirect(True)
        overlay.geometry(f"{size}x{size}+{x - size // 2}+{y - size // 2}")
        overlay.attributes("-topmost", True)  # Ensure the box is always on top
        self.flash_box(overlay)
        return overlay

    def flash_box(self, box, color_index=0):
        colors = ["red", "yellow"]
        box.configure(bg=colors[color_index])
        next_color_index = (color_index + 1) % len(colors)
        box.after(500, self.flash_box, box, next_color_index)

##################################################
# Pen Allocation and Color Picker
##################################################

    def pen_allocation(self):
        self.pen_allocation_popup = tk.Toplevel(self.master)
        popup_geometry = "+{}+{}".format(self.master.winfo_x() + 100, self.master.winfo_y() + 100)
        self.pen_allocation_popup.geometry(popup_geometry)
        tk.Label(self.pen_allocation_popup, text="Click on an object and press V to set the Pen Number, the script will start from 0 and go up in increments of 1. Check the box to enable hatch pen number allocation changing too.").pack()

        # Add the checkbox for Hatch Pen Number Allocation
        self.hatch_checkbox_var = tk.IntVar()
        self.hatch_checkbox = tk.Checkbutton(self.pen_allocation_popup, text="Enable Hatch Pen Number Allocation", variable=self.hatch_checkbox_var)
        self.hatch_checkbox.pack()

        # Add the checkbox for Reorder along with allocation
        self.reorder_checkbox_var = tk.IntVar()
        self.reorder_checkbox = tk.Checkbutton(self.pen_allocation_popup, text="Reorder along with allocation", variable=self.reorder_checkbox_var)
        self.reorder_checkbox.pack()

        # Add the textbox for starting Pen Number
        tk.Label(self.pen_allocation_popup, text="Start from Pen Number:").pack()
        self.start_pen_number_entry = tk.Entry(self.pen_allocation_popup)
        self.start_pen_number_entry.insert(0, "0")
        self.start_pen_number_entry.pack()

        self.pen_allocation_popup.protocol("WM_DELETE_WINDOW", self.close_pen_allocation)  # Handle window close
        self.pen_allocation_popup.grab_set()  # Ensure the popup is modal

        self.pen_number_initialized = False  # Ensure the initialization flag is reset
        self.start_pen_allocation()

    def start_pen_allocation(self):
        self.pen_allocation_active = True

        def on_key_event(event):
            if event.name == 'v' and self.pen_allocation_active:
                self.original_cursor_position = pyautogui.position()  # Store the original cursor position
                self.select_and_allocate_pen()

        self.pen_allocation_key_hook = keyboard.on_press(on_key_event)  # Hook the keyboard event handler

    def close_pen_allocation(self):
        self.pen_allocation_active = False
        self.pen_number_initialized = False  # Reset the initialization flag
        keyboard.unhook(self.pen_allocation_key_hook)  # Unhook the keyboard event handler
        self.pen_allocation_popup.destroy()

    def select_and_allocate_pen(self):
        try:
            # Only initialize the pen number from the textbox once when `pen_number` is not set or reset
            if not hasattr(self, 'pen_number_initialized') or not self.pen_number_initialized:
                try:
                    self.pen_number = int(self.start_pen_number_entry.get())
                    self.pen_number_initialized = True  # Mark that initialization has been done
                except ValueError:
                    self.pen_number = 0  # Default to 0 if invalid input

            # Store the original cursor position when V is pressed
            original_position = pyautogui.position()

            # Move to Pen Number coordinates and select the current pen number
            self.change_pen_number(self.pen_number)
            time.sleep(0.1)  # Small delay to ensure actions are performed smoothly

            # Right click on the Pen Number
            self.right_click_pen_number()
            time.sleep(0.1)

            # Move cursor down 5 pixels and left click
            pyautogui.move(0, 5)
            pyautogui.click()
            print(f"Pen Number {self.pen_number} allocated.")

            # Move the cursor back to the original position
            pyautogui.moveTo(self.original_cursor_position)

            # If the checkbox is ticked, perform additional actions for hatch pen number allocation
            if self.hatch_checkbox_var.get() == 1:
                print("Hatch Pen Number Allocation enabled.")
                # Move to Hatch Setting coordinates
                hatch_x, hatch_y = int(self.location_entries[self.locations.index("Hatch Setting")][0].get()), int(self.location_entries[self.locations.index("Hatch Setting")][1].get())
                pyautogui.moveTo(hatch_x, hatch_y)
                pyautogui.click()
                print(f"Clicked Hatch Setting at ({hatch_x}, {hatch_y})")

                # Move to the specified hatch pen number
                pyautogui.press('up', presses=50)  # Move up to the top
                print(f"Returned to Pen Number 0")

                # Press down arrow key (Pen Number) times
                pyautogui.press('down', presses=self.pen_number)
                print(f"Pressed down key {self.pen_number} times for Hatch Setting")

                # Press Enter key
                pyautogui.press('enter')
                print(f"Pressed Enter key for Hatch Setting")

                # Move to Apply Button coordinates
                apply_x, apply_y = int(self.location_entries[self.locations.index("Apply Button")][0].get()), int(self.location_entries[self.locations.index("Apply Button")][1].get())
                pyautogui.moveTo(apply_x, apply_y)
                time.sleep(0.1)
                pyautogui.click()
                print(f"Clicked Apply Button at ({apply_x}, {apply_y})")



            # If reorder checkbox is checked, perform reorder action
            if self.reorder_checkbox_var.get() == 1:
                print("Reorder along with allocation enabled.")
                self.perform_reorder_action()

                # Move the cursor back to the original position
                pyautogui.moveTo(original_position)
                print(f"Moved cursor back to original position {original_position}")

            # Increment the pen number for the next allocation
            self.pen_number += 1

        except Exception as e:
            print(f"Error during pen allocation for Pen Number {self.pen_number}: {e}")

    def perform_reorder_action(self):
        try:
            # Retrieve the start coordinates for Object List
            start_x = int(self.location_entries[self.locations.index("Object List")][0].get())
            start_y = int(self.location_entries[self.locations.index("Object List")][1].get())

            print(f"Reordering: Moving to Object List coordinates ({start_x}, {start_y})")

            # Move cursor to the Object List coordinates and perform the reorder action
            pyautogui.moveTo(start_x, start_y)
            pyautogui.click(button='right')
            pyautogui.press('up')
            pyautogui.press('enter')

            print(f"Performed reorder action at ({start_x}, {start_y})")

        except Exception as e:
            print(f"Error during reorder action: {e}")

    def open_coordinates_popup(self, x_entry, y_entry):
        popup = tk.Toplevel(self.master)
        popup_geometry = "+{}+{}".format(self.master.winfo_x() + 100, self.master.winfo_y() + 100)
        popup.geometry(popup_geometry)
        tk.Label(popup, text="Move the mouse cursor to selected location and press A to save coordinates").pack()
        self.save_coordinates_and_close(popup, x_entry, y_entry)

    def save_coordinates_and_close(self, popup, x_entry, y_entry):
        def on_key_event(event):
            if event.name == "a":
                x, y = pyautogui.position()
                x_entry.delete(0, tk.END)
                x_entry.insert(0, str(x))
                y_entry.delete(0, tk.END)
                y_entry.insert(0, str(y))
                popup.destroy()  # Close the popup window after coordinates are saved
                keyboard.unhook_all()  # Remove all keyboard event handlers

        keyboard.on_press(on_key_event)  # Hook the keyboard event handler

##################################################
# Save and Load Coordinates
##################################################

    def save_coordinates(self):
        with open("coordinates.txt", "w") as file:
            # Save coordinates for each location
            for loc in self.locations:
                x = self.location_entries[self.locations.index(loc)][0].get()
                y = self.location_entries[self.locations.index(loc)][1].get()
                file.write(f"{loc},{x},{y}\n")
                self.location_coordinates[loc] = (x, y)

            # Save delay
            file.write(f"Delay,{self.delay_entry.get()}\n")

            # Save RGB values
            file.write(f"RGB,{self.rgb_r_entry.get()},{self.rgb_g_entry.get()},{self.rgb_b_entry.get()}\n")

        print("Settings saved to coordinates.txt")

    def load_coordinates(self):
        try:
            with open("coordinates.txt", "r") as file:
                for line in file:
                    if line.startswith("Delay"):
                        _, delay = line.strip().split(",")
                        self.delay_entry.delete(0, tk.END)
                        self.delay_entry.insert(0, delay)
                    elif line.startswith("RGB"):
                        _, r, g, b = line.strip().split(",")
                        self.rgb_r_entry.delete(0, tk.END)
                        self.rgb_r_entry.insert(0, r)
                        self.rgb_g_entry.delete(0, tk.END)
                        self.rgb_g_entry.insert(0, g)
                        self.rgb_b_entry.delete(0, tk.END)
                        self.rgb_b_entry.insert(0, b)
                    else:
                        loc, x, y = line.strip().split(",")
                        self.location_coordinates[loc] = (int(x), int(y))
                        idx = self.locations.index(loc)
                        if idx < len(self.location_entries):
                            self.location_entries[idx][0].delete(0, tk.END)
                            self.location_entries[idx][0].insert(0, x)
                            self.location_entries[idx][1].delete(0, tk.END)
                            self.location_entries[idx][1].insert(0, y)
                        else:
                            print(f"Index {idx} is out of range for location entries.")
            print("Settings loaded from coordinates.txt")
        except FileNotFoundError:
            print("No coordinates file found.")

    def confirm_save_coordinates(self):
        if mb.askyesno("Confirmation", "Are you sure you want to save coordinates?"):
            self.save_coordinates()
            print("Settings saved to coordinates.txt")

    def confirm_load_coordinates(self):
        if mb.askyesno("Confirmation", "Are you sure you want to load coordinates?"):
            self.load_coordinates()
            print("Settings loaded")

##################################################
# Utility Functions
##################################################

    def coordinate_reader(self):
        def update_coordinates():
            x, y = pyautogui.position()
            coord_label.config(text=f"X: {x}, Y: {y}")
            rgb = pyautogui.screenshot().getpixel((x, y))
            rgb_label.config(text=f"RGB: {rgb}")
            coord_label.after(100, update_coordinates)

        coord_window = tk.Toplevel(self.master)
        coord_window.title("Coordinate Reader")
        coord_window.geometry("275x40")
        coord_label = tk.Label(coord_window, text="")
        coord_label.pack()
        rgb_label = tk.Label(coord_window, text="")
        rgb_label.pack()
        update_coordinates()

    def move_to_coordinates(self, idx, draw_box=True):
        def move_and_return():
            try:
                original_x, original_y = pyautogui.position()  # Store original position
                x = int(self.location_entries[idx][0].get())
                y = int(self.location_entries[idx][1].get())
                self.location_coordinates[loc_name] = (x, y)

                if draw_box:  # Only draw the box if draw_box is True
                    self.draw_flashing_box_at_coordinates(x, y)

                pyautogui.moveTo(x, y, duration=0.2)  # Move to specified coordinates
                time.sleep(1)  # Wait for 1 second at the specified coordinates

                pyautogui.moveTo(original_x, original_y)  # Move back to original position
            except ValueError:
                print("Invalid coordinates entered.")

        loc_name = self.locations[idx]
        threading.Thread(target=move_and_return).start()  # Run move_and_return in a separate thread

    def move_to_coordinates_custom(self, location_name):
        def move_and_return():
            try:
                original_x, original_y = pyautogui.position()  # Store original position
                x = int(self.location_entries[self.locations.index(location_name)][0].get())
                y = int(self.location_entries[self.locations.index(location_name)][1].get())

                pyautogui.moveTo(x, y, duration=0.2)  # Move to specified coordinates
                time.sleep(1)  # Wait for 1 second at the specified coordinates

                pyautogui.moveTo(original_x, original_y)  # Move back to original position
            except ValueError:
                print("Invalid coordinates entered.")

        threading.Thread(target=move_and_return).start()  # Run move_and_return in a separate thread

    def create_location_entries(self):
        for i, loc in enumerate(self.locations, start=1):
            tk.Label(self.coord_settings_frame, text=loc).grid(row=i, column=0)
            x_entry = tk.Entry(self.coord_settings_frame)
            y_entry = tk.Entry(self.coord_settings_frame)
            x_entry.grid(row=i, column=1)
            y_entry.grid(row=i, column=2)
            self.location_entries.append((x_entry, y_entry))

            loc_coords = self.location_coordinates.get(loc, (0, 0))
            x_entry.insert(0, loc_coords[0])
            y_entry.insert(0, loc_coords[1])

            move_button = tk.Button(self.coord_settings_frame, text="Move", command=lambda idx=i - 1: self.handle_move_button(idx))
            move_button.grid(row=i, column=3)

            coordinates_button = tk.Button(self.coord_settings_frame, text="Coordinates", command=lambda idx=i - 1: self.open_coordinates_popup(self.location_entries[idx][0], self.location_entries[idx][1]))
            coordinates_button.grid(row=i, column=4)

        # Delay entry
        self.delay_label = tk.Label(self.coord_settings_frame, text="Delay (seconds):")
        self.delay_label.grid(row=len(self.locations) + 1, column=0)
        self.delay_entry = tk.Entry(self.coord_settings_frame)
        self.delay_entry.grid(row=len(self.locations) + 1, column=1, pady=5)

    def add_tooltip(self, widget, text):
        # Bind the tooltip to mouse enter and leave events
        widget.bind("<Enter>", lambda event, txt=text: self.show_tooltip(event, txt))
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event, text):
        # Create and display a tooltip window
        self.tooltip_window = tk.Toplevel()
        self.tooltip_window.geometry("+{}+{}".format(event.x_root, event.y_root))
        self.tooltip_window.overrideredirect(True)  # Remove window decorations
        self.tooltip_window.configure(bd=1, relief=tk.SOLID, highlightbackground="black")  # Add black border

        # Configure tooltip label with custom colors
        tooltip_label = tk.Label(self.tooltip_window, text=text, bg="white", fg="blue")
        tooltip_label.pack()

    def hide_tooltip(self, event):
        # Close the tooltip window
        self.tooltip_window.destroy()

    def focus_root_window(self):
        self.master.focus_set()

    def open_array_calculator(self):
        self.array_calculator_popup = tk.Toplevel(self.master)
        self.array_calculator_popup.title("Array Calculator")
        self.array_calculator_popup.geometry("+0+0")  # Position at the top left corner

        # Frame for dropdown and textboxes
        input_frame = tk.Frame(self.array_calculator_popup)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        # Array Object Type dropdown
        tk.Label(input_frame, text="Array Object Type:").grid(row=0, column=0, padx=10)
        self.array_type_var = tk.StringVar(value="Lattice Dot")
        self.array_type_var.trace('w', self.update_array_image)  # Bind the update_array_image method to the dropdown menu changes
        self.array_type_menu = tk.OptionMenu(input_frame, self.array_type_var, "Lattice Dot", "Hex Dot")
        self.array_type_menu.grid(row=0, column=1, padx=10)

        # Dot Diameter textbox (previously Dot Spacing)
        tk.Label(input_frame, text="Dot Diameter (ø):").grid(row=1, column=0, padx=10)
        self.dot_diameter_entry = tk.Entry(input_frame)
        self.dot_diameter_entry.grid(row=1, column=1, padx=10)

        # Dot Spacing textbox (previously Dot Diameter)
        tk.Label(input_frame, text="Dot Spacing:").grid(row=2, column=0, padx=10)
        self.dot_spacing_entry = tk.Entry(input_frame)
        self.dot_spacing_entry.grid(row=2, column=1, padx=10)

        # Box Length textbox
        tk.Label(input_frame, text="Box Length:").grid(row=3, column=0, padx=10)
        self.box_length_entry = tk.Entry(input_frame)
        self.box_length_entry.grid(row=3, column=1, padx=10)

        # Image frame
        image_frame = tk.Frame(self.array_calculator_popup)
        image_frame.grid(row=0, column=1, rowspan=4, padx=10, pady=10, sticky="ne")
        self.array_image_label = tk.Label(image_frame, width=200, height=200)
        self.array_image_label.pack()

        # Separator line
        separator = tk.Frame(self.array_calculator_popup, height=2, bd=1, relief=tk.SUNKEN)
        separator.grid(row=4, columnspan=2, pady=20, sticky="we")

        # New section for array outputs
        array_output_frame = tk.LabelFrame(self.array_calculator_popup, text="Array Outputs", padx=10)
        array_output_frame.grid(row=5, columnspan=2, padx=10, pady=10, sticky="we")

        # Array Number textbox 1
        tk.Label(array_output_frame, text="Array Number (A):").grid(row=0, column=0, padx=10)
        self.array_number_entry_a = tk.Entry(array_output_frame, state='disabled')
        self.array_number_entry_a.grid(row=0, column=1, padx=10)

        # Array Spacing textbox 1
        tk.Label(array_output_frame, text="Array Spacing (A):").grid(row=1, column=0, padx=10)
        self.array_spacing_entry_a = tk.Entry(array_output_frame, state='disabled')
        self.array_spacing_entry_a.grid(row=1, column=1, padx=10)

        # Array Number textbox 2
        self.array_number_label_b = tk.Label(array_output_frame, text="Array Number (B):")
        self.array_number_entry_b = tk.Entry(array_output_frame, state='disabled')

        # Array Spacing textbox 2
        self.array_spacing_label_b = tk.Label(array_output_frame, text="Array Spacing (B):")
        self.array_spacing_entry_b = tk.Entry(array_output_frame, state='disabled')

        # Array Type textbox 1
        tk.Label(array_output_frame, text="Array Type (A):", font=("Helvetica", 9, "bold")).grid(row=2, column=0, padx=10)
        self.array_type_entry_a = tk.Entry(array_output_frame, state='disabled')
        self.array_type_entry_a.grid(row=2, column=1, padx=10)

        # Array Type textbox 2
        self.array_type_label_b = tk.Label(array_output_frame, text="Array Type (B):", font=("Helvetica", 9, "bold"))
        self.array_type_entry_b = tk.Entry(array_output_frame, state='disabled')

        # Calculate button
        self.calculate_button = tk.Button(self.array_calculator_popup, text="Calculate", command=self.calculate_array_outputs)
        self.calculate_button.grid(row=6, columnspan=2, pady=20)  # Increase pady for more spacing

        # Dummy update to ensure that the textboxes are correctly displayed as disabled
        self.update_array_outputs()

        self.update_array_image()  # Initial call to display the image

    def update_array_image(self, *args):
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        image_folder = os.path.join(base_path, 'SetupHelper')

        selected_type = self.array_type_var.get()
        image_path = os.path.join(image_folder, f"{selected_type.replace(' ', '')}.png")

        try:
            image = Image.open(image_path)
            image = image.resize((200, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.array_image_label.config(image=photo)
            self.array_image_label.image = photo  # Keep a reference to avoid garbage collection
        except FileNotFoundError:
            print(f"Image not found: {image_path}")
            self.array_image_label.config(image='')

        # Update visibility of (B) textboxes based on selected type
        if selected_type == "Hex Dot":
            self.array_number_label_b.grid(row=0, column=2, padx=10)
            self.array_number_entry_b.grid(row=0, column=3, padx=10)
            self.array_spacing_label_b.grid(row=1, column=2, padx=10)
            self.array_spacing_entry_b.grid(row=1, column=3, padx=10)
            self.array_type_label_b.grid(row=2, column=2, padx=10)
            self.array_type_entry_b.grid(row=2, column=3, padx=10)
        else:
            if self.array_number_label_b is not None:
                self.array_number_label_b.grid_forget()
            if self.array_number_entry_b is not None:
                self.array_number_entry_b.grid_forget()
            if self.array_spacing_label_b is not None:
                self.array_spacing_label_b.grid_forget()
            if self.array_spacing_entry_b is not None:
                self.array_spacing_entry_b.grid_forget()
            if self.array_type_label_b is not None:
                self.array_type_label_b.grid_forget()
            if self.array_type_entry_b is not None:
                self.array_type_entry_b.grid_forget()

    def update_array_outputs(self):
        self.array_number_entry_a.config(state='normal')
        self.array_number_entry_a.delete(0, tk.END)
        self.array_number_entry_a.insert(0, "")
        self.array_number_entry_a.config(state='disabled')

        self.array_spacing_entry_a.config(state='normal')
        self.array_spacing_entry_a.delete(0, tk.END)
        self.array_spacing_entry_a.insert(0, "")
        self.array_spacing_entry_a.config(state='disabled')

        self.array_number_entry_b.config(state='normal')
        self.array_number_entry_b.delete(0, tk.END)
        self.array_number_entry_b.insert(0, "")
        self.array_number_entry_b.config(state='disabled')

        self.array_spacing_entry_b.config(state='normal')
        self.array_spacing_entry_b.delete(0, tk.END)
        self.array_spacing_entry_b.insert(0, "")
        self.array_spacing_entry_b.config(state='disabled')

        self.array_type_entry_a.config(state='normal')
        self.array_type_entry_a.delete(0, tk.END)
        self.array_type_entry_a.insert(0, "")
        self.array_type_entry_a.config(state='disabled')

        self.array_type_entry_b.config(state='normal')
        self.array_type_entry_b.delete(0, tk.END)
        self.array_type_entry_b.insert(0, "")
        self.array_type_entry_b.config(state='disabled')

    def calculate_array_outputs(self):
        try:
            dot_spacing = float(self.dot_spacing_entry.get())
            dot_diameter = float(self.dot_diameter_entry.get())
            box_length = float(self.box_length_entry.get())

            array_number_a = round(box_length / (dot_diameter + dot_spacing))
            array_spacing_a = dot_spacing
            array_type_a = "Graph"

            array_number_b = round(box_length / (dot_diameter + dot_spacing)) - 1
            array_spacing_b = dot_spacing
            array_type_b = "Graph"

            self.array_number_entry_a.config(state='normal')
            self.array_number_entry_a.delete(0, tk.END)
            self.array_number_entry_a.insert(0, array_number_a)
            self.array_number_entry_a.config(state='disabled')

            self.array_spacing_entry_a.config(state='normal')
            self.array_spacing_entry_a.delete(0, tk.END)
            self.array_spacing_entry_a.insert(0, array_spacing_a)
            self.array_spacing_entry_a.config(state='disabled')

            self.array_type_entry_a.config(state='normal')
            self.array_type_entry_a.delete(0, tk.END)
            self.array_type_entry_a.insert(0, array_type_a)
            self.array_type_entry_a.config(state='disabled')

            self.array_number_entry_b.config(state='normal')
            self.array_number_entry_b.delete(0, tk.END)
            self.array_number_entry_b.insert(0, array_number_b)
            self.array_number_entry_b.config(state='disabled')

            self.array_spacing_entry_b.config(state='normal')
            self.array_spacing_entry_b.delete(0, tk.END)
            self.array_spacing_entry_b.insert(0, array_spacing_b)
            self.array_spacing_entry_b.config(state='disabled')

            self.array_type_entry_b.config(state='normal')
            self.array_type_entry_b.delete(0, tk.END)
            self.array_type_entry_b.insert(0, array_type_b)
            self.array_type_entry_b.config(state='disabled')
        except ValueError:
            mb.showerror("Error", "Please enter valid numerical values for Dot Spacing, Dot Diameter, and Box Length.")

    ##################################################
# Change Parameters
##################################################

    def confirm_change_parameters(self):
        if mb.askyesno("Confirmation", "Are you sure you want to change parameters?"):
            self.show_script_running_popup()  # Show the popup
            print("Confirmed to change parameters")
            self.read_excel_and_start_parameter_change()

    def read_excel_and_start_parameter_change(self):
        try:
            print("Reading Excel file")
            workbook = xlrd.open_workbook("Parameters.xls")
            sheet = workbook.sheet_by_name("Parameters")

            self.parameter_data = []
            for row_idx in range(1, sheet.nrows):  # Skip header row
                row = sheet.row(row_idx)
                try:
                    pen_number = int(row[0].value) if row[0].value != '' else None
                    loops = int(row[1].value) if row[1].value != '' else None
                    speed = int(row[2].value) if row[2].value != '' else None
                    power = int(row[3].value) if row[3].value != '' else None
                    frequency = int(row[4].value) if row[4].value != '' else None
                    checkbox = row[5].value
                    print(f"Row data: {row}")
                    if checkbox:  # Check if the checkbox value is True
                        self.parameter_data.append({
                            "pen_number": pen_number,
                            "loops": loops,
                            "speed": speed,
                            "power": power,
                            "frequency": frequency
                        })
                except ValueError as e:
                    print(f"Skipping row {row_idx} due to error: {e}")

            print(f"Loaded parameters: {self.parameter_data}")
            self.start_parameter_change_thread()
        except FileNotFoundError:
            mb.showerror("Error", "Parameters.xls file not found.")
        except xlrd.biffh.XLRDError:
            mb.showerror("Error", "Parameters sheet not found in the workbook.")
        except Exception as e:
            mb.showerror("Error", str(e))

    def start_parameter_change_thread(self):
        self.stop_script = False  # Reset the flag
        print("Starting parameter change thread")
        threading.Thread(target=self.change_parameters).start()

    def change_parameters(self):
        print("Starting change_parameters")
        # Move to Clear Selection coordinates and perform three clicks with a 0.1 second delay between each click
        clear_selection_x = int(self.location_entries[self.locations.index("Clear Selection")][0].get())
        clear_selection_y = int(self.location_entries[self.locations.index("Clear Selection")][1].get())

        pyautogui.moveTo(clear_selection_x, clear_selection_y)
        for _ in range(3):
            pyautogui.click()
            time.sleep(0.1)

        print(f"Clicked clear selection at ({clear_selection_x}, {clear_selection_y})")

        # Press the Escape key
        pyautogui.press('esc')
        print("Pressed ESC key")

        # Retrieve the delay value entered by the user
        delay = float(self.delay_entry.get()) if self.delay_entry.get() else 0.1
        print(f"Using delay: {delay} seconds")

        if not self.parameter_data:
            print("No parameters to change.")
            return

        for data in self.parameter_data:
            if self.stop_script:
                print("Script execution stopped.")
                break

            pen_number = data["pen_number"]
            loops = data["loops"]
            speed = data["speed"]
            power = data["power"]
            frequency = data["frequency"]

            try:
                if pen_number is not None:
                    print(f"Performing actions for Pen Number {pen_number}")
                    self.change_pen_number(pen_number)
                    time.sleep(delay)  # Add delay after changing pen number
                    print("Clicked Pen Number")
                    self.click_pen_number()
                    time.sleep(delay)  # Add delay after clicking pen number
                    print("Clicked Pen Number")

                print("Checking Default Parameters")
                if not self.check_default():
                    continue
                time.sleep(delay)  # Add delay after checking default parameters
                print("Default Parameters Checked")

                if loops is not None:
                    print("Changing Loops")
                    self.change_loops(loops)
                    time.sleep(delay)  # Add delay after changing loops
                    print("Changed Loops")

                if speed is not None:
                    print("Changing Speed")
                    self.change_speed(speed)
                    time.sleep(delay)  # Add delay after changing speed
                    print("Changed Speed")

                if power is not None:
                    print("Changing Power")
                    self.change_power(power)
                    time.sleep(delay)  # Add delay after changing power
                    print("Changed Power")

                if frequency is not None:
                    print("Changing Frequency")
                    self.change_frequency(frequency)
                    time.sleep(delay)  # Add delay after changing frequency
                    print("Changed Frequency")

            except Exception as e:
                print(f"Error occurred during parameter change for Pen Number {pen_number}: {e}")
                # You may add additional error handling here

        self.close_script_running_popup()  # Close the "Script Running" popup before showing "Actions Completed"

        if not self.escape_pressed:
            self.show_actions_completed_popup()

        self.escape_pressed = False  # Reset the flag for next run

    def change_pen_number(self, pen_number):
        print(f"Changing to Pen Number {pen_number}")
        # Move cursor to Pen Window and click
        x = int(self.location_entries[self.locations.index("Pen Window")][0].get())
        y = int(self.location_entries[self.locations.index("Pen Window")][1].get())
        print(f"Moving to Pen Window coordinates: ({x}, {y})")
        pyautogui.click(x, y)
        pyautogui.press('0')
        # Press down arrow key (Pen Number) times
        pyautogui.press('down', presses=int(pen_number))  # Ensure pen_number is an integer
        print(f"Pressed down key {pen_number} times")
        time.sleep(0.1)

    def right_click_pen_number(self):
        print("Right clicking Pen Number")
        # Retrieve the RGB values entered by the user
        target_color = (
            int(self.rgb_r_entry.get()),
            int(self.rgb_g_entry.get()),
            int(self.rgb_b_entry.get())
        )
        print(f"Target color: {target_color}")
        # Retrieve the start and stop coordinates entered by the user
        start_x = int(self.location_entries[self.locations.index("Target RGB Start")][0].get())
        start_y = int(self.location_entries[self.locations.index("Target RGB Start")][1].get())
        end_x = int(self.location_entries[self.locations.index("Target RGB Stop")][0].get())
        end_y = int(self.location_entries[self.locations.index("Target RGB Stop")][1].get())
        step = 5  # Step size for iteration
        print(f"Searching for target color from ({start_x}, {start_y}) to ({end_x}, {end_y})")

        # Loop through the specified range of pixels with the specified step size
        for x in range(start_x, end_x + 1, step):
            for y in range(start_y, end_y + 1, step):
                pixel_color = pyautogui.pixel(x, y)
                if pixel_color == target_color:
                    print(f"Found target color at ({x}, {y})")
                    # Right-click the center of the found pixel
                    pyautogui.click(x, y, button='right')
                    return  # Exit the function once the target color is found
        # If the target color is not found, print a message
        print("Target color not found within the specified range.")

    def click_pen_number(self):
        print("Clicking Pen Number")
        # Retrieve the RGB values entered by the user
        target_color = (
            int(self.rgb_r_entry.get()),
            int(self.rgb_g_entry.get()),
            int(self.rgb_b_entry.get())
        )
        print(f"Target color: {target_color}")
        # Retrieve the start and stop coordinates entered by the user
        start_x = int(self.location_entries[self.locations.index("Target RGB Start")][0].get())
        start_y = int(self.location_entries[self.locations.index("Target RGB Start")][1].get())
        end_x = int(self.location_entries[self.locations.index("Target RGB Stop")][0].get())
        end_y = int(self.location_entries[self.locations.index("Target RGB Stop")][1].get())
        step = 5  # Step size for iteration
        print(f"Searching for target color from ({start_x}, {start_y}) to ({end_x}, {end_y})")

        # Loop through the specified range of pixels with the specified step size
        for x in range(start_x, end_x + 1, step):
            for y in range(start_y, end_y + 1, step):
                pixel_color = pyautogui.pixel(x, y)
                if pixel_color == target_color:
                    print(f"Found target color at ({x}, {y})")
                    # Click the center of the found pixel
                    pyautogui.click(x, y)
                    return  # Exit the function once the target color is found
        # If the target color is not found, print a message
        print("Target color not found within the specified range.")

    def check_default(self):
        print("Checking default parameters")
        # Check if pixel at Default Parameter Tickbox coordinates is (0, 0, 0) or (255, 255, 255)
        x = int(self.location_entries[self.locations.index("Default Parameter Tickbox")][0].get())
        y = int(self.location_entries[self.locations.index("Default Parameter Tickbox")][1].get())
        pixel_color = pyautogui.pixel(x, y)
        print(f"Pixel color at Default Parameter Tickbox coordinates: {pixel_color}")
        if pixel_color == (0, 0, 0):
            pyautogui.click(x, y)
            print("Clicked Default Parameter Tickbox (black)")
            return True
        elif pixel_color == (255, 255, 255):
            print("Default Parameter Tickbox is white, no need to click")
            return True
        print("Default Parameter Tickbox is neither black nor white")
        return False

    def change_loops(self, loops):
        print(f"Changing loops to {loops}")
        # Move cursor to Loops coordinates
        x = int(self.location_entries[self.locations.index("Loops")][0].get())
        y = int(self.location_entries[self.locations.index("Loops")][1].get())
        print(f"Moving to Loops coordinates: ({x}, {y})")
        pyautogui.click(x, y)
        time.sleep(0.1)
        pyautogui.click(x, y)
        time.sleep(0.1)
        pyautogui.typewrite(str(loops))
        print(f"Changed loops to {loops}")

    def change_speed(self, speed):
        print(f"Changing speed to {speed}")
        # Move cursor to Speed coordinates
        x = int(self.location_entries[self.locations.index("Speed")][0].get())
        y = int(self.location_entries[self.locations.index("Speed")][1].get())
        print(f"Moving to Speed coordinates: ({x}, {y})")
        pyautogui.click(x, y)
        time.sleep(0.1)
        pyautogui.click(x, y)
        time.sleep(0.1)
        pyautogui.typewrite(str(speed))
        print(f"Changed speed to {speed}")

    def change_power(self, power):
        print(f"Changing power to {power}")
        # Move cursor to Power coordinates
        x = int(self.location_entries[self.locations.index("Power")][0].get())
        y = int(self.location_entries[self.locations.index("Power")][1].get())
        print(f"Moving to Power coordinates: ({x}, {y})")
        pyautogui.click(x, y)
        time.sleep(0.1)
        pyautogui.click(x, y)
        time.sleep(0.1)
        pyautogui.typewrite(str(power))
        print(f"Changed power to {power}")

    def change_frequency(self, frequency):
        print(f"Changing frequency to {frequency}")
        # Move cursor to Frequency coordinates
        x = int(self.location_entries[self.locations.index("Frequency")][0].get())
        y = int(self.location_entries[self.locations.index("Frequency")][1].get())
        print(f"Moving to Frequency coordinates: ({x}, {y})")
        pyautogui.click(x, y)
        time.sleep(0.1)
        pyautogui.click(x, y)
        time.sleep(0.1)
        pyautogui.typewrite(str(frequency))
        print(f"Changed frequency to {frequency}")

    ##################################################
# Popups and Notifications
##################################################

    def show_script_running_popup(self):
        self.popup_window = tk.Toplevel(self.master)
        self.popup_window.title("Script Running")
        self.popup_window.geometry("+0+0")  # Position at the top left corner

        # Set the desired background color
        background_color = "#ff0000"  # Replace with your desired color
        self.popup_window.configure(bg=background_color)

        self.message_label = tk.Label(self.popup_window, text="Do not move the mouse, the script is performing actions. Press Escape to stop the script.", bg=background_color, wraplength=300, font=("Helvetica", 16, "bold"))
        self.message_label.pack(padx=20, pady=20)

        self.popup_window.protocol("WM_DELETE_WINDOW", self.close_script_running_popup)

        # Start flashing the message
        self.flash_message()

    def close_script_running_popup(self):
        if hasattr(self, 'popup_window'):
            self.popup_window.destroy()
            del self.popup_window

    def flash_message(self):
        if hasattr(self, 'popup_window') and self.popup_window.winfo_exists():
            current_bg = self.message_label.cget("bg")
            current_fg = self.message_label.cget("fg")

            new_bg = "red" if current_bg == "black" else "black"
            new_fg = "black" if current_fg == "red" else "red"

            self.message_label.config(bg=new_bg, fg=new_fg)
            self.popup_window.config(bg=new_bg)  # Update the Toplevel window background color

            self.popup_window.after(350, self.flash_message)  # Toggle colors every 500 ms


    def show_actions_completed_popup(self):
        # Only show the popup if the script was not halted by pressing Escape
        if not self.escape_pressed:
            if hasattr(self, 'completed_popup'):
                self.close_actions_completed_popup()

            self.completed_popup = tk.Toplevel(self.master)
            self.completed_popup.title("Actions Completed")
            self.completed_popup.geometry("+0+0")  # Position at the top left corner

            # Set your desired RGB color here
            background_color = "#57eb72"  # Light Green color as an example
            self.completed_popup.configure(bg=background_color)

            message = "Actions performed."
            tk.Label(self.completed_popup, text=message, bg=background_color, wraplength=300, font=("Helvetica", 16, "bold")).pack(padx=20, pady=20)

            close_button = tk.Button(self.completed_popup, text="Close", command=self.close_actions_completed_popup)
            close_button.pack(pady=0)
            close_button.focus_set()  # Set focus on the close button

            self.completed_popup.protocol("WM_DELETE_WINDOW", self.close_actions_completed_popup)

    def close_actions_completed_popup(self):
        if hasattr(self, 'completed_popup'):
            self.completed_popup.destroy()
            del self.completed_popup

    def show_default_parameter_popup(self, is_correct):
        popup = tk.Toplevel(self.master)
        popup.geometry("+0+0")  # Position at the top left corner

        if is_correct:
            popup.title("Coordinates Correct")
            popup.configure(bg="#57eb72")  # Light Green color
            message = "Default Parameter Tickbox coordinates correct."
        else:
            popup.title("Coordinates Incorrect")
            popup.configure(bg="#ff0000")  # Red color
            message = "Default Parameter Tickbox coordinates incorrect."

        tk.Label(popup, text=message, bg=popup.cget("bg"), wraplength=300, font=("Helvetica", 16, "bold")).pack(padx=20, pady=20)
        tk.Button(popup, text="Close", command=popup.destroy).pack(pady=10)

    def show_escape_pressed_popup(self):
        if hasattr(self, 'escape_popup'):
            self.close_escape_pressed_popup()

        self.escape_popup = tk.Toplevel(self.master)
        self.escape_popup.title("Script Halted")
        self.escape_popup.geometry("+0+0")  # Position at the top left corner

        # Set your desired RGB color here
        background_color = "#ffff00"
        self.escape_popup.configure(bg=background_color)

        self.escape_popup_label = tk.Label(self.escape_popup, text="", bg=background_color, wraplength=300, font=("Helvetica", 16, "bold"))
        self.escape_popup_label.pack(padx=20, pady=20)

        close_button = tk.Button(self.escape_popup, text="Close", command=self.close_escape_pressed_popup)
        close_button.pack(pady=0)
        close_button.focus_set()  # Set focus on the close button

        self.escape_popup.protocol("WM_DELETE_WINDOW", self.close_escape_pressed_popup)

        # Start the countdown
        self.countdown_and_close_escape_popup(8)

    def countdown_and_close_escape_popup(self, countdown):
        if hasattr(self, 'escape_popup') and self.escape_popup.winfo_exists():
            self.escape_popup_label.config(text=f"Escape key pressed, actions halted.\nScript will complete current action sequence.\nWindow will close in {countdown} seconds.")
            if countdown > 0:
                self.master.after(1000, self.countdown_and_close_escape_popup, countdown - 1)
            else:
                self.close_escape_pressed_popup()

    def close_escape_pressed_popup(self):
        if hasattr(self, 'escape_popup'):
            self.escape_popup.destroy()
            del self.escape_popup

##################################################
# Main Application Initialization
##################################################

root = tk.Tk()
app = LaserParameterChanger(root)
root.mainloop()
