import discord
import os
import requests
from dotenv import load_dotenv
import threading
import asyncio
from flask import Flask, request, jsonify

# ===============================================
# SEÇÃO DE CONFIGURAÇÃO
# ===============================================
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
TARGET_SERVER_ID = int(os.getenv('DISCORD_SERVER_ID'))
N8N_WEBHOOK_URL_TEST = os.getenv('N8N_WEBHOOK_URL_TEST')
N8N_WEBHOOK_URL_PROD = os.getenv('N8N_WEBHOOK_URL_PROD')

WEBHOOK_URLS = [
    url for url in [N8N_WEBHOOK_URL_TEST, N8N_WEBHOOK_URL_PROD] if url
]

# ===============================================
# SEÇÃO DO BOT DISCORD (discord.py)
# ===============================================
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('-----------------------------------------')
    print(f'Bot Helios conectado como {client.user}')
    print(f'Monitorando o servidor com ID: {TARGET_SERVER_ID}')
    print('-----------------------------------------')

@client.event
async def on_message(message):
    if message.author == client.user or not message.guild or message.guild.id != TARGET_SERVER_ID:
        return

    print(f"Nova mensagem de '{message.author.name}' detectada no canal #{message.channel.name}")

    payload = {
        "chat": {"id": str(message.channel.id), "name": message.channel.name},
        "member": {"id": str(message.author.id), "name": message.author.name, "displayName": message.author.display_name, "roles": [role.name for role in message.author.roles]},
        "message": {"id": str(message.id), "text": message.content}
    }

    for url in WEBHOOK_URLS:
        try:
            requests.post(url, json=payload, timeout=10).raise_for_status()
            print(f"  -> Webhook enviado para {url}")
        except requests.exceptions.RequestException as e:
            print(f"  -> ERRO ao enviar para {url}: {e}")
    print('-----------------------------------------')

# Função assíncrona para enviar mensagens, para ser chamada pelo Flask
async def send_discord_message(channel_id, message_content):
    try:
        channel = client.get_channel(int(channel_id))
        if channel:
            await channel.send(message_content)
            return True
        else:
            print(f"ERRO: Canal com ID {channel_id} não encontrado.")
            return False
    except Exception as e:
        print(f"ERRO ao tentar enviar mensagem para o canal {channel_id}: {e}")
        return False

# ===============================================
# SEÇÃO DO SERVIDOR WEB (Flask)
# ===============================================
app = Flask(__name__)

@app.route('/send-reply', methods=['POST'])
def send_reply():
    data = request.get_json()
    channel_id = data.get('channel_id')
    message = data.get('message')

    if not channel_id or not message:
        return jsonify({"status": "error", "message": "channel_id e message são obrigatórios"}), 400

    # Como o Flask roda numa thread separada, precisamos de uma forma segura
    # de chamar a função assíncrona do bot. Usamos run_coroutine_threadsafe.
    future = asyncio.run_coroutine_threadsafe(send_discord_message(channel_id, message), client.loop)
    
    try:
        # Espera pelo resultado (opcional, mas bom para ter a certeza)
        result = future.result(timeout=10) 
        if result:
            return jsonify({"status": "success", "message": "Mensagem enviada com sucesso!"})
        else:
            return jsonify({"status": "error", "message": "Falha ao enviar a mensagem."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Erro interno: {e}"}), 500


def run_flask_app():
    # O servidor Flask vai rodar na porta 5002 DENTRO do contentor
    app.run(host='0.0.0.0', port=5002)

# ===============================================
# INICIALIZAÇÃO
# ===============================================
if __name__ == "__main__":
    # Inicia o servidor Flask numa thread separada para não bloquear o bot
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()

    # Inicia o bot do Discord
    print("Iniciando o bot Helios e o servidor de API...")
    client.run(DISCORD_BOT_TOKEN)