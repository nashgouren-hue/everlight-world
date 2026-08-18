import os
import json
import urllib.parse
import discord
import aiohttp
import io
import sqlite3
from discord import app_commands
from discord.ext import tasks
from TikTokLive import TikTokLiveClient
from PIL import Image, ImageDraw, ImageFont
from aiohttp import web


TOKEN = os.getenv("DISCORD_TOKEN")
LIVE_CHANNEL_ID = 1513414157897043998

TIKTOK_LIVE_ACCOUNTS = [
    "kurocatkurimu",
    "nashgouren_",
    "hiharuhere",
    "louiegospellvt",
    "everlightvirtual",
]
# ==========================================
# EVERLIGHT MODERATION DATABASE
# ==========================================

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
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class EverlightBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

async def setup_hook(self):
        await self.tree.sync()
        await start_web_server()
bot = EverlightBot()
async def create_welcome_image(member):
    # Buka template
    template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "welcome.png"
    )

    image = Image.open(template_path).convert("RGBA")

    # Ambil avatar Discord
    avatar_bytes = await member.display_avatar.replace(
        size=256,
        format="png"
    ).read()

    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

    # Ukuran avatar
    avatar_size = 300
    avatar = avatar.resize((avatar_size, avatar_size))

    # Bikin avatar bulat
    mask = Image.new("L", (avatar_size, avatar_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse(
        (0, 0, avatar_size, avatar_size),
        fill=255
    )

    # Posisi avatar di tengah
    avatar_x = (image.width - avatar_size) // 2
    avatar_y = 35

    image.paste(
        avatar,
        (avatar_x, avatar_y),
        mask
    )

    # Tulis nama Discord
    draw = ImageDraw.Draw(image)
    nama = member.display_name

    try:
        font_nama = ImageFont.truetype("arialbd.ttf", 100)
    except:
        font_nama = ImageFont.load_default()

    bbox = draw.textbbox(
        (0, 0),
        nama,
        font=font_nama
    )

    text_width = bbox[2] - bbox[0]

    nama_x = (image.width - text_width) // 2
    nama_y = 410

    draw.text(
        (nama_x, nama_y),
        nama,
        font=font_nama,
        fill="white",
        stroke_width=4,
        stroke_fill="#4a3c3c"
    )

    # Simpan hasil ke memory
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)

    return discord.File(
        output,
        filename="welcome.png"
    )

live_status = {}

@tasks.loop(seconds=60)
async def live_checker():
    channel = bot.get_channel(LIVE_CHANNEL_ID)

    if channel is None:
        print("❌ Channel LIVE Discord tidak ditemukan.")
        return

    for username in TIKTOK_LIVE_ACCOUNTS:
        try:
            client = TikTokLiveClient(unique_id=f"@{username}")

            is_live = await client.is_live()

            sebelumnya_live = live_status.get(username, False)

            print(f"TikTok @{username} | LIVE: {is_live}")

            if is_live and not sebelumnya_live:
                await channel.send(
                    f"🔴 **@{username} sedang LIVE di TikTok!**\n"
                    f"https://www.tiktok.com/@{username}/live"
                )

            live_status[username] = is_live

        except Exception as e:
            print(f"❌ Gagal cek @{username}: {e}")
@bot.event
async def on_ready():
    print(f"==============================")
    print(f"Everlight Bot ONLINE!")
    print(f"Login sebagai: {bot.user}")
    print(f"==============================")

    if not live_checker.is_running():
        live_checker.start()
        
@bot.tree.command(name="hello", description="Say hello to Everlight!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"✨ Hello {interaction.user.mention}! Welcome to Everlight!"
    )
    # =====================================================
# EVERLIGHT MODERATION SYSTEM
# =====================================================


# -------------------------
# WARN
# -------------------------

@bot.tree.command(
    name="warn",
    description="Berikan warning kepada member"
)
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str
):
    if member == interaction.user:
        await interaction.response.send_message(
            "❌ Kamu tidak bisa memberikan warning kepada diri sendiri.",
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
            f"⚠️ **EVERLIGHT VIRTUAL — OFFICIAL WARNING**\n\n"
            f"Server: **{interaction.guild.name}**\n"
            f"Warning ID: **#{warning_id}**\n"
            f"Reason: **{reason}**\n"
            f"Moderator: **{interaction.user}**\n\n"
            f"Harap mengikuti peraturan server untuk menghindari "
            f"tindakan moderasi selanjutnya."
        )

        dm_status = "📨 Warning telah dikirim melalui DM."

    except discord.Forbidden:
        dm_status = "⚠️ DM member tidak dapat dikirim."

    await interaction.response.send_message(
        f"⚠️ **MEMBER WARNED**\n\n"
        f"👤 Member: {member.mention}\n"
        f"🆔 Warning ID: **#{warning_id}**\n"
        f"📝 Reason: **{reason}**\n"
        f"🛡️ Moderator: {interaction.user.mention}\n\n"
        f"{dm_status}"
    )


