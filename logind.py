import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage,font
import os
import re 
#from newcode import show_input_window
# import OG_FINALD
#from common import current_user 
#import newcode import show
from tkinter import messagebox
from PIL import Image, ImageTk
from databased import login_user, register_user
# current_user = None 

#from newcode import show_input_window
def login_page():
    import OG_FINALD
    import commond
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

        # Password validation: must contain uppercase, lowercase, number, and special character
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',password):
            messagebox.showinfo("Login Failed", "Password must contain at least 8 characters, including an uppercase letter, lowercase letter, a number, and a special character")
            return

        # If login_user function returns True, proceed to login
        if login_user(username, password):
            # global current_user
            # current_user = username
            commond.set_current_user(username)
            print(f"Logged in user: {commond.get_current_user()}") 
            messagebox.showinfo("Login Successful", "Welcome!")  
            OG_FINALD.show_input_window()

        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
    def handle_register():
        username = username_entry.get()
        password = password_entry.get()
        if username == "" or password == "":
            messagebox.showinfo("Register Failed", "Username/Password cannot be empty")
            return

        # Username validation: must not start with a number
        if re.match(r'^\d', username):
            messagebox.showinfo("Register Failed", "Username cannot start with a number")
            return

        # Password validation: must contain uppercase, lowercase, number, and special character
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',password):
            messagebox.showinfo("Register Failed", "Password must contain at least 8 characters, including an uppercase letter, lowercase letter, a number, and a special character")
            return
        if register_user(username, password):
            messagebox.showinfo("Registration Successful", "User registered successfully!")
        else:
            messagebox.showerror("Registration Failed", "Username already exists")

    root = tk.Tk()
    root.title("Login Page")

    heading = tk.Label(root, text="Aerosafe Navigator", font=("Book Antiqua", 25, "bold"), fg="midnight blue")
    heading1 = tk.Label(root, text="An Interactive Geospatial Path Simulation with Danger Zone Detection", font=("Book Antiqua", 15), fg="midnight blue")
    heading2 = tk.Label(root, text="Login Page", font=("Book Antiqua", 20,"bold"), fg="maroon")
    heading.pack(pady=15)
    heading1.pack(pady=15)
    heading2.pack(pady=15)
    img = Image.open("papu.jpg")  
    img = img.resize((300, 300))  
    photo = ImageTk.PhotoImage(img)
    image_label = tk.Label(root, image=photo)
    image_label.photo = photo  # Reference to avoid garbage collection
    image_label.pack(pady=10)

    label_font = ("Helvetica", 10)
    tk.Label(root, text="Username:",font =label_font).pack(pady=10)
    username_entry = tk.Entry(root)
    username_entry.pack(pady=5)

    tk.Label(root, text="Password:",font =label_font).pack(pady=5)
    password_entry = tk.Entry(root, show='*')
    password_entry.pack(pady=10)

    tk.Button(root, text="Login", command=handle_login).pack(pady=10)
    tk.Button(root, text="Register", command=handle_register).pack(pady=10)
    root.mainloop() 
    
if __name__ == "__main__":
    
    login_page()



# Start the application with input window
#login_page()