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
    cursor.execute("SELECT power, pixel FROM main_table WHERE table_name = ? ORDER BY rowid DESC LIMIT 1", (current_table,))
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
    
    # No need to attach the database dynamically
    if not db_attached:
        # Ensure foreign keys are enabled
        cursor.execute("PRAGMA foreign_keys=ON")
        db_attached = True

    # Insert the table name as a new entry into the main_table (if not exists)
    cursor.execute("INSERT INTO main_table (table_name, power, pixel) VALUES (?, NULL, NULL)", (current_table,))
    conn.commit()

    # Get the last known power and pixel for the selected table
    get_last_power_and_pixel()
    
# # Set the initial table
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
        # cursor.execute(f"INSERT INTO {current_table} (power, pixel) VALUES (?, ?)", (power, pixel_value))
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
    
    # Ask the user for the pixel value to delete from
    pixel_value = simpledialog.askinteger("Delete Entries", "Enter the pixel value to delete from:")
    if pixel_value is None:
        return

    # Query the main_table for rows with the specified table name and pixel value
    cursor.execute("SELECT rowid FROM main_table WHERE table_name = ? AND pixel <= ? ORDER BY pixel DESC", (current_table, pixel_value))
    rows_to_delete = cursor.fetchall()

    if rows_to_delete:
        # Delete the entries in main_table that match the current_table and pixel condition
        cursor.execute("DELETE FROM main_table WHERE table_name = ? AND pixel <= ?", (current_table, pixel_value))
        conn.commit()
        
        # Display a success message
        messagebox.showinfo("Success", f"Deleted all entries with pixel value {pixel_value} and below from {current_table}")
        
        # Update last_power and last_pixel based on the remaining entries
        get_last_power_and_pixel()
    else:
        # Show an error message if no entries were found
        messagebox.showerror("Error", f"No entries found with pixel value {pixel_value} or below in {current_table}.")


# Function to retrieve and display entries in a table
def retrieve_entry():
    # Create a style for the Treeview and heading
    style = ttk.Style()
    # print(current_table)
    # Configure the Treeview style with a larger font
    style.configure("Custom.Treeview", font=("Helvetica", 12))  # Change '12' to the desired font size
    style.configure("Custom.Treeview.Heading", font=("Helvetica", 14, "bold"))  # For the heading, set a larger and bold font
    # title_label.config(text=f"                                                              Data of {current_table}")
    # cursor.execute(f"SELECT * FROM {current_table}")
    # entries = cursor.fetchall()

    # Clear the table sub-frame before adding the new table
    for widget in table_frame_right.winfo_children():
        widget.destroy()
    
    cursor.execute("SELECT DISTINCT table_name FROM main_table")
    distinct_tables = cursor.fetchall()
    
    table_listbox.delete(0, tk.END)
    
    if distinct_tables:
        for table in distinct_tables:
            table_listbox.insert(tk.END, table[0])
    else:
        messagebox.showinfo("No Entries", "No tabels found in the database.")
        
def show_table_entries(event):
    selected_table = table_listbox.get(table_listbox.curselection())
    cursor.execute(f"SELECT power, pixel FROM main_table WHERE table_name = ? and power is not null and pixel is not null", (selected_table,))
    entries = cursor.fetchall()

    # Clear the Treeview for displaying new entries
    for widget in table_frame_right.winfo_children():
        widget.destroy()

    if entries:
        # Create and populate the Treeview for the selected table
        data_table = ttk.Treeview(table_frame_right, columns=("Power", "Pixel"), show="headings", height=10, style="Custom.Treeview")
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
    # Create a fixed figure and axis
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



#Function to show the graph with concentric circles and pixel data points
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
        ax.plot(x, y, 'ro')  # 'ro' represents red circles for points

        # Annotate each point with its pixel value
        #ax.text(x + 1, y + 1, str(pixel), fontsize=10, color='black')

    # Re-apply fixed graph settings
    ax.set_xlim(-60, 60)
    ax.set_ylim(-60, 60)
    ax.set_aspect('equal', 'box')
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")
    ax.set_title(f"Pixel Data for  {selected_table}", fontsize=15, fontstyle='italic', fontweight='bold')

    # Redraw the updated plot
    canvas.draw()

