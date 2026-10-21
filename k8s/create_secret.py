import json
import logging
import secrets
from pathlib import Path
SECRET_FILE = Path(__file__).with_name("02-secret.yaml")
SECRET_BYTES = 32
POSTGRES_USER = "music"
POSTGRES_DB = "music"

def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if SECRET_FILE.exists():
        logging.info("02-secret.yaml уже существует, значения сохранены")
        return
    postgres_password = secrets.token_hex(SECRET_BYTES)
    minio_pwd = secrets.token_hex(SECRET_BYTES)
    vals = {
        "JWT_SECRET_KEY": secrets.token_hex(SECRET_BYTES),
        "POSTGRES_PASSWORD": postgres_password,
        "DATABASE_URL": f"postgresql+asyncpg://{POSTGRES_USER}:{postgres_password}@db:5432/{POSTGRES_DB}",
        "MINIO_ROOT_PASSWORD": minio_pwd,
        "S3_SECRET_KEY": minio_pwd,
    }
    manifest = "apiVersion: v1\nkind: Secret\nmetadata: {name: locals-secret, namespace: locals}\ntype: Opaque\nstringData:\n"
    manifest += "".join(f"  {key}: {json.dumps(val)}\n" for key, val in vals.items())
    with SECRET_FILE.open("x", encoding="utf-8") as target:
        target.write(manifest)
    SECRET_FILE.chmod(0o600)
    logging.info("Создан 02-secret.yaml со случайными значениями")

if __name__ == "__main__":
    main()
