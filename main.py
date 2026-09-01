import os
import json
import urllib.parse
import xml.etree.ElementTree as ET
import discord
import aiohttp
import io
import sqlite3

from discord import app_commands
from discord.ext import tasks
from TikTokLive import TikTokLiveClient
from PIL import Image, ImageDraw, ImageFont
from aiohttp import web


# =====================================================
# CONFIG
# =====================================================

TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

YOUTUBE_CHANNELS = {
    "kurocat": {
        "name": "Kurocat Kurimu",
        "channel_id": "UChOFqp5RjGTt8FZZFvmxtsg"
    }
}

# =========================================================
# TIKTOK FOLLOWER MILESTONE
# =========================================================

FOLLOWER_MILESTONE_STEP = 500

TIKTOK_FOLLOWER_MILESTONES = {
    "kurocatkurimu": {
        "name": "Kurocat Kurimu",
        "channel_id": 1513404982471164034,
        "last_milestone": 0,
        "message": (
            "🎉 CONGRATULATIONS! 🎉\n\n"
            "Selamat kepada **{name}** yang telah mencapai "
            "**{followers:,} FOLLOWERS**! ✨\n\n"
            "Terima kasih atas semua dukungannya!\n"
            "— EVERLIGHT VIRTUAL"
        )
    },

    "nashgouren_": {
        "name": "Nash Gouren",
        "channel_id": 1513405816714170408,
        "last_milestone": 0,
        "message": (
            "🎉 CONGRATULATIONS! 🎉\n\n"
            "Selamat kepada **{name}** yang telah mencapai "
            "**{followers:,} FOLLOWERS**! ✨\n\n"
            "Terima kasih atas semua dukungannya!\n"
            "— EVERLIGHT VIRTUAL"
        )
    },

    "hiharuhere": {
        "name": "Ikkito Haru",
        "channel_id": 1516754539166957568,
        "last_milestone": 0,
        "message": (
            "🎉 CONGRATULATIONS! 🎉\n\n"
            "Selamat kepada **{name}** yang telah mencapai "
            "**{followers:,} FOLLOWERS**! ✨\n\n"
            "Terima kasih atas semua dukungannya!\n"
            "— EVERLIGHT VIRTUAL"
        )
    },

    "louiegospellvt": {
        "name": "Louise Gospell",
        "channel_id": 1516756829412134942,
        "last_milestone": 0,
        "message": (
            "🎉 CONGRATULATIONS! 🎉\n\n"
            "Selamat kepada **{name}** yang telah mencapai "
            "**{followers:,} FOLLOWERS**! ✨\n\n"
            "Terima kasih atas semua dukungannya!\n"
            "— EVERLIGHT VIRTUAL"
        )
    },

    "everlightvirtual": {
        "name": "Everlight Virtual",
        "channel_id": 1514097716995821638,
        "last_milestone": 0,
        "message": (
            "🎉 CONGRATULATIONS! 🎉\n\n"
            "Selamat kepada **{name}** yang telah mencapai "
            "**{followers:,} FOLLOWERS**! ✨\n\n"
            "Terima kasih atas semua dukungannya!\n"
            "— EVERLIGHT VIRTUAL"
        )
    }
}

FOLLOWER_MILESTONE_FILE = "follower_milestones.json"


