FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ARG RELEASE_ID=dev
ARG VCS_REF=unknown
ARG VCS_URL
ENV RELEASE_ID=${RELEASE_ID}
LABEL org.opencontainers.image.version="${RELEASE_ID}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="${VCS_URL}"

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

RUN groupadd --system app && useradd --system --gid app app
COPY --chown=app:app APP ./APP
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app scripts ./scripts

USER app
CMD ["python", "-m", "APP"]
