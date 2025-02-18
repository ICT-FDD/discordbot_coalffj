# Utiliser une image Python légère
FROM python:3.9-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /bot

# Copier les fichiers nécessaires dans le conteneur
COPY . .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Définir la commande de démarrage du bot
CMD ["python", "core.py"]
