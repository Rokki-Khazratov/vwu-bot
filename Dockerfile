FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /code

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

COPY bot ./bot

CMD ["python", "-m", "bot.main"]
