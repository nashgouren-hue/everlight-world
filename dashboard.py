from flask import Flask, render_template, request, redirect, url_for
import json
import os
import requests

app = Flask(__name__)

SETTINGS_FILE = "welcome_settings.json"


# ==================================================
# SETTINGS
# ==================================================

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

        # Profile images
        "image_kurocat": "",
        "image_nash": "",
        "image_haru": "",
        "image_louise": "",
        "image_everlight": "",

        # Discord notification
        "notif_title": "🔴 {creator} IS LIVE!",
        "notif_message": (
            "✨ {creator} sedang LIVE di TikTok! "
            "Ayo mampir dan ramaikan live-nya!"
        ),
        "notif_mention": "none",
        "notif_banner": "",
        "notif_color": "#ff3355",
        "notif_button": "🔴 Watch Stream",

        # Welcome message
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

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            saved_settings = json.load(file)

        # Ini penting supaya setting baru tetap muncul
        # walaupun JSON lama belum punya key tersebut.
        default_settings.update(saved_settings)
        return default_settings

    except (json.JSONDecodeError, OSError):
        return default_settings


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            settings,
            file,
            indent=4,
            ensure_ascii=False
        )


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():
    return render_template("dashboard.html")


# ==================================================
# WELCOME SETTINGS
# ==================================================

@app.route("/welcome", methods=["GET", "POST"])
def welcome():
    settings = load_settings()

    if request.method == "POST":
        # Jangan membuat dict baru karena itu bisa
        # menghapus setting TikTok yang sudah tersimpan.
        settings["avatar_size"] = int(request.form["avatar_size"])
        settings["avatar_x"] = int(request.form["avatar_x"])
        settings["avatar_y"] = int(request.form["avatar_y"])
        settings["username_size"] = int(request.form["username_size"])
        settings["username_y"] = int(request.form["username_y"])
        settings["welcome_channel"] = request.form["welcome_channel"]
        settings["auto_role"] = request.form["auto_role"]
        settings["message"] = request.form["message"]

        save_settings(settings)

        return redirect(
            url_for(
                "welcome",
                saved="1"
            )
        )

    return render_template(
        "welcome.html",
        settings=settings
    )


# ==================================================
# AUTO ROLE SETTINGS
# ==================================================

@app.route("/autorole", methods=["GET", "POST"])
def autorole():
    settings = load_settings()

    if request.method == "POST":
        settings["auto_role"] = request.form["auto_role"]

        save_settings(settings)

        return redirect(
            url_for(
                "autorole",
                saved="1"
            )
        )

    return render_template(
        "autorole.html",
        settings=settings
    )


# ==================================================
# TIKTOK SETTINGS
# ==================================================

@app.route("/tiktok", methods=["GET", "POST"])
def tiktok():
    settings = load_settings()

    if request.method == "POST":
        settings["tiktok_channel"] = request.form.get(
            "tiktok_channel",
            "livenotification"
        )

        # Kurocat
        settings["tiktok_kurocat"] = request.form.get(
            "tiktok_kurocat",
            "@kurocatkurimu"
        )
        settings["enable_kurocat"] = (
            "enable_kurocat" in request.form
        )

        # Nash
        settings["tiktok_nash"] = request.form.get(
            "tiktok_nash",
            "@nashgouren_"
        )
        settings["enable_nash"] = (
            "enable_nash" in request.form
        )

        # Haru
        settings["tiktok_haru"] = request.form.get(
            "tiktok_haru",
            "@hiharuhere"
        )
        settings["enable_haru"] = (
            "enable_haru" in request.form
        )

        # Louise
        settings["tiktok_louise"] = request.form.get(
            "tiktok_louise",
            "@louiegospellvt"
        )
        settings["enable_louise"] = (
            "enable_louise" in request.form
        )

        # Everlight
        settings["tiktok_everlight"] = request.form.get(
            "tiktok_everlight",
            "@everlightvirtual"
        )
        settings["enable_everlight"] = (
            "enable_everlight" in request.form
        )

        settings["tiktok_message"] = request.form.get(
            "tiktok_message",
            "🔴 {creator} sedang LIVE di TikTok!"
        )

        # Profile Image URLs
        settings["image_kurocat"] = request.form.get(
            "image_kurocat",
            ""
        ).strip()

        settings["image_nash"] = request.form.get(
            "image_nash",
            ""
        ).strip()

        settings["image_haru"] = request.form.get(
            "image_haru",
            ""
        ).strip()

        settings["image_louise"] = request.form.get(
            "image_louise",
            ""
        ).strip()

        settings["image_everlight"] = request.form.get(
            "image_everlight",
            ""
        ).strip()

        # Notification appearance
        settings["notif_title"] = request.form.get(
            "notif_title",
            "🔴 {creator} IS LIVE!"
        )

        settings["notif_message"] = request.form.get(
            "notif_message",
            "✨ {creator} sedang LIVE di TikTok!"
        )

        settings["notif_mention"] = request.form.get(
            "notif_mention",
            "none"
        )

        settings["notif_banner"] = request.form.get(
            "notif_banner",
            ""
        ).strip()

        settings["notif_color"] = request.form.get(
            "notif_color",
            "#ff3355"
        )

        settings["notif_button"] = request.form.get(
            "notif_button",
            "🔴 Watch Stream"
        )

        save_settings(settings)

        return redirect(
            url_for(
                "tiktok",
                saved="1"
            )
        )

    return render_template(
        "tiktok.html",
        settings=settings
    )


# ==================================================
# TEST TIKTOK DISCORD NOTIFICATION
# ==================================================

@app.route("/tiktok/test", methods=["POST"])
def test_tiktok_notification():
    webhook_url = os.environ.get(
        "DISCORD_LIVE_WEBHOOK"
    )

    if not webhook_url:
        return (
            "DISCORD_LIVE_WEBHOOK belum diatur.",
            500
        )

    # Untuk tombol Test Notification,
    # sementara menggunakan Kurocat sebagai contoh.
    creator = "Kurocat Kurimu"

    live_url = (
        "https://www.tiktok.com/"
        "@kurocatkurimu/live"
    )

    # ----------------------------------------------
    # TITLE
    # ----------------------------------------------

    title = request.form.get(
        "notif_title",
        "🔴 {creator} IS LIVE!"
    )

    title = title.replace(
        "{creator}",
        creator
    )

    # ----------------------------------------------
    # MESSAGE
    # ----------------------------------------------

    message = request.form.get(
        "notif_message",
        (
            "✨ {creator} sedang LIVE di TikTok! "
            "Ayo mampir dan ramaikan live-nya!"
        )
    )

    message = (
        message
        .replace("{creator}", creator)
        .replace("{url}", live_url)
    )

    # ----------------------------------------------
    # IMAGE / BUTTON / COLOR
    # ----------------------------------------------

    banner = request.form.get(
        "notif_banner",
        ""
    ).strip()

    profile_image = request.form.get(
        "image_kurocat",
        ""
    ).strip()

    button_text = request.form.get(
        "notif_button",
        "🔴 Watch Stream"
    ).strip()

    if not button_text:
        button_text = "🔴 Watch Stream"

    color_hex = request.form.get(
        "notif_color",
        "#ff3355"
    )

    color_hex = color_hex.lstrip("#")

    try:
        color = int(
            color_hex,
            16
        )
    except ValueError:
        color = 0xFF3355

    # ----------------------------------------------
    # MENTION
    # ----------------------------------------------

    mention_setting = request.form.get(
        "notif_mention",
        "none"
    )

    if mention_setting == "everyone":
        mention = "@everyone"

    elif mention_setting == "here":
        mention = "@here"

    else:
        mention = ""

    # ----------------------------------------------
    # TEXT ABOVE EMBED
    # ----------------------------------------------

    if mention:
        content = (
            f"{mention}\n"
            f"HI {mention} "
            f"**{creator} | Everlight VT** "
            f"Live on TikTok!\n"
            f"{live_url}"
        )
    else:
        content = (
            f"**{creator} | Everlight VT** "
            f"Live on TikTok!\n"
            f"{live_url}"
        )

    # ----------------------------------------------
    # DISCORD EMBED
    # ----------------------------------------------

    embed = {
        "title": title,
        "description": message,
        "color": color,
        "footer": {
            "text": (
                "EVERLIGHT VIRTUAL "
                "• TEST NOTIFICATION"
            )
        }
    }

    # Profile image diprioritaskan.
    # Kalau kosong, gunakan banner.
    if profile_image:
        embed["image"] = {
            "url": profile_image
        }

    elif banner:
        embed["image"] = {
            "url": banner
        }

    # ----------------------------------------------
    # WATCH STREAM BUTTON
    # ----------------------------------------------

    components = [
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
    ]

    # ----------------------------------------------
    # ALLOWED MENTIONS
    # ----------------------------------------------

    if mention_setting == "everyone":
        allowed_mentions = {
            "parse": ["everyone"]
        }

    else:
        allowed_mentions = {
            "parse": []
        }

    # ----------------------------------------------
    # WEBHOOK PAYLOAD
    # ----------------------------------------------

    payload = {
        "content": content,
        "embeds": [embed],
        "components": components,
        "allowed_mentions": allowed_mentions
    }

    # ----------------------------------------------
    # SEND TO DISCORD
    # ----------------------------------------------

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )

    except requests.RequestException as error:
        return (
            f"Gagal terhubung ke Discord webhook: {error}",
            500
        )

    if response.status_code not in (
        200,
        204
    ):
        return (
            "Gagal mengirim test notification: "
            f"{response.text}",
            500
        )

    return redirect(
        url_for(
            "tiktok",
            tested="1"
        )
    )


# ==================================================
# START DASHBOARD
# ==================================================

if __name__ == "__main__":
    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )