"""
SVG Path Builder Application
==========================
A professional-grade tool for creating and editing SVG paths with text animation.
Features include point manipulation, image tracing, undo/redo, SVG export/import, and canvas scrolling.

Requirements:
- Python 3.8+
- tkinter
- pyperclip
- Pillow (for image loading)

Usage Instructions:
1. Run the script to launch the application.
2. Use the left canvas to draw/edit paths:
   - 'Add Points' mode: Click to add points, creating a continuous path.
   - 'Edit Points' mode: Click and drag to move points or control handles.
3. Load an image to trace using the 'Load Image' button, then trace by adding points.
4. Use the right control panel to:
   - Input custom path data or load SVG files.
   - Adjust text properties (content, size, color, spacing).
   - Control animation settings.
   - Export/import SVG files, copy SVG code, or fit path to canvas.
   - Undo/redo actions.
5. Scroll the canvas using the mouse wheel or scrollbars if the path/image extends beyond view.
6. Use 'Fit to Canvas' to rescale large paths.
7. Copy SVG code using the 'Copy SVG Code' button.

Controls:
- Left-click: Add point (Add Points mode) or select point (Edit Points mode).
- Drag: Move selected point/control handle (constrained to canvas).
- Mouse wheel: Scroll canvas vertically.
- Shift + Mouse wheel: Scroll canvas horizontally.
- Ctrl+Z: Undo
- Ctrl+Y: Redo
- Ctrl+S: Save SVG file
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import pyperclip
import math
import time
import os
from typing import List, Tuple, Optional
import re
from PIL import Image, ImageTk

class SVGPathBuilder:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SVG Path Builder")
        self.root.geometry("1200x800")
        
        # Initialize state
        self.points: List[Tuple] = []
        self.undo_stack: List[List[Tuple]] = []
        self.redo_stack: List[List[Tuple]] = []
        self.dragging: bool = False
        self.selected_point_index: Optional[Tuple[int, int]] = None
        self.is_animating: bool = False
        self.image = None  # Store the image
        self.image_id = None  # Canvas image ID
        self.photo = None  # Tkinter PhotoImage
        
        # Canvas settings
        self.canvas_width: int = 800
        self.canvas_height: int = 600
        self.animation_speed: float = 0.05  # Seconds per frame
        
        self.create_ui()
        self.setup_keybindings()
        
    def create_ui(self) -> None:
        """Create and configure the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Canvas with scrollbars
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", 
                              width=self.canvas_width, 
                              height=self.canvas_height,
                              scrollregion=(0, 0, self.canvas_width*2, self.canvas_height*2))
        hbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        hbar.config(command=self.canvas.xview)
        vbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        vbar.config(command=self.canvas.yview)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas bindings
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux
        
        # Title
        ttk.Label(control_frame, text="SVG Path Builder", 
                 font=("Arial", 16, "bold")).pack(pady=10)
        
        # Mode selection
        mode_frame = ttk.LabelFrame(control_frame, text="Mode", padding="5")
        mode_frame.pack(fill=tk.X, pady=5)
        self.mode_var = tk.StringVar(value="add_points")
        ttk.Radiobutton(mode_frame, text="Add Points", 
                       variable=self.mode_var, 
                       value="add_points").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(mode_frame, text="Edit Points", 
                       variable=self.mode_var, 
                       value="edit_points").pack(anchor=tk.W, pady=2)
        
        # Path controls
        path_frame = ttk.LabelFrame(control_frame, text="Path", padding="5")
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="Path Data:").pack(anchor=tk.W, pady=(5, 2))
        self.path_data_var = tk.StringVar()
        path_entry = ttk.Entry(path_frame, textvariable=self.path_data_var, width=40)
        path_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(path_frame, text="Load Path", 
                  command=self.load_path_data).pack(anchor=tk.W, pady=(0, 5))
        
        # Sample path
        ttk.Button(path_frame, text="Load Sample Path", 
                  command=lambda: [
                      self.path_data_var.set("M63,766 C55,25 776,782 775,38"),
                      self.letter_spacing_var.set(-2),
                      self.font_size_var.set(18),
                      self.text_var.set("Thank You 😉"),
                      self.load_path_data()
                  ]).pack(fill=tk.X, pady=5)
        
        # Text controls
        text_frame = ttk.LabelFrame(control_frame, text="Text Properties", padding="5")
        text_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(text_frame, text="Text Content:").pack(anchor=tk.W, pady=(5, 2))
        self.text_var = tk.StringVar(value="Your text here")
        ttk.Entry(text_frame, textvariable=self.text_var, width=30).pack(fill=tk.X, pady=(0, 5))
        self.text_var.trace_add("write", self.update_preview)
        
        ttk.Label(text_frame, text="Font Size:").pack(anchor=tk.W, pady=(5, 2))
        self.font_size_var = tk.StringVar(value="36")
        ttk.Entry(text_frame, textvariable=self.font_size_var, width=10).pack(anchor=tk.W, pady=(0, 5))
        self.font_size_var.trace_add("write", self.update_preview)
        
        ttk.Label(text_frame, text="Text Color:").pack(anchor=tk.W, pady=(5, 2))
        self.text_color_var = tk.StringVar(value="black")
        ttk.Entry(text_frame, textvariable=self.text_color_var, width=10).pack(anchor=tk.W, pady=(0, 5))
        self.text_color_var.trace_add("write", self.update_preview)
        
        ttk.Label(text_frame, text="Letter Spacing:").pack(anchor=tk.W, pady=(5, 2))
        self.letter_spacing_var = tk.IntVar(value=0)
        ttk.Scale(text_frame, from_=-20, to=50, 
                 variable=self.letter_spacing_var,
                 command=lambda e: self.update_preview()).pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(text_frame, text="Start Offset (%):").pack(anchor=tk.W, pady=(5, 2))
        self.start_offset_var = tk.StringVar(value="0")
        ttk.Entry(text_frame, textvariable=self.start_offset_var, width=10).pack(anchor=tk.W, pady=(0, 5))
        self.start_offset_var.trace_add("write", self.update_preview)
        
        # Animation controls
        anim_frame = ttk.LabelFrame(control_frame, text="Animation", padding="5")
        anim_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(anim_frame, text="Duration (seconds):").pack(anchor=tk.W, pady=(5, 2))
        self.duration_var = tk.StringVar(value="10")
        ttk.Entry(anim_frame, textvariable=self.duration_var, width=10).pack(anchor=tk.W, pady=(0, 5))
        
        # Action buttons
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(action_frame, text="Clear Canvas", 
                  command=self.clear_canvas).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(action_frame, text="Preview Animation", 
                  command=self.toggle_animation).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Undo/Redo buttons
        ttk.Button(action_frame, text="Undo", 
                  command=self.undo).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(action_frame, text="Redo", 
                  command=self.redo).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Export/Import buttons
        export_frame = ttk.Frame(control_frame)
        export_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(export_frame, text="Save SVG", 
                  command=self.save_svg_file).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(export_frame, text="Load SVG", 
                  command=self.load_svg_file).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(export_frame, text="Copy SVG Code", 
                  command=self.copy_svg_code).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Image and Fit buttons
        ttk.Button(export_frame, text="Load Image", 
                  command=self.load_image).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(export_frame, text="Fit to Canvas", 
                  command=self.fit_to_canvas).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # SVG code display (no heading)
        self.svg_code_text = scrolledtext.ScrolledText(control_frame, 
                                                    width=40, 
                                                    height=15, 
                                                    wrap=tk.WORD,
                                                    state='normal')
        self.svg_code_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
    def setup_keybindings(self) -> None:
        """Configure keyboard shortcuts."""
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-s>", lambda e: self.save_svg_file())
        
    def on_mouse_wheel(self, event: tk.Event) -> None:
        """Handle mouse wheel for vertical scrolling."""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
            
    def on_shift_mouse_wheel(self, event: tk.Event) -> None:
        """Handle shift + mouse wheel for horizontal scrolling."""
        if event.delta > 0:
            self.canvas.xview_scroll(-1, "units")
        elif event.delta < 0:
            self.canvas.xview_scroll(1, "units")
        
    def load_image(self) -> None:
        """Load and display an image on the canvas for tracing."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        if file_path:
            try:
                # Open and resize image to fit canvas
                image = Image.open(file_path)
                # Scale image to fit canvas while preserving aspect ratio
                img_width, img_height = image.size
                scale = min(self.canvas_width / img_width, self.canvas_height / img_height)
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Store image and create PhotoImage
                self.image = image
                self.photo = ImageTk.PhotoImage(image)
                
                # Display image on canvas (top-left corner)
                if self.image_id:
                    self.canvas.delete(self.image_id)
                self.image_id = self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
                
                # Ensure image is at the bottom layer
                self.canvas.lower(self.image_id)
                self.draw_path()  # Redraw path over image
                self.show_status("Image loaded successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
        
    def save_state(self) -> None:
        """Save current points state for undo/redo."""
        self.undo_stack.append(self.points.copy())
        self.redo_stack.clear()
        if len(self.undo_stack) > 50:  # Limit undo history
            self.undo_stack.pop(0)
            
    def undo(self) -> None:
        """Revert to previous state."""
        if self.undo_stack:
            self.redo_stack.append(self.points.copy())
            self.points = self.undo_stack.pop()
            self.draw_path()
            
    def redo(self) -> None:
        """Restore undone state."""
        if self.redo_stack:
            self.undo_stack.append(self.points.copy())
            self.points = self.redo_stack.pop()
            self.draw_path()
            
    def load_path_data(self) -> None:
        """Parse and load SVG path data, supporting absolute and relative commands."""
        try:
            path_string = self.path_data_var.get().strip()
            if not path_string:
                return
                
            self.save_state()
            self.points = []
            current_x, current_y = 0, 0  # Track current position for relative commands
            
            # Normalize spaces and split into tokens
            path_string = re.sub(r'\s+', ' ', path_string).strip()
            # Tokenize commands and numbers
            tokens = []
            i = 0
            while i < len(path_string):
                char = path_string[i]
                if char.isalpha():
                    tokens.append(char)
                    i += 1
                elif char in ' ,':
                    i += 1
                    continue
                else:
                    # Extract number (including negative and scientific notation)
                    match = re.match(r'[+-]?\d*\.?\d+(?:[eE][+-]?\d+)?', path_string[i:])
                    if match:
                        num = match.group()
                        tokens.append(num)
                        i += len(num)
                    else:
                        raise ValueError(f"Invalid character in path data at position {i}: {char}")
            
            i = 0
            while i < len(tokens):
                cmd = tokens[i]
                i += 1
                
                if cmd.lower() == 'm':
                    if i + 1 >= len(tokens):
                        raise ValueError("Incomplete 'M'/'m' command")
                    x = float(tokens[i])
                    y = float(tokens[i + 1])
                    if cmd == 'm':  # Relative
                        x += current_x
                        y += current_y
                    self.points.append(('M', x, y))
                    current_x, current_y = x, y
                    i += 2
                    
                    # Handle implicit line-to commands after M
                    while i < len(tokens) and tokens[i] not in 'MmCcZz':
                        x = float(tokens[i])
                        y = float(tokens[i + 1])
                        if cmd == 'm':
                            x += current_x
                            y += current_y
                        # Convert implicit line-to into a Cubic Bezier with control points
                        last_x, last_y = current_x, current_y
                        cp1_x = last_x + (x - last_x) / 3
                        cp1_y = last_y + (y - last_y) / 3
                        cp2_x = last_x + 2 * (x - last_x) / 3
                        cp2_y = last_y + 2 * (y - last_y) / 3
                        self.points.append(('C', cp1_x, cp1_y, cp2_x, cp2_y, x, y))
                        current_x, current_y = x, y
                        i += 2
                    
                elif cmd.lower() == 'c':
                    while i < len(tokens) and tokens[i] not in 'MmCcZz':
                        if i + 5 >= len(tokens):
                            raise ValueError("Incomplete 'C'/'c' command")
                        cp1_x = float(tokens[i])
                        cp1_y = float(tokens[i + 1])
                        cp2_x = float(tokens[i + 2])
                        cp2_y = float(tokens[i + 3])
                        end_x = float(tokens[i + 4])
                        end_y = float(tokens[i + 5])
                        if cmd == 'c':  # Relative
                            cp1_x += current_x
                            cp1_y += current_y
                            cp2_x += current_x
                            cp2_y += current_y
                            end_x += current_x
                            end_y += current_y
                        self.points.append(('C', cp1_x, cp1_y, cp2_x, cp2_y, end_x, end_y))
                        current_x, current_y = end_x, end_y
                        i += 6
                    
                elif cmd.lower() == 'z':
                    # Close path (not fully implemented, skip for now)
                    continue
                    
                else:
                    raise ValueError(f"Unsupported path command: {cmd}")
            
            if self.points:
                self.normalize_path()
                self.draw_path()
                self.generate_svg()
                self.show_status("Path loaded successfully!")
            else:
                raise ValueError("No valid path commands found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Invalid path data: {str(e)}")
            self.svg_code_text.delete(1.0, tk.END)
            self.svg_code_text.insert(tk.END, f"Error loading path: {str(e)}")
            
    def normalize_path(self) -> None:
        """Scale and center points to fit canvas with padding."""
        if not self.points:
            return
            
        all_x = [p[1] for p in self.points if p[0] == 'M'] + \
                [p[i] for p in self.points if p[0] == 'C' for i in [1, 3, 5]]
        all_y = [p[2] for p in self.points if p[0] == 'M'] + \
                [p[i] for p in self.points if p[0] == 'C' for i in [2, 4, 6]]
                
        if not all_x or not all_y:
            return
            
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        # Avoid division by zero
        width = max_x - min_x if max_x != min_x else 1
        height = max_y - min_y if max_y != min_y else 1
        
        padding = 50
        width_scale = (self.canvas_width - 2 * padding) / width
        height_scale = (self.canvas_height - 2 * padding) / height
        scale = min(width_scale, height_scale)
        
        # Center the path
        offset_x = (self.canvas_width - width * scale) / 2 - min_x * scale
        offset_y = (self.canvas_height - height * scale) / 2 - min_y * scale
        
        for i, point in enumerate(self.points):
            if point[0] == 'M':
                x = point[1] * scale + offset_x
                y = point[2] * scale + offset_y
                self.points[i] = ('M', x, y)
            elif point[0] == 'C':
                cp1_x = point[1] * scale + offset_x
                cp1_y = point[2] * scale + offset_y
                cp2_x = point[3] * scale + offset_x
                cp2_y = point[4] * scale + offset_y
                end_x = point[5] * scale + offset_x
                end_y = point[6] * scale + offset_y
                self.points[i] = ('C', cp1_x, cp1_y, cp2_x, cp2_y, end_x, end_y)
                
    def fit_to_canvas(self) -> None:
        """Rescale path to fit within canvas boundaries."""
        self.save_state()
        self.normalize_path()
        self.draw_path()
        self.show_status("Path fitted to canvas!")
        
    def on_canvas_click(self, event: tk.Event) -> None:
        """Handle canvas click events."""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        # Constrain to canvas boundaries
        x = max(0, min(x, self.canvas_width))
        y = max(0, min(y, self.canvas_height))
        
        if self.mode_var.get() == "add_points":
            self.save_state()
            if not self.points:
                self.points.append(('M', x, y))
            else:
                last_x, last_y = self.get_previous_endpoint(len(self.points))
                cp1_x = last_x + (x - last_x) / 3
                cp1_y = last_y + (y - last_y) / 3
                cp2_x = last_x + 2 * (x - last_x) / 3
                cp2_y = last_y + 2 * (y - last_y) / 3
                self.points.append(('C', cp1_x, cp1_y, cp2_x, cp2_y, x, y))
            self.draw_path()
            
        elif self.mode_var.get() == "edit_points":
            for i, point in enumerate(self.points):
                if point[0] == 'M':
                    px, py = point[1], point[2]
                    if math.hypot(x - px, y - py) < 10:
                        self.selected_point_index = (i, 0)
                        self.dragging = True
                        return
                elif point[0] == 'C':
                    for j in range(3):
                        px, py = point[1 + j*2], point[2 + j*2]
                        if math.hypot(x - px, y - py) < 10:
                            self.selected_point_index = (i, j)
                            self.dragging = True
                            return
                            
    def on_canvas_drag(self, event: tk.Event) -> None:
        """Handle canvas drag events."""
        if self.dragging and self.selected_point_index is not None:
            x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            # Constrain to canvas boundaries
            x = max(0, min(x, self.canvas_width))
            y = max(0, min(y, self.canvas_height))
            
            idx, point_type = self.selected_point_index
            
            self.save_state()
            if idx < len(self.points):
                if self.points[idx][0] == 'M':
                    self.points[idx] = ('M', x, y)
                elif self.points[idx][0] == 'C' and point_type < 3:
                    old_point = list(self.points[idx])
                    old_point[1 + point_type*2] = x
                    old_point[2 + point_type*2] = y
                    self.points[idx] = tuple(old_point)
                self.draw_path()
                
    def on_canvas_release(self, event: tk.Event) -> None:
        """Handle canvas release events."""
        self.dragging = False
        self.selected_point_index = None
        self.draw_path()  # Ensure a clean redraw after release
        
    def clear_canvas(self) -> None:
        """Clear all points, image, and reset canvas."""
        if self.points:
            self.save_state()
        self.points = []
        self.image = None
        self.photo = None
        if self.image_id:
            self.canvas.delete(self.image_id)
            self.image_id = None
        self.canvas.delete("all")
        self.is_animating = False
        self.svg_code_text.delete(1.0, tk.END)
        self.update_preview()
        
    def draw_path(self) -> None:
        """Render the path and control points on canvas."""
        # Clear all path-related items, including any duplicates
        self.canvas.delete("path", "point", "cp1", "cp2", "label", "handle", "text_preview")
        
        # Redraw image if present
        if self.image_id:
            self.canvas.create_image(0, 0, image=self.photo, anchor="nw", tags="image")
            self.canvas.lower("image")
        
        if not self.points:
            return
            
        path_coords = []
        if self.points[0][0] == 'M':
            path_coords.extend([self.points[0][1], self.points[0][2]])
            
        for i, point in enumerate(self.points[1:], start=1):
            if point[0] == 'C':
                prev_x, prev_y = self.get_previous_endpoint(i)
                cp1_x, cp1_y = point[1], point[2]
                cp2_x, cp2_y = point[3], point[4]
                end_x, end_y = point[5], point[6]
                
                # Sample Bezier curve for smooth rendering
                segments = 20
                for j in range(1, segments + 1):
                    t = j / segments
                    x = (1-t)**3 * prev_x + 3*(1-t)**2*t * cp1_x + \
                        3*(1-t)*t**2 * cp2_x + t**3 * end_x
                    y = (1-t)**3 * prev_y + 3*(1-t)**2*t * cp1_y + \
                        3*(1-t)*t**2 * cp2_y + t**3 * end_y
                    path_coords.extend([x, y])
                    
        if len(path_coords) >= 4:
            self.canvas.create_line(path_coords, fill="black", width=2, 
                                  smooth=True, tags="path")
            
        for i, point in enumerate(self.points):
            if point[0] == 'M':
                x, y = point[1], point[2]
                self.canvas.create_oval(x-5, y-5, x+5, y+5, 
                                      fill="blue", tags="point")
                self.canvas.create_text(x, y-15, text=f"M{i}", 
                                      tags="label")
            elif point[0] == 'C':
                cp1_x, cp1_y = point[1], point[2]
                cp2_x, cp2_y = point[3], point[4]
                x, y = point[5], point[6]
                
                self.canvas.create_oval(cp1_x-4, cp1_y-4, cp1_x+4, cp1_y+4, 
                                      fill="red", tags="cp1")
                self.canvas.create_oval(cp2_x-4, cp2_y-4, cp2_x+4, cp2_y+4, 
                                      fill="green", tags="cp2")
                self.canvas.create_oval(x-5, y-5, x+5, y+5, 
                                      fill="blue", tags="point")
                
                if i > 0:
                    prev_x, prev_y = self.get_previous_endpoint(i)
                    self.canvas.create_line(prev_x, prev_y, cp1_x, cp1_y, 
                                          fill="red", dash=(2, 2), 
                                          tags="handle")
                    self.canvas.create_line(x, y, cp2_x, cp2_y, 
                                          fill="green", dash=(2, 2), 
                                          tags="handle")
                
                self.canvas.create_text(cp1_x, cp1_y-10, text=f"CP1.{i}", 
                                      tags="label")
                self.canvas.create_text(cp2_x, cp2_y-10, text=f"CP2.{i}", 
                                      tags="label")
                self.canvas.create_text(x, y-15, text=f"P{i}", 
                                      tags="label")
        
        self.update_preview()
        
    def get_previous_endpoint(self, index: int) -> Tuple[float, float]:
        """Get the endpoint of the previous segment."""
        if index <= 0:
            return 0, 0
        prev = self.points[index-1]
        return (prev[1], prev[2]) if prev[0] == 'M' else (prev[5], prev[6])
        
    def update_preview(self, *args) -> None:
        """Update text preview along path."""
        self.canvas.delete("text_preview")
        if not self.points or not self.text_var.get():
            self.svg_code_text.delete(1.0, tk.END)
            return
            
        try:
            font_size = int(self.font_size_var.get())
            start_offset_percent = float(self.start_offset_var.get())
            letter_spacing = self.letter_spacing_var.get()
            text_color = self.text_color_var.get()
        except ValueError:
            self.svg_code_text.delete(1.0, tk.END)
            self.svg_code_text.insert(tk.END, "Invalid font size or offset value.")
            return
            
        path_points = self.sample_path_points(100)
        if not path_points:
            self.svg_code_text.delete(1.0, tk.END)
            return
            
        start_offset_idx = max(0, min(int(len(path_points) * start_offset_percent / 100), 
                                   len(path_points)-1))
        char_width = font_size * 0.6
        current_pos = start_offset_idx
        
        for char in self.text_var.get():
            if current_pos >= len(path_points):
                break
            x, y = path_points[current_pos]
            self.canvas.create_text(x, y, text=char, fill=text_color, 
                                 font=("Arial", font_size), angle=0, 
                                 anchor="center", tags="text_preview")
            current_pos += int(char_width) + letter_spacing
        
        self.generate_svg()
        
    def sample_path_points(self, num_points: int) -> List[Tuple[float, float]]:
        """Sample points along the path."""
        path_points = []
        if not self.points:
            return path_points
            
        if self.points[0][0] == 'M':
            path_points.append((self.points[0][1], self.points[0][2]))
            
        for i in range(1, len(self.points)):
            if self.points[i][0] == 'C':
                prev_x, prev_y = self.get_previous_endpoint(i)
                cp1_x, cp1_y = self.points[i][1], self.points[i][2]
                cp2_x, cp2_y = self.points[i][3], self.points[i][4]
                end_x, end_y = self.points[i][5], self.points[i][6]
                
                points_per_segment = num_points // max(1, len(self.points)-1)
                for j in range(1, points_per_segment + 1):
                    t = j / points_per_segment
                    x = (1-t)**3 * prev_x + 3*(1-t)**2*t * cp1_x + \
                        3*(1-t)*t**2 * cp2_x + t**3 * end_x
                    y = (1-t)**3 * prev_y + 3*(1-t)**2*t * cp1_y + \
                        3*(1-t)*t**2 * cp2_y + t**3 * end_y
                    path_points.append((x, y))
        return path_points
        
    def generate_svg(self) -> None:
        """Generate SVG code from current path and settings."""
        try:
            if not self.points:
                self.svg_code_text.delete(1.0, tk.END)
                self.svg_code_text.insert(tk.END, "No path defined yet.")
                return
                
            path_data = []
            for point in self.points:
                if point[0] == 'M':
                    path_data.append(f"M{point[1]:.2f},{point[2]:.2f}")
                elif point[0] == 'C':
                    path_data.append(f"C{point[1]:.2f},{point[2]:.2f} " +
                                   f"{point[3]:.2f},{point[4]:.2f} " +
                                   f"{point[5]:.2f},{point[6]:.2f}")
            
            all_x = [p[1] for p in self.points if p[0] == 'M'] + \
                    [p[i] for p in self.points if p[0] == 'C' for i in [1, 3, 5]]
            all_y = [p[2] for p in self.points if p[0] == 'M'] + \
                    [p[i] for p in self.points if p[0] == 'C' for i in [2, 4, 6]]
                    
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            viewbox = f"{min_x-50:.2f} {min_y-50:.2f} {(max_x-min_x+100):.2f} {(max_y-min_y+100):.2f}"
            
            svg_code = f"""<svg xmlns="http://www.w3.org/2000/svg" 
