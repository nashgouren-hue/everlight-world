from flask import Flask, render_template, request, redirect, url_for
import json
import os
import requests

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

"tiktok_channel": "livenotification",
"tiktok_kurocat": "@kurocatkurimu",
"enable_kurocat": True,
"tiktok_nash": "@nashgouren_",
"enable_nash": True,
"tiktok_haru": "@hiharuhere",
"enable_haru": True,
"tiktok_louise": "@louiegospellvt",
"enable_louise": True,
"tiktok_everlight": "@everlightvirtual",
"enable_everlight": True,
"tiktok_message": "🔴 {creator} sedang LIVE di TikTok!",

"notif_title": "🔴 {creator} IS LIVE!",
"notif_message": "✨ {creator} sedang LIVE di TikTok! Ayo mampir dan ramaikan live-nya!",
"notif_mention": "none",
"notif_banner": "",
"notif_color": "#ff3355",
"notif_button": "🔴 Watch Live",

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


@app.route("/tiktok", methods=["GET", "POST"])
def tiktok():
    settings = load_settings()

    if request.method == "POST":
        settings["tiktok_channel"] = request.form["tiktok_channel"]

        settings["tiktok_kurocat"] = request.form["tiktok_kurocat"]
        settings["enable_kurocat"] = "enable_kurocat" in request.form

        settings["tiktok_nash"] = request.form["tiktok_nash"]
        settings["enable_nash"] = "enable_nash" in request.form

        settings["tiktok_haru"] = request.form["tiktok_haru"]
        settings["enable_haru"] = "enable_haru" in request.form

        settings["tiktok_louise"] = request.form["tiktok_louise"]
        settings["enable_louise"] = "enable_louise" in request.form

        settings["tiktok_everlight"] = request.form["tiktok_everlight"]
        settings["enable_everlight"] = "enable_everlight" in request.form

        settings["tiktok_message"] = request.form["tiktok_message"]

        settings["image_kurocat"] = request.form.get("image_kurocat", "")
        settings["image_nash"] = request.form.get("image_nash", "")
        settings["image_haru"] = request.form.get("image_haru", "")
        settings["image_louise"] = request.form.get("image_louise", "")
        settings["image_everlight"] = request.form.get("image_everlight", "")

        settings["notif_title"] = request.form["notif_title"]
        settings["notif_message"] = request.form["notif_message"]
        settings["notif_mention"] = request.form["notif_mention"]
        settings["notif_banner"] = request.form["notif_banner"]
        settings["notif_color"] = request.form["notif_color"]
        settings["notif_button"] = request.form["notif_button"]

        save_settings(settings)

        return redirect(url_for("tiktok", saved="1"))

    return render_template(
        "tiktok.html",
        settings=settings
    )

@app.route("/tiktok/test", methods=["POST"])
def test_tiktok_notification():
    webhook_url = os.environ.get("DISCORD_LIVE_WEBHOOK")

    if not webhook_url:
        return "DISCORD_LIVE_WEBHOOK belum diatur.", 500

    creator = "Kurocat Kurimu"
    live_url = "https://www.tiktok.com/@kurocatkurimu/live"

    title = request.form.get(
        "notif_title",
        "🔴 {creator} IS LIVE!"
    ).replace("{creator}", creator)

    message = request.form.get(
        "notif_message",
        "✨ {creator} sedang LIVE di TikTok!"
    ).replace("{creator}", creator).replace("{url}", live_url)

    banner = request.form.get("notif_banner", "").strip()
    profile_image = request.form.get("image_kurocat", "").strip()
    button_text = request.form.get("notif_button", "🔴 Watch Live")
    color_hex = request.form.get("notif_color", "#ff3355").lstrip("#")

    try:
        color = int(color_hex, 16)
    except ValueError:
        color = 0xFF3355

    mention_setting = request.form.get("notif_mention", "none")

    if mention_setting == "everyone":
        content = "@everyone"
    elif mention_setting == "here":
        content = "@here"
    else:
        content = ""

    embed = {
        "title": title,
        "description": message,
        "color": color,
        "url": live_url,
        "footer": {
            "text": "EVERLIGHT VIRTUAL • TEST NOTIFICATION"
        }
    }

    if profile_image:
        embed["image"] = {
            "url": profile_image
        }
    elif banner:
        embed["image"] = {
            "url": banner
        }

    payload = {
        "content": content,
        "embeds": [embed],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 5,
                        "label": button_text,
                        "url": live_url
                    }
                ]
            }
        ],
        "allowed_mentions": {
            "parse": ["everyone"] if content else []
        }
    }

    response = requests.post(
        webhook_url,
        json=payload,
        timeout=10
    )

    if response.status_code not in (200, 204):
        return f"Gagal mengirim test notification: {response.text}", 500

    return redirect(url_for("tiktok", tested="1"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )