from flask import Flask, request, render_template, redirect

app = Flask(__name__)


# ----- Global Variables ------
USERS = [
    {"email": "ali@gmail.com", "password": "12345"},
    {"email": "ahmad@gmail.com", "password": "54321"}
]



# ----- Application Routes -----

@app.route("/", methods = ["GET", "POST"])
def index():
    if request.method == "POST" and "start-now" in request.form:
        return render_template("login.html")
    return render_template("index.html")

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST" and "email" in request.form and "password" in request.form:
        email = request.form.get("email")
        password = request.form.get("password")
        for user in USERS:
            if email == user["email"] and password == user["password"]:
                return render_template("main.html", name=email)
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST" and "email" in request.form:
        signup_email = request.form.get("email")
        signup_password = request.form.get("password")
        for user in USERS:
            if user["email"] == signup_email:
                return render_template("signup.html")
        USERS.append({"email": signup_email, "password": signup_password})
        return render_template("main.html", name=signup_email)
    return render_template("signup.html")

@app.route("/admin")
def admin():
    return render_template("admin.html", USERS=USERS)



if __name__ == "__main__":
    app.run(debug="True",port=8000)