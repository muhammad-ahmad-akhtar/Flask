from flask import Flask, render_template, request
from cs50 import SQL


app = Flask(__name__)

db = SQL("sqlite:///froshims.db")

SPORTS = [
    "Basketball",
    "Soccer",
    "Ultimate Frisbsee",
]


@app.route("/")
def index():
    return render_template("index.html", sports=SPORTS)

@app.route("/register", methods=["POST"])
def register():
    
    name = request.form.get("name")
    sport = request.form.get("sport")
    
    if not name:
        return render_template("error.html", message="Misssing Name")
    if not sport:
        return render_template("error.html", message="Missing Sport")
    if sport not in SPORTS:
        return render_template("error.html", message="Invalid Sport")
    
    db.execute("INSERT INTO registrants (name, sport) VALUES(?, ?)", name, sport)
    
    return render_template("success.html")


@app.route("/registrants")
def registrants():
    registrants = db.execute("SELECT name, sport FROM registrants")
    return render_template("registrants.html", registrants=registrants)

if __name__ == "__main__":
    app.run(debug="True",port=8000)