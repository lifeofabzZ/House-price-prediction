from flask import Flask, request, jsonify, render_template,flash,redirect,url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler
from flask_bcrypt import Bcrypt
import sqlite3


app = Flask(__name__)
app.secret_key = "ImASecretKey"
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
DATABASE = "database.db"


# User Model
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash


@login_manager.user_loader
def load_user(user_id):
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    con.close()
    if user:
        return User(*user)
    return None

def init_db():
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
        con.commit()

init_db()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        
        try:
            con = sqlite3.connect(DATABASE)
            cur = con.cursor()
            cur.execute("INSERT INTO users (username,password) VALUES (?, ?)", (username,hashed_password))
            con.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "danger")
        finally:
            con.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        con = sqlite3.connect(DATABASE)
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        con.close()

        if user and bcrypt.check_password_hash(user[2], password):
            login_user(User(*user))
            flash("Login successful!", "success")
            return redirect(url_for("house_price_prediction"))
        else:
            flash("Invalid credentials!", "danger")

    return render_template("login.html")

# Load trained model
with open("model/model.pkl", "rb") as f:
    model = pickle.load(f)


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/profile")
@login_required
def profile():
    return render_template("myprofile.html",user=current_user)

@app.route("/house_price_prediction")
@login_required
def house_price_prediction():
    return render_template("index.html")

# Prediction route (handles form submission & API requests)
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.form if request.form else request.get_json()

        # Extract input values
        area = float(data["area"])
        bedrooms = int(data["bedrooms"])
        bathrooms = int(data["bathrooms"])
        stories = int(data["stories"])

        # Prepare input
        features = np.array([[area, bedrooms, bathrooms,stories]])

        # Predict price
        predicted_price = model.predict(features)[0]

        return render_template("result.html", price=round(predicted_price, 2))

    except Exception as e:
        return render_template("result.html", error=str(e))

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
