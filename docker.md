# Guide complet : Utiliser Docker Compose avec BarmanBot (Dev & Prod)

Docker Compose est un outil qui permet de définir et de gérer plusieurs conteneurs Docker à partir d’un seul fichier `docker-compose.yml`. Il est idéal pour lancer des applications multi-services comme BarmanBot avec sa base de données, ses outils de dev, etc.

Depuis Docker Compose v2, on utilise la commande :
    docker compose
(sans tiret)

---

## Structure du fichier docker-compose.yml avec profils

```yaml
services:
  barmanbot:
    container_name: barmanbot
    build:
      context: .
    env_file: .env
    restart: unless-stopped
    volumes:
      - .:/app
    profiles: [dev, prod]
```

---

## Mode développement

Ce mode inclut :

- Montage du code local (`volumes`)

Lancer en mode dev :

```bash
docker compose --profile dev up
```

---

## Mode production

Ce mode utilise :

- L’image Docker finale
- Pas de montage de volume

Lancer en mode prod : (-d c'est pour le mode détaché, le terminal se ferme, mais le laisse en arrière plan)
    docker compose --profile prod up -d

---

## Commandes utiles

▶️ Démarrer les services :

```bash
docker compose --profile dev up
docker compose --profile prod up -d
```

⏹️ Arrêter les services :

```bash
docker compose down
```

🔁 Redémarrer :

```bash
docker compose restart
```

🔍 Voir les logs :

```bash
docker compose logs -f
```

🔨 Rebuild après modification :

```bash
docker compose --profile dev up --build
```

📋 Voir les profils disponibles :

```bash
docker compose config --profiles
```

---

## Bonnes pratiques

- Utilise des fichiers `.env.dev` et `.env.prod` si tu veux séparer les variables.
- Ne monte pas de volumes en production.
- Utilise `depends_on` pour garantir l’ordre de démarrage.
- Utilise `volumes` pour persister les données de la base.

---
