FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    RAMANUJAN_PUBLIC_WEB=1 \
    RAMANUJAN_CACHE_DIR=/tmp/ramanujan_lab_cache \
    RAMANUJAN_DATA_DIR=/data/ramanujan_lab

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      texlive-latex-base texlive-latex-recommended texlive-fonts-recommended \
      curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app
RUN mkdir -p /tmp/ramanujan_lab_cache /data/ramanujan_lab

EXPOSE 8501 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=3)" || exit 1

CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501}"]
