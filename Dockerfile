FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy only what the bot needs
COPY harun_site/telegram_bot/ harun_site/telegram_bot/
COPY harun_site/utils/ harun_site/utils/
COPY harun_site/state/ harun_site/state/
COPY harun_site/theme.py harun_site/theme.py
COPY harun_site/__init__.py harun_site/__init__.py
COPY data/ data/
COPY posts/ posts/
COPY run_telegram_bot.py .
COPY prod_start.py .

CMD ["uv", "run", "python", "prod_start.py"]
