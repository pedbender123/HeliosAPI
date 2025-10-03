import discord
import os
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
TARGET_SERVER_ID = int(os.getenv('DISCORD_SERVER_ID'))

# Carregar as duas URLs de webhook
N8N_WEBHOOK_URL_TEST = os.getenv('N8N_WEBHOOK_URL_TEST')
N8N_WEBHOOK_URL_PROD = os.getenv('N8N_WEBHOOK_URL_PROD')

# Criar uma lista com os webhooks que devem ser notificados
# O bot vai ignorar qualquer URL que não for encontrada no .env
WEBHOOK_URLS = [
    url for url in [N8N_WEBHOOK_URL_TEST, N8N_WEBHOOK_URL_PROD] if url
]


# Definir as permissões (intents) que o bot precisa
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True # Essencial para ler o conteúdo das mensagens

# Criar a instância do cliente do bot
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    """
    Função chamada quando o bot se conecta com sucesso ao Discord.
    """
    print('-----------------------------------------')
    print('--- INICIANDO DIAGNÓSTICO DE WEBHOCKS ---')
    print(f"  URL de Teste carregada: {N8N_WEBHOOK_URL_TEST}")
    print(f"  URL de Produção carregada: {N8N_WEBHOOK_URL_PROD}")
    print(f'--- FIM DO DIAGNÓSTICO ---')
    print('-----------------------------------------')
    
    print(f'Bot Helios conectado como {client.user}')
    print(f'Monitorando o servidor com ID: {TARGET_SERVER_ID}')
    if not WEBHOOK_URLS:
        print('AVISO: Nenhuma URL de webhook foi configurada no arquivo .env!')
    else:
        print(f'Enviando notificações para {len(WEBHOOK_URLS)} webhook(s).')
    print('-----------------------------------------')

@client.event
async def on_message(message):
    """
    Função chamada para cada nova mensagem em qualquer canal que o bot tem acesso.
    """
    # 1. Ignorar mensagens do próprio bot
    if message.author == client.user:
        return

    # 2. Verificar se a mensagem veio de um servidor (ignorar DMs)
    if not message.guild:
        return

    # 3. Verificar se a mensagem é do servidor correto (PBPM)
    if message.guild.id != TARGET_SERVER_ID:
        return

    # Se todas as verificações passaram, preparamos os dados para o n8n
    print(f"Nova mensagem detectada no servidor {message.guild.name} no canal #{message.channel.name}")

    # Extrair os nomes dos cargos do membro
    member_roles = [role.name for role in message.author.roles]

    # Montar o payload (dados a serem enviados) em formato JSON
    payload = {
        "chat": {
            "id": message.channel.id,
            "name": message.channel.name
        },
        "member": {
            "id": message.author.id,
            "name": message.author.name,
            "displayName": message.author.display_name,
            "roles": member_roles
        },
        "message": {
            "id": message.id,
            "text": message.content
        }
    }

    # Enviar a notificação para CADA webhook na nossa lista
    for url in WEBHOOK_URLS:
        try:
            response = requests.post(url, json=payload, timeout=10)
            # Levanta um erro se a requisição falhou (status code 4xx ou 5xx)
            response.raise_for_status()
            print(f"Mensagem de '{message.author.name}' enviada para {url} com sucesso! Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"ERRO: Falha ao enviar a mensagem para {url}. Erro: {e}")

    print('-----------------------------------------')


# Iniciar o bot usando o token
print("Iniciando o bot Helios...")
client.run(DISCORD_BOT_TOKEN)