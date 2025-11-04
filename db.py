import mysql.connector
from mysql.connector import errorcode
import os
import time

DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME')
}

TABLES = {}
TABLES['error_logs'] = (
    "CREATE TABLE IF NOT EXISTS `error_logs` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,"
    "  `vps_name` varchar(100) NOT NULL,"
    "  `container_name` varchar(255) NOT NULL,"
    "  `raw_log` text NOT NULL,"
    "  `ai_summary` text,"
    "  `status` varchar(50) DEFAULT 'reported',"
    "  PRIMARY KEY (`id`)"
    ") ENGINE=InnoDB"
)

def get_db_connection():
    """Tenta conectar ao banco de dados com retentativas."""
    attempts = 5
    delay = 5
    for i in range(attempts):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
        except mysql.connector.Error as err:
            print(f"Erro ao conectar ao MySQL (Host: {DB_CONFIG['host']}): {err}")
            if i < attempts - 1:
                print(f"Tentando novamente em {delay} segundos...")
                time.sleep(delay)
            else:
                print("Falha ao conectar ao MySQL após várias tentativas.")
                return None

def init_db():
    """Garante que a tabela 'error_logs' exista no banco 'db_apps'."""
    conn = get_db_connection()
    if not conn:
        print("Falha ao conectar ao DB. Tabela não verificada.")
        return

    cursor = conn.cursor()
    try:
        print(f"Conectado ao DB '{DB_CONFIG['database']}'. Verificando/Criando tabela 'error_logs'...")
        cursor.execute(TABLES['error_logs'])
        print("Tabela 'error_logs' pronta.")
    except mysql.connector.Error as err:
        print(f"Erro ao verificar/criar tabela: {err.msg}")
    finally:
        cursor.close()
        conn.close()

def log_error_to_db(vps_name, container_name, raw_log, ai_summary=""):
    """Insere um novo registro de erro no banco de dados."""
    conn = get_db_connection()
    if not conn:
        print("Falha ao logar no DB: Sem conexão.")
        return None
        
    cursor = conn.cursor()
    query = (
        "INSERT INTO error_logs (vps_name, container_name, raw_log, ai_summary) "
        "VALUES (%s, %s, %s, %s)"
    )
    try:
        cursor.execute(query, (vps_name, container_name, raw_log, ai_summary))
        conn.commit()
        log_id = cursor.lastrowid
        print(f"Erro logado no DB com ID: {log_id}")
        return log_id
    except mysql.connector.Error as err:
        print(f"Erro ao inserir no DB: {err}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()