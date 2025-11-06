import os
from openai import OpenAI

# --- MUDANÇA AQUI ---
# Removemos a configuração de 'base_url' e 'api_key' do Ollama.
# O cliente agora vai ler a variável 'OPENAI_API_KEY' do ambiente.
client = OpenAI()
# A API key será lida automaticamente de os.getenv('OPENAI_API_KEY')

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
    """Usa o GPT-4o-mini para analisar um log de erro e gerar um resumo."""
    print("Enviando log para análise da OpenAI (GPT-4o-mini)...")
    try:
        completion = client.chat.completions.create(
            
            # --- MUDANÇA AQUI ---
            model="gpt-4o-mini", # Alterado de "codestral:latest"
            
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
        # --- MUDANÇA AQUI ---
        print(f"Falha ao contatar a API da OpenAI: {e}")
        return "Falha ao analisar o log com a IA (OpenAI). Verifique o log bruto."