def load_follower_milestones():
    try:
        with open(FOLLOWER_MILESTONE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_follower_milestones(data):
    try:
        with open(FOLLOWER_MILESTONE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(
            f"ERROR save follower milestone: {e}",
            flush=True
        )


follower_milestone_data = load_follower_milestones()

async def get_tiktok_follower_count(username):
    url = f"https://www.tiktok.com/@{username}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:

                if response.status != 200:
                    print(
                        f"TIKTOK FOLLOWER ERROR @{username}: "
                        f"HTTP {response.status}",
                        flush=True
                    )
                    return None

                html = await response.text()

                import re

                match = re.search(
                    r'"followerCount":(\d+)',
                    html
                )

                if not match:
                    print(
                        f"TIKTOK FOLLOWER: followerCount "
                        f"tidak ditemukan @{username}",
                        flush=True
                    )
                    return None

                followers = int(match.group(1))

                print(
                    f"TIKTOK FOLLOWER @{username}: {followers}",
                    flush=True
                )

                return followers

    except Exception as e:
        print(
            f"TIKTOK FOLLOWER ERROR @{username}: {e}",
            flush=True
        )
        return None

# Channel notifikai Youtube
YOUTUBE_LIVE_CHANNEL_ID = 1513414157897043998
YOUTUBE_POST_CHANNEL_ID = 1513404982471164034

# Channel notifikasi LIVE TikTok
LIVE_CHANNEL_ID = 1513414157897043998

# Channel notifikasi POST TikTok
TIKTOK_POST_CHANNELS = {
    "kurocatkurimu": 1513404982471164034,
    "nashgouren_": 1513405816714170408,
    "hiharuhere": 1516754539166957568,
    "louiegospellvt": 1516756829412134942,
    "everlightvirtual": 1513443800327000117,
}

TIKTOK_LIVE_ACCOUNTS = [
    "kurocatkurimu",
    "nashgouren_",
    "hiharuhere",
    "louiegospellvt",
    "everlightvirtual",
]

TIKTOK_CREATORS = {
    "kurocatkurimu": {
        "name": "Kurocat Kurimu",
        "image": ""
    },
    "nashgouren_": {
        "name": "Nash Gouren",
        "image": ""
    },
    "hiharuhere": {
        "name": "Ikkito Haru",
        "image": ""
    },
    "louiegospellvt": {
        "name": "Louise Gospell",
        "image": ""
    },
    "everlightvirtual": {
        "name": "Everlight Virtual",
        "image": ""
    }
}


# =====================================================
# DATABASE
# =====================================================

db = sqlite3.connect("warnings.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

db.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS reaction_role_messages (
    message_id INTEGER PRIMARY KEY,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reaction_role_items (
    message_id INTEGER NOT NULL,
    emoji TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    description TEXT DEFAULT '',
    PRIMARY KEY (message_id, emoji)
)
""")

db.commit()

# =====================================================
# DISCORD BOT
# =====================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class EverlightBot(discord.Client):

    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.web_runner = None

    async def setup_hook(self):
        await self.tree.sync()
        self.web_runner = await start_web_server()


bot = EverlightBot()

def get_reaction_role(message_id, emoji):
    cursor.execute(
        """
        SELECT role_id
        FROM reaction_role_items
        WHERE message_id = ? AND emoji = ?
        """,
        (
            message_id,
            emoji
        )
    )

    result = cursor.fetchone()

    if result is None:
        return None

    return result[0]


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    role_id = get_reaction_role(
        payload.message_id,
        str(payload.emoji)
    )

    if role_id is None:
        return

    guild = bot.get_guild(payload.guild_id)

    if guild is None:
        return

    role = guild.get_role(role_id)

    if role is None:
        return

    member = payload.member

    if member is None:
        try:
            member = await guild.fetch_member(
                payload.user_id
            )
        except discord.NotFound:
            return

    try:
        await member.add_roles(
            role,
            reason="Everlight Reaction Role"
        )
    except discord.Forbidden:
        print(
            f"Gagal memberi role {role.name}. "
            "Periksa posisi role dan permission bot.",
            flush=True
        )


@bot.event
async def on_raw_reaction_remove(payload):
    role_id = get_reaction_role(
        payload.message_id,
        str(payload.emoji)
    )

    if role_id is None:
        return

    guild = bot.get_guild(payload.guild_id)

    if guild is None:
        return

    role = guild.get_role(role_id)

    if role is None:
        return

    try:
        member = await guild.fetch_member(
            payload.user_id
        )
    except discord.NotFound:
        return

    if member.bot:
        return

    try:
        await member.remove_roles(
            role,
            reason="Everlight Reaction Role removed"
        )
    except discord.Forbidden:
        print(
            f"Gagal mencabut role {role.name}. "
            "Periksa posisi role dan permission bot.",
            flush=True
        )

# =====================================================
# WELCOME IMAGE
# =====================================================

async def create_welcome_image(member):

    template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "welcome.png"
    )

    image = Image.open(template_path).convert("RGBA")

    avatar_bytes = await member.display_avatar.replace(
        size=256,
        format="png"
    ).read()

    avatar = Image.open(
        io.BytesIO(avatar_bytes)
    ).convert("RGBA")

    avatar_size = 300
    avatar = avatar.resize((avatar_size, avatar_size))

    mask = Image.new(
        "L",
        (avatar_size, avatar_size),
        0
    )

    mask_draw = ImageDraw.Draw(mask)

    mask_draw.ellipse(
        (0, 0, avatar_size, avatar_size),
        fill=255
    )

    avatar_x = (image.width - avatar_size) // 2
    avatar_y = 35

    image.paste(
        avatar,
        (avatar_x, avatar_y),
        mask
    )

    draw = ImageDraw.Draw(image)

    nama = member.display_name

    try:
        font_nama = ImageFont.truetype(
            "arialbd.ttf",
            100
        )
    except Exception:
        font_nama = ImageFont.load_default()

    bbox = draw.textbbox(
        (0, 0),
        nama,
        font=font_nama
    )

    text_width = bbox[2] - bbox[0]

    nama_x = (
        image.width - text_width
    ) // 2

    nama_y = 410

    draw.text(
        (nama_x, nama_y),
        nama,
        font=font_nama,
        fill="white",
        stroke_width=4,
        stroke_fill="#4a3c3c"
    )

    output = io.BytesIO()

    image.save(
        output,
        format="PNG"
    )

    output.seek(0)

    return discord.File(
        output,
        filename="welcome.png"
    )


# =====================================================
# TIKTOK LIVE CHECKER
# =====================================================

live_status = {}


@tasks.loop(seconds=60)
async def live_checker():

    channel = bot.get_channel(
        LIVE_CHANNEL_ID
    )

    if channel is None:
        print(
            "ERROR: Channel LIVE Discord tidak ditemukan.",
            flush=True
        )
        return

    for username in TIKTOK_LIVE_ACCOUNTS:

        try:

            client = TikTokLiveClient(
                unique_id=f"@{username}"
            )

            is_live = await client.is_live()

            sebelumnya_live = live_status.get(
                username,
                False
            )

            print(
                f"TikTok @{username} | LIVE: {is_live}",
                flush=True
            )

            if is_live and not sebelumnya_live:

                creator_info = TIKTOK_CREATORS.get(
                    username,
                    {
                        "name": username,
                        "image": ""
                    }
                )

                creator_name = creator_info.get(
                    "name",
                    username
                )

                creator_image = creator_info.get(
                    "image",
                    ""
                )

                live_url = (
                    f"https://www.tiktok.com/"
                    f"@{username}/live"
                )

                embed = discord.Embed(
                    title=(
                        f"🔴 {creator_name} IS LIVE!"
                    ),
                    description=(
                        f"✨ {creator_name} sedang "
                        f"LIVE di TikTok!\n"
                        f"Ayo mampir dan ramaikan "
                        f"live-nya!"
                    ),
                    url=live_url,
                    color=discord.Color.red()
                )

                embed.set_footer(
                    text="EVERLIGHT VIRTUAL"
                )

                if creator_image:
                    embed.set_image(
                        url=creator_image
                    )

                view = discord.ui.View()

                watch_button = discord.ui.Button(
                    label="Watch Stream",
                    style=discord.ButtonStyle.link,
                    url=live_url,
                    emoji="🔴"
                )

                view.add_item(
                    watch_button
                )

                await channel.send(
                    embed=embed,
                    view=view
                )

            live_status[username] = is_live

        except Exception as e:

            print(
                f"ERROR cek LIVE @{username}: {e}",
                flush=True
            )


# =====================================================
# TIKTOK TOKEN
# =====================================================

def load_tiktok_token():

    # PRIORITAS 1:
    # Ambil token dari Railway Variables
    access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
    refresh_token = os.getenv("TIKTOK_REFRESH_TOKEN")
    open_id = os.getenv("TIKTOK_OPEN_ID")

    if access_token:

        print(
            "TikTok token ditemukan dari Railway Variables.",
            flush=True
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "open_id": open_id
        }

    # PRIORITAS 2:
    # Kalau belum ada di Railway Variables,
    # baca token hasil login dari file.
    try:

        with open(
            "/data/tiktok_token.json",
            "r",
            encoding="utf-8"
        ) as f:

            token_data = json.load(f)

        print(
            "TikTok token ditemukan dari tiktok_token.json.",
            flush=True
        )

        return token_data

    except FileNotFoundError:

        print(
            "TikTok token belum tersedia.",
            flush=True
        )

        return None

    except Exception as e:

        print(
            f"ERROR membaca TikTok token: {e}",
            flush=True
        )

        return None

# =====================================================
# TIKTOK VIDEO API
# =====================================================

async def get_tiktok_videos():

    token_data = load_tiktok_token()

    if not token_data:

        print(
            "TikTok belum terhubung. "
            "Login melalui /tiktok/login",
            flush=True
        )

        return None

    access_token = token_data.get(
        "access_token"
    )

    if not access_token:

        print(
            "TikTok access token tidak ditemukan.",
            flush=True
        )

        return None

    url = (
        "https://open.tiktokapis.com/"
        "v2/video/list/"
        "?fields=id,title,video_description,"
        "duration,cover_image_url,"
        "share_url,create_time"
    )

    headers = {
        "Authorization": (
            f"Bearer {access_token}"
        ),
        "Content-Type": "application/json"
    }

    payload = {
        "max_count": 10
    }

    try:

        async with aiohttp.ClientSession() as session:

            async with session.post(
                url,
                headers=headers,
                json=payload
            ) as response:

                try:
                    result = await response.json()

                except Exception:

                    text = await response.text()

                    print(
                        "TikTok API bukan JSON:",
                        text,
                        flush=True
                    )

                    return None

                if response.status != 200:

                    print(
                        "TikTok API ERROR:",
                        result,
                        flush=True
                    )

                    return None

                return result

    except Exception as e:

        print(
            f"ERROR request TikTok API: {e}",
            flush=True
        )

        return None


async def get_latest_tiktok_video():

    result = await get_tiktok_videos()

    if not result:
        return None

    videos = (
        result
        .get("data", {})
        .get("videos", [])
    )

    if not videos:
        return None

    videos.sort(
        key=lambda video: video.get(
            "create_time",
            0
        ),
        reverse=True
    )

    return videos[0]


# =====================================================
# TIKTOK POST CHECKER
# =====================================================

last_tiktok_video_id = None


async def check_new_tiktok_video():

    global last_tiktok_video_id

    video = await get_latest_tiktok_video()

    if not video:
        return

    video_id = video.get("id")

    if not video_id:
        return

    # Pertama kali bot hidup:
    # simpan video terbaru, jangan kirim notif lama.
    if last_tiktok_video_id is None:

        last_tiktok_video_id = video_id

        print(
            f"Video TikTok awal tersimpan: {video_id}",
            flush=True
        )

        return

    # Tidak ada video baru.
    if video_id == last_tiktok_video_id:
        return

    # Ada video baru.
    last_tiktok_video_id = video_id

    print(
        f"VIDEO TIKTOK BARU TERDETEKSI: {video_id}",
        flush=True
    )

    share_url = video.get(
        "share_url"
    )

    title = (
        video.get("title")
        or video.get("video_description")
        or "Postingan TikTok baru!"
    )

    cover_image = video.get(
        "cover_image_url"
    )

    # Saat ini OAuth terhubung ke akun Kurocat.
    # Nanti akun lain bisa ditambahkan setelah
    # masing-masing akun mendapat authorization.
    username = "kurocatkurimu"

    channel_id = TIKTOK_POST_CHANNELS.get(
        username
    )

    channel = bot.get_channel(
        channel_id
    )

    if channel is None:

        print(
            f"ERROR: Channel post @{username} "
            f"tidak ditemukan.",
            flush=True
        )

        return

    creator_name = (
        TIKTOK_CREATORS
        .get(username, {})
        .get("name", username)
    )

    embed = discord.Embed(
        title=f"🎬 {creator_name} POSTED!",
        description=title[:4000],
        url=share_url,
        color=discord.Color.from_rgb(
            254,
            44,
            85
        )
    )

    if cover_image:
        embed.set_image(
            url=cover_image
        )

    embed.set_footer(
        text="EVERLIGHT VIRTUAL • TikTok"
    )

    view = None

    if share_url:

        view = discord.ui.View()

        button = discord.ui.Button(
            label="Watch on TikTok",
            style=discord.ButtonStyle.link,
            url=share_url,
            emoji="🎵"
        )

        view.add_item(button)

    await channel.send(
        embed=embed,
        view=view
    )


@tasks.loop(minutes=2)
async def tiktok_video_checker():

    try:

        await check_new_tiktok_video()

    except Exception as e:

        print(
            f"ERROR TikTok post checker: {e}",
            flush=True
        )

# =====================================================
# YOUTUBE UPLOAD CHECKER
# =====================================================

youtube_last_video = {}


youtube_upload_playlists = {}

async def get_latest_youtube_video(channel_id):
    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY belum tersedia.", flush=True)
        return None

    try:
        async with aiohttp.ClientSession() as session:

            # Ambil Uploads Playlist ID sekali saja
            uploads_id = youtube_upload_playlists.get(channel_id)

            if not uploads_id:
                url = "https://www.googleapis.com/youtube/v3/channels"

                params = {
                    "key": YOUTUBE_API_KEY,
                    "id": channel_id,
                    "part": "contentDetails"
                }

                async with session.get(url, params=params) as response:
                    result = await response.json()

                    if response.status != 200:
                        print(
                            "YOUTUBE CHANNEL API ERROR:",
                            result,
                            flush=True
                        )
                        return None

                    items = result.get("items", [])

                    if not items:
                        print(
                            f"YOUTUBE: channel tidak ditemukan {channel_id}",
                            flush=True
                        )
                        return None

                    uploads_id = (
                        items[0]
                        .get("contentDetails", {})
                        .get("relatedPlaylists", {})
                        .get("uploads")
                    )

                    if not uploads_id:
                        print(
                            f"YOUTUBE: uploads playlist tidak ditemukan {channel_id}",
                            flush=True
                        )
                        return None

                    youtube_upload_playlists[channel_id] = uploads_id

                    print(
                        f"YOUTUBE uploads playlist: {uploads_id}",
                        flush=True
                    )

            # Ambil video terbaru dari uploads playlist
            url = "https://www.googleapis.com/youtube/v3/playlistItems"

            params = {
                "key": YOUTUBE_API_KEY,
                "playlistId": uploads_id,
                "part": "snippet,contentDetails",
                "maxResults": 1
            }

            async with session.get(url, params=params) as response:
                result = await response.json()

                if response.status != 200:
                    print(
                        "YOUTUBE PLAYLIST API ERROR:",
                        result,
                        flush=True
                    )
                    return None

                items = result.get("items", [])

                if not items:
                    print(
                        f"YOUTUBE: belum ada upload untuk {channel_id}",
                        flush=True
                    )
                    return None

                item = items[0]

                video_id = (
                    item.get("contentDetails", {})
                    .get("videoId")
                )

                if not video_id:
                    print(
                        "YOUTUBE: videoId tidak ditemukan.",
                        flush=True
                    )
                    return None

                snippet = item.get("snippet", {})

                print(
                    f"YOUTUBE OK | channel={channel_id} "
                    f"| video={video_id}",
                    flush=True
                )

                return {
                    "id": video_id,
                    "snippet": snippet
                }

    except Exception as e:
        print(
            f"YOUTUBE ERROR: {e}",
            flush=True
        )
        return None
    
@tasks.loop(minutes=2)
async def youtube_upload_checker():

        for username, creator in YOUTUBE_CHANNELS.items():

            try:

                video = await get_latest_youtube_video(
                    creator["channel_id"]
                )

                if not video:
                    continue

                video_id = video.get("id")

                if not video_id:
                    continue

                # saat bot pertama hidup:
                # simpan video terbaru tanpa mengirim notif lama.
                if username not in youtube_last_video:

                    youtube_last_video[username] = video_id

                    print(
                        f"YouTube awal@{username}: {video_id}",
                        flush=True
                    )

                    continue

                # Belum ada upload baru.
                if youtube_last_video[username] == video_id:
                    continue

                youtube_last_video[username] = video_id

                snippet = video.get("snippet", {})

                tittle = snippet.get(
                    "tittle",
                    "Video YouTube nbaru!"
                )

                thumbnail = (
                    snippet.get("thumbnails", {})
                    .get("high", {})
                    .get("url")
                )

                video_url = (
                    f"https://www.youtube.com/watch?v={video_id}"
                )

                channel = bot.get_channel(
                    YOUTUBE_POST_CHANNEL_ID
                )

                if channel is None:
                    print(
                        "ERROR Channel YouTube POST Discord tidak ditemukan.",
                        flush=True
                    )
                    continue

                enbed = discord.Embed(
                    tittle=f"🎬 {creator['name']} UPLOADED!",
                    description=tittle,
                    url=video_url,
                    color=discord.color.red()
                )

                if thumbnail:
                    embed.set_image(url=thumbnail)

                embed.set_footer(
                    text="EVERLIGHT VIRTUAL • YouTube"
                )

                view = discord.ui.view()

                button = discord.ui.Button(
                    label="watch on YouTube",
                    style=discord.ButtonStyle.link,
                    url=video_url,
                    emoji="▶"
                )

                view.add_item(button)

                await channel.send(
                    embed=embed,
                    view=view
                )

                print(
                    f"YOUTUBE UPLOAD: {creator['name']} | {tittle}",
                    flush=True
                )

            except Exception as e:

                print(
                    f"ERROR YouTube @{username}: {e}",
                    flush=True
                )

@tasks.loop(minutes=5)
async def tiktok_follower_milestone_checker():

    for username, data in TIKTOK_FOLLOWER_MILESTONES.items():

        try:
            followers = await get_tiktok_follower_count(username)

            if followers is None:
                continue

            # Cari milestone 500 terdekat yang SUDAH tercapai
            current_milestone = (
                followers // FOLLOWER_MILESTONE_STEP
            ) * FOLLOWER_MILESTONE_STEP

            # Pertama kali bot membaca follower:
            # simpan posisi sekarang tanpa kirim pengumuman lama
            if data["last_milestone"] == 0:
                data["last_milestone"] = current_milestone

                print(
                    f"MILESTONE INIT @{username}: "
                    f"{current_milestone} | followers={followers}",
                    flush=True
                )

                continue

            # Belum mencapai milestone berikutnya
            if current_milestone <= data["last_milestone"]:
                continue

            # Ada milestone baru
            data["last_milestone"] = current_milestone

            channel = bot.get_channel(
                TIKTOK_FOLLOWER_MILESTONE_CHANNEL_ID
            )

            if channel is None:
                print(
                    "ERROR: Channel milestone TikTok tidak ditemukan.",
                    flush=True
                )
                continue

            message = data["message"].format(
                name=data["name"],
                followers=current_milestone
            )

            await channel.send(message)

            print(
                f"MILESTONE SENT @{username}: "
                f"{current_milestone}",
                flush=True
            )

        except Exception as e:
            print(
                f"ERROR milestone @{username}: {e}",
                flush=True
            )

# =====================================================
# BOT READY
# =====================================================

@bot.tree.command(
    name="testmilestone",
    description="Test TikTok follower milestone notification"
)
async def testmilestone(interaction: discord.Interaction):

    data = TIKTOK_FOLLOWER_MILESTONES["kurocatkurimu"]

    test_followers = 9000

    message = data["message"].format(
        name=data["name"],
        followers=test_followers
    )

    channel = bot.get_channel(
        data["channel_id"]
    )

    if channel is None:
        await interaction.response.send_message(
            "❌ Channel milestone tidak ditemukan.",
            ephemeral=True
        )
        return

    await channel.send(
        f"@everyone\n\n{message}",
        allowed_mentions=discord.AllowedMentions(
            everyone=True
        )
    )

    await interaction.response.send_message(
        "✅ Test milestone 9,000 followers berhasil dikirim.",
        ephemeral=True
    )

@bot.event
async def on_ready():

    print(
        "==============================",
        flush=True
    )

    print(
        "Everlight Bot ONLINE!",
        flush=True
    )

    print(
        f"Login sebagai: {bot.user}",
        flush=True
    )

    print(
        "==============================",
        flush=True
    )
    

    # Fungsi checker SUDAH didefinisikan di atas,
    # jadi aman dipanggil dari sini.

    if not live_checker.is_running():

        live_checker.start()

        print(
            "TikTok LIVE checker STARTED.",
            flush=True
        )

    if not tiktok_video_checker.is_running():

        tiktok_video_checker.start()

        print(
            "TikTok POST checker STARTED.",
            flush=True
        )

    if not youtube_upload_checker.is_running():

        youtube_upload_checker.start()

        print(
            "YouTube UPLOAD checker STARTED.",
            flush=True
        )

    if not tiktok_follower_milestone_checker.is_running():

        tiktok_follower_milestone_checker.start()

        print(
            "TikTok FOLLOWER MILESTONE checker STARTED.",
              flush=True
              )


# =====================================================
# HELLO COMMAND
# =====================================================

@bot.tree.command(
    name="hello",
    description="Say hello to Everlight!"
)
async def hello(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        f"✨ Hello {interaction.user.mention}! "
        f"Welcome to Everlight!"
    )


# =====================================================
# MODERATION - WARN
# =====================================================

@bot.tree.command(
    name="warn",
    description="Berikan warning kepada member"
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
async def warn(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str
):

    if member == interaction.user:

        await interaction.response.send_message(
            "❌ Kamu tidak bisa memberikan "
            "warning kepada diri sendiri.",
            ephemeral=True
        )

        return

    cursor.execute(
        """
        INSERT INTO warnings
        (guild_id, user_id, moderator_id, reason)
        VALUES (?, ?, ?, ?)
        """,
        (
            interaction.guild.id,
            member.id,
            interaction.user.id,
            reason
        )
    )

    db.commit()

    warning_id = cursor.lastrowid

    try:

        await member.send(
            f"⚠️ **EVERLIGHT VIRTUAL — "
            f"OFFICIAL WARNING**\n\n"
            f"Server: **{interaction.guild.name}**\n"
            f"Warning ID: **#{warning_id}**\n"
            f"Reason: **{reason}**\n"
            f"Moderator: **{interaction.user}**\n\n"
            f"Harap mengikuti peraturan server "
            f"untuk menghindari tindakan "
            f"moderasi selanjutnya."
        )

        dm_status = (
            "📨 Warning telah dikirim melalui DM."
        )

    except discord.Forbidden:

        dm_status = (
            "⚠️ DM member tidak dapat dikirim."
        )

    await interaction.response.send_message(
        f"⚠️ **MEMBER WARNED**\n\n"
        f"👤 Member: {member.mention}\n"
        f"🆔 Warning ID: **#{warning_id}**\n"
        f"📝 Reason: **{reason}**\n"
        f"🛡️ Moderator: "
        f"{interaction.user.mention}\n\n"
        f"{dm_status}"
    )


# =====================================================
# MODERATION - WARNINGS
# =====================================================

@bot.tree.command(
    name="warnings",
    description="Lihat warning seorang member"
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
async def warnings(
    interaction: discord.Interaction,
    member: discord.Member
):

    cursor.execute(
        """
        SELECT id, moderator_id, reason, created_at
        FROM warnings
        WHERE guild_id = ? AND user_id = ?
        ORDER BY id ASC
        """,
        (
            interaction.guild.id,
            member.id
        )
    )

    results = cursor.fetchall()

    if not results:

        await interaction.response.send_message(
            f"✅ {member.mention} "
            f"tidak memiliki warning.",
            ephemeral=True
        )

        return

    text = (
        f"⚠️ **WARNING HISTORY — "
        f"{member.display_name}**\n\n"
    )

    for (
        warning_id,
        moderator_id,
        reason,
        created_at
    ) in results:

        text += (
            f"**#{warning_id}** — {reason}\n"
            f"Moderator: <@{moderator_id}>\n"
            f"Date: {created_at}\n\n"
        )

    await interaction.response.send_message(
        text,
        ephemeral=True
    )


# =====================================================
# MODERATION - UNWARN
# =====================================================

@bot.tree.command(
    name="unwarn",
    description=(
        "Hapus satu warning berdasarkan Warning ID"
    )
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
async def unwarn(
    interaction: discord.Interaction,
    member: discord.Member,
    warning_id: int
):

    cursor.execute(
        """
        DELETE FROM warnings
        WHERE id = ?
        AND guild_id = ?
        AND user_id = ?
        """,
        (
            warning_id,
            interaction.guild.id,
            member.id
        )
    )

    db.commit()

    if cursor.rowcount == 0:

        await interaction.response.send_message(
            f"❌ Warning **#{warning_id}** "
            f"tidak ditemukan untuk "
            f"{member.mention}.",
            ephemeral=True
        )

        return

    await interaction.response.send_message(
        f"✅ Warning **#{warning_id}** "
        f"milik {member.mention} telah dihapus."
    )


# =====================================================
# MODERATION - CLEAR WARNINGS
# =====================================================

@bot.tree.command(
    name="clearwarnings",
    description="Hapus semua warning seorang member"
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
async def clearwarnings(
    interaction: discord.Interaction,
    member: discord.Member
):

    cursor.execute(
        """
        DELETE FROM warnings
        WHERE guild_id = ? AND user_id = ?
        """,
        (
            interaction.guild.id,
            member.id
        )
    )

    deleted = cursor.rowcount

    db.commit()

    await interaction.response.send_message(
        f"🧹 Semua warning "
        f"{member.mention} telah dihapus.\n"
        f"Total warning dihapus: **{deleted}**"
    )


# =====================================================
# MODERATION - KICK
# =====================================================

@bot.tree.command(
    name="kick",
    description="Kick member dari Everlight"
)
@app_commands.checks.has_permissions(
    kick_members=True
)
async def kick(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "Tidak ada alasan"
):

    if member == interaction.user:

        await interaction.response.send_message(
            "❌ Kamu tidak bisa kick diri sendiri.",
            ephemeral=True
        )

        return

    try:

        await member.send(
            f"👢 **EVERLIGHT VIRTUAL — "
            f"KICK NOTICE**\n\n"
            f"Kamu telah dikeluarkan dari "
            f"**{interaction.guild.name}**.\n"
            f"Reason: **{reason}**\n"
            f"Moderator: **{interaction.user}**"
        )

    except discord.Forbidden:
        pass

    try:

        await member.kick(
            reason=reason
        )

        await interaction.response.send_message(
            f"👢 **MEMBER KICKED**\n\n"
            f"👤 Member: **{member}**\n"
            f"📝 Reason: **{reason}**\n"
            f"🛡️ Moderator: "
            f"{interaction.user.mention}"
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ Bot tidak memiliki permission "
            "untuk kick member ini.",
            ephemeral=True
        )


# =====================================================
# MODERATION - BAN
# =====================================================

@bot.tree.command(
    name="ban",
    description="Ban member dari Everlight"
)
@app_commands.checks.has_permissions(
    ban_members=True
)
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "Tidak ada alasan"
):

    if member == interaction.user:

        await interaction.response.send_message(
            "❌ Kamu tidak bisa ban diri sendiri.",
            ephemeral=True
        )

        return

    try:

        await member.send(
            f"🔨 **EVERLIGHT VIRTUAL — "
            f"BAN NOTICE**\n\n"
            f"Kamu telah dibanned secara permanen "
            f"dari **{interaction.guild.name}**.\n\n"
            f"Reason: **{reason}**\n"
            f"Moderator: **{interaction.user}**"
        )

    except discord.Forbidden:
        pass

    try:

        await member.ban(
            reason=reason
        )

        await interaction.response.send_message(
            f"🔨 **MEMBER BANNED**\n\n"
            f"👤 Member: **{member}**\n"
            f"📝 Reason: **{reason}**\n"
            f"🛡️ Moderator: "
            f"{interaction.user.mention}"
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ Bot tidak memiliki permission "
            "untuk ban member ini.",
            ephemeral=True
        )


# =====================================================
# MEMBER JOIN / AUTO ROLE
# =====================================================

@bot.event
async def on_member_join(member):

    channel = discord.utils.get(
        member.guild.text_channels,
        name="welcome"
    )

    role = discord.utils.get(
        member.guild.roles,
        name="moonwalker"
    )

    if role:

        try:

            await member.add_roles(
                role,
                reason="Auto role member baru"
            )

        except discord.Forbidden:

            print(
                "Gagal memberikan role moonwalker.",
                flush=True
            )

    if channel:

        message = (
            f"✨ **A New Star Has Appeared** ✨\n"
            f"Selamat datang, {member.mention} ✨ "
            f"Kamu telah memasuki "
            f"**Everlight Virtual**, tempat di mana "
            f"kreativitas, persahabatan, dan mimpi "
            f"bersinar bersama.\n\n"
            f"📚 Baca aturan di #welcome\n"
            f"🎭 Pilih role di #self-roles\n"
            f"🌸 Perkenalkan dirimu di #introduction\n"
            f"💬 Bergabunglah dalam percakapan "
            f"dan event komunitas\n\n"
            f"Kami berharap perjalananmu di sini "
            f"dipenuhi tawa, kenangan indah, "
            f"dan teman-teman baru.\n"
            f"🌙 *May your light continue "
            f"to shine brightly.* ✨"
        )

        banner = await create_welcome_image(
            member
        )

        await channel.send(
            content=message,
            file=banner
        )


# =====================================================
# SERVER BOOSTER
# =====================================================

@bot.event
async def on_member_update(
    before,
    after
):

    if (
        before.premium_since is None
        and after.premium_since is not None
    ):

        channel = discord.utils.get(
            after.guild.text_channels,
            name="booster"
        )

        if channel is None:

            print(
                "Channel #booster tidak ditemukan.",
                flush=True
            )

            return

        embed = discord.Embed(
            title="💎 EVERLIGHT SERVER BOOST 💎",
            description=(
                f"✨ Thank you {after.mention}! ✨\n\n"
                f"You just boosted "
                f"**{after.guild.name}**!\n\n"
                f"Your support helps Everlight "
                f"shine even brighter. 🌙✨\n"
                f"Thank you for supporting "
                f"our community!"
            ),
            color=discord.Color.from_rgb(
                255,
                105,
                180
            )
        )

        embed.set_thumbnail(
            url=after.display_avatar.url
        )

        embed.set_footer(
            text=(
                "Everlight Virtual • "
                "Keep Your Light Alive ✨"
            )
        )

        await channel.send(
            content=f"💎 {after.mention}",
            embed=embed
        )

        print(
            f"BOOST DETECTED: {after}",
            flush=True
        )


# =====================================================
# TEST BOOSTER
# =====================================================

@bot.tree.command(
    name="testbooster",
    description=(
        "Test Everlight booster notification"
    )
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def testbooster(
    interaction: discord.Interaction
):

    channel = discord.utils.get(
        interaction.guild.text_channels,
        name="booster"
    )

    if channel is None:

        await interaction.response.send_message(
            "❌ Channel #booster tidak ditemukan.",
            ephemeral=True
        )

        return

    member = interaction.user

    embed = discord.Embed(
        title="💎 EVERLIGHT SERVER BOOST 💎",
        description=(
            f"✨ Thank you {member.mention}! ✨\n\n"
            f"You just boosted "
            f"**{interaction.guild.name}**!\n\n"
            f"Your support helps Everlight "
            f"shine even brighter. 🌙✨\n"
            f"Thank you for supporting "
            f"our community!"
        ),
        color=discord.Color.from_rgb(
            255,
            105,
            180
        )
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.set_footer(
        text=(
            "Everlight Virtual • "
            "Keep Your Light Alive ✨"
        )
    )

    await channel.send(
        content=f"💎 {member.mention}",
        embed=embed
    )

    await interaction.response.send_message(
        "✅ Booster notification "
        "berhasil dites!",
        ephemeral=True
    )


# =====================================================
# TIKTOK WEBHOOK
# =====================================================

async def tiktok_webhook(request):

    try:

        data = await request.json()

        print(
            "TikTok Webhook:",
            data,
            flush=True
        )

        return web.Response(
            text="OK",
            status=200
        )

    except Exception as e:

        print(
            "TikTok Webhook Error:",
            e,
            flush=True
        )

        return web.Response(
            text="OK",
            status=200
        )


# =====================================================
# TERMS
# =====================================================

async def terms_page(request):

    html = """
    <html>
    <head>
        <title>Everlight Bot - Terms of Service</title>
    </head>

    <body>

        <h1>Everlight Bot - Terms of Service</h1>

        <p>Last updated: August 13, 2026</p>

        <h2>1. About Everlight Bot</h2>

        <p>
        Everlight Bot is a Discord community bot
        operated by Everlight Virtual.
        It provides community features and
        TikTok-related notifications.
        </p>

        <h2>2. Use of the Service</h2>

        <p>
        Users may use Everlight Bot for its intended
        community and notification features.
        Misuse, abuse, or attempts to disrupt
        the service are prohibited.
        </p>

        <h2>3. TikTok Integration</h2>

        <p>
        Everlight Bot may use TikTok APIs to access
        authorized TikTok information and public
        content for notification features.
        </p>

        <h2>4. Availability</h2>

        <p>
        The service may be changed, suspended,
        or discontinued at any time.
        </p>

        <h2>5. Contact</h2>

        <p>
        For questions regarding Everlight Bot,
        contact Everlight Virtual.
        </p>

    </body>
    </html>
    """

    return web.Response(
        text=html,
        content_type="text/html"
    )


# =====================================================
# PRIVACY
# =====================================================

async def privacy_page(request):

    html = """
    <html>

    <head>
        <title>Everlight Bot - Privacy Policy</title>
    </head>

    <body>

        <h1>Everlight Bot - Privacy Policy</h1>

        <p>Last updated: August 13, 2026</p>

        <h2>Information We Process</h2>

        <p>
        Everlight Bot may process TikTok account
        identifiers, basic profile information,
        and public video information when authorized.
        </p>

        <h2>How Information Is Used</h2>

        <p>
        Information is used to provide TikTok
        content notifications and community features
        in the Everlight Virtual Discord server.
        </p>

        <h2>Data Sharing</h2>

        <p>
        Everlight Bot does not sell
        personal information.
        </p>

        <h2>Data Retention</h2>

        <p>
        Information is retained only as necessary
        to operate the service.
        </p>

        <h2>Contact</h2>

        <p>
        For privacy questions,
        contact Everlight Virtual.
        </p>

    </body>

    </html>
    """

    return web.Response(
        text=html,
        content_type="text/html"
    )


# =====================================================
# TIKTOK VERIFY
# =====================================================

async def tiktok_verify_file(request):

    verification = (
        "tiktok-developers-site-verification="
        "7caxFt77pT4f9XdUEIWEeJlBBRo2HXUL"
    )

    return web.Response(
        body=verification.encode("utf-8"),
        headers={
            "Content-Type":
            "text/plain; charset=utf-8"
        }
    )


async def verify_root_txt(request):

    return web.Response(
        text=(
            "tiktok-developers-site-verification="
            "lw0KJ6SVO5YSdgbS2vKFqeTW40mKZ25P"
        ),
        content_type="text/plain"
    )


async def verify_terms_txt(request):

    return web.Response(
        text=(
            "tiktok-developers-site-verification="
            "4qL77aFCylLLUtAlB6s3QVzGyUKHA071"
        ),
        content_type="text/plain"
    )


async def verify_privacy_txt(request):

    return web.Response(
        text=(
            "tiktok-developers-site-verification="
            "9AMaLRt3zKWPyXzfmiIEGnYrfXMS5WFJ"
        ),
        content_type="text/plain"
    )


async def test_route(request):

    return web.Response(
        text="EVERLIGHT TEST OK"
    )


# =====================================================
# TIKTOK LOGIN
# =====================================================

async def tiktok_login(request):

    client_key = os.getenv(
        "TIKTOK_CLIENT_KEY"
    )

    if not client_key:

        return web.Response(
            text="TIKTOK_CLIENT_KEY belum diatur.",
            status=500
        )

    redirect_uri = (
        "https://everlight-world-production."
        "up.railway.app/tiktok/callback"
    )

    params = {
        "client_key": client_key,
        "scope": (
            "user.info.basic,video.list"
        ),
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": "everlight"
    }

    login_url = (
        "https://www.tiktok.com/"
        "v2/auth/authorize/?"
        + urllib.parse.urlencode(params)
    )

    raise web.HTTPFound(
        login_url
    )


# =====================================================
# TIKTOK CALLBACK
# =====================================================

async def tiktok_callback(request):

    code = request.query.get("code")
    error = request.query.get("error")

    if error:

        return web.Response(
            text=f"TikTok Login Error: {error}"
        )

    if not code:

        return web.Response(
            text=(
                "Authorization code "
                "tidak ditemukan."
            )
        )

    client_key = os.getenv(
        "TIKTOK_CLIENT_KEY"
    )

    client_secret = os.getenv(
        "TIKTOK_CLIENT_SECRET"
    )

    if not client_key or not client_secret:

        return web.Response(
            text=(
                "TikTok client key/secret "
                "belum diatur."
            ),
            status=500
        )

    redirect_uri = (
        "https://everlight-world-production."
        "up.railway.app/tiktok/callback"
    )

    token_url = (
        "https://open.tiktokapis.com/"
        "v2/oauth/token/"
    )

    data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }

    async with aiohttp.ClientSession() as session:

        async with session.post(
            token_url,
            data=data
        ) as response:

            try:

                result = await response.json()

            except Exception:

                text = await response.text()

                return web.Response(
                    text=(
                        "TikTok token response "
                        f"bukan JSON: {text}"
                    ),
                    status=500
                )

    if "access_token" not in result:

        return web.Response(
            text=(
                "Gagal mendapatkan TikTok "
                f"access token: {result}"
            )
        )

    token_data = {
        "access_token":
            result["access_token"],

        "refresh_token":
            result.get("refresh_token"),

        "open_id":
            result.get("open_id")
    }

    with open(
        "/data/tiktok_token.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            token_data,
            f
        )

    print(
        "TikTok authorization berhasil!",
        flush=True
    )

    print(
        f"TikTok Open ID: "
        f"{result.get('open_id')}",
        flush=True
    )

    return web.Response(
        text=(
            "TikTok berhasil terhubung "
            "ke Everlight Bot!"
        )
    )


# =====================================================
# TIKTOK VIDEOS PAGE
# =====================================================

async def tiktok_videos(request):

    result = await get_tiktok_videos()

    if not result:

        return web.json_response(
            {
                "status": "error",
                "message": (
                    "TikTok belum terhubung "
                    "atau API gagal."
                )
            },
            status=400
        )

    videos = (
        result
        .get("data", {})
        .get("videos", [])
    )

    return web.json_response(
        {
            "status": "success",
            "video_count": len(videos),
            "videos": videos
        }
    )


# =====================================================
# HOME PAGE
# =====================================================

async def home_page(request):

    html = """
    <!DOCTYPE html>

    <html>

    <head>
        <title>Everlight World</title>
    </head>

    <body>

        <h1>Everlight World</h1>

        <p>
        Connect your TikTok account
        with Everlight Bot.
        </p>

        <a href="/tiktok/login">
            <button>
                Login with TikTok
            </button>
        </a>

        <br><br>

        <a href="/tiktok/videos">
            View TikTok Videos
        </a>

    </body>

    </html>
    """

    return web.Response(
        text=html,
        content_type="text/html"
    )


# =====================================================
# WEB SERVER
# =====================================================

async def start_web_server():

    app = web.Application()

    app.router.add_get(
        "/",
        home_page
    )

    app.router.add_get(
        "/test",
        test_route
    )

    app.router.add_get(
        "/tiktok/login",
        tiktok_login
    )

    app.router.add_get(
        "/tiktok/callback",
        tiktok_callback
    )

    app.router.add_get(
        "/tiktok/videos",
        tiktok_videos
    )

    app.router.add_get(
        "/cek-tiktok",
        verify_root_txt
    )

    app.router.add_get(
        "/{filename}.txt",
        verify_root_txt
    )

    app.router.add_get(
        "/terms/"
        "tiktok4qL77aFCylLLUtAlB6s3QVzGyUKHA071.txt",
        verify_terms_txt
    )

    app.router.add_get(
        "/privacy/"
        "tiktok9AMaLRt3zKWPyXzfmiIEGnYrfXMS5WFJ.txt",
        verify_privacy_txt
    )

    app.router.add_post(
        "/tiktok/webhook",
        tiktok_webhook
    )

    app.router.add_get(
        "/terms",
        terms_page
    )

    app.router.add_get(
        "/privacy",
        privacy_page
    )

    app.router.add_get(
        "/tiktok7caxFt77pT4f9XdUEIWEeJlBBRo2HXUL.txt",
        tiktok_verify_file
    )

    runner = web.AppRunner(
        app
    )

    await runner.setup()

    port = int(
        os.getenv(
            "PORT",
            8080
        )
    )

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

    print(
        f"Web server berjalan di port {port}",
        flush=True
    )

    return runner


# =====================================================
# START BOT
# =====================================================

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN belum diisi "
        "di environment"
    )


bot.run(TOKEN)
