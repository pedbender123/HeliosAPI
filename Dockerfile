# Usar uma imagem base oficial do Python
FROM python:3.10-slim

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar o arquivo de dependências
COPY requirements.txt .

# Instalar as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto do código do projeto para o diretório de trabalho
COPY . .

# Comando para executar o bot quando o contêiner iniciar
CMD ["python", "bot.py"]