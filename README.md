# Sowaa MVP Telegram Bot

## Requirements
- Docker and docker-compose
- Environment variables configured in `.env` (refer to `.env.example`)

## Setup & Running

1. Copy `.env.example` to `.env` and fill the configurations:
   - `BOT_TOKEN`: Your Telegram Bot Token.
   - `ADMIN_IDS`: Comma-separated admin Telegram IDs.
   - `ENCRYPTION_KEY`: A 32-url-safe base64-encoded string (you can generate one using `cryptography.fernet.Fernet.generate_key()`).
   - `REDIS_URL`: Connection string for Redis.
   - `DATABASE_URL`: Connection string for PostgreSQL.

2. Build and start the services using `docker-compose`:
```bash
docker-compose up -d --build
```

3. Run migrations:
```bash
docker-compose exec bot alembic upgrade head
```

4. You can seed a test document template by running:
```bash
docker-compose exec bot python -m bot.seed_template
```

## Running Tests
Tests use `pytest` and `aiosqlite` without depending on Docker. Ensure you have installed the test dependencies from `requirements.txt`:
```bash
pip install -r requirements.txt
pytest tests/
```
