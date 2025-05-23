from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pymongo import MongoClient

app = Flask(__name__)

def init_sqlite_db():
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

init_sqlite_db()

client = MongoClient("mongodb://localhost:27017/")
db = client["restaurantDB"]
restaurants_collection = db["restaurant"]

# Home page route
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
                user = cursor.fetchone()
        except sqlite3.OperationalError as e:
            error = f"Error in database: {str(e)}"
            user = None
        except Exception as e:
            error = f"Unexpected error: {str(e)}"
            user = None

        if user:
            return redirect(url_for('welcome', username=username))
        else:
            error = error or "The username or password is incorrect."

    return render_template('login.html', error=error)


@app.route('/register', methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            with sqlite3.connect('users.db', timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL
                    )
                ''')

                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            error = "The username already exists. Please choose another one."
        except sqlite3.OperationalError as e:
            error = f"Database is busy. Please try again later. <br>{str(e)}"

    return render_template('register.html', error=error)


@app.route('/welcome')
def welcome():
    username = request.args.get('username', 'user')
    return render_template('welcome.html', username=username)


@app.route('/search', methods=["GET", "POST"])
def search_restaurants():
    results = []
    if request.method == "POST":
        # Gather fields from form
        name = request.form.get("name")
        borough = request.form.get("borough")
        cuisine = request.form.get("cuisine")
        grade = request.form.get("grades")

        # Check if all fields are empty
        if not any([name, borough, cuisine, grade]):
            return render_template('search.html', results=[], message="Please enter at least one search criteria.")

        query = {}
        if name:
            query["name"] = {"$regex": name, "$options": "i"}
        if borough:
            query["borough"] = {"$regex": borough, "$options": "i"}
        if cuisine:
            query["cuisine"] = {"$regex": cuisine, "$options": "i"}
        if grade:
            query["grades.grade"] = grade.upper()

        print("Query being executed:", query)

        results = list(restaurants_collection.find(query, {"_id": 0}).limit(3))

        for res in results:
            if "grades" in res:
                valid_grades = [g["grade"] for g in res["grades"] if "grade" in g and g["grade"] in ["A", "B", "C", "Z"]]
                res["grades"] = [valid_grades[0]] if valid_grades else []

        if not results:
            return render_template('search.html', results=[], message="No results found.")

    return render_template('search.html', results=results)


# Run the application
if __name__ == '__main__':
    print("Server is running at: http://127.0.0.1:5000/register")
    app.run(debug=True)
