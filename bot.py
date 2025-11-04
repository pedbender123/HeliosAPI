import discord
import os
import requests
import threading
import asyncio
import re               # <--- CORRIGIDO
import datetime         # <--- CORRIGIDO
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Importa nossos novos módulos
import db
import ai_analyzer

# ===============================================
# CONFIGURAÇÃO
# ===============================================
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
ERROR_CHANNEL_ID = int(os.getenv('DISCORD_ERROR_CHANNEL_ID'))

# Regex para parsear a mensagem do vps-log-agent
LOG_PARSE_REGEX = re.compile(
    r"\*\*Container:\*\* `(.*?)`\n\*\*Log:\*\*\n```([\s\S]*)```", 
    re.MULTILINE
)

# ===============================================
# BOT DISCORD (APENAS ENVIO)
# ===============================================
intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('-----------------------------------------')
    print(f'Helios Central conectado como {client.user}')
    print(f'Enviando relatórios para o canal ID: {ERROR_CHANNEL_ID}')
    print('-----------------------------------------')
    # Garante que o banco de dados e tabelas existam na inicialização
    # Isso agora tenta conectar ao seu DB externo e criar a tabela
    print("Inicializando conexão com o banco de dados externo...")
    db.init_db()
        
async def send_error_report(embed):
    try:
        channel = client.get_channel(ERROR_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
            print("Relatório de erro enviado ao Discord.")
        else:
            print(f"ERRO: Canal com ID {ERROR_CHANNEL_ID} não encontrado.")
    except Exception as e:
        print(f"ERRO ao tentar enviar mensagem para o Discord: {e}")

# ===============================================
# SERVIDOR WEB (Flask)
# ===============================================
app = Flask(__name__)

@app.route('/mensagem', methods=['POST'])
def receive_message():
    data = request.get_json()
    remetente = data.get('remetente') # Ex: "VPS-Producao-01"
    mensagem = data.get('mensagem') # Ex: "**Container:** `bot-xyz`\n**Log:**\n```erro...```"

    if not remetente or not mensagem:
        return jsonify({"status": "error", "message": "remetente e mensagem são obrigatórios"}), 400

    print(f"\n--- Novo Alerta Recebido de: {remetente} ---")
    
    # 1. Parsear a mensagem
    match = LOG_PARSE_REGEX.search(mensagem)
    if not match:
        print(f"ERRO: Formato de log irreconhecível recebido de {remetente}.")
        return jsonify({"status": "error", "message": "Formato de log inválido"}), 400
    
    container_name = match.group(1)
    raw_log = match.group(2)
    print(f"Container: {container_name}")

    # 2. Pedir análise da IA
    ai_summary = ai_analyzer.get_error_summary(raw_log)

    # 3. Salvar TUDO no banco de dados
    try:
        db.log_error_to_db(remetente, container_name, raw_log, ai_summary)
    except Exception as e:
        print(f"Falha GRAVE ao salvar log no DB: {e}")

    # 4. Criar o Embed bonito para o Discord
    embed = discord.Embed(
        title=f"🚨 Alerta de Erro: `{container_name}`",
        description=f"Um erro foi detectado na **{remetente}**.",
        color=discord.Color.red()
    )
    embed.add_field(name="🤖 Resumo da IA (Codestral)", value=f"```{ai_summary}```", inline=False)
    embed.add_field(name="📄 Log Bruto (Snippet)", value=f"```{raw_log[:1000]}...```", inline=False)
    embed.set_footer(text=f"Servidor: {remetente} | Container: {container_name}")
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

    # 5. Enviar para o Discord (de forma segura entre threads)
    future = asyncio.run_coroutine_threadsafe(send_error_report(embed), client.loop)
    future.result(timeout=10) # Espera o envio ser concluído

    return jsonify({"status": "success", "message": "Log recebido e reportado."})


def run_flask_app():
    app.run(host='0.0.0.0', port=5002)

# ===============================================
# INICIALIZAÇÃO
# ===============================================
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()

    print("Iniciando Helios Central (Bot e API)...")
    client.run(DISCORD_BOT_TOKEN)