import os
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

VOTE_CHANNEL_NAME = "▏🗳️・𝗩otes"
DEPUTE_ROLE = "・Député"
PRESIDENT_ROLES = [
    "・Président de la Chambre des Députés",
    "・Vice-Président de la Chambre des Députés"
]

scrutins = {}  # stock en mémoire


# ---------------- VOTE BUTTONS ----------------

class VoteView(discord.ui.View):
    def __init__(self, scrutin_id):
        super().__init__(timeout=None)
        self.scrutin_id = scrutin_id

    async def register_vote(self, interaction, choice):
        guild = interaction.guild
        user = interaction.user

        role = discord.utils.get(guild.roles, name=DEPUTE_ROLE)
        if role not in user.roles:
            return await interaction.response.send_message(
                "❌ Tu n’es pas député.", ephemeral=True
            )

        scrutin = scrutins.get(self.scrutin_id)
        if not scrutin or not scrutin["open"]:
            return await interaction.response.send_message(
                "❌ Scrutin fermé.", ephemeral=True
            )

        scrutin["votes"][user.id] = choice

        await interaction.response.send_message(
            "✅ Vote enregistré.", ephemeral=True
        )

    @discord.ui.button(label="Pour", style=discord.ButtonStyle.green)
    async def pour(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, "pour")

    @discord.ui.button(label="Contre", style=discord.ButtonStyle.red)
    async def contre(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, "contre")

    @discord.ui.button(label="Abstention", style=discord.ButtonStyle.gray)
    async def abstention(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, "abstention")


# ---------------- READY ----------------

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} est connecté !")


# ---------------- OUVRIR SCRUTIN ----------------

@bot.tree.command(name="scrutin_ouvrir", description="Ouvre un scrutin")
@app_commands.describe(titre="Titre du vote")
async def scrutin_ouvrir(interaction: discord.Interaction, titre: str):

    guild = interaction.guild
    user = interaction.user

    if not any(r.name in PRESIDENT_ROLES for r in user.roles):
        return await interaction.response.send_message(
            "❌ Tu n’as pas le droit d’ouvrir un scrutin.",
            ephemeral=True
        )

    channel = discord.utils.get(guild.channels, name=VOTE_CHANNEL_NAME)
    if not channel:
        return await interaction.response.send_message(
            "❌ Salon de vote introuvable.",
            ephemeral=True
        )

    scrutin_id = str(len(scrutins) + 1)

    scrutins[scrutin_id] = {
        "title": titre,
        "open": True,
        "votes": {}
    }

    view = VoteView(scrutin_id)

    await channel.send(
        f"🏛️ **Scrutin ouvert**\n\n📜 {titre}",
        view=view
    )

    await interaction.response.send_message(
        f"✅ Scrutin ouvert dans {VOTE_CHANNEL_NAME}",
        ephemeral=True
    )


# ---------------- FERMER SCRUTIN ----------------

@bot.tree.command(name="scrutin_fermer", description="Ferme le scrutin")
async def scrutin_fermer(interaction: discord.Interaction):

    guild = interaction.guild
    user = interaction.user

    if not any(r.name in PRESIDENT_ROLES for r in user.roles):
        return await interaction.response.send_message(
            "❌ Tu n’as pas le droit.",
            ephemeral=True
        )

    if not scrutins:
        return await interaction.response.send_message(
            "❌ Aucun scrutin actif.",
            ephemeral=True
        )

    scrutin_id, scrutin = list(scrutins.items())[-1]
    scrutin["open"] = False

    results = {"pour": 0, "contre": 0, "abstention": 0}

    for v in scrutin["votes"].values():
        results[v] += 1

    text = (
        f"🏛️ Résultats du scrutin\n\n"
        f"📜 {scrutin['title']}\n\n"
        f"✅ Pour : {results['pour']}\n"
        f"❌ Contre : {results['contre']}\n"
        f"⚪ Abstention : {results['abstention']}\n"
        f"\n👥 Total : {len(scrutin['votes'])} votants"
    )

    try:
        await user.send(text)
    except:
        pass

    await interaction.response.send_message(
        "🔒 Scrutin fermé. Résultats envoyés en MP.",
        ephemeral=True
    )


bot.run(TOKEN)
