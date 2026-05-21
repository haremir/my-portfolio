FROM python:3.12-slim

# System deps for Reflex (Node.js) + build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl unzip gcc g++ && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python deps first (cache layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy project
COPY . .

# Initialize Reflex (creates .web dir)
RUN uv run reflex init

# Build production frontend
RUN uv run reflex export --frontend-only --no-zip

# Move exported frontend into place
RUN rm -rf .web/_static && mv frontend/* .web/_static/ 2>/dev/null || true

EXPOSE 8080

CMD ["uv", "run", "python", "prod_start.py"]
