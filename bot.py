import discord
from discord.ext import commands
import random
import string
import json
from flask import Flask, render_template_string
import threading

# --- CONFIG ---

TOKEN = 'MTM4ODYwODMyMzE4NzkwNDY4Mw.GC_uyh.5hccNNdMHhydBF02M1PGOhyenqiWXAeLi4C25A'
CHANNEL_ID = 1390039916657770526
EMAIL_DOMAIN = "exemple.com"
EMAILS_FILE = "emails.json"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

app = Flask(__name__)

# --- Fonctions utilitaires ---

def load_emails():
    try:
        with open(EMAILS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"emails": []}

def save_emails(data):
    with open(EMAILS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def generate_email():
    user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    email = f"{user}@{EMAIL_DOMAIN}"
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return email, password

# --- Discord UI ---

class ConnectButton(discord.ui.View):
    def __init__(self, email):
        super().__init__()
        url = f"https://mail.google.com/mail/u/0/#inbox?authuser={email}"
        self.add_item(discord.ui.Button(label="Se connecter", style=discord.ButtonStyle.link, url=url))

# --- Discord Bot events ---

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id != CHANNEL_ID:
        return

    if message.content.strip() == "!gmail":
        try:
            await message.delete()
        except discord.Forbidden:
            print("❌ Pas la permission de supprimer le message.")
        except discord.NotFound:
            pass

        email, password = generate_email()

        # Charger emails existants
        data = load_emails()
        # Ajouter le nouveau
        data["emails"].append({
            "email": email,
            "password": password,
            "has_mail": False  # Pour évolution future
        })
        save_emails(data)

        embed = discord.Embed(title="📧 Compte Email créé", color=discord.Color.green())
        embed.add_field(name="Email", value=email, inline=False)
        embed.add_field(name="Mot de passe", value=password, inline=False)

        view = ConnectButton(email)
        await message.channel.send(embed=embed, view=view)

# --- Flask Web Server ---

@app.route('/')
def index():
    data = load_emails()
    emails = data.get("emails", [])

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
      <title>Emails créés</title>
      <style>
        /* Menu hamburger */
        #menuToggle {
          display: block;
          position: relative;
          top: 50px;
          left: 50px;
          z-index: 1;
          -webkit-user-select:none;
          user-select:none;
        }
        #menuToggle input {
          display: block;
          width: 40px;
          height: 32px;
          position: absolute;
          top: -7px;
          left: -5px;
          cursor: pointer;
          opacity: 0; /* caché */
          z-index: 2;
          -webkit-touch-callout: none;
        }
        #menuToggle span {
          display: block;
          width: 33px;
          height: 4px;
          margin-bottom: 5px;
          position: relative;
          background: #cdcdcd;
          border-radius: 3px;
          z-index: 1;
          transform-origin: 4px 0px;
          transition: transform 0.5s cubic-bezier(0.77,0.2,0.05,1.0),
                      background 0.5s cubic-bezier(0.77,0.2,0.05,1.0),
                      opacity 0.55s ease;
        }
        #menu {
          position: absolute;
          width: 250px;
          margin: -100px 0 0 -50px;
          padding: 50px;
          padding-top: 125px;
          background: #ededed;
          list-style-type: none;
          -webkit-font-smoothing: antialiased;
          transform-origin: 0% 0%;
          transform: translate(-100%, 0);
          transition: transform 0.5s cubic-bezier(0.77,0.2,0.05,1.0);
          box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        }
        #menuToggle input:checked ~ ul {
          transform: none;
        }
        #menu li {
          padding: 10px 0;
          font-size: 18px;
          border-bottom: 1px solid #ccc;
        }
        #menu li a {
          color: #333;
          text-decoration: none;
          cursor: pointer;
        }
      </style>
    </head>
    <body>
      <div id="menuToggle">
        <input type="checkbox" />
        <span></span>
        <span></span>
        <span></span>

        <ul id="menu">
        {% for e in emails %}
          <li><a href="https://mail.google.com/mail/u/0/#inbox?authuser={{e.email}}" target="_blank">{{ e.email }}</a></li>
        {% endfor %}
        </ul>
      </div>
    </body>
    </html>
    '''
    return render_template_string(html, emails=emails)

# --- Lancement parallèle bot + serveur web ---

def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    # Démarrer Flask en thread
    threading.Thread(target=run_flask).start()
    # Démarrer le bot Discord (bloquant)
    bot.run(TOKEN)