# -------------------------
# CHECK WARNINGS
# -------------------------

@bot.tree.command(
    name="warnings",
    description="Lihat warning seorang member"
)
@app_commands.checks.has_permissions(moderate_members=True)
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
            f"✅ {member.mention} tidak memiliki warning.",
            ephemeral=True
        )
        return

    text = (
        f"⚠️ **WARNING HISTORY — {member.display_name}**\n\n"
    )

    for warning_id, moderator_id, reason, created_at in results:
        text += (
            f"**#{warning_id}** — {reason}\n"
            f"Moderator: <@{moderator_id}>\n"
            f"Date: {created_at}\n\n"
        )

    await interaction.response.send_message(
        text,
        ephemeral=True
    )


# -------------------------
# REMOVE ONE WARNING
# -------------------------

@bot.tree.command(
    name="unwarn",
    description="Hapus satu warning berdasarkan Warning ID"
)
@app_commands.checks.has_permissions(moderate_members=True)
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
            f"❌ Warning **#{warning_id}** tidak ditemukan untuk "
            f"{member.mention}.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"✅ Warning **#{warning_id}** milik "
        f"{member.mention} telah dihapus."
    )


# -------------------------
# CLEAR ALL WARNINGS
# -------------------------

@bot.tree.command(
    name="clearwarnings",
    description="Hapus semua warning seorang member"
)
@app_commands.checks.has_permissions(moderate_members=True)
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
        f"🧹 Semua warning {member.mention} telah dihapus.\n"
        f"Total warning dihapus: **{deleted}**"
    )


# -------------------------
# KICK
# -------------------------

@bot.tree.command(
    name="kick",
    description="Kick member dari Everlight"
)
@app_commands.checks.has_permissions(kick_members=True)
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
            f"👢 **EVERLIGHT VIRTUAL — KICK NOTICE**\n\n"
            f"Kamu telah dikeluarkan dari **{interaction.guild.name}**.\n"
            f"Reason: **{reason}**\n"
            f"Moderator: **{interaction.user}**"
        )

    except discord.Forbidden:
        pass

    try:
        await member.kick(reason=reason)

        await interaction.response.send_message(
            f"👢 **MEMBER KICKED**\n\n"
            f"👤 Member: **{member}**\n"
            f"📝 Reason: **{reason}**\n"
            f"🛡️ Moderator: {interaction.user.mention}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Bot tidak memiliki permission untuk kick member ini.",
            ephemeral=True
        )


# -------------------------
# BAN
# -------------------------

@bot.tree.command(
    name="ban",
    description="Ban member dari Everlight"
)
@app_commands.checks.has_permissions(ban_members=True)
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
            f"🔨 **EVERLIGHT VIRTUAL — BAN NOTICE**\n\n"
            f"Kamu telah dibanned secara permanen dari "
            f"**{interaction.guild.name}**.\n\n"
            f"Reason: **{reason}**\n"
            f"Moderator: **{interaction.user}**"
        )

    except discord.Forbidden:
        pass

    try:
        await member.ban(reason=reason)

        await interaction.response.send_message(
            f"🔨 **MEMBER BANNED**\n\n"
            f"👤 Member: **{member}**\n"
            f"📝 Reason: **{reason}**\n"
            f"🛡️ Moderator: {interaction.user.mention}"
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Bot tidak memiliki permission untuk ban member ini.",
            ephemeral=True
        )
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

    # Auto role
    if role:
        try:
            await member.add_roles(
                role,
                reason="Auto role member baru"
            )
        except discord.Forbidden:
            print("Gagal memberikan role moonwalker.")

    # Welcome
    if channel:
        message = (
            f"✨ **A New Star Has Appeared** ✨\n"
            f"Selamat datang, {member.mention} ✨ Kamu telah memasuki "
            f"**Everlight Virtual**, tempat di mana kreativitas, "
            f"persahabatan, dan mimpi bersinar bersama.\n\n"
            f"📚 Baca aturan di #welcome\n"
            f"🎭 Pilih role di #self-roles\n"
            f"🌸 Perkenalkan dirimu di #introduction\n"
            f"💬 Bergabunglah dalam percakapan dan event komunitas\n\n"
            f"Kami berharap perjalananmu di sini dipenuhi tawa, "
            f"kenangan indah, dan teman-teman baru.\n"
            f"🌙 *May your light continue to shine brightly.* ✨"
        )

        banner = await create_welcome_image(member)

        await channel.send(
            content=message,
            file=banner
        )


