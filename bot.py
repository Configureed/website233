import discord
from discord.ext import commands
import sqlite3
import datetime
import random
import string
import asyncio
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import os

TOKEN = "MTQ4NzMyOTIyNTA5MzY3NzA5Ng.GxUSix.EuCCU9zHU9umgjrov3vqVk3Y6mdvf80ArRC0JU"
KEY_CHANNEL_ID = 1487318128634495097
DASHBOARD_CHANNEL_ID = 1487317963211276380
OWNER_KEY = "K7XM-9P42-3N8R-5V6W"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

conn = sqlite3.connect('keys.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS keys (
    key TEXT PRIMARY KEY,
    days INTEGER,
    expires TEXT,
    generated_by TEXT,
    generated_at TEXT,
    last_ip TEXT,
    last_username TEXT,
    status TEXT DEFAULT 'active'
)''')

c.execute('''CREATE TABLE IF NOT EXISTS logins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT,
    username TEXT,
    ip TEXT,
    login_time TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS banned_ips (
    ip TEXT PRIMARY KEY
)''')

conn.commit()

def generate_key():
    parts = []
    for i in range(5):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        parts.append(part)
    return '-'.join(parts)

def add_key(days, generated_by):
    key = generate_key()
    expires = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    c.execute("INSERT INTO keys (key, days, expires, generated_by, generated_at, status) VALUES (?, ?, ?, ?, ?, 'active')",
              (key, days, expires, generated_by, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    return key

def validate_key(key, ip=None, username=None):
    c.execute("SELECT days, expires, status FROM keys WHERE key = ?", (key,))
    row = c.fetchone()
    if not row:
        return False, "Key not found"
    days, expires, status = row
    if status != 'active':
        return False, "Key is revoked"
    if expires < datetime.datetime.now().strftime('%Y-%m-%d'):
        c.execute("UPDATE keys SET status = 'expired' WHERE key = ?", (key,))
        conn.commit()
        return False, "Key expired"
    if ip:
        c.execute("UPDATE keys SET last_ip = ?, last_username = ? WHERE key = ?", (ip, username, key))
        c.execute("INSERT INTO logins (key, username, ip, login_time) VALUES (?, ?, ?, ?)",
                  (key, username, ip, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    return True, expires

def get_all_keys():
    c.execute("SELECT key, days, expires, generated_by, last_ip, last_username, status FROM keys ORDER BY generated_at DESC")
    return c.fetchall()

def revoke_key(key):
    c.execute("UPDATE keys SET status = 'revoked' WHERE key = ?", (key,))
    conn.commit()
    return c.rowcount > 0

def ban_ip(ip):
    c.execute("INSERT OR IGNORE INTO banned_ips (ip) VALUES (?)", (ip,))
    conn.commit()

def is_ip_banned(ip):
    c.execute("SELECT 1 FROM banned_ips WHERE ip = ?", (ip,))
    return c.fetchone() is not None

def unban_ip(ip):
    c.execute("DELETE FROM banned_ips WHERE ip = ?", (ip,))
    conn.commit()

async def update_dashboard():
    channel = bot.get_channel(DASHBOARD_CHANNEL_ID)
    if not channel:
        return
    keys = get_all_keys()
    lines = []
    for k in keys[:25]:
        key, days, expires, gen_by, last_ip, last_user, status = k
        last_ip = last_ip or '-'
        last_user = last_user or '-'
        status_icon = "✅" if status == "active" else "❌"
        lines.append(f"{status_icon} `{key}` | {days}d | exp {expires} | {last_user} | {last_ip}")
    
    if not lines:
        lines = ["No keys yet"]
    
    content = "**== KEY DASHBOARD ==**\n```\n" + "\n".join(lines[:20]) + "\n```"
    
    async for msg in channel.history(limit=5):
        if msg.author == bot.user:
            await msg.edit(content=content)
            return
    
    await channel.send(content)

@bot.event
async def on_ready():
    print(f'Bot online: {bot.user}')
    await update_dashboard()

@bot.command(name='gen')
async def gen_key(ctx, days: int):
    if ctx.author.id not in [825052434980831262] and ctx.author.name != 'owner':
        await ctx.send("❌ No permission")
        return
    if days not in [1, 7, 30, 60, 90]:
        await ctx.send("Use: `/gen 1` `/gen 7` `/gen 30` `/gen 60` `/gen 90`")
        return
    key = add_key(days, str(ctx.author))
    await ctx.send(f"✅ Key generated: `{key}` ({days} days)")
    
    key_channel = bot.get_channel(KEY_CHANNEL_ID)
    if key_channel:
        await key_channel.send(f"🔑 New key: `{key}` | {days} days | by {ctx.author}")
    
    await update_dashboard()

@bot.command(name='keys')
async def list_keys(ctx):
    if ctx.author.id not in [825052434980831262]:
        await ctx.send("❌ No permission")
        return
    keys = get_all_keys()
    if not keys:
        await ctx.send("No keys")
        return
    msg = "**ALL KEYS**\n```\n"
    for k in keys[:30]:
        key, days, expires, gen_by, last_ip, last_user, status = k
        msg += f"{key} | {days}d | {expires} | {status} | {last_user}\n"
    msg += "```"
    await ctx.send(msg[:1900])

@bot.command(name='info')
async def key_info(ctx, key: str):
    if ctx.author.id not in [825052434980831262]:
        await ctx.send("❌ No permission")
        return
    c.execute("SELECT days, expires, generated_by, generated_at, last_ip, last_username, status FROM keys WHERE key = ?", (key.upper(),))
    row = c.fetchone()
    if not row:
        await ctx.send("Key not found")
        return
    days, expires, gen_by, gen_at, last_ip, last_user, status = row
    c.execute("SELECT username, ip, login_time FROM logins WHERE key = ? ORDER BY login_time DESC LIMIT 5", (key.upper(),))
    logins = c.fetchall()
    msg = f"**Key: {key}**\nDays: {days}\nExpires: {expires}\nStatus: {status}\nGenerated: {gen_at}\nLast User: {last_user or '-'}\nLast IP: {last_ip or '-'}\n"
    if logins:
        msg += "\n**Recent logins:**\n"
        for l in logins:
            msg += f"  {l[0]} | {l[1]} | {l[2]}\n"
    await ctx.send(msg[:1900])

@bot.command(name='revoke')
async def revoke_key_cmd(ctx, key: str):
    if ctx.author.id not in [825052434980831262]:
        await ctx.send("❌ No permission")
        return
    if revoke_key(key.upper()):
        await ctx.send(f"✅ Key `{key}` revoked")
        await update_dashboard()
    else:
        await ctx.send("Key not found")

@bot.command(name='banip')
async def ban_ip_cmd(ctx, ip: str):
    if ctx.author.id not in [825052434980831262]:
        await ctx.send("❌ No permission")
        return
    ban_ip(ip)
    await ctx.send(f"✅ IP `{ip}` banned")

@bot.command(name='unbanip')
async def unban_ip_cmd(ctx, ip: str):
    if ctx.author.id not in [825052434980831262]:
        await ctx.send("❌ No permission")
        return
    unban_ip(ip)
    await ctx.send(f"✅ IP `{ip}` unbanned")

@bot.command(name='dashboard')
async def dashboard_cmd(ctx):
    if ctx.author.id not in [825052434980831262]:
        await ctx.send("❌ No permission")
        return
    await update_dashboard()
    await ctx.send("✅ Dashboard updated")

app = Flask(__name__)
CORS(app)

@app.route('/validate', methods=['POST'])
def validate():
    data = request.json
    key = data.get('key', '').upper()
    ip = data.get('ip', '')
    username = data.get('username', '')
    
    if is_ip_banned(ip):
        return jsonify({'success': False, 'message': 'IP banned'})
    
    valid, result = validate_key(key, ip, username)
    if valid:
        return jsonify({'success': True, 'message': 'Valid', 'expires': result})
    else:
        return jsonify({'success': False, 'message': result})

@app.route('/keys', methods=['GET'])
def get_keys():
    keys = get_all_keys()
    return jsonify([{'key': k[0], 'days': k[1], 'expires': k[2], 'status': k[6]} for k in keys])

@app.route('/check', methods=['POST'])
def check():
    data = request.json
    key = data.get('key', '').upper()
    c.execute("SELECT expires, status FROM keys WHERE key = ?", (key,))
    row = c.fetchone()
    if not row:
        return jsonify({'valid': False, 'message': 'Key not found'})
    expires, status = row
    if status != 'active':
        return jsonify({'valid': False, 'message': 'Key revoked'})
    if expires < datetime.datetime.now().strftime('%Y-%m-%d'):
        return jsonify({'valid': False, 'message': 'Key expired'})
    return jsonify({'valid': True, 'expires': expires})

def run_flask():
    app.run(host='0.0.0.0', port=5001, debug=False)

threading.Thread(target=run_flask, daemon=True).start()
bot.run(TOKEN)