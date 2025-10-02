FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# A variável de ambiente DOCKER_HOST é necessária para o SDK do Docker se comunicar
# com o daemon do host a partir de dentro do contêiner.
CMD ["python", "log_monitor.py"]