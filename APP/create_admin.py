import argparse
import asyncio
import getpass
import logging
import warnings
from datetime import UTC, datetime

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from APP.core.config import get_settings
from APP.core.constants import UserLevel
from APP.core.db import create_engine, create_session_factory
from APP.core.logging import configure_logging
from APP.core.security import hash_password
from APP.models.auth_session import AuthSession
from APP.models.user import User
from APP.schemas.auth import RegisterInput
from APP.services.activity import record_event
from APP.services.library import ensure_liked

logger = logging.getLogger(__name__)


async def provision_admin(session, settings, payload=None, promote_email=None):
    async with session.begin():
        if promote_email is not None:
            user = await session.scalar(
                select(User)
                .where(User.email == promote_email.lower())
                .with_for_update(key_share=True)
            )
            if user is None:
                raise HTTPException(status_code=404, detail="Account not found")
            if not user.is_active:
                raise HTTPException(
                    status_code=409, detail="Activate this account before promotion"
                )
        else:
            user = User(
                email=str(payload.email),
                display_name=payload.display_name,
                password_hash=hash_password(
                    payload.password.get_secret_value(), settings.bcrypt_rounds
                ),
            )
            session.add(user)
            await session.flush()
            await ensure_liked(session, user.id)
        previous = user.level.value
        user.level = UserLevel.admin
        user.weight = settings.rating_weight_admin

        await session.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        record_event(
            session,
            user.id,
            "developer_admin_provisioned",
            "user",
            user.id,
            public=False,
            payload={"previous_level": previous, "method": "local_cli"},
        )
        await session.flush()
        return user.id


async def run(args):
    settings = get_settings()
    configure_logging(settings.log_level)
    payload = None
    if args.promote:
        confirmation = (
            input("Введите email аккаунта ещё раз для назначения admin: ")
            .strip()
            .lower()
        )
        if confirmation != args.email.lower():
            raise ValueError("Email confirmation does not match")
    else:
        warnings.simplefilter("error", getpass.GetPassWarning)
        password = getpass.getpass("Пароль администратора: ")
        if password != getpass.getpass("Повторите пароль: "):
            raise ValueError("Passwords do not match")
        payload = RegisterInput(
            email=args.email, display_name=args.display_name, password=password
        )
    engine = create_engine(settings)
    try:
        async with create_session_factory(engine)() as session:
            user_id = await provision_admin(
                session, settings, payload, args.email if args.promote else None
            )
        logger.info("Administrator provisioned", extra={"user_id": user_id})
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(
        description="Создание admin только из окружения разработчика"
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name", default="Administrator")
    parser.add_argument(
        "--promote",
        action="store_true",
        help="Назначить admin существующему активному аккаунту",
    )
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except getpass.GetPassWarning:
        parser.exit(1, "Для безопасного ввода пароля нужен интерактивный терминал.\n")
    except ValidationError:
        parser.exit(
            1,
            "Некорректные email, имя или пароль; пароль должен быть от 8 до 128 символов.\n",
        )
    except IntegrityError:
        parser.exit(
            1, "Email уже занят. Для существующего аккаунта используйте --promote.\n"
        )
    except (HTTPException, ValueError) as exc:
        parser.exit(
            1, str(exc.detail if isinstance(exc, HTTPException) else exc) + "\n"
        )


if __name__ == "__main__":
    main()
