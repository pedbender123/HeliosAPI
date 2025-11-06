import os
from openai import OpenAI

# --- CORREÇÃO AQUI ---
# Ler as variáveis do .env para o Codestral local
CODESTRAL_URL = os.getenv("CODESTRAL_API_URL") # Vem do .env (http://ollama:11434/v1)
CODESTRAL_KEY = os.getenv("CODESTRAL_API_KEY") # Vem do .env (ollama)

# Configurar o cliente para apontar para o Ollama
client = OpenAI(
    base_url=CODESTRAL_URL,
    api_key=CODESTRAL_KEY
)

SYSTEM_PROMPT = """
Você é um Gerente de SRE (Site Reliability Engineering) sênior.
Sua tarefa é analisar um log de erro de um container Docker.
Seu relatório deve ser conciso e direto ao ponto, em português.
O relatório deve conter:
1.  **O Problema:** Qual é o erro principal (ex: "Connection Timeout", "NullPointerException")?
2.  **Causa Provável:** O que provavelmente causou isso?
3.  **Ação Recomendada:** O que o desenvolvedor deve verificar? (Seja específico, ex: "Verificar a string de conexão do banco" ou "Checar se a API externa está online").
"""

def get_error_summary(raw_log: str) -> str:
    """Usa o Codestral local (via Ollama) para analisar um log de erro e gerar um resumo."""
    
    # --- CORREÇÃO AQUI ---
    print(f"Enviando log para análise local (Codestral em {CODESTRAL_URL})...")
    
    try:
        completion = client.chat.completions.create(
            
            # --- CORREÇÃO AQUI ---
            model="codestral:latest", # Apontando para o modelo local
            
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analise o seguinte log de erro:\n\n```{raw_log}```"}
            ],
            temperature=0.3,
        )
        summary = completion.choices[0].message.content
        print("Resumo da IA recebido.")
        return summary
    except Exception as e:
        # --- CORREÇÃO AQUI ---
        print(f"Falha ao contatar a IA (Codestral em {CODESTRAL_URL}): {e}")
        return "Falha ao analisar o log com a IA (Codestral). Verifique o log bruto."
