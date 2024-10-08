import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Path to the database file
db_path = os.path.abspath('bel.db')

# Set up the database connection
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Initialize last_power and last_pixel dictionaries to store values per table
last_power = {}
last_pixel = {}

# Function to initialize the database
def initialize_database():
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS entries (
    #     power TEXT,
    #     pixel INTEGER UNIQUE
    # )
    # ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS main_table (
        table_number INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT,
        power TEXT,
        pixel INTEGER
    )
    ''')
    conn.commit()

# Function to retrieve the last stored power range and pixel value from the database
def get_last_power_and_pixel():
    current_table = table_listbox.get(table_listbox.curselection())
    global last_power, last_pixel
    cursor.execute(f"SELECT power, pixel FROM {current_table} ORDER BY rowid DESC LIMIT 1")
    last_entry = cursor.fetchone()
    if last_entry:
        power, last_pixel[current_table] = last_entry
        last_power[current_table] = int(power.split('-')[-1])
    else:
        last_power[current_table] = 0
        last_pixel[current_table] = 55

db_attached = False

# Function to set the current table
def set_current_table(table_name):
    global current_table, db_attached
    current_table = table_name
    if not db_attached:
        cursor.execute(f"ATTACH DATABASE '{db_path}' AS {current_table}")
        db_attached = True
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {current_table} (power TEXT, pixel INTEGER UNIQUE)")
    cursor.execute(f"PRAGMA foreign_keys=ON")
    conn.commit()
    get_last_power_and_pixel()

# Set the initial table
# current_table = 'entries'
# set_current_table(current_table)

# Function to add entry to the database with power stored as a range

def add_entry():
    current_table = table_listbox.get(table_listbox.curselection())
    global last_power, last_pixel
    power_value = int(power_scrollbar.get()) 
    pixel_value = int(pixel_scrollbar.get())

    if power_value <= last_power.get(current_table, 0):
        messagebox.showerror("Error", f"Power value must be greater than {last_power.get(current_table, 0)}.")
        return

    if pixel_value >= last_pixel.get(current_table, 55):
        messagebox.showerror("Error", f"Pixel value must be lesser than {last_pixel.get(current_table, 55)}.")
        return

    power = f"{last_power.get(current_table, 0) + 1}-{power_value}"

    try:
        cursor.execute(f"INSERT INTO {current_table} (power, pixel) VALUES (?, ?)", (power, pixel_value))
        # Also insert into the main_table
        cursor.execute("INSERT INTO main_table (table_name, power, pixel) VALUES (?, ?, ?)", 
                       (current_table, power, pixel_value))
        conn.commit()
        last_power[current_table] = power_value
        last_pixel[current_table] = pixel_value
        messagebox.showinfo("Success", f"Entry added to {current_table}: Power = {power}, Pixel = {pixel_value}")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", f"Pixel value {pixel_value} already exists. Please choose a different value.")

# Function to delete a specific pixel and all previous entries (pop operation)
def delete_from_pixel():
    current_table = table_listbox.get(table_listbox.curselection())
    print(current_table)
    pixel_value = simpledialog.askinteger("Delete Entries", "Enter the pixel value to delete from:")
    if pixel_value is None:
        return

    cursor.execute(f"SELECT rowid FROM {current_table} WHERE pixel <= ? ORDER BY pixel DESC", (pixel_value,))
    rows_to_delete = cursor.fetchall()

    if rows_to_delete:
        cursor.execute(f"DELETE FROM {current_table} WHERE pixel <= ?", (pixel_value,))
        cursor.execute(f"DELETE FROM main_table WHERE table_name = ? AND pixel <= ?", (current_table, pixel_value))
        conn.commit()
        messagebox.showinfo("Success", f"Deleted all entries with pixel value {pixel_value} and below.from {current_table}")
        
        # Update last_power and last_pixel based on the remaining entries
        get_last_power_and_pixel()
    else:
        messagebox.showerror("Error", f"No entries found with pixel value {pixel_value} or below.")

# Function to retrieve and display entries in a table
def retrieve_entry():
    # current_table = table_listbox.get(table_listbox.curselection())
    # Create a style for the Treeview and heading
    style = ttk.Style()
    
    # Configure the Treeview style with a larger font
    style.configure("Custom.Treeview", font=("Helvetica", 12))  # Change '12' to the desired font size
    style.configure("Custom.Treeview.Heading", font=("Helvetica", 14, "bold"))  # For the heading, set a larger and bold font
    
    # Clear the table sub-frame before adding the new table
    for widget in table_frame_right.winfo_children():
        widget.destroy()

    # Retrieve from the main_table for grouped display
    cursor.execute("SELECT DISTINCT table_name FROM main_table")
    distinct_tables = cursor.fetchall()

    # Clear the Listbox
    table_listbox.delete(0, tk.END)

    if distinct_tables:
        for table in distinct_tables:
            table_listbox.insert(tk.END, table[0])
    else:
        messagebox.showinfo("No Entries", "No tabels found in the database.")

# Function to display the entries of the selected table in the Treeview
def show_table_entries(event):
    selected_table = table_listbox.get(table_listbox.curselection())
    cursor.execute(f"SELECT power, pixel FROM main_table WHERE table_name = ?", (selected_table,))
    entries = cursor.fetchall()

    # Clear the Treeview for displaying new entries
    for widget in table_frame_entries.winfo_children():
        widget.destroy()

    if entries:
        # Create and populate the Treeview for the selected table
        data_table = ttk.Treeview(table_frame_entries, columns=("Power", "Pixel"), show="headings", height=10, style="Custom.Treeview")
        data_table.heading("Power", text="Power", anchor=tk.NW)
        data_table.heading("Pixel", text="Pixel", anchor=tk.NW)

        for entry in entries:
            data_table.insert("", tk.END, values=(entry[0], entry[1]))

        data_table.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Show data in the graph for the selected table
        show_data(selected_table)
    else:
        messagebox.showinfo("No Entries", f"No entries found for table '{selected_table}'.")

def create_fixed_graph():
    global ax, canvas  # We will reuse 'ax' and 'canvas' across table switches
    fig, ax = plt.subplots(figsize=(6, 6))  # Fixed figure size

    # Draw concentric circles with fixed radii
    circles = [18, 36, 54]
    for radius in circles:
        circle = plt.Circle((0, 0), radius, color='b', fill=False, linestyle='--')
        ax.add_artist(circle)

    # Set fixed limits and labels for the graph
    ax.set_xlim(-60, 60)
    ax.set_ylim(-60, 60)
    ax.set_aspect('equal', 'box')
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")
    ax.set_title("Fixed Graph", fontsize=15, fontstyle='italic', fontweight='bold')

    # Display the fixed graph in the right frame only once
    canvas = FigureCanvasTkAgg(fig, master=graph_frame_right)
    canvas.draw()
    canvas.get_tk_widget().pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Function to show the graph with concentric circles and pixel data points
def show_data(selected_table):
    cursor.execute(f"SELECT pixel FROM main_table WHERE table_name = ?", (selected_table,))
    pixel_values = [row[0] for row in cursor.fetchall()]

    # Clear previous points on the graph, but keep the circles
    ax.cla()  # Clear the axes (removes previous points)
    
    # Recreate the concentric circles (since we cleared the axes)
    circles = [18, 36, 54]
    for radius in circles:
        circle = plt.Circle((0, 0), radius, color='b', fill=False)
        ax.add_artist(circle)

    # Check if pixel_values is empty
    if not pixel_values:
        messagebox.showinfo("No Data", f"No pixel data available for table '{selected_table}'.")
        return

    # Plot the new pixel points with fixed angles
    for i, pixel in enumerate(pixel_values):
        if pixel is None:  # Skip if pixel is None
            print(f"Warning: Pixel value at index {i} is None, skipping.")
            continue
        angle = (2 * np.pi / len(pixel_values)) * i  # Spread points evenly
        x = pixel * np.cos(angle)
        y = pixel * np.sin(angle)
        ax.plot(x, y, 'ro')  # Plot points as red dots

    # Set fixed limits and labels for the graph
    ax.set_xlim(-60, 60)
    ax.set_ylim(-60, 60)
    ax.set_aspect('equal', 'box')
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")
    ax.set_title(f"Pixel Data for {selected_table}", fontsize=15, fontstyle='italic', fontweight='bold')

    canvas.draw()  # Refresh the canvas with updated graph

# Function to delete a specific table
def delete_table():
    current_table = table_listbox.get(table_listbox.curselection())
    if messagebox.askyesno("Delete Table", "Are you sure you want to delete this table?"):
        cursor.execute(f"DROP TABLE {current_table}")
        cursor.execute(f"DELETE FROM main_table WHERE table_name = ?", (current_table,))
        conn.commit()
        messagebox.showinfo("Success", f"Table {current_table} deleted successfully.")
        # Reset to default
        ax.cla()
        for widget in table_frame_entries.winfo_children():
            widget.destroy()
        
        retrieve_entry()

# Function to create a new table
def create_new_table():
    table_name = simpledialog.askstring("Create New Table", "Enter a name for the new table:")
    if table_name:
        try:
            cursor.execute(f"CREATE TABLE {table_name} (power TEXT, pixel INTEGER UNIQUE)")
            cursor.execute(f"INSERT INTO main_table (table_name) VALUES (?)", (table_name,))
            conn.commit()
            messagebox.showinfo("Success", f"Table '{table_name}' created successfully.")
            set_current_table(table_name)  # Switch to the new table
            retrieve_entry()
        except sqlite3.OperationalError:
            messagebox.showerror("Error", f"Table '{table_name}' already exists.")

# Main Tkinter window setup
window = tk.Tk()
window.title("Pixel Power Database")
window.geometry("1200x600")

# Create frames
frame_left = tk.Frame(window)
frame_left.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

frame_right = tk.Frame(window)
frame_right.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a title label
title_label = tk.Label(frame_right, text="Data of Current Table", font=("Helvetica", 14, "bold"))
title_label.pack(pady=10)

# Create scrollbars for power and pixel
power_scrollbar = tk.Scale(frame_left, from_=0, to=100, orient='horizontal', label='Power')
power_scrollbar.pack(padx=10, pady=10)

pixel_scrollbar = tk.Scale(frame_left, from_=0, to=100, orient='horizontal', label='Pixel')
pixel_scrollbar.pack(padx=10, pady=10)

# Create buttons
add_entry_button = tk.Button(frame_left, text="Add Entry", command=add_entry)
add_entry_button.pack(padx=10, pady=5)

delete_pixel_button = tk.Button(frame_left, text="Delete Entries by Pixel", command=delete_from_pixel)
delete_pixel_button.pack(padx=10, pady=5)

retrieve_button = tk.Button(frame_left, text="Retrieve Entries", command=retrieve_entry)
retrieve_button.pack(padx=10, pady=5)

create_new_table_button = tk.Button(frame_left, text="Create New Table", command=create_new_table)
create_new_table_button.pack(padx=10, pady=5)

delete_table_button = tk.Button(frame_left, text="Delete Table", command=delete_table)
delete_table_button.pack(padx=10, pady=5)

# Create a Listbox to display table names
table_listbox = tk.Listbox(frame_left)
table_listbox.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
# selected_table = table_listbox.get(table_listbox.curselection())
# Bind click event on the Listbox
table_listbox.bind('<<ListboxSelect>>', show_table_entries)

# Create frames for displaying entries
table_frame_right = tk.Frame(frame_right)
table_frame_right.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

table_frame_entries = tk.Frame(frame_right)
table_frame_entries.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

graph_frame_right = tk.Frame(frame_right)
graph_frame_right.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

# Create the fixed graph on startup
create_fixed_graph()

# Initialize the database
initialize_database()

# Start the Tkinter main loop
window.mainloop()

# Close the database connection
conn.close()
