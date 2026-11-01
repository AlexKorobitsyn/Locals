FROM locals-backend:k8s
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY scripts/prober.py ./prober.py
USER 10001
CMD ["python", "prober.py"]
