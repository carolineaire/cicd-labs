
FROM python:3.12-slim

WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt requirements-dev.txt ./

# Installer toutes les dépendances
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copier le code de l'application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "minishop.api:app", "--host", "0.0.0.0", "--port", "8000"]
