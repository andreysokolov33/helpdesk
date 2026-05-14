from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import and_, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dao.base import BaseDAO
from app.models.oss import OssUserTokens
from app.models.users import SkystreamProjects
from app.models.users import SkystreamUserProjectAccess
from app.models.users import SkystreamUsers
from app.models.users import User as AbsSubscriber
from app.utils.model_utils import _model_to_dict


class SkystreamUsersDAO(BaseDAO[SkystreamUsers]):
    """DAO для таблицы users.skystream_users."""

    model = SkystreamUsers

    @classmethod
    async def find_by_lower_login(cls, session: AsyncSession, login: str) -> Optional[Dict[str, Any]]:
        from sqlalchemy import func

        stmt = select(cls.model).where(func.lower(cls.model.login) == login.strip().lower())
        result = await session.execute(stmt)
        return _model_to_dict(result.scalar_one_or_none())


class SkystreamUserProjectAccessDAO(BaseDAO[SkystreamUserProjectAccess]):
    """Сопоставление пользователя skystream и проекта (users.skystream_user_project_access)."""

    model = SkystreamUserProjectAccess

    @classmethod
    async def user_can_login_helpdesk(cls, session: AsyncSession, user_id: int) -> bool:
        """Активная строка доступа: can_login, проект helpdesk, проект активен, срок не истёк."""
        now = datetime.now(timezone.utc)
        pid = settings.HELPDESK_SKYSTREAM_PROJECT_ID
        pkey = settings.HELPDESK_PROJECT_KEY

        stmt = (
            select(cls.model.user_id)
            .join(SkystreamProjects, SkystreamProjects.id == cls.model.project_id)
            .where(
                cls.model.user_id == user_id,
                cls.model.can_login.is_(True),
                SkystreamProjects.is_active.is_(True),
                or_(
                    SkystreamProjects.id == pid,
                    SkystreamProjects.project_key == pkey,
                ),
                or_(
                    cls.model.expires_at.is_(None),
                    cls.model.expires_at > now,
                ),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None


class SubscriberDAO(BaseDAO[AbsSubscriber]):
    """DAO для таблицы users.user (абоненты ЛК)."""

    model = AbsSubscriber

    @classmethod
    async def find_by_lower_login(cls, session: AsyncSession, login: str) -> Optional[Dict[str, Any]]:
        from sqlalchemy import func

        stmt = select(cls.model).where(func.lower(cls.model.login) == login.strip().lower())
        result = await session.execute(stmt)
        return _model_to_dict(result.scalar_one_or_none())


class OssUserTokensDAO(BaseDAO[OssUserTokens]):
    """DAO для таблицы oss.oss_user_tokens."""

    model = OssUserTokens

    @classmethod
    async def find_by_access_jti(cls, session: AsyncSession, jti: str) -> Optional[Dict[str, Any]]:
        stmt = select(cls.model).where(cls.model.access_jti == UUID(jti))
        result = await session.execute(stmt)
        return _model_to_dict(result.scalar_one_or_none())

    @classmethod
    async def find_by_refresh_jti(cls, session: AsyncSession, jti: str) -> Optional[Dict[str, Any]]:
        stmt = select(cls.model).where(cls.model.refresh_jti == UUID(jti))
        result = await session.execute(stmt)
        return _model_to_dict(result.scalar_one_or_none())

    @classmethod
    async def find_latest_active_session(
        cls, session: AsyncSession, user_id: int
    ) -> Optional[Dict[str, Any]]:
        stmt = (
            select(cls.model)
            .where(and_(cls.model.user_id == user_id, cls.model.is_revoked == False))
            .order_by(desc(cls.model.created_at))
            .limit(1)
        )
        result = await session.execute(stmt)
        return _model_to_dict(result.scalar_one_or_none())

    @classmethod
    async def revoke_sessions(
        cls,
        session: AsyncSession,
        filter_by: dict,
        auto_commit: bool = True,
    ) -> int:
        stmt = (
            update(cls.model)
            .filter_by(**filter_by)
            .values(is_revoked=True, revoked_at=datetime.now(timezone.utc))
            .execution_options(synchronize_session="fetch")
        )
        result = await session.execute(stmt)
        if auto_commit:
            await session.commit()
        return result.rowcount

    @classmethod
    async def rotate_refresh(
        cls,
        session: AsyncSession,
        old_refresh_jti: str,
        new_access_jti: str,
        new_refresh_jti: str,
        access_expires_at: datetime,
        refresh_expires_at: datetime,
    ) -> None:
        """Атомарно отзывает старый токен и создаёт новую запись."""
        now = datetime.now(timezone.utc)

        old_stmt = select(cls.model).where(cls.model.refresh_jti == UUID(old_refresh_jti))
        old_result = await session.execute(old_stmt)
        old_record = old_result.scalar_one_or_none()
        if not old_record:
            return

        await session.execute(
            update(cls.model)
            .where(cls.model.refresh_jti == UUID(old_refresh_jti))
            .values(is_revoked=True, revoked_at=now)
        )

        new_token = OssUserTokens(
            user_id=old_record.user_id,
            access_jti=UUID(new_access_jti),
            refresh_jti=UUID(new_refresh_jti),
            ip_address=old_record.ip_address,
            user_agent=old_record.user_agent,
            device_info=old_record.device_info,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
        )
        session.add(new_token)
