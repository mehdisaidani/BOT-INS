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
async def addpoints(ctx, member: discord.Member, amount: int):
    if not is_allowed(ctx):
        return await ctx.send("🚫 No tienes permiso para usar este comando.")
    user_id = str(member.id)
    points[user_id] = points.get(user_id, 0) + amount
    save_points(points)
    embed = discord.Embed(
        title="✅ Puntos Añadidos",
        description=f"{amount} puntos añadidos a {member.mention}",
        color=0x00ff00)
    await ctx.send(embed=embed)


@bot.command()
async def removepoints(ctx, member: discord.Member, amount: int):
    if not is_allowed(ctx):
        return await ctx.send("🚫 No tienes permiso para usar este comando.")
    user_id = str(member.id)
    points[user_id] = points.get(user_id, 0) - amount
    save_points(points)
    embed = discord.Embed(
        title="⚠️ Puntos Removidos",
        description=f"{amount} puntos removidos de {member.mention}",
        color=0xff0000)
    await ctx.send(embed=embed)


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
        description += f"**{i}. {name}** — {score} puntos\\n"
    embed = discord.Embed(title="🏆 Ranking de Puntos",
                          description=description,
                          color=0xf1c40f)
    await ctx.send(embed=embed)


bot.run(os.environ["TOKEN"])
