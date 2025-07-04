import discord
from discord.ext import commands
import json
import os
from flask import Flask
from threading import Thread

# --- Flask server (mantener online) ---
app = Flask(__name__)


@app.route('/')
def home():
    return "I'm alive, bro."


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


keep_alive()

# --- Discord Bot Config ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

POINTS_FILE = "points.json"
ALLOWED_ROLES = ["Capitán", "Líder", "Gerente", "Oficial"]


def load_points():
    if os.path.exists(POINTS_FILE):
        with open(POINTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_points(points):
    with open(POINTS_FILE, "w") as f:
        json.dump(points, f)


points = load_points()


def is_allowed(ctx):
    return any(role.name in ALLOWED_ROLES for role in ctx.author.roles)


@bot.event
async def on_ready():
    print(f"{bot.user} está en línea.")


@bot.command()
async def addpoints(ctx, *args):
    try:
        amount = int(args[-1])
        members = ctx.message.mentions
        if not members:
            await ctx.send("❌ Tienes que mencionar al menos a un usuario.")
            return

        for member in members:
            user_id = str(member.id)
            if user_id not in points:
                points[user_id] = 0
            points[user_id] += amount

        save_points(points)

        names = ', '.join([member.name for member in members])
        await ctx.send(f"✅ Se añadieron {amount} puntos a: {names}")
    except (ValueError, IndexError):
        await ctx.send(
            "❌ Usa el comando así: `!addpoints @usuario1 @usuario2 cantidad`")


@bot.command()
async def removepoints(ctx, *args):
    try:
        amount = int(args[-1])
        members = ctx.message.mentions
        if not members:
            await ctx.send("❌ Tienes que mencionar al menos a un usuario.")
            return

        for member in members:
            user_id = str(member.id)
            if user_id not in points:
                points[user_id] = 0
            points[user_id] -= amount

        with open("points.json", "w") as f:
            json.dump(points, f)

        names = ', '.join([member.name for member in members])
        await ctx.send(f"✅ Se restaron {amount} puntos a: {names}")
    except (ValueError, IndexError):
        await ctx.send(
            "❌ Usa el comando así: `!removepoints @usuario1 @usuario2 cantidad`"
        )


@bot.command()
async def mypoints(ctx):
    user_id = str(ctx.author.id)
    user_points = points.get(user_id, 0)
    embed = discord.Embed(title="🎯 Tus Puntos",
                          description=f"Tienes **{user_points}** puntos.",
                          color=0x3498db)
    await ctx.send(embed=embed)


@bot.command()
async def ranking(ctx):
    if not points:
        return await ctx.send("No hay puntos registrados todavía.")
    sorted_points = sorted(points.items(), key=lambda x: x[1], reverse=True)
    description = ""
    for i, (user_id, score) in enumerate(sorted_points[:10], 1):
        member = ctx.guild.get_member(int(user_id))
        name = member.display_name if member else f"User {user_id}"
        description += f"**{i}. {name}** — {score} puntos\n"
    embed = discord.Embed(title="🏆 Ranking de Puntos",
                          description=description,
                          color=0xf1c40f)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_any_role(*ALLOWED_ROLES)
async def resetpoints(ctx):
    global points
    points = {}
    save_points(points)
    await ctx.send("🔄 Todos los puntos han sido reseteados.")


bot.run(os.environ["TOKEN"])
