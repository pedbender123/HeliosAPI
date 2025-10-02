# bot.py (versão modificada)
import discord
import os
import requests
import logging
from dotenv import load_dotenv

# Configuração básica do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
TARGET_SERVER_ID = int(os.getenv('DISCORD_SERVER_ID'))
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')

# ... (o resto do seu código de intents e cliente)
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    """
    Função chamada quando o bot se conecta com sucesso ao Discord.
    """
    logging.info(f'Bot Helios conectado como {client.user}')
    logging.info(f'Monitorando o servidor com ID: {TARGET_SERVER_ID}')
    logging.info('-----------------------------------------')

@client.event
async def on_message(message):
    """
    Função chamada para cada nova mensagem em qualquer canal que o bot tem acesso.
    """
    if message.author == client.user:
        return

    if not message.guild:
        return

    if message.guild.id != TARGET_SERVER_ID:
        return

    logging.info(f"Nova mensagem detectada no servidor {message.guild.name} no canal #{message.channel.name}")

    member_roles = [role.name for role in message.author.roles]

    payload = {
        "chat": { "id": message.channel.id, "name": message.channel.name },
        "member": { "id": message.author.id, "name": message.author.name, "displayName": message.author.display_name, "roles": member_roles },
        "message": { "id": message.id, "text": message.content }
    }

    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"Mensagem de '{message.author.name}' enviada para o n8n com sucesso! Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Falha ao enviar a mensagem para o n8n. Erro: {e}")

    logging.info('-----------------------------------------')

logging.info("Iniciando o bot Helios...")
client.run(DISCORD_BOT_TOKEN)