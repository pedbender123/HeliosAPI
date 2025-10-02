import docker
import requests
import time
import os

# Webhook para enviar os logs de erro (fixo, como solicitado)
ERROR_LOG_WEBHOOK = "https://n8n.pbpmdev.com/webhook/5d102a17-9fab-4baa-95f6-127aa760d0dc"

# Nome do contêiner a ser monitorado
TARGET_CONTAINER_NAME = "helios-bot"

def send_log_to_webhook(log_message):
    """Envia uma mensagem de log para o webhook."""
    try:
        payload = {"text": f"🚨 **Erro no Helios Bot**:\n```\n{log_message}\n```"}
        response = requests.post(ERROR_LOG_WEBHOOK, json=payload, timeout=10)
        response.raise_for_status()
        print(f"Log de erro enviado com sucesso!")
    except requests.exceptions.RequestException as e:
        print(f"Falha ao enviar log para o webhook. Erro: {e}")

def monitor_logs():
    """Monitora os logs de um contêiner Docker e envia erros para um webhook."""
    print("Iniciando monitor de logs...")
    client = docker.from_env()

    while True:
        try:
            container = client.containers.get(TARGET_CONTAINER_NAME)
            print(f"Monitorando logs do contêiner '{TARGET_CONTAINER_NAME}'...")
            # 'since' garante que não pegamos logs antigos a cada reconexão
            for log in container.logs(stream=True, follow=True, since=int(time.time())):
                log_line = log.decode('utf-8').strip()
                # Filtra por linhas que contenham "ERROR" (graças ao logging que adicionamos)
                if "ERROR" in log_line:
                    print(f"Erro detectado: {log_line}")
                    send_log_to_webhook(log_line)
        except docker.errors.NotFound:
            print(f"Contêiner '{TARGET_CONTAINER_NAME}' não encontrado. Tentando novamente em 30 segundos...")
            time.sleep(30)
        except Exception as e:
            print(f"Ocorreu um erro inesperado no monitor: {e}. Reiniciando em 30 segundos...")
            time.sleep(30)

if __name__ == "__main__":
    monitor_logs()