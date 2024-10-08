import tkinter as tk
from tkinter import ttk, messagebox
import tkintermapview
from shapely.geometry import Polygon, Point ,LineString
import math
import pygame
from PIL import Image, ImageTk
import pandas as pd
import pyperclip  # To handle clipboard operations
from datetime import datetime 
import os
import io
import sys
from tkinter import filedialog 
from PIL import ImageGrab, ImageTk, Image
from tkinter import filedialog, messagebox, simpledialog
from databased import save_image, get_user_images, get_image_data
# from logind import current_user


pygame.mixer.init()

# Load audio files
sound_safe_zone = pygame.mixer.Sound('safe_zone.mp3')
sound_danger_zone = pygame.mixer.Sound('danger_zone.mp3')
# sound_destination = pygame.mixer.Sound('Destination.mp3')
global logged_in_user
#logged_in_user=current_user


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
last_direction = None 
direction_popup = None 
last_status = None
last_zones = set()  
airplane_marker = None
airplane_markers = []
previous_marker = []
path_markers = []
danger_zones = []



# Function to load danger zones from Excel file with validation
def load_danger_zones(file):
    global danger_zones
    df = pd.read_excel(file)
    
    for index, row in df.iterrows():  #itterates through each row 
        nation = row['Nation'] # fetches the value
        coords = []
        i = 1
        
        while True:
            lat_key = f'Lat{i}'
            lon_key = f'Lon{i}'
            if lat_key in row and lon_key in row:
                lat = row[lat_key]
                lon = row[lon_key]

                if pd.isna(lat) or pd.isna(lon):  # Stop if either lat or lon is empty
                    break
                coords.append((lat, lon))
                i += 1
            else:
                break
        
        # Check if the number of coordinates is valid
        if len(coords) < 3 or len(coords) > 16:
            # Show pop-up message
            error_popup = tk.Tk()
            error_popup.title("Error")
            tk.Label(error_popup, text="Error: Count of Lat lon pair must be min 3 and max 16!", font=("Arial", 14),fg='red').pack(pady=20, padx=20)
            tk.Button(error_popup, text="Exit", command=sys.exit).pack(pady=10)
            error_popup.mainloop()
            return [] 

        danger_zones.append((nation, coords))
    print(danger_zones)
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
       
def write_date(filename="latlon.txt"):
    global today_date 
    today_date = datetime.now().strftime("%Y-%m-%d")
    desktop_path = os.path.join("C:\\Users\BANUPRAKASH G\\Desktop\\plane", filename)
    with open(desktop_path, 'a') as file:
        file.write("\n_______\n") 
        file.write("Date : " +today_date)
        file.write("\n_______\n")  

    
def write_safelatlon_to_file(coords, filename='latlon.txt'):
    desktop_path = os.path.join("C:\\Users\BANUPRAKASH G\\Desktop\\plane", filename)
    with open(desktop_path, 'a') as file:  
        for coord in coords:
            file.write(f"\n Safe zone : {coord[0]} {coord[1]}") 
    

def write_dangerlatlon_to_file(coords, filename='latlon.txt'):
    desktop_path = os.path.join("C:\\Users\BANUPRAKASH G\\Desktop\\plane", filename)
    with open(desktop_path, 'a') as file:  
        for coord in coords:
            file.write(f"\n Danger zone : {coord[0]} {coord[1]}")
    

# Create the initial input window
def show_input_window():
    def close_input_window():
        input_window.destroy()
        show_map_window()
    
    input_window = tk.Toplevel()
    #input_window=tk.Tk()
    # Heading
    heading = tk.Label(input_window, text="Aerosafe Navigator", font=("Book Antiqua", 25, "bold"), fg="midnight blue")
    heading1 = tk.Label(input_window, text="An Interactive Geospatial Path Simulation with Danger Zone Detection", font=("Book Antiqua", 15), fg="midnight blue")
    heading.pack(pady=15)
    heading1.pack(pady=15)

    img = Image.open("plane.png")  
    img = img.resize((800, 600))  
    photo = ImageTk.PhotoImage(img)
    image_label = tk.Label(input_window, image=photo)
    image_label.photo = photo
    image_label.pack(pady=10)

    input_window.title("Version 1.0")

    # Close the input window after 4 seconds and show the map window
    input_window.after(4000, close_input_window)
    input_window.mainloop()
    
# Show the main map window
def show_map_window():
    global danger_zones
    global path_coords, selected_speed, is_moving, update_interval, paused, direction_popup
    global factor, step, red_path, last_status, status_popup
    write_date()
    danger_zones = load_danger_zones('zone.xlsx')

    # Create tkinter window
    root_tk = tk.Toplevel()
    #root_tk=tk.Tk()
    root_tk.geometry(f"{1000}x{700}")
    root_tk.title("Version 1.0")
    root_tk.clipboard_clear()
   
   # Load the airplane image (adjust the path to your image file)
    airplane_image = tk.PhotoImage(file="plane.png")  
    airplane_marker = None
    
    # Create map widget
    map_widget = tkintermapview.TkinterMapView(root_tk, width=1000, height=700, corner_radius=0)
    map_widget.pack(fill="both", expand=True)
    
    def polygon_click(polygon):
        print(f"polygon clicked - text: {polygon.name}")

    # Set marker for Karnataka
    map_widget.set_zoom(7)

    # Define and draw danger zones with labels
    for idx, (nation, coords) in enumerate(danger_zones, start=1):
        polygon = map_widget.set_polygon(coords, outline_color="red", fill_color="red")
        
        # Calculate the centroid of the polygon to place the text
        polygon_shape = Polygon([(lon, lat) for lat, lon in coords])
        centroid = polygon_shape.centroid
        centroid_lat, centroid_lon = centroid.y, centroid.x
        
        # Set a marker with the zone label at the centroid
        map_widget.set_marker(centroid_lat, centroid_lon, text=f"Zone {idx}")


    # Define and draw danger zones
    for nation, coords in danger_zones:
        map_widget.set_polygon(coords, outline_color="red", fill_color="red")

    def browse_file():
        global danger_zones
        file_path = filedialog.askopenfilename(
            initialdir=os.path.expanduser('~/Documents'),
            title="Select XLSX file",
            filetypes=(("Excel files", ".xlsx"), ("All files", ".*"))
        )
        if file_path:
            map_widget.delete_all_marker()
            danger_zones.clear()  
            danger_zones = load_danger_zones(file_path)
            draw_danger_zones_on_map(danger_zones)
            for idx, (nation, coords) in enumerate(danger_zones, start=1):
                polygon = map_widget.set_polygon(coords, outline_color="red", fill_color="red")
        
                # Calculate the centroid of the polygon to place the text
                polygon_shape = Polygon([(lon, lat) for lat, lon in coords])
                centroid = polygon_shape.centroid
                centroid_lat, centroid_lon = centroid.y, centroid.x
                
                # Set a marker with the zone label at the centroid
                map_widget.set_marker(centroid_lat, centroid_lon, text=f"Zone {idx}")

    def draw_danger_zones_on_map(danger_zones):
        map_widget.delete_all_polygon()
        for nation, coords in danger_zones:
            map_widget.set_polygon(coords, outline_color="red", fill_color="red")

    # Convert danger zones to polygons for Shapely
    danger_polygons = [Polygon([(lon, lat) for lat, lon in coords]) for _, coords in danger_zones]
    
    # Function to check if point is inside any danger zone or impact zone
    def check_location(lat, lon):
        point = Point(lon, lat)
        is_inside_danger = any(point.within(poly) for poly in danger_polygons)
        return is_inside_danger
    
    def check_nearby_danger(lat, lon, segment_start, segment_end):
        point = Point(lon, lat)  # Note the order: (longitude, latitude)
        print(type(point))
        for poly in danger_polygons:
            print(type(poly[1]))
            if point.distance(poly[1]) < 20:  # Adjust threshold as necessary
                zone_center = poly[1].centroid
                side = calculate_side_of_point(
                    (segment_start[0], segment_start[1]),  # Convert to (latitude, longitude)
                    (segment_end[0], segment_end[1]),      # Convert to (latitude, longitude)
                    (zone_center.y, zone_center.x)          # Convert to (latitude, longitude)
                )
                return side
        return None
    
    # Function to create a path with multiple points
    def create_path(coords):
        return coords
       
    # Function to draw path on the map
    def draw_path(path_coords):
        map_widget.set_path(path_coords, color="blue")
    
    # Function to handle map clicks
    def on_map_click(lat, lon):
        global path_coords
        path_coords.append((lat, lon))
        map_widget.set_marker(lat, lon, text=f"Marker {len(path_coords)}")
        draw_path(path_coords)
        
    print("zones",danger_zones)    
    danger_polygons = [(nation, Polygon([(lon, lat) for lat, lon in coords])) for nation, coords in danger_zones]
    print("poly",danger_polygons)

    def check_overlapping_zones(lat, lon):
        danger_polygons = [(nation, Polygon([(lon, lat) for lat, lon in coords])) for nation, coords in danger_zones]
        point = Point(lon, lat)
        overlapping_zones = [nation for nation, poly in danger_polygons if point.within(poly)]
        print("1",overlapping_zones)
        return overlapping_zones        
    
    def rotate_image(image, angle):
        """Rotate the image to a given angle."""
        return image.rotate(angle, expand=True)    
        
    def move_line():
      
        global path_coords, selected_speed, is_moving, update_interval, paused
        global factor, step, red_path, last_status, status_popup, last_direction, direction_popup, airplane_marker 

        filename = 'latlon.txt'
        desktop_path = os.path.join("C:\\Users\BANUPRAKASH G\\Desktop\\plane", filename)

        if not path_coords or len(path_coords) < 2:
            print("Not enough path coordinates.")
            return

        def interpolate(start, end, factor):
            return start + factor * (end - start)

        def interpolate_point(p1, p2, factor):
            return (interpolate(p1[0], p2[0], factor), interpolate(p1[1], p2[1], factor))
        
        def update_line():
            global factor, step, red_path, last_status, status_popup, last_direction, direction_popup, airplane_marker ,last_zones
            global previous_marker

            start_point = path_coords[step]
            end_point = path_coords[step + 1]
            intermediate_point = interpolate_point(start_point, end_point, factor)
            red_path.append(intermediate_point)
            
            delta_x = end_point[1] - start_point[1]  # Change in longitude
            delta_y = end_point[0] - start_point[0]  # Change in latitude

            # Calculate the angle in radians and then convert to degrees
            angle1 = math.degrees(math.atan2(delta_y, delta_x))

            # Adjusting the angle to ensure it points in the correct direction
            angle = (angle1 + 360) % 360
            
            # angle = math.degrees(math.atan2(end_point[1] - start_point[1], end_point[0] - start_point[0]))

            # Rotate the airplane image to point in the direction of travel
            airplane_img = Image.open("plane_icon.png")
            resized_airplane_img = airplane_img.resize((60, 60), Image.LANCZOS)
            rotated_airplane_img = rotate_image(resized_airplane_img, angle)
            airplane_photo = ImageTk.PhotoImage(rotated_airplane_img)
            
            # Draw the red path
            if len(red_path) > 1:
                try:
                    map_widget.set_path(red_path, color="red")
                except Exception as e:
                    print(f"Error drawing path: {e}")

            
            if len(red_path) == 1:  # Create the airplane marker at the start
                marker = map_widget.set_marker(intermediate_point[0], intermediate_point[1], icon=airplane_photo)
                airplane_markers.append(marker)
            else:
                print(airplane_markers)
                if airplane_markers:  # Check if the list is not empty
                    previous_marker = airplane_markers[-1]
                else:
                    print("No previous marker available. Cannot update line.")
                    return 
                # previous_marker = airplane_markers[-1]
                previous_marker.set_position(-999, -999)  # Move it off-screen
                # Create a new marker for the airplane at the new position
                marker = map_widget.set_marker(intermediate_point[0], intermediate_point[1], icon=airplane_photo)
                airplane_markers.append(marker)

                # Optionally remove the previous marker from the list
                airplane_markers.pop(-2)
            
               
            # Check zone status
            overlapping_zones = check_overlapping_zones(intermediate_point[0], intermediate_point[1])
            print(overlapping_zones)
            nearby_danger_side = check_nearby_danger(intermediate_point[0], intermediate_point[1], start_point, end_point)
            
            if overlapping_zones:
                    if last_status != "Impact Zone" or set(overlapping_zones) != last_zones:
                        status = f"You have entered the danger zones of {', '.join(overlapping_zones)}!"
                        if status_popup:
                            status_popup.destroy()
                        status_popup = tk.Toplevel(root_tk)
                        status_popup.title("Zone Status")
                        tk.Label(status_popup, text=status, font=("Arial", 14)).pack(pady=20, padx=20)
                        root_tk.after(3000, status_popup.destroy)
                        sound_danger_zone.play()
                        last_status = "Impact Zone"
                        last_zones = set(overlapping_zones)  # Update last zones
                    write_dangerlatlon_to_file([intermediate_point])
                    
            elif nearby_danger_side:
                status = f"Danger Zone on the {nearby_danger_side} side!"
                if last_status != status:
                    if status_popup:
                        status_popup.destroy()
                    status_popup = tk.Toplevel(root_tk)
                    status_popup.title("Zone Status")
                    tk.Label(status_popup, text=status, font=("Arial", 14)).pack(pady=20, padx=20)
                    root_tk.after(5000, status_popup.destroy)
                    last_status = status
                    # sound_danger_zone.play()
            else:
                status = "You are Safe now"
                if last_status != "Safe Zone":
                    if status_popup:
                        status_popup.destroy()
                    status_popup = tk.Toplevel(root_tk)
                    status_popup.title("Zone Status")
                    tk.Label(status_popup, text=status, font=("Arial", 14)).pack(pady=20, padx=20)
                    root_tk.after(3000, status_popup.destroy)
                    sound_safe_zone.play()
                    last_status = "Safe Zone"
                    last_zones = set()
                write_safelatlon_to_file([intermediate_point])

            # Calculate direction
            # direction_angle = math.degrees(math.atan2(end_point[0] - start_point[0], end_point[1] - start_point[1]))
            # if last_direction != direction_angle:
            #     if direction_popup:
            #         direction_popup.destroy()
            #     direction_popup = tk.Toplevel(root_tk)
            #     direction_popup.title("Flight Direction")
            #     tk.Label(direction_popup, text=f"Current Direction: {direction_angle:.2f}°", font=("Arial", 14)).pack(pady=20, padx=20)
            #     last_direction = direction_angle

        
            factor += 0.01
            if factor >= 1:
                factor = 0
                step += 1

            if step < len(path_coords) - 1 and not paused:
                
                root_tk.after(update_interval, update_line)
            elif step >= len(path_coords) - 1:
                sound_destination.play()
                with open(desktop_path,'a') as file:
                    file.write(f"\n------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n")

        # Reset and start simulation
        if not is_moving:
            is_moving = True
            factor = factor if not paused else 0
            red_path = red_path if not paused else []
            print("Starting simulation...")

            # Adjust update interval based on speed
            update_interval = int(50000 / selected_speed) 
            update_line()
        else:
            print("Simulation is already running.")

    
    def clear_path():
        global path_coords, is_moving, factor, step, red_path, last_status, airplane_marker
        airplane_marker=None
        if not path_coords:
            messagebox.showwarning("Warning","Please Draw Path First")
        # Clear the list of path coordinates
        path_coords.clear()
        
        # Reset simulation control variables
        is_moving = False
        factor = 0
        step = 0
        red_path = []
        last_status = None
        
        if airplane_marker:
            map_widget.delete(airplane_marker)
            airplane_marker = None
    # Remove only the markers related to the path (not the zone labels)
        for marker in airplane_markers:
            map_widget.delete(marker)
            
        for marker in path_markers:
            map_widget.delete(marker)

        airplane_markers.clear()  # Clear the list of airplane markers
        # Remove the path from the map without deleting other markers or polygons
        map_widget.delete_all_path()
        
        # Remove the airplane marker if it exists
        # if airplane_marker:
        #     map_widget.delete(airplane_marker)
        #     airplane_marker = None
        
        # # Clear the map
        # map_widget.delete_all_marker()  
        # map_widget.delete_all_path()
    def undo_path():
        global path_coords, airplane_markers, airplane_marker
        
        # Check and clear airplane markers from the map first
        if airplane_markers:
            for marker in airplane_markers:
                map_widget.delete(marker)  # Remove each marker from the map
            airplane_markers.clear()  # Clear the list after deleting markers
        
        if len(path_coords) > 0:
            path_coords.pop()  # Remove the last coordinate from the path
            # Remove airplane_marker from the map if it exists
            if airplane_marker:
                map_widget.delete(airplane_marker)
                airplane_marker = None
            
            # Delete all previous path markers
            for marker in path_markers:
                map_widget.delete(marker)
            map_widget.delete_all_path()  # Remove all paths
            
            # Redraw remaining markers and path
            path_markers.clear()  # Clear the list to redraw new markers
            for idx, (lat, lon) in enumerate(path_coords):
                a = map_widget.set_marker(lat, lon, text=f"Marker {idx + 1}")  # Add marker
                path_markers.append(a)  # Append to path_markers

            # Redraw the path if there are at least two points left
            if len(path_coords) > 1:
                draw_path(path_coords)

            print(f"Path markers: {path_markers}")
            print(f"Airplane markers: {airplane_markers}")
        else:
            messagebox.showwarning("Warning","No Markers to Undo")
            
            # If no coordinates, clear the path markers as well
            for marker in path_markers:
                map_widget.delete(marker)
            path_markers.clear()  # Clear the path markers list
        
        print("Undo completed.")
        

    def on_load_lat_lon_button_click():
        global path_coords
        # Use clipboard content for coordinates
        clipboard_content = pyperclip.paste().strip()  # Clean any extra spaces or new lines and pasteis to copy the content of clipboard
        #print(clipboard_content)
        if clipboard_content == "":
            messagebox.showwarning("Warning","Clipboard Content is Empty")
        else:
            try:
                # Expecting coordinates in the format "lat lon"
                lat, lon = map(float, clipboard_content.split()) # clipboard content is split based on space or new line and it is stored inside lat lon 
                path_coords.append((lat, lon))
                s = map_widget.set_marker(lat, lon, text=f"Marker {len(path_coords)}")
                path_markers.append(s)
                draw_path(path_coords)
                
                # Clear the clipboard content after loading
                pyperclip.copy("")
            except ValueError:
                print("Clipboard content is not in the correct format.")

    def start_simulation():
        global airplane_markers
        
        global paused
        if not is_moving and path_coords:
            paused = False
            print("Starting simulation...")
            move_line()
        elif is_moving:
            print(is_moving, path_coords)
            print("Cannot start simulation: Already running or no path coordinates.")
        else:
            messagebox.showwarning("Warning","Please Draw Path First")

    def stop_simulation():
        global is_moving, paused,previous_marker
        print(airplane_markers)
        if airplane_markers:
            previous_marker = airplane_markers.copy() 
            print("copy")
        # airplane_markers.clear()
        if is_moving:
            print("Stopping simulation...")
            paused = True  # Ensure paused is reset
            is_moving = False
            print("Simulation stopped.")
        else:
             messagebox.showwarning("Warning","Start Simulation First")

   
    def save_screenshot(): 
        # from logind import current_user
        # print(current_user)
        import commond
        logged_in_user= commond.get_current_user()
        print(logged_in_user)
        if path_markers == []:
            messagebox.showwarning("Warning", "No Path Found")
        else:
            try:
                # Get the window coordinates
                x = root_tk.winfo_rootx()
                y = root_tk.winfo_rooty()
                width = x + root_tk.winfo_width()
                height = y + root_tk.winfo_height()
                
                # Take screenshot
                screenshot = ImageGrab.grab(bbox=(x, y, width, height))

                # Ask user for a name to save the file
                file_name = simpledialog.askstring("Input", "Enter a name for the screenshot:", parent=root_tk)
                
                if file_name:
                    # Convert the screenshot to binary data for storage
                    image_data = io.BytesIO()
                    screenshot.save(image_data, format='PNG')
                    image_data = image_data.getvalue()  # Get the binary data

                    # Save the screenshot in the database with the logged-in user's username
                    save_image(logged_in_user, file_name, image_data)
                    messagebox.showinfo("Success", "Screenshot saved successfully!")

                else:
                    messagebox.showwarning("Cancelled", "No name provided. Save operation cancelled.")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save screenshot: {e}")
    def display_images_window():
        # from logind import current_user
        # print(current_user)
        import commond
        logged_in_user= commond.get_current_user()
        print(logged_in_user)
        # Create a new window to display the list of saved images
        retrieve_window = tk.Toplevel()
        retrieve_window.title("Saved Images")

        # Fetch the list of images saved by the logged-in user
        images = get_user_images(logged_in_user)

        if images:
            listbox = tk.Listbox(retrieve_window)
            listbox.pack(fill=tk.BOTH, expand=True)

            for image_name in images:
                listbox.insert(tk.END, image_name)

            def on_image_select(event):
                selected_image_name = listbox.get(listbox.curselection())
                display_image(selected_image_name)

            listbox.bind('<<ListboxSelect>>', on_image_select)
        else:
            tk.Label(retrieve_window, text="No images saved.").pack()

    def display_image(image_name):
        # from logind import current_user
        import commond
        logged_in_user= commond.get_current_user()
        print(logged_in_user)
        try:
            image_data = get_image_data(logged_in_user, image_name)

            if image_data:
                image = Image.open(io.BytesIO(image_data))
                image.show()  # This opens the image in the default image viewer
            else:
                messagebox.showerror("Error", "Image not found.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve image: {e}")

    # Buttons
    
    button_frame = tk.Frame(root_tk)
    button_frame.pack(fill='x', side='bottom')

    move_button = tk.Button(button_frame, text="       Start       ", command=start_simulation,font=15,bg='lightblue',fg='black')
    move_button.pack(side='left', padx=5, pady=5)
    
    stop_button = tk.Button(button_frame, text="       Stop       ", command=stop_simulation,font=15,bg='lightblue',fg='black')
    stop_button.pack(side='left', padx=5, pady=5)
    
    clear_button = tk.Button(button_frame, text="      Clear Path     ", command=clear_path,font=15,bg='lightblue',fg='black')
    clear_button.pack(side='left', padx=5, pady=5)

    undo_button = tk.Button(button_frame, text="      Undo Path     ", command=undo_path,font=15,bg='lightblue',fg='black')
    undo_button.pack(side='left', padx=5, pady=5)

    load_lat_lon_button = tk.Button(button_frame, text="      Load Lat Lon       ", command=on_load_lat_lon_button_click,font=15,bg='lightblue',fg='black')
    load_lat_lon_button.pack(side='left', padx=5, pady=5)

    browse_button = tk.Button(button_frame, text="        Browse file         ", command=browse_file,font=15,bg='lightblue',fg='black')
    browse_button.pack(side='left', padx=5, pady=5)

    save_button = tk.Button(button_frame, text="        Save         ", command=save_screenshot,font=15,bg='lightblue',fg='black')
    save_button.pack(side='left', padx=5, pady=5)

    retrieve_button = tk.Button(button_frame, text="        Retrieve         ", command=display_images_window,font=15,bg='lightblue',fg='black')
    retrieve_button.pack(side='left', padx=5, pady=5)


     # Speed selection dropdown
    speed_label = tk.Label(root_tk, text="Select Speed:",font=10)
    speed_label.pack(side='left', padx=5, pady=5)

    speed_options = [50,100,150,200,250,300,350,400,450,500,550,600,650,700,750,800,850,900,950,1000,1050,1100,1150,1200,1250,1300,1350,1400,1450,1500,1550,1600,1650,1700,1750,1800,1850,1900,1950,2000]
    speed_dropdown = ttk.Combobox(root_tk, values=speed_options)
    speed_dropdown.current(3)  # Set default value
    speed_dropdown.pack(side='left', padx=5, pady=5)

    def on_speed_select(event):
        global selected_speed
        selected_speed = int(speed_dropdown.get())

    speed_dropdown.bind("<<ComboboxSelected>>", on_speed_select) 
    # Bind map click event
    map_widget.bind("<Button-1>", lambda e: on_map_click(map_widget.get_lat(e.x, e.y), map_widget.get_lon(e.x, e.y)))
    

    root_tk.mainloop()
# if __name__ == "_main_":
#     show_input_window()

# Start the application with input window
show_input_window()