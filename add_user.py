import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

username = "admin"
password = "12345"


cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
conn.commit()
conn.close()

print("The user has been added successfully.")
