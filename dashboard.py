from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)

SETTINGS_FILE = "welcome_settings.json"


def load_settings():
    default_settings = {
    "avatar_size": 180,
    "avatar_x": 510,
    "avatar_y": 25,
    "username_size": 38,
    "username_y": 215,
    "welcome_channel": "welcome",
    "auto_role": "moonwalker",
    "message": """✨ **A New Star Has Appeared** ✨
Selamat datang, {member} ✨ Kamu telah memasuki **Everlight Virtual**, tempat di mana kreativitas, persahabatan, dan mimpi bersinar bersama.

📚 Baca aturan di #welcome
🎭 Pilih role di #self-roles
🌸 Perkenalkan dirimu di #introduction
💬 Bergabunglah dalam percakapan dan event komunitas

Kami berharap perjalananmu di sini dipenuhi tawa, kenangan indah, dan teman-teman baru.
🌙 *May your light continue to shine brightly.* ✨"""
}

    if not os.path.exists(SETTINGS_FILE):
        return default_settings

    with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4, ensure_ascii=False)


@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/welcome", methods=["GET", "POST"])
def welcome():

    if request.method == "POST":

        settings = {
            "avatar_size": int(request.form["avatar_size"]),
            "avatar_x": int(request.form["avatar_x"]),
            "avatar_y": int(request.form["avatar_y"]),
            "username_size": int(request.form["username_size"]),
            "username_y": int(request.form["username_y"]),
            "welcome_channel": request.form["welcome_channel"],
            "auto_role": request.form["auto_role"],
            "message": request.form["message"]
        }

        save_settings(settings)

        return redirect(url_for("welcome", saved="1"))

    settings = load_settings()

    return render_template(
        "welcome.html",
        settings=settings
    )

@app.route("/autorole", methods=["GET", "POST"])
def autorole():

    settings = load_settings()

    if request.method == "POST":
        settings["auto_role"] = request.form["auto_role"]

        save_settings(settings)

        return redirect(url_for("autorole", saved="1"))

    return render_template(
        "autorole.html",
        settings=settings
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )