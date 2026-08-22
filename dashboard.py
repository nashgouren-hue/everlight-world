from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import requests


app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "everlight-dev-secret"
)

TIKTOK_CLIENT_KEY = os.environ.get("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET", "")

TIKTOK_REDIRECT_URI = (
    "https://everlight-world-production.up.railway.app/tiktok/callback"
)

@app.route("/tiktok/videos")
def tiktok_videos():

    if not os.path.exists(TIKTOK_TOKEN_FILE):
        return (
            "Belum ada akun TikTok yang terhubung. "
            "Login lewat /tiktok/login dulu.",
            400
        )

    with open(TIKTOK_TOKEN_FILE, "r", encoding="utf-8") as f:
        token_data = json.load(f)

    access_token = token_data.get("access_token")

    if not access_token:
        return "TikTok access token tidak ditemukan.", 400

    response = requests.post(
        "https://open.tiktokapis.com/v2/video/list/",
        params={
            "fields": (
                "id,title,video_description,"
                "duration,cover_image_url,"
                "share_url,create_time"
            )
        },
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "max_count": 10
        },
        timeout=20
    )

    try:
        data = response.json()
    except ValueError:
        return "TikTok memberikan response yang tidak valid.", 500

    if response.status_code != 200:
        return {
            "status": "error",
            "tiktok_response": data
        }, response.status_code

    videos = data.get("data", {}).get("videos", [])

    # Jangan tampilkan access token ke browser.
    return {
        "status": "success",
        "video_count": len(videos),
        "videos": videos
    }

TIKTOK_TOKEN_FILE = "tiktok_tokens.json"


def save_tiktok_token(token_data):
    with open(TIKTOK_TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=4)

SETTINGS_FILE = "welcome_settings.json"


# ==================================================
# SETTINGS
# ==================================================

def load_settings():
    default_settings = {
        # Welcome
        "avatar_size": 180,
        "avatar_x": 510,
        "avatar_y": 25,
        "username_size": 38,
        "username_y": 215,
        "welcome_channel": "welcome",
        "auto_role": "moonwalker",

        # Moderation
        "mod_log_channel": "mod-logs",
        "mod_dm_warn": True,
        "mod_dm_kick": True,
        "mod_dm_ban": True,
        "mod_dm_timeout": True,

        # TikTok Live
        "tiktok_channel": "livenotification",

        # TikTok Accounts
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

        # TikTok Profile Images
        "image_kurocat": "",
        "image_nash": "",
        "image_haru": "",
        "image_louise": "",
        "image_everlight": "",

        # TikTok Live Notification Appearance
        "notif_title": "🔴 {creator} IS LIVE!",
        "notif_message": (
            "✨ {creator} sedang LIVE di TikTok! "
            "Ayo mampir dan ramaikan live-nya!"
        ),
        "notif_mention": "none",
        "notif_banner": "",
        "notif_color": "#ff3355",
        "notif_button": "🔴 Watch Stream",

        # ==================================================
        # TikTok Post Notification
        # ==================================================

        # Post ON/OFF per account
        "enable_post_kurocat": True,
        "enable_post_nash": True,
        "enable_post_haru": True,
        "enable_post_louise": True,
        "enable_post_everlight": True,

        # Discord destination channel per account
        "post_channel_kurocat": "user-news",
        "post_channel_nash": "user-news",
        "post_channel_haru": "user-news",
        "post_channel_louise": "user-news",
        "post_channel_everlight": "user-news",

        # Post Notification Appearance
        "post_notif_title": "🎬 {creator} NEW POST!",
        "post_notif_message": (
            "✨ {creator} baru saja mengupload "
            "postingan baru di TikTok!"
        ),
        "post_notif_mention": "none",
        "post_notif_color": "#8b5cf6",
        "post_notif_button": "🎬 View Post",

        # General Bot Settings
        "bot_status": "Everlight Virtual",
        "bot_activity_type": "watching",
        "command_prefix": "!",

        # Welcome Message
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
        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            saved_settings = json.load(file)

        default_settings.update(saved_settings)

    except (json.JSONDecodeError, OSError) as error:
        print(f"Gagal membaca settings: {error}")

    return default_settings


def save_settings(settings):
    with open(
        SETTINGS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
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
        settings["avatar_size"] = int(
            request.form["avatar_size"]
        )

        settings["avatar_x"] = int(
            request.form["avatar_x"]
        )

        settings["avatar_y"] = int(
            request.form["avatar_y"]
        )

        settings["username_size"] = int(
            request.form["username_size"]
        )

        settings["username_y"] = int(
            request.form["username_y"]
        )

        settings["welcome_channel"] = request.form[
            "welcome_channel"
        ]

        settings["auto_role"] = request.form[
            "auto_role"
        ]

        settings["message"] = request.form[
            "message"
        ]

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
        settings["auto_role"] = request.form.get(
            "auto_role",
            "moonwalker"
        )

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
# MODERATION SETTINGS
# ==================================================

@app.route("/moderation", methods=["GET", "POST"])
def moderation():
    settings = load_settings()

    if request.method == "POST":
        settings["mod_log_channel"] = request.form.get(
            "mod_log_channel",
            "mod-logs"
        )

        settings["mod_dm_warn"] = (
            "mod_dm_warn" in request.form
        )

        settings["mod_dm_kick"] = (
            "mod_dm_kick" in request.form
        )

        settings["mod_dm_ban"] = (
            "mod_dm_ban" in request.form
        )

        settings["mod_dm_timeout"] = (
            "mod_dm_timeout" in request.form
        )

        save_settings(settings)

        return redirect(
            url_for(
                "moderation",
                saved="1"
            )
        )

    return render_template(
        "moderation.html",
        settings=settings
    )


# ==================================================
# TIKTOK SETTINGS
# ==================================================

@app.route("/tiktok", methods=["GET", "POST"])
def tiktok():
    settings = load_settings()

    if request.method == "POST":

        # ==================================================
        # LIVE SETTINGS
        # ==================================================

        settings["tiktok_channel"] = request.form.get(
            "tiktok_channel",
            "livenotification"
        ).strip()

        # Kurocat
        settings["tiktok_kurocat"] = request.form.get(
            "tiktok_kurocat",
            "@kurocatkurimu"
        ).strip()

        settings["enable_kurocat"] = (
            "enable_kurocat" in request.form
        )

        # Nash
        settings["tiktok_nash"] = request.form.get(
            "tiktok_nash",
            "@nashgouren_"
        ).strip()

        settings["enable_nash"] = (
            "enable_nash" in request.form
        )

        # Haru
        settings["tiktok_haru"] = request.form.get(
            "tiktok_haru",
            "@hiharuhere"
        ).strip()

        settings["enable_haru"] = (
            "enable_haru" in request.form
        )

        # Louise
        settings["tiktok_louise"] = request.form.get(
            "tiktok_louise",
            "@louiegospellvt"
        ).strip()

        settings["enable_louise"] = (
            "enable_louise" in request.form
        )

        # Everlight
        settings["tiktok_everlight"] = request.form.get(
            "tiktok_everlight",
            "@everlightvirtual"
        ).strip()

        settings["enable_everlight"] = (
            "enable_everlight" in request.form
        )

        settings["tiktok_message"] = request.form.get(
            "tiktok_message",
            "🔴 {creator} sedang LIVE di TikTok!"
        )

        # ==================================================
        # PROFILE IMAGES
        # ==================================================

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

        # ==================================================
        # LIVE NOTIFICATION APPEARANCE
        # ==================================================

        settings["notif_title"] = request.form.get(
            "notif_title",
            "🔴 {creator} IS LIVE!"
        )

        settings["notif_message"] = request.form.get(
            "notif_message",
            (
                "✨ {creator} sedang LIVE di TikTok! "
                "Ayo mampir dan ramaikan live-nya!"
            )
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

        # ==================================================
        # POST ON/OFF
        # ==================================================

        settings["enable_post_kurocat"] = (
            "enable_post_kurocat" in request.form
        )

        settings["enable_post_nash"] = (
            "enable_post_nash" in request.form
        )

        settings["enable_post_haru"] = (
            "enable_post_haru" in request.form
        )

        settings["enable_post_louise"] = (
            "enable_post_louise" in request.form
        )

        settings["enable_post_everlight"] = (
            "enable_post_everlight" in request.form
        )

        # ==================================================
        # POST DESTINATION CHANNEL PER ACCOUNT
        # ==================================================

        settings["post_channel_kurocat"] = request.form.get(
            "post_channel_kurocat",
            "user-news"
        ).strip()

        settings["post_channel_nash"] = request.form.get(
            "post_channel_nash",
            "user-news"
        ).strip()

        settings["post_channel_haru"] = request.form.get(
            "post_channel_haru",
            "user-news"
        ).strip()

        settings["post_channel_louise"] = request.form.get(
            "post_channel_louise",
            "user-news"
        ).strip()

        settings["post_channel_everlight"] = request.form.get(
            "post_channel_everlight",
            "user-news"
        ).strip()

        # ==================================================
        # POST NOTIFICATION APPEARANCE
        # ==================================================

        settings["post_notif_title"] = request.form.get(
            "post_notif_title",
            "🎬 {creator} NEW POST!"
        )

        settings["post_notif_message"] = request.form.get(
            "post_notif_message",
            (
                "✨ {creator} baru saja mengupload "
                "postingan baru di TikTok!"
            )
        )

        settings["post_notif_mention"] = request.form.get(
            "post_notif_mention",
            "none"
        )

        settings["post_notif_color"] = request.form.get(
            "post_notif_color",
            "#8b5cf6"
        )

        settings["post_notif_button"] = request.form.get(
            "post_notif_button",
            "🎬 View Post"
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
# TEST TIKTOK LIVE NOTIFICATION
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

    creator = "Kurocat Kurimu"
    live_url = (
        "https://www.tiktok.com/"
        "@kurocatkurimu/live"
    )

    title = request.form.get(
        "notif_title",
        "🔴 {creator} IS LIVE!"
    ).replace(
        "{creator}",
        creator
    )

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
    ).lstrip("#")

    try:
        color = int(color_hex, 16)

    except ValueError:
        color = 0xFF3355

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

        "embeds": [
            embed
        ],

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
            "parse": (
                ["everyone"]
                if mention_setting == "everyone"
                else []
            )
        }
    }

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
# TEST TIKTOK POST NOTIFICATION
# ==================================================

@app.route("/tiktok/test-post", methods=["POST"])
def test_tiktok_post_notification():
    """
    Test sementara menggunakan Kurocat.
    Nanti pengiriman otomatis tidak bergantung pada
    satu channel global lagi.
    """

    webhook_url = os.environ.get(
        "DISCORD_POST_WEBHOOK"
    )

    if not webhook_url:
        return (
            "DISCORD_POST_WEBHOOK belum diatur.",
            500
        )

    creator = "Kurocat Kurimu"

    post_url = (
        "https://www.tiktok.com/"
        "@kurocatkurimu"
    )

    selected_channel = request.form.get(
        "post_channel_kurocat",
        "user-news"
    ).strip()

    title = request.form.get(
        "post_notif_title",
        "🎬 {creator} NEW POST!"
    ).replace(
        "{creator}",
        creator
    )

    message = request.form.get(
        "post_notif_message",
        "✨ {creator} baru saja mengupload postingan baru di TikTok!"
    )

    message = (
        message
        .replace("{creator}", creator)
        .replace("{url}", post_url)
    )

    button_text = request.form.get(
        "post_notif_button",
        "🎬 View Post"
    ).strip()

    if not button_text:
        button_text = "🎬 View Post"

    color_hex = request.form.get(
        "post_notif_color",
        "#8b5cf6"
    ).lstrip("#")

    try:
        color = int(
            color_hex,
            16
        )

    except ValueError:
        color = 0x8B5CF6

    mention_setting = request.form.get(
        "post_notif_mention",
        "none"
    )

    if mention_setting == "everyone":
        mention = "@everyone"

    elif mention_setting == "here":
        mention = "@here"

    else:
        mention = ""

    if mention:
        content = (
            f"{mention}\n"
            f"**{creator} | Everlight VT** "
            f"just uploaded a new TikTok!\n"
            f"{post_url}"
        )

    else:
        content = (
            f"**{creator} | Everlight VT** "
            f"just uploaded a new TikTok!\n"
            f"{post_url}"
        )

    embed = {
        "title": title,
        "description": message,
        "color": color,
        "url": post_url,

        "footer": {
            "text": (
                "EVERLIGHT VIRTUAL "
                f"• TARGET #{selected_channel}"
            )
        }
    }

    profile_image = request.form.get(
        "image_kurocat",
        ""
    ).strip()

    if profile_image:
        embed["image"] = {
            "url": profile_image
        }

    payload = {
        "content": content,

        "embeds": [
            embed
        ],

        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 5,
                        "label": button_text,
                        "url": post_url
                    }
                ]
            }
        ],

        "allowed_mentions": {
            "parse": (
                ["everyone"]
                if mention_setting == "everyone"
                else []
            )
        }
    }

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
            "Gagal mengirim test POST notification: "
            f"{response.text}",
            500
        )

    return redirect(
        url_for(
            "tiktok",
            tested_post="1"
        )
    )


# ==================================================
# GENERAL SETTINGS
# ==================================================

@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    settings = load_settings()

    if request.method == "POST":
        settings["bot_status"] = request.form.get(
            "bot_status",
            "Everlight Virtual"
        )

        settings["bot_activity_type"] = request.form.get(
            "bot_activity_type",
            "watching"
        )

        settings["command_prefix"] = request.form.get(
            "command_prefix",
            "!"
        )

        save_settings(settings)

        return redirect(
            url_for(
                "settings_page",
                saved="1"
            )
        )

    return render_template(
        "settings.html",
        settings=settings
    )

# ==================================================
# TIKTOK LOGIN KIT
# ==================================================

@app.route("/tiktok/login")
def tiktok_login():

    if not TIKTOK_CLIENT_KEY:
        return "TIKTOK_CLIENT_KEY belum diatur di Railway.", 500

    # Token acak untuk melindungi proses login
    state = os.urandom(24).hex()
    session["tiktok_oauth_state"] = state

    params = {
        "client_key": TIKTOK_CLIENT_KEY,
        "response_type": "code",
        "scope": "user.info.basic,video.list",
        "redirect_uri": TIKTOK_REDIRECT_URI,
        "state": state
    }

    from urllib.parse import urlencode

    authorization_url = (
        "https://www.tiktok.com/v2/auth/authorize/?"
        + urlencode(params)
    )

    return redirect(authorization_url)


@app.route("/tiktok/callback")
def tiktok_callback():

    error = request.args.get("error")

    if error:
        error_description = request.args.get(
            "error_description",
            "TikTok authorization failed."
        )

        return (
            f"TikTok authorization error: "
            f"{error_description}",
            400
        )

    code = request.args.get("code")
    returned_state = request.args.get("state")

    saved_state = session.pop(
        "tiktok_oauth_state",
        None
    )

    if not code:
        return "Authorization code TikTok tidak ditemukan.", 400

    if (
        not returned_state
        or not saved_state
        or returned_state != saved_state
    ):
        return "OAuth state TikTok tidak valid.", 400

    if not TIKTOK_CLIENT_KEY or not TIKTOK_CLIENT_SECRET:
        return (
            "TikTok Client Key / Client Secret "
            "belum diatur di Railway.",
            500
        )

    token_response = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={
            "Content-Type":
            "application/x-www-form-urlencoded"
        },
        data={
            "client_key": TIKTOK_CLIENT_KEY,
            "client_secret": TIKTOK_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": TIKTOK_REDIRECT_URI
        },
        timeout=20
    )

    try:
        token_data = token_response.json()

    except ValueError:
        return (
            "TikTok memberikan response token "
            "yang tidak valid.",
            500
        )

    if token_response.status_code != 200:
        return (
            "Gagal mendapatkan TikTok access token: "
            f"{token_data}",
            400
        )

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    open_id = token_data.get("open_id")
    granted_scope = token_data.get("scope", "")

    if not access_token:
        return (
            "TikTok tidak memberikan access token: "
            f"{token_data}",
            400
        )

    save_tiktok_token({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "open_id": open_id,
        "scope": granted_scope,
        "expires_in": token_data.get("expires_in"),
        "refresh_expires_in": token_data.get("refresh_expires_in")
    })

    print("✅ TikTok account connected.")
    print(f"Open ID: {open_id}")
    print(f"Scopes: {granted_scope}")

    # SEMENTARA untuk tahap testing.
    # Jangan menampilkan access_token atau refresh_token
    # ke halaman/browser/log.
    session["tiktok_connected"] = True
    session["tiktok_open_id"] = open_id
    session["tiktok_scope"] = granted_scope

    return redirect(
        url_for(
            "tiktok",
            connected="1"
        )
    )

# ==================================================
# LEGAL PAGES
# ==================================================

@app.route("/terms")
def terms():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Terms of Service - Everlight Bot</title>
        <style>
            body {
                background: #0b0b14;
                color: #eeeeff;
                font-family: Arial, sans-serif;
                max-width: 850px;
                margin: 0 auto;
                padding: 50px 25px;
                line-height: 1.7;
            }
            h1, h2 {
                color: white;
            }
            a {
                color: #9d8cff;
            }
        </style>
    </head>

    <body>

        <h1>Everlight Bot - Terms of Service</h1>

        <p>Last updated: August 22, 2026</p>

        <p>
            Everlight Bot is a Discord integration operated for
            Everlight Virtual. The service provides community management
            features and notifications related to authorized TikTok
            creator accounts.
        </p>

        <h2>TikTok Integration</h2>

        <p>
            Users may voluntarily connect their TikTok account through
            TikTok Login Kit. Everlight Bot may access information
            authorized by the user, including basic account information
            and public video information.
        </p>

        <h2>Use of the Service</h2>

        <p>
            TikTok information accessed through the service is used to
            provide Everlight Virtual Discord features, including
            notifications when an authorized creator publishes new
            public TikTok content.
        </p>

        <h2>User Authorization</h2>

        <p>
            Users are responsible for connecting only TikTok accounts
            they are authorized to use. Access to TikTok information
            depends on permissions granted by the TikTok account holder.
        </p>

        <h2>Availability</h2>

        <p>
            Everlight Bot may be modified, temporarily unavailable,
            or discontinued at any time.
        </p>

        <h2>Changes</h2>

        <p>
            These Terms may be updated when features or integrations
            change.
        </p>

        <p>
            <a href="/">Return to Everlight Bot</a>
        </p>

    </body>
    </html>
    """


@app.route("/privacy")
def privacy():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Privacy Policy - Everlight Bot</title>
        <style>
            body {
                background: #0b0b14;
                color: #eeeeff;
                font-family: Arial, sans-serif;
                max-width: 850px;
                margin: 0 auto;
                padding: 50px 25px;
                line-height: 1.7;
            }
            h1, h2 {
                color: white;
            }
            a {
                color: #9d8cff;
            }
        </style>
    </head>

    <body>

        <h1>Everlight Bot - Privacy Policy</h1>

        <p>Last updated: August 22, 2026</p>

        <p>
            This Privacy Policy explains how Everlight Bot uses
            information when a user connects a TikTok account.
        </p>

        <h2>Information We Access</h2>

        <p>
            With user authorization, Everlight Bot may access basic
            TikTok profile information and information about the user's
            public TikTok videos through TikTok's official APIs.
        </p>

        <h2>How Information Is Used</h2>

        <p>
            TikTok information is used to identify authorized creator
            accounts and provide Discord notifications when new public
            TikTok content is published.
        </p>

        <h2>Data Sharing</h2>

        <p>
            Everlight Bot does not sell TikTok user information.
            Information obtained through TikTok is used only for
            functionality associated with Everlight Virtual services.
        </p>

        <h2>Authorization and Access</h2>

        <p>
            TikTok access is provided only after the account holder
            authorizes Everlight Bot through TikTok Login Kit.
        </p>

        <h2>Data Retention</h2>

        <p>
            Information is retained only as necessary to operate the
            connected TikTok and Discord notification features.
        </p>

        <h2>Changes to This Policy</h2>

        <p>
            This Privacy Policy may be updated when Everlight Bot
            features or integrations change.
        </p>

        <p>
            <a href="/">Return to Everlight Bot</a>
        </p>

    </body>
    </html>
    """

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