def delete_table():
    current_table = table_listbox.get(table_listbox.curselection())
    
    if messagebox.askyesno("Delete Table", f"Are you sure you want to delete the entries associated with the table '{current_table}'?"):
        # Delete all entries related to this table in the main_table
        cursor.execute("DELETE FROM main_table WHERE table_name = ?", (current_table,))
        conn.commit()
        
        messagebox.showinfo("Success", f"All entries for table '{current_table}' deleted successfully.")
        
        # Clear plot or visualization
        ax.cla()
        
        # Clear the right-side frame widgets
        for widget in table_frame_right.winfo_children():
            widget.destroy()
        
        # Refresh the entry list or UI
        retrieve_entry()


# Function to create a new table
def create_new_table():
    table_name = simpledialog.askstring("Create New Table", "Enter a name for the new table:")
    
    if table_name:
        try:
            # Check if the table name already exists in the main_table
            cursor.execute("SELECT 1 FROM main_table WHERE table_name = ?", (table_name,))
            if cursor.fetchone():
                raise sqlite3.OperationalError  # Simulate table exists error
            
            # Insert the new logical table (just its name) into the main_table
            cursor.execute(f"INSERT INTO main_table (table_name) VALUES (?)", (table_name,))
            conn.commit()
            
            messagebox.showinfo("Success", f"Logical table '{table_name}' added successfully.")
            
            # Set the new logical table as the current one
            set_current_table(table_name)
            
            # Update the UI or entries list
            retrieve_entry()
        
        except sqlite3.OperationalError:
            messagebox.showerror("Error", f"Table '{table_name}' already exists.")


        

# Function to save the current table data (no prompt for table name)
# def save_current_table():
#     global current_table
#     if current_table:
#         cursor.execute(f"CREATE TABLE IF NOT EXISTS {current_table} (power TEXT, pixel INTEGER UNIQUE)")
#         conn.commit()
#         messagebox.showinfo("Success", f"Table '{current_table}' saved successfully!")
#         update_table_list()
#     else:
#         messagebox.showerror("Error", "No table selected to save.")

# Function to update the list of saved tables
# def update_table_list():
#     table_list.delete(0, tk.END)
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
#     tables = cursor.fetchall()
#     for table in tables:
#         table_list.insert(tk.END, table[0])

# Function to select a table from the list
# def select_table(event):
#     global current_table
#     selected_table = table_list.get(tk.ACTIVE)
    
#     if selected_table and selected_table != current_table:
#         current_table = selected_table
#         set_current_table(current_table)

#         # Call retrieve_entry() and show_data() when switching tables
#         retrieve_entry()  # Update table view with the selected table's data
#         show_data()       # Update graph with the selected table's points

#         #messagebox.showinfo("Table Selected", f"Switched to table '{current_table}'.")

# # Function to delete a selected table
# def delete_table():
#     selected_table = table_list.get(tk.ACTIVE)
#     if selected_table:
#         confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the table '{selected_table}'?")
#         if confirm:
#             cursor.execute(f"DROP TABLE IF EXISTS {selected_table}")
#             conn.commit()
#             messagebox.showinfo("Success", f"Table '{selected_table}' deleted successfully.")
#             update_table_list()

#             if current_table == selected_table:
#                 current_table = 'entries'
#                 set_current_table(current_table)
#                 messagebox.showinfo("Switched Table", f"Switched to the default table 'entries'.")
#     else:
#         messagebox.showerror("Error", "No table selected for deletion.")

# Function to update the power label
def update_power_label(value):
    power_value_label.config(text=f"Power: {int(float(value))}")

# Function to update the pixel label
def update_pixel_label(value):
    pixel_value_label.config(text=f"Pixel: {int(float(value))}")

# Set up the GUI
root = tk.Tk()
root.title("Power and Pixel Entry")
root.geometry("1920x1080")
root.state('zoomed')

# Set up the main frame
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# Set up the left vertical section (list of tables)
left_frame = tk.Frame(main_frame, width=500)
left_frame.pack(side=tk.LEFT, fill=tk.Y)
#left_frame.pack_propagate(False)

table_list_label = ttk.Label(left_frame, text="Table List", font=("Times New Roman", 20,"bold"))
table_list_label.pack(padx=10, pady=10)

table_listbox = tk.Listbox(left_frame,width=40)
listboxfont=("Times New Roman",14)
table_listbox.config(font=listboxfont)
table_listbox.pack(padx=10, pady=10, fill=tk.Y, expand=True)
table_listbox.bind('<<ListboxSelect>>', show_table_entries)

# Set up the middle vertical section (scrollbars and table title)
middle_frame = tk.Frame(main_frame)
middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

power_label = ttk.Label(middle_frame, text="Power", font=("Times New Roman", 20,"bold"))
power_label.pack(padx=10, pady=10)

power_scrollbar = ttk.Scale(middle_frame, from_=0, to=127, orient=tk.HORIZONTAL, command=update_power_label, length=350)
power_scrollbar.pack(padx=10, pady=10)

power_value_label = ttk.Label(middle_frame, text="Power: 0",font=("Times New Roman", 12))
power_value_label.pack(padx=10, pady=10)

pixel_label = ttk.Label(middle_frame, text="Pixel", font=("Times New Roman", 20,"bold"))
pixel_label.pack(padx=10, pady=10)

pixel_scrollbar = ttk.Scale(middle_frame, from_=18, to=54, orient=tk.HORIZONTAL, command=update_pixel_label, length=350)
pixel_scrollbar.pack(padx=10, pady=10)

pixel_value_label = ttk.Label(middle_frame, text="Pixel: 18", font=("Times New Roman", 12))
pixel_value_label.pack(padx=10, pady=10)

# Use tk.Button for more control over button size
add_entry_button = tk.Button(middle_frame, text="Add Entry", command=add_entry, width=20, height=2, font=("Helvetica", 12),bg="Lightgreen")
add_entry_button.pack(padx=10, pady=10)

delete_button = tk.Button(middle_frame, text="Delete Pixel", command=delete_from_pixel, width=20, height=2, font=("Helvetica", 12),bg="Lightcoral")
delete_button.pack(padx=10, pady=10)

# Set up the right vertical section (table and graph display)
right_frame = tk.Frame(main_frame)
right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Title of the current table
title_label = tk.Label(right_frame, text=f"Data of current tabel", font=("Times New Roman", 20,"bold"))
title_label.grid(row=0, column=0, columnspan=3, pady=10)

# Sub-frame for displaying the data table (right section)
table_frame_right = tk.Frame(right_frame)
table_frame_right.grid(row=1, column=1, columnspan=3, sticky="nsew")

# Sub-frame for displaying the graph (right section)
graph_frame_right = tk.Frame(right_frame)
graph_frame_right.grid(row=2, column=1, columnspan=3, sticky="nsew")

# Use tk.Button for more control over button size
# save_table_button = tk.Button(right_frame, text="Save Table", command=save_current_table, width=20, height=2, font=("Helvetica", 12),bg="Lightgreen")
# save_table_button.grid(row=3, column=1, padx=20, pady=20)

delete_table_button = tk.Button(right_frame, text="Delete Table", command=delete_table, width=20, height=2, font=("Helvetica", 12),bg="Lightcoral")
delete_table_button.grid(row=3, column=2, padx=10, pady=10)
retrieve_button = tk.Button(right_frame, text="Retrieve Entries", command=retrieve_entry,width=20, height=2, font=("Helvetica", 12),bg="Lightcoral")
retrieve_button.grid(row=3, column=1, padx=10, pady=10)
new_table_button = tk.Button(right_frame, text="Create New Table", command=create_new_table, width=20, height=2, font=("Helvetica", 12),bg="Lightgreen")
new_table_button.grid(row=3, column=3, padx=10, pady=10)

# Add weight to columns and rows so the layout expands
right_frame.columnconfigure(0, weight=0)
right_frame.columnconfigure(1, weight=1)
right_frame.columnconfigure(2, weight=1)
right_frame.columnconfigure(3, weight=1)
right_frame.rowconfigure(1, weight=1)
right_frame.rowconfigure(2, weight=1)
right_frame.rowconfigure(3, weight=0)

create_fixed_graph()
initialize_database()
# Call update_table_list initially to show tables
# update_table_list()

# Load the default table 'entries' data and graph at the start
retrieve_entry()
# show_data()

# Run the Tkinter event loop
root.mainloop()
conn.close()