viewBox="{viewbox}" 
width="100%" 
height="100%">
    <path id="curve" 
        d="{' '.join(path_data)}" 
        fill="none" 
        stroke="black" 
        stroke-width="2"/>
    <text font-size="{self.font_size_var.get()}" 
        fill="{self.text_color_var.get()}" 
        letter-spacing="{self.letter_spacing_var.get()}px">
        <textPath href="#curve" 
            startOffset="{self.start_offset_var.get()}%">
            {self.text_var.get()}
            <animate 
                attributeName="startOffset" 
                from="100%" 
                to="-100%" 
                dur="{self.duration_var.get()}s" 
                repeatCount="indefinite"/>
        </textPath>
    </text>
</svg>"""
            
            self.svg_code_text.delete(1.0, tk.END)
            self.svg_code_text.insert(tk.END, svg_code.strip())
            
        except Exception as e:
            self.svg_code_text.delete(1.0, tk.END)
            self.svg_code_text.insert(tk.END, f"Error generating SVG: {str(e)}")
            
    def copy_svg_code(self) -> None:
        """Copy SVG code to clipboard."""
        try:
            svg_code = self.svg_code_text.get(1.0, tk.END).strip()
            if svg_code and "No path defined" not in svg_code and "Error generating" not in svg_code:
                pyperclip.copy(svg_code)
                self.show_status("SVG code copied to clipboard!")
            else:
                self.show_status("No valid SVG code to copy!", color="red")
        except Exception as e:
            self.show_status(f"Failed to copy SVG code: {str(e)}", color="red")
        
    def save_svg_file(self) -> None:
        """Save SVG code to file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.svg_code_text.get(1.0, tk.END).strip())
                self.show_status("SVG saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save SVG: {str(e)}")
                
    def load_svg_file(self) -> None:
        """Load SVG file and extract path data."""
        file_path = filedialog.askopenfilename(
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Find path data using regex
                    path_match = re.search(r'<path[^>]*d="([^"]+)"', content)
                    if path_match:
                        path_data = path_match.group(1)
                        self.path_data_var.set(path_data)
                        self.load_path_data()
                    else:
                        raise ValueError("No valid path data found in SVG file")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load SVG: {str(e)}")
                
    def show_status(self, message: str, color: str = "green") -> None:
        """Display temporary status message."""
        status_label = ttk.Label(self.root, text=message, foreground=color)
        status_label.place(relx=0.5, rely=0.9, anchor="center")
        self.root.after(2000, status_label.destroy)
        
    def toggle_animation(self) -> None:
        """Start/stop text animation."""
        self.is_animating = not self.is_animating
        if self.is_animating:
            self.animate_text()
            
    def animate_text(self) -> None:
        """Animate text along path."""
        if not self.is_animating:
            return
            
        self.canvas.delete("text_preview")
        text = self.text_var.get()
        if not text:
            self.root.after(int(self.animation_speed * 1000), self.animate_text)
            return
            
        try:
            font_size = int(self.font_size_var.get())
            letter_spacing = self.letter_spacing_var.get()
            duration = float(self.duration_var.get())
        except ValueError:
            self.root.after(int(self.animation_speed * 1000), self.animate_text)
            return
            
        path_points = self.sample_path_points(200)
        if not path_points:
            self.root.after(int(self.animation_speed * 1000), self.animate_text)
            return
            
        current_time = time.time()
        progress = (current_time % duration) / duration
        start_offset = int(len(path_points) * (1 - progress))
        char_width = font_size * 0.6
        
        current_pos = start_offset
        for char in text:
            if current_pos >= len(path_points) or current_pos < 0:
                continue
            x, y = path_points[current_pos]
            self.canvas.create_text(x, y, 
                                 text=char, 
                                 fill=self.text_color_var.get(), 
                                 font=("Arial", font_size), 
                                 angle=0, 
                                 anchor="center", 
                                 tags="text_preview")
            current_pos += int(char_width) + letter_spacing
        
        self.root.after(int(self.animation_speed * 1000), self.animate_text)

def main() -> None:
    """Launch the application."""
    root = tk.Tk()
    app = SVGPathBuilder(root)
    root.mainloop()

if __name__ == "__main__":
    main()
