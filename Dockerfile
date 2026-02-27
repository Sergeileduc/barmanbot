FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

WORKDIR /app

# 1- Dépendances système pour WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    pango1.0-tools \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi8 \
    libxml2 \
    libxslt1.1 \
    libjpeg62-turbo \
    libpng16-16 \
    libfreetype6 \
    libharfbuzz0b \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2- Installation des dépendances Python
COPY pyproject.toml /app/
COPY . /app/
RUN pip install --no-cache-dir .

# 3- Télécharge et installe les binaires des navigateurs (Chromium ici)
# RUN python -m playwright install --with-deps chromium

# COPY . /app/

ENTRYPOINT ["python", "barmanbot.py"]
