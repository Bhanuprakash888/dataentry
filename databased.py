import sqlite3
import hashlib
from tkinter import simpledialog
def create_users_table():
    conn = sqlite3.connect('C:\\Users\\BANUPRAKASH G\\Desktop\\plane\\user1.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            image_name TEXT,
            image_data BLOB,
            FOREIGN KEY(username) REFERENCES user1(username)
    )
    ''') 
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = sqlite3.connect('user1.db')
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    try:
        cursor.execute('INSERT INTO user1 (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect('user1.db')
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute('SELECT * FROM user1 WHERE username = ? AND password = ?', (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return bool(user)

def save_image(username, image_name, image_data):
    conn = sqlite3.connect('user1.db')  # Connect to your database
    cursor = conn.cursor()
    
    # Insert image into the database
    cursor.execute("INSERT INTO images (username, image_name, image_data) VALUES (?, ?, ?)",
                   (username, image_name, image_data))
    conn.commit()
    conn.close()

def get_user_images(username):
    conn = sqlite3.connect('user1.db')
    cursor = conn.cursor()

    # Retrieve image names for the logged-in user
    cursor.execute("SELECT image_name FROM images WHERE username = ?", (username,))
    images = cursor.fetchall()  # Returns a list of tuples containing image names
    conn.close()
    
    return [img[0] for img in images]  # Return a list of image names

def get_image_data(username, image_name):
    conn = sqlite3.connect('user1.db')
    cursor = conn.cursor()

    # Retrieve image data for the selected image name
    cursor.execute("SELECT image_data FROM images WHERE username = ? AND image_name = ?",
                   (username, image_name))
    image_data = cursor.fetchone()[0]
    conn.close()

    return image_data
create_users_table()