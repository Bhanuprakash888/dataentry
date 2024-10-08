import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import sqlite3
import hashlib
import re
import os
import threading
import time
import Eg

import threading

# Global variable to track if the database is locked
is_db_locked = False

# Global variable for timer and lock release interval
timer = None
lock_release_interval = 5  # Time in seconds to wait before attempting to release the lock

def set_busy_timeout(connection):
    connection.execute("PRAGMA busy_timeout = 5000")  # Adjust this as needed

def get_db_connection():
    conn = sqlite3.connect('users.db')
    set_busy_timeout(conn)
    return conn

# def start_lock_timer():
#     global timer
#     if timer is not None:
#         timer.cancel()  # Cancel the previous timer if it exists
#     timer = threading.Timer(5.0, release_lock)  # Example duration for the lock to release
#     timer.start()
    
def release_lock():
    global is_db_locked
    global timer

    if is_db_locked:
        is_db_locked = False  # Release the lock
        print("Database lock released.")
        
        # If there are pending operations, you might want to retry them here
        # or log that the lock was released.
    else:
        print("Database was not locked.")

def start_lock_timer():
    global timer
    if timer is not None:
        timer.cancel()  # Cancel any existing timer
    timer = threading.Timer(lock_release_interval, release_lock)
    timer.start()

# Function to create the necessary tables (users and sessions)
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')

    # Create sessions table
    cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
                        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        FOREIGN KEY(username) REFERENCES users(username))''')

    # Create screenshots table
    cursor.execute('''CREATE TABLE IF NOT EXISTS screenshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        image_path TEXT,
                        FOREIGN KEY(username) REFERENCES users(username))''')

    conn.commit()
    conn.close()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to register a new user
def register_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        cursor.close()  # Close the cursor
        conn.close()  # Close the connection
        start_lock_timer()  

# Function to log in a user
def login_user(username, password):
    conn = get_db_connection()
    start_lock_timer()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return bool(user)

# Function to create a session for a user
def create_session(username):
    conn = get_db_connection()
    start_lock_timer()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO sessions (username) VALUES (?)', (username,))
        conn.commit()
        print("Session created successfully.")
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e}")  # Log the error for debugging
    finally:
        cursor.close()  # Close the cursor
        conn.close()  # Close the connection
        start_lock_timer()  
        if timer is not None:
            timer.cancel()  # Stop the timer after successful completion

# Function to get the current user session
def get_current_session():
    conn = get_db_connection()
    start_lock_timer()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM sessions ORDER BY session_id DESC LIMIT 1')
    user = cursor.fetchone()
    # cursor.close()
    # conn.close()
    return user[0],cursor,conn if user else None

# Function to end the current session (log out)
def end_session():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sessions')
    conn.commit()
    cursor.close()
    conn.close()
    print("Session ended successfully.")

# Function to save screenshot for the logged-in user
def save_screenshot(image_path):
    user = get_current_session()  # Get the current session user
    if user:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO screenshots (username, image_path) VALUES (?, ?)', (user, image_path))
        conn.commit()
        cursor.close()
        conn.close()
        messagebox.showinfo("Success", "Screenshot saved successfully")
    else:
        messagebox.showerror("Error", "No active session found. Please log in.")

# Function to retrieve screenshots for the logged-in user
def retrieve_screenshots():
    user = get_current_session()  # Get the current session user
    if user:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT image_path FROM screenshots WHERE username = ?', (user,))
        screenshots = cursor.fetchall()
        cursor.close()
        conn.close()

        if screenshots:
            for screenshot in screenshots:
                print(f"Screenshot: {screenshot[0]}")  # Modify this to display the screenshot in the UI
        else:
            messagebox.showinfo("Info", "No screenshots found for this user.")
    else:
        messagebox.showerror("Error", "No active session found. Please log in.")

# Main function for the login page
def login_page():
    def handle_login():
        username = username_entry.get()
        password = password_entry.get()

        # Check if username or password is empty
        if username == "" or password == "":
            messagebox.showinfo("Login Failed", "Username/Password cannot be empty")
            return

        # Username validation: must not start with a number
        if re.match(r'^\d', username):
            messagebox.showinfo("Login Failed", "Username cannot start with a number")
            return

        # Password validation
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%?&])[A-Za-z\d@$!%?&]{8,}$', password):
            messagebox.showinfo("Login Failed", "Password must contain at least 8 characters, including an uppercase letter, lowercase letter, a number, and a special character")
            return

        # If login_user function returns True, proceed to login
        if login_user(username, password):
            global current_user
            current_user = username
            create_session(current_user)  # Create a session for the logged-in user
            messagebox.showinfo("Login Successful", "Welcome!")  
            Eg.show_input_window()
            
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    def handle_register():
        username = username_entry.get()
        password = password_entry.get()
        if username == "" or password == "":
            messagebox.showinfo("Register Failed", "Username/Password cannot be empty")
            return

        # Username validation
        if re.match(r'^\d', username):
            messagebox.showinfo("Register Failed", "Username cannot start with a number")
            return

        # Password validation
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%?&])[A-Za-z\d@$!%?&]{8,}$', password):
            messagebox.showinfo("Register Failed", "Password must contain at least 8 characters, including an uppercase letter, lowercase letter, a number, and a special character")
            return
        
        if register_user(username, password):
            messagebox.showinfo("Registration Successful", "User registered successfully!")
        else:
            messagebox.showerror("Registration Failed", "Username already exists")

    # Create the main window
    root = tk.Tk()
    root.title("Login Page")

    # Create and pack heading labels
    heading = tk.Label(root, text="Aerosafe Navigator", font=("Book Antiqua", 25, "bold"), fg="midnight blue")
    heading1 = tk.Label(root, text="An Interactive Geospatial Path Simulation with Danger Zone Detection", font=("Book Antiqua", 15), fg="midnight blue")
    heading2 = tk.Label(root, text="Login Page", font=("Book Antiqua", 20, "bold"), fg="maroon")
    heading.pack(pady=15)
    heading1.pack(pady=15)
    heading2.pack(pady=15)

    # Load user image
    img_path = os.path.join(os.path.dirname(__file__), "papu.jpg")  # Ensure correct path to image
    img = Image.open(img_path)
    img = img.resize((300, 300))
    photo = ImageTk.PhotoImage(img)
    image_label = tk.Label(root, image=photo)
    image_label.photo = photo  # Reference to avoid garbage collection
    image_label.pack(pady=10)

    # Create username and password entry fields
    label_font = ("Helvetica", 10)
    tk.Label(root, text="Username:", font=label_font).pack(pady=10)
    username_entry = tk.Entry(root)
    username_entry.pack(pady=5)

    tk.Label(root, text="Password:", font=label_font).pack(pady=5)
    password_entry = tk.Entry(root, show='*')
    password_entry.pack(pady=10)

    # Create Login and Register buttons
    tk.Button(root, text="Login", command=handle_login).pack(pady=10)
    tk.Button(root, text="Register", command=handle_register).pack(pady=10)

    # Start the GUI main loop
    create_tables()  # Create tables on startup
    root.mainloop()

# Call the login page function to start the application
if __name__ == "__main__":
    login_page()