# ==================================================
# 💎 EVERLIGHT SERVER BOOSTER NOTIFICATION
# ==================================================

@bot.event
async def on_member_update(before, after):

    # Member baru saja mulai boost server
    if before.premium_since is None and after.premium_since is not None:

        channel = discord.utils.get(
            after.guild.text_channels,
            name="booster"
        )

        if channel is None:
            print("Channel #booster tidak ditemukan.")
            return

        embed = discord.Embed(
            title="💎 EVERLIGHT SERVER BOOST 💎",
            description=(
                f"✨ Thank you {after.mention}! ✨\n\n"
                f"You just boosted **{after.guild.name}**!\n\n"
                f"Your support helps Everlight shine even brighter. 🌙✨\n"
                f"Thank you for supporting our community!"
            ),
            color=discord.Color.from_rgb(255, 105, 180)
        )

        embed.set_thumbnail(
            url=after.display_avatar.url
        )

        embed.set_footer(
            text="Everlight Virtual • Keep Your Light Alive ✨"
        )

        await channel.send(
            content=f"💎 {after.mention}",
            embed=embed
        )

        print(f"BOOST DETECTED: {after}")

# ==================================================
# 💎 TEST BOOSTER COMMAND
# ==================================================

@bot.tree.command(
    name="testbooster",
    description="Test Everlight booster notification"
)
@app_commands.checks.has_permissions(administrator=True)
async def testbooster(interaction: discord.Interaction):

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
            f"You just boosted **{interaction.guild.name}**!\n\n"
            f"Your support helps Everlight shine even brighter. 🌙✨\n"
            f"Thank you for supporting our community!"
        ),
        color=discord.Color.from_rgb(255, 105, 180)
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    embed.set_footer(
        text="Everlight Virtual • Keep Your Light Alive ✨"
    )

    await channel.send(
        content=f"💎 {member.mention}",
        embed=embed
    )

    await interaction.response.send_message(
        "✅ Booster notification berhasil dites!",
        ephemeral=True
    )
# =========================
# TIKTOK WEBHOOK
# =========================

async def tiktok_webhook(request):
    try:
        data = await request.json()
        print("TikTok Webhook:", data)
        return web.Response(text="OK", status=200)
    except Exception as e:
        print("TikTok Webhook Error:", e)
        return web.Response(text="OK", status=200)
async def terms_page(request):
    html = """
    <html>
    <head><title>Everlight Bot - Terms of Service</title></head>
    <body>
        <h1>Everlight Bot - Terms of Service</h1>
        <p>Last updated: August 13, 2026</p>

        <h2>1. About Everlight Bot</h2>
        <p>Everlight Bot is a Discord community bot operated by Everlight Virtual.
        It provides community features and TikTok-related notifications.</p>

        <h2>2. Use of the Service</h2>
        <p>Users may use Everlight Bot for its intended community and notification
        features. Misuse, abuse, or attempts to disrupt the service are prohibited.</p>

        <h2>3. TikTok Integration</h2>
        <p>Everlight Bot may use TikTok APIs to access authorized TikTok information
        and public content for notification features.</p>

        <h2>4. Availability</h2>
        <p>The service may be changed, suspended, or discontinued at any time.</p>

        <h2>5. Contact</h2>
        <p>For questions regarding Everlight Bot, contact Everlight Virtual.</p>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")


async def privacy_page(request):
    html = """
    <html>
    <head><title>Everlight Bot - Privacy Policy</title></head>
    <body>
        <h1>Everlight Bot - Privacy Policy</h1>
        <p>Last updated: August 13, 2026</p>

        <h2>Information We Process</h2>
        <p>Everlight Bot may process TikTok account identifiers, basic profile
        information, and public video information when authorized.</p>

        <h2>How Information Is Used</h2>
        <p>Information is used to provide TikTok content notifications and
        community features in the Everlight Virtual Discord server.</p>

        <h2>Data Sharing</h2>
        <p>Everlight Bot does not sell personal information.</p>

        <h2>Data Retention</h2>
        <p>Information is retained only as necessary to operate the service.</p>

        <h2>Contact</h2>
        <p>For privacy questions, contact Everlight Virtual.</p>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")  
async def tiktok_verify_file(request):
    verification = "tiktok-developers-site-verification=7caxFt77pT4f9XdUEIWEeJlBBRo2HXUL"
    return web.Response(
        body=verification.encode("utf-8"),
        headers={
            "Content-Type": "text/plain; charset=utf-8"
        }
    )


