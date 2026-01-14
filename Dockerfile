FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

WORKDIR /app

# ÉTAPE X: Installation de wkhtmltopdf (et autres trucs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wkhtmltopdf \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    libfreetype6 \
    libx11-6 \
    fontconfig \
    fonts-dejavu-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ÉTAPE X: Installation des dépendances Python
COPY pyproject.toml /app/
COPY . /app/
RUN pip install --no-cache-dir .

# ÉTAPE X : Télécharge et installe les binaires des navigateurs (Chromium ici)
# RUN python -m playwright install --with-deps chromium

# COPY . /app/

ENTRYPOINT ["python", "barmanbot.py"]
