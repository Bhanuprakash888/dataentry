import tkinter as tk
from tkinter import ttk
import tkintermapview
from shapely.geometry import Polygon, Point
import math
import pygame
from PIL import Image, ImageTk
import pandas as pd
import pyperclip

# Initialize pygame mixer
pygame.mixer.init()

# Load audio files
sound_safe_zone = pygame.mixer.Sound('safe_zone.mp3')
sound_danger_zone = pygame.mixer.Sound('danger_zone.mp3')

# Function to load danger zones from Excel file
def load_danger_zones(file):
    danger_zones = []
    df = pd.read_excel(file)
    
    for index, row in df.iterrows():
        nation = row['Nation']
        coords = []
        for i in range(1, len(row), 2):
            try:
                lat = row[f'Lat{i//2+1}']
                lon = row[f'Lon{i//2+1}']
                coords.append((lat, lon))
            except (KeyError, ValueError):
                break
        if len(coords) >= 3:
            danger_zones.append((nation, coords))
    return danger_zones

def calculate_total_distance(coords):
    total_distance = 0
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        total_distance += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return total_distance

def show_input_window():
    def on_ok_button_click():
        global selected_speed
        selected_speed = int(speed_combobox.get())
        input_window.destroy()
        show_map_window()
    
    input_window = tk.Tk()

    heading = tk.Label(input_window, text="SkyTrace", font=("Book Antiqua", 25, "bold"), fg="midnight blue")
    heading1 = tk.Label(input_window, text="An interactive Geospatial Path Simulation with Danger Zone Detection", font=("Book Antiqua", 15), fg="midnight blue")
    heading.pack(pady=15)
    heading1.pack(pady=15)

    img = Image.open("plane.png")  
    img = img.resize((500, 300))  
    photo = ImageTk.PhotoImage(img)
    image_label = tk.Label(input_window, image=photo)
    image_label.photo = photo
    image_label.pack(pady=10)

    input_window.title("Select Speed")

    tk.Label(input_window, text="Select speed (km/hr):", font=("Book Antiqua", 14, "bold")).pack(pady=20)
    speed_combobox = ttk.Combobox(input_window, values=[i for i in range(50, 2050, 50)])
    speed_combobox.pack(pady=10)
    speed_combobox.current(0)
    
    ok_button = tk.Button(input_window, text="OK", command=on_ok_button_click)
    ok_button.pack(pady=10)
    
    input_window.mainloop()