async def tiktok_verify_terms(request):
    return web.Response(
        text="tiktok-developers-site-verification=4qL77aFCylLLUtAlB6s3QVzGyUKHA07l",
        content_type="text/plain"
    )
async def tiktok_verify_privacy(request):
    return web.Response(
        text="tiktok-developers-site-verification=9AMaLRt3zKWPyXzfmiIEGnYrfXMS5WFJ",
        content_type="text/plain"
    )
    async def test_route(request):
        return web.Response(text="EVERLIGHT TEST OK")

    async def verify_root_txt(request):
        return web.Response(
            text="tiktok-developers-site-verification=lw0KJ6SVO5YSdgbS2vKFqeTW40mKZ25P",
            content_type="text/plain"
        )
        
    async def verify_terms_txt(request):
        return web.Response(
            text="tiktok-developers-site-verification=4qL77aFCylLLUtAlB6s3QVzGyUKHA071",
            content_type="text/plain"
        )

    async def verify_privacy_txt(request):
        return web.Response(
            text="tiktok-developers-site-verification=9AMaLRt3zKWPyXzfmiIEGnYrfXMS5WFJ",
            content_type="text/plain"
        )

    async def tiktok_login(request):
        client_key = os.getenv("TIKTOK_CLIENT_KEY")

        redirect_uri = "https://everlight-world-production.up.railway.app/tiktok/callback"

        params = {
            "client_key": client_key,
            "scope": "user.info.basic,video.list",
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": "everlight"
        }

        login_url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode(params)

        raise web.HTTPFound(login_url)

    async def tiktok_callback(request):
        code = request.query.get("code")
        error = request.query.get("error")

        if error:
            return web.Response(text=f"TikTok Login Error: {error}")

        if not code:
            return web.Response(text="Authorization code tidak ditemukan.")

        client_key = os.getenv("TIKTOK_CLIENT_KEY")
        client_secret = os.getenv("TIKTOK_CLIENT_SECRET")

        redirect_uri = "https://everlight-world-production.up.railway.app/tiktok/callback"
        token_url = "https://open.tiktokapis.com/v2/oauth/token/"

        data = {
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                result = await response.json()

        if "access_token" not in result:
            return web.Response(
                text=f"Gagal mendapatkan TikTok access token: {result}"
            )

        access_token = result["access_token"]
        refresh_token = result.get("refresh_token")
        open_id = result.get("open_id")

        token_data = {
    "access_token": access_token,
    "refresh_token": refresh_token,
    "open_id": open_id
}

    with open("tiktok_token.json", "w") as f:
        json.dump(token_data, f)
        
    print("TikTok authorization berhasil!")
    print(f"TikTok Open ID: {open_id}")

    return web.Response(
            text="TikTok berhasil terhubung ke Everlight Bot!"
        )
        
    async def home_page(request):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Everlight World</title>
        </head>
        <body>
            <h1>Everlight World</h1>
            <p>Connect your TikTok account with Everlight Bot.</p>
            <a href="/tiktok/login">
                <button>Login with TikTok</button>
            </a>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")

async def start_web_server():
    app = web.Application()

    async def test_route(request):
        return web.Response(text="EVERLIGHT TEST OK")
    async def home_page(request):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Everlight World</title>
        </head>
        <body>
            <h1>Everlight World</h1>
            <p>Connect your TikTok account with Everlight Bot.</p>
            <a href="/tiktok/login">
                <button>Login with TikTok</button>
            </a>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")

    app.router.add_get("/test", test_route)
    app.router.add_get("/", home_page)
    app.router.add_get("/tiktok/login", tiktok_login)
    app.router.add_get("/cek-tiktok", verify_root_txt)
    
    app.router.add_get(
        "/{filename}.txt",
        verify_root_txt
    )
    
    app.router.add_get("/tiktok/callback", tiktok_callback)  

    app.router.add_get(
        "/terms/tiktok4qL77aFCylLLUtAlB6s3QVzGyUKHA071.txt",
        verify_terms_txt
    )

    app.router.add_get(
        "/privacy/tiktok9AMaLRt3zKWPyXzfmiIEGnYrfXMS5WFJ.txt",
        verify_privacy_txt
    )

    app.router.add_post("/tiktok/webhook", tiktok_webhook)
    app.router.add_get("/terms", terms_page)
    app.router.add_get("/privacy", privacy_page)
    
    app.router.add_get(
        "/tiktok7caxFt77pT4f9XdUEIWEeJIBBRo2HXUL.txt",
        tiktok_verify_file
    )
    
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"TikTok Webhook server berjalan di port {port}")
    
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN belum diisi di file .env")

bot.run(TOKEN)
