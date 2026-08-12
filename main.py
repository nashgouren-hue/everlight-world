import os
import discord
import io
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
from aiohttp import web


TOKEN = os.getenv("DISCORD_TOKEN")

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

@bot.event
async def on_ready():
    print(f"==============================")
    print(f"Everlight Bot ONLINE!")
    print(f"Login sebagai: {bot.user}")
    print(f"==============================")


@bot.tree.command(name="hello", description="Say hello to Everlight!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"✨ Hello {interaction.user.mention}! Welcome to Everlight!"
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
async def start_web_server():
    app = web.Application()
    app.router.add_post("/tiktok/webhook", tiktok_webhook)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"TikTok Webhook server berjalan di port {port}")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN belum diisi di file .env")

bot.run(TOKEN)
