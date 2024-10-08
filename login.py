import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import sqlite3
import hashlib
import re
import os
import Eg  # Ensure this module exists and has the correct function defined

# Function to create users table
def create_users_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to register a new user
def register_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Function to log in a user
def login_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return bool(user)

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
            print(f"Logged in user: {current_user}") 
            messagebox.showinfo("Login Successful", "Welcome!")  
            Eg.show_input_window()  # Call to the next function or window here

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
    
    # Start the main loop
    root.mainloop()

# Create the users table
create_users_table()

# Start the application with the login page
login_page()
