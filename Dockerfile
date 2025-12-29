FROM python:3.13-slim

WORKDIR /app

# Tylko zależności do budowy Pythona (bez crona!)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    libsodium-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY . /app

ENV PYTHONUNBUFFERED=1 
ENV PYTHONDONTWRITEBYTECODE=1

#RUN addgroup --system app && adduser --system --ingroup app appuser
#RUN chown -R appuser:app /app
#USER appuser
# Domyślnie uruchamia API
CMD ["uvicorn", "presentation.main:app", "--host", "0.0.0.0", "--port", "8000"]