def show_map_window():
    global path_coords, selected_speed, is_moving, update_interval
    global is_paused, paused_step, paused_factor

    path_coords = []
    is_moving = False
    is_paused = False
    paused_step = 0
    paused_factor = 0

    danger_zones = load_danger_zones('zone.xlsx')

    root_tk = tk.Tk()
    root_tk.geometry(f"{1000}x{700}")
    root_tk.title("Karnataka Map")
    
    map_widget = tkintermapview.TkinterMapView(root_tk, width=1000, height=700, corner_radius=0)
    map_widget.pack(fill="both", expand=True)
    
    def polygon_click(polygon):
        print(f"polygon clicked - text: {polygon.name}")

    map_widget.set_zoom(7)
    
    for nation, coords in danger_zones:
        map_widget.set_polygon(coords, outline_color="red", fill_color="red")

    danger_polygons = [Polygon([(lon, lat) for lat, lon in coords]) for _, coords in danger_zones]

    def check_location(lat, lon):
        point = Point(lon, lat)
        is_inside_danger = any(point.within(poly) for poly in danger_polygons)
        return is_inside_danger

    def create_path(coords):
        return coords
    
    def draw_path(path_coords):
        map_widget.set_path(path_coords, color="blue")
    
    def on_map_click(lat, lon):
        global path_coords
        path_coords.append((lat, lon))
        map_widget.set_marker(lat, lon, text=f"Point {len(path_coords)}")
        draw_path(path_coords)
    
    def move_line():
        global path_coords, selected_speed, is_moving, update_interval
        global is_paused, paused_step, paused_factor

        if not path_coords or len(path_coords) < 2:
            print("Not enough path coordinates.")
            return

        def interpolate(start, end, factor):
            return start + factor * (end - start)
        
        def interpolate_point(p1, p2, factor):
            return (interpolate(p1[0], p2[0], factor), interpolate(p1[1], p2[1], factor))

        red_path = [path_coords[0]]
        step = paused_step if is_paused else 0
        factor = paused_factor if is_paused else 0
        last_status = None
        status_popup = None

        def update_line():
            nonlocal factor, step, red_path, last_status, status_popup
            if step >= len(path_coords) - 1:
                print("Reached end of path.")
                return
            
            start_point = path_coords[step]
            end_point = path_coords[step + 1]
            intermediate_point = interpolate_point(start_point, end_point, factor)
            red_path.append(intermediate_point)
            
            if len(red_path) > 1:
                try:
                    map_widget.set_path(red_path, color="red")
                except Exception as e:
                    print(f"Error drawing path: {e}")

            is_inside_danger = check_location(intermediate_point[0], intermediate_point[1])
            if is_inside_danger:
                status = "You have entered the Danger Zone!"
                if last_status != "Impact Zone":
                    if status_popup:
                        status_popup.destroy()
                    status_popup = tk.Toplevel(root_tk)
                    status_popup.title("Zone Status")
                    tk.Label(status_popup, text=status, font=("Arial", 14)).pack(pady=20, padx=20)
                    sound_danger_zone.play()
                    last_status = "Impact Zone"
            else:
                status = "You are Safe now"
                if last_status != "Safe Zone":
                    if status_popup:
                        status_popup.destroy()
                    status_popup = tk.Toplevel(root_tk)
                    status_popup.title("Zone Status")
                    tk.Label(status_popup, text=status, font=("Arial", 14)).pack(pady=20, padx=20)
                    sound_safe_zone.play()
                    last_status = "Safe Zone"

            factor += 0.01
            if factor >= 1:
                factor = 0
                step += 1

            if step < len(path_coords) - 1:
                if not is_paused:
                    root_tk.after(update_interval, update_line)
                else:
                    # Save the current state when paused
                    paused_step = step
                    paused_factor = factor

        selected_speed = 500
        update_interval = int(50000 / selected_speed)
        
        if not is_moving:
            is_moving = True
            update_line()
            
    def clear_path():
        global path_coords
        path_coords.clear()
        map_widget.delete_all_marker()
        map_widget.delete_all_path()

    def undo_path():
        global path_coords
        if len(path_coords) > 0:
            path_coords.pop()
            map_widget.delete_all_marker()
            map_widget.delete_all_path()
            for idx, (lat, lon) in enumerate(path_coords):
                map_widget.set_marker(lat, lon, text=f"Point {idx + 1}")
            if len(path_coords) > 1:
                draw_path(path_coords)
        else:
            print("No more markers to undo.")

    def on_load_lat_lon_button_click():
        global path_coords
        
        clipboard_content = pyperclip.paste().strip()
        try:
            lat, lon = map(float, clipboard_content.split())
            path_coords.append((lat, lon))
            map_widget.set_marker(lat, lon, text=f"Marker {len(path_coords)}")
            draw_path(path_coords)
            
            pyperclip.copy("")
        except ValueError:
            print("Clipboard content is not in the correct format.")

    def pause_path():
        global is_paused
        if is_moving and not is_paused:
            is_paused = True

    def resume_path():
        global is_paused
        if is_paused:
            is_paused = False
            move_line()
            
    button_frame = tk.Frame(root_tk)
    button_frame.pack(fill='x', side='bottom')
    
    move_button = tk.Button(button_frame, text="Move", command=move_line)
    move_button.pack(side='left', padx=5, pady=5)
    
    clear_button = tk.Button(button_frame, text="Clear Path", command=clear_path)
    clear_button.pack(side='left', padx=5, pady=5)

    undo_button = tk.Button(button_frame, text="Undo Path", command=undo_path)
    undo_button.pack(side='left', padx=5, pady=5)

    load_lat_lon_button = tk.Button(button_frame, text="Load Lat Lon", command=on_load_lat_lon_button_click)
    load_lat_lon_button.pack(side='left', padx=5, pady=5)

    pause_button = tk.Button(button_frame, text="Pause", command=pause_path)
    pause_button.pack(side='left', padx=5, pady=5)

    resume_button = tk.Button(button_frame, text="Resume", command=resume_path)
    resume_button.pack(side='left', padx=5, pady=5)
    
    map_widget.bind("<Button-1>", lambda e: on_map_click(map_widget.get_lat(e.x, e.y), map_widget.get_lon(e.x, e.y)))
    
    root_tk.mainloop()

show_input_window()
