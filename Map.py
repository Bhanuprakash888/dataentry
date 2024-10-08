import tkinter as tk
from tkinter import ttk
import tkintermapview
from shapely.geometry import Polygon, Point
import math
import pygame
from PIL import Image, ImageTk
import pandas as pd
import pyperclip  # To handle clipboard operations

# Initialize pygame mixer
pygame.mixer.init()

# Load audio files
sound_safe_zone = pygame.mixer.Sound('safe_zone.mp3')
sound_danger_zone = pygame.mixer.Sound('danger_zone.mp3')

# Define global variables
# Define global variables
path_coords = []
selected_speed = 500
is_moving = False
update_interval = 1000
paused = False
factor = 0
step = 0
red_path = []
last_status = None
status_popup = None
blue_path_id = None  # Add this line


# Function to load danger zones from Excel file
def load_danger_zones(file):
    danger_zones = []
    df = pd.read_excel(file)
    
    for index, row in df.iterrows():
        nation = row['Nation']
        coords = []
        # Iterate through columns containing coordinates
        for i in range(1, len(row), 2):
            try:
                lat = row[f'Lat{i//2+1}']
                lon = row[f'Lon{i//2+1}']
                coords.append((lat, lon))
            except (KeyError, ValueError):
                break
        if len(coords) >= 3:  # Ensure at least 3 points to form a polygon
            danger_zones.append((nation, coords))
    return danger_zones

# Function to calculate if a danger zone is on the right or left side of the path
def calculate_side_of_point(p1, p2, point):
    """
    Determine if a point is to the left or right of the line segment from p1 to p2.
    """
    # Coordinates should be in (latitude, longitude) order
    dx1 = p2[1] - p1[1]
    dy1 = p2[0] - p1[0]
    dx2 = point[1] - p1[1]
    dy2 = point[0] - p1[0]

    cross_product = dx1 * dy2 - dy1 * dx2
    
    if cross_product > 0:
        return "left"
    elif cross_product < 0:
        return "right"
    else:
        return "on the line"

# Create the initial input window
def show_input_window():
    def on_ok_button_click():
        global selected_speed
        selected_speed = int(speed_combobox.get())
        input_window.destroy()
        show_map_window()
    
    input_window = tk.Tk()

    # Heading
    heading = tk.Label(input_window, text="SkyTrace", font=("Book Antiqua", 25, "bold"), fg="midnight blue")
    heading1 = tk.Label(input_window, text="An interactive Geospatial Path Simulation with Danger Zone Detection", font=("Book Antiqua", 15), fg="midnight blue")
    heading.pack(pady=15)
    heading1.pack(pady=15)

    img = Image.open("plane.png")  
    img = img.resize((500, 300))  
    photo = ImageTk.PhotoImage(img)
    image_label = tk.Label(input_window, image=photo)
    image_label.photo = photo  # Reference to avoid garbage collection
    image_label.pack(pady=10)

    input_window.title("Select Speed")

    tk.Label(input_window, text="Select speed (km/hr):", font=("Book Antiqua", 14, "bold")).pack(pady=20)
    speed_combobox = ttk.Combobox(input_window, values=[i for i in range(50, 2050, 50)])
    speed_combobox.pack(pady=10)
    speed_combobox.current(0)
    
    ok_button = tk.Button(input_window, text="OK", command=on_ok_button_click)
    ok_button.pack(pady=10)
    
    input_window.mainloop()

# Show the main map window
def show_map_window():
    global path_coords, selected_speed, is_moving, update_interval, paused
    global factor, step, red_path, last_status, status_popup

    # Load danger zones from the Excel file
    danger_zones = load_danger_zones('zone.xlsx')

    # Create tkinter window
    root_tk = tk.Tk()
    root_tk.geometry(f"{1000}x{700}")
    root_tk.title("Karnataka Map")
    
    # Create map widget
    map_widget = tkintermapview.TkinterMapView(root_tk, width=1000, height=700, corner_radius=0)
    map_widget.pack(fill="both", expand=True)
    
    def polygon_click(polygon):
        print(f"polygon clicked - text: {polygon.name}")

    # Set marker for Karnataka
    map_widget.set_zoom(7)

    # Define and draw danger zones
    for nation, coords in danger_zones:
        map_widget.set_polygon(coords, outline_color="red", fill_color="red")

    # Convert danger zones to polygons for Shapely
    danger_polygons = [Polygon([(lon, lat) for lat, lon in coords]) for _, coords in danger_zones]

    # Function to check if point is inside any danger zone
    def check_location(lat, lon):
        point = Point(lon, lat)  # Note the order: (longitude, latitude)
        is_inside_danger = any(point.within(poly) for poly in danger_polygons)
        return is_inside_danger

    # Function to check if a point is near a danger zone and determine the side of danger zone
    def check_nearby_danger(lat, lon, segment_start, segment_end):
        point = Point(lon, lat)  # Note the order: (longitude, latitude)
        for poly in danger_polygons:
            if point.distance(poly) < 1.0:  # Adjust threshold as necessary
                zone_center = poly.centroid
                side = calculate_side_of_point(
                    (segment_start[0], segment_start[1]),  # Convert to (latitude, longitude)
                    (segment_end[0], segment_end[1]),      # Convert to (latitude, longitude)
                    (zone_center.y, zone_center.x)          # Convert to (latitude, longitude)
                )
                return side
        return None

    # Function to draw path on the map
    # def draw_path(path_coords):
    #     map_widget.set_path(path_coords, color="blue")
        
    def draw_path(path_coords):
        global blue_path_id

        # Clear the blue path by redrawing it
        if blue_path_id is not None:
            # Optionally, you can handle the removal of the blue path if needed.
            pass
        
        # Draw the blue path
        blue_path_id = map_widget.set_path(path_coords, color="blue")



    # Function to handle map clicks
    def on_map_click(lat, lon):
        global path_coords
        path_coords.append((lat, lon))
        map_widget.set_marker(lat, lon, text=f"Point {len(path_coords)}")
        draw_path(path_coords)

    def move_line():
        global path_coords, selected_speed, is_moving, update_interval, paused
        global factor, step, red_path, last_status, status_popup

        if not path_coords or len(path_coords) < 2:
            print("Not enough path coordinates.")
            return

        def interpolate(start, end, factor):
            return start + factor * (end - start)

        def interpolate_point(p1, p2, factor):
            return (interpolate(p1[0], p2[0], factor), interpolate(p1[1], p2[1], factor))

        def update_line():
            global factor, step, red_path, last_status, status_popup

            if step >= len(path_coords) - 1:
                print("Reached end of path.")
                stop_simulation()
                # Show popup message indicating the destination is reached
                status_popup = tk.Toplevel(root_tk)
                status_popup.title("Destination Reached")
                tk.Label(status_popup, text="You have reached your destination!", font=("Arial", 14)).pack(pady=20, padx=20)
                return

            start_point = path_coords[step]
            end_point = path_coords[step + 1]
            intermediate_point = interpolate_point(start_point, end_point, factor)
            red_path.append(intermediate_point)

            # Clear the blue path before drawing the red path
            draw_path(path_coords)

            # Draw the red path
            if len(red_path) > 1:
                try:
                    map_widget.set_path(red_path, color="red")
                except Exception as e:
                    print(f"Error drawing path: {e}")

            # Check zone status
            is_inside_danger = check_location(intermediate_point[0], intermediate_point[1])
            nearby_danger_side = check_nearby_danger(intermediate_point[0], intermediate_point[1], start_point, end_point)

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
            elif nearby_danger_side:
                status = f"Danger Zone on the {nearby_danger_side.capitalize()}!"
                if last_status != status:
                    if status_popup:
                        status_popup.destroy()
                    status_popup = tk.Toplevel(root_tk)
                    status_popup.title("Zone Status")
                    tk.Label(status_popup, text=status, font=("Arial", 14)).pack(pady=20, padx=20)
                    last_status = status
            else:
                status = "Safe Zone"
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
                
                if step >= len(path_coords) - 1:
                    # Show popup message indicating the destination is reached
                    status_popup = tk.Toplevel(root_tk)
                    status_popup.title("Destination Reached")
                    tk.Label(status_popup, text="You have reached your destination!", font=("Arial", 14)).pack(pady=20, padx=20)
                    
                    root_tk.after(5000, status_popup.destroy)
                    stop_simulation()
                    return

            if step < len(path_coords) - 1 and not paused:
                root_tk.after(update_interval, update_line)
            else:
                print("Simulation stopped or paused.")
                stop_simulation()



        # Reset and start simulation
        if not is_moving:
            is_moving = True
            factor = factor if not paused else 0
            red_path = red_path if not paused else []
            print("Starting simulation...")
            update_interval = int(50000 / selected_speed)  # Adjust update interval based on speed
            update_line()
        else:
            print("Simulation is already running.")

    def clear_path():
        global path_coords
        path_coords.clear()  # Clear the list of path coordinates
        map_widget.delete_all_marker()  # Remove all markers from the map
        map_widget.delete_all_path()  # Remove all paths from the map

    def undo_path():
        global path_coords
        if len(path_coords) > 0:
            path_coords.pop()  # Remove the last coordinate from the path
            map_widget.delete_all_marker()  # Remove all markers
            map_widget.delete_all_path()  # Remove all paths
            # Redraw remaining markers and path
            for idx, (lat, lon) in enumerate(path_coords):
                map_widget.set_marker(lat, lon, text=f"Point {idx + 1}")
            if len(path_coords) > 1:
                draw_path(path_coords)  # Redraw the blue path with remaining coordinates
        else:
            print("No more markers to undo.")

    def on_load_lat_lon_button_click():
        global path_coords
        
        # Use clipboard content for coordinates
        clipboard_content = pyperclip.paste().strip()  # Clean any extra spaces or new lines
        try:
            # Expecting coordinates in the format "lat lon"
            lat, lon = map(float, clipboard_content.split())
            path_coords.append((lat, lon))
            map_widget.set_marker(lat, lon, text=f"Marker {len(path_coords)}")
            draw_path(path_coords)
            
            # Clear the clipboard content after loading
            pyperclip.copy("")
        except ValueError:
            print("Clipboard content is not in the correct format.")

    def start_simulation():
        global paused
        if not is_moving and path_coords:
            paused = False
            print("Starting simulation...")
            move_line()
        else:
            print(is_moving, path_coords)
            print("Cannot start simulation: Already running or no path coordinates.")

    def stop_simulation():
        global is_moving, paused
        if is_moving:
            print("Stopping simulation...")
            paused = True  # Ensure paused is reset
            is_moving = False
            print("Simulation stopped.")

    def pause_simulation():
        global paused
        paused = not paused
        if not paused and is_moving:
            move_line()

    def restart_simulation():
        global factor, step, red_path, paused
        factor = 0
        step = 0
        red_path = []
        paused = False
        start_simulation()

    # Buttons
    button_frame = tk.Frame(root_tk)
    button_frame.pack(fill='x', side='bottom')
    
    move_button = tk.Button(button_frame, text="Start Simulation", command=start_simulation)
    move_button.pack(side='left', padx=5, pady=5)
    
    stop_button = tk.Button(button_frame, text="Stop Simulation", command=stop_simulation)
    stop_button.pack(side='left', padx=5, pady=5)
    
    clear_button = tk.Button(button_frame, text="Clear Path", command=clear_path)
    clear_button.pack(side='left', padx=5, pady=5)

    undo_button = tk.Button(button_frame, text="Undo Path", command=undo_path)
    undo_button.pack(side='left', padx=5, pady=5)

    load_lat_lon_button = tk.Button(button_frame, text="Load Lat Lon", command=on_load_lat_lon_button_click)
    load_lat_lon_button.pack(side='left', padx=5, pady=5)
    
    # Bind map click event
    map_widget.bind("<Button-1>", lambda e: on_map_click(map_widget.get_lat(e.x, e.y), map_widget.get_lon(e.x, e.y)))
    
    root_tk.mainloop()

# Start the application with input window
show_input_window()
