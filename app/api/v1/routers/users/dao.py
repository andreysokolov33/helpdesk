from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import delete
from app.models.monitoring import TopActiveSubscriber
from app.models.partner import Diler, Technician, TechnicianPartner, TechnicianStation
from app.models.radius import RadUserGroup, Radacct, Radgroupcheck, Radgroupreply, Radreply, RadreplyUnlim
from app.models.stations import ChannelSatellite, IpGroup, Satellite
from app.models.traffic import UserNetflow
from app.utils.model_utils import _model_to_dict
from app.dao.base import BaseDAO
from sqlalchemy import and_, desc, extract, func, or_, select, text, update
from sqlalchemy.exc import DBAPIError
from app.exceptions import WrongStateParameter
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import *
from app.models.oss import *
from app.models.service import *
from uuid import UUID

logger = logging.getLogger("abs")

#### User tables ###

class CheckJurBalanceDAO(BaseDAO):
    model = CheckJurBalance

class LkAuthDAO(BaseDAO):
    model = LkAuth

class LkAuthWrongDAO(BaseDAO):
    model = LkAuthWrong

class LkLogDAO(BaseDAO):
    model = LkLog

class LkPwdChangeDAO(BaseDAO):
    model = LkPwdChange

class NetflowUsersDAO(BaseDAO):
    model = NetflowUsers

class OperationsDAO(BaseDAO):
    model = Operations

class PrivilegedUsersDAO(BaseDAO):
    model = PrivilegedUsers

class UsersDAO(BaseDAO):
    model = User

    @classmethod
    async def find_by_lower_login(cls, session: AsyncSession, login: str):
        query = select(cls.model).where(func.lower(cls.model.login) == login.lower())
        result = await session.execute(query)
        obj = result.scalar_one_or_none()
        return _model_to_dict(obj)
    
    @classmethod
    async def get_balance(cls, session: AsyncSession, **filter_by):
        query = select(cls.model.balanse).filter_by(**filter_by)
        result = await session.execute(query)
        row = result.one_or_none()
        if row is None:
            raise Exception
        column_names = ["balanse"]
        return dict(zip(column_names, row))
    
    @classmethod
    async def count_by_station_id(cls, session: AsyncSession, station_id: int) -> int:
        """
        Возвращает количество пользователей, привязанных к конкретной станции (id_grp).
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            station_id: ID станции (в таблице user это поле id_grp)
        
        Returns:
            int: Общее количество зарегистрированных пользователей на станции
        """
        # Формируем запрос: SELECT count(*) FROM users.user WHERE id_grp = :station_id
        query = (
            select(func.count())
            .select_from(cls.model)
            .where(cls.model.id_grp == station_id)
        )
        
        result = await session.execute(query)
        # scalar() возвращает результат первого столбца первой строки
        return result.scalar() or 0

    @classmethod
    async def get_display_name(cls, session: AsyncSession, user_id: int) -> Optional[str]:
        """
        Имя для отображения: из users.user_details (Surname + Name + Patronymic с большой буквы),
        если пусто — из users.user.full_name.
        """
        sql = text("""
            SELECT COALESCE(
                NULLIF(TRIM(
                    INITCAP(COALESCE(ud.surname, '')) || ' ' ||
                    INITCAP(COALESCE(ud.name, '')) || ' ' ||
                    INITCAP(COALESCE(ud.patronymic, ''))
                ), ''),
                u.full_name
            ) AS display_name
            FROM users."user" u
            LEFT JOIN users.user_details ud ON ud.user_id = u.id AND ud.is_actual = true
            WHERE u.id = :user_id
        """)
        result = await session.execute(sql, {"user_id": user_id})
        row = result.fetchone()
        if not row or row[0] is None:
            return None
        name = (row[0] or "").strip()
        return name if name else None

    @classmethod
    async def search_subscribers(
        cls,
        session: AsyncSession,
        pattern: str,
        limit: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        Поиск абонентов по ФИО/организации, телефону, email, паспорту, ИНН, id, логину.
        Регистронезависимый (lower). Несколько целевых запросов для скорости.
        """
        from app.api.v1.routers.users.subscriber_search import run_subscriber_search

        return await run_subscriber_search(session, pattern, limit=limit)


class UserArchiveDAO(BaseDAO):
    model = UserArchive


class UserRegistrationsDAO(BaseDAO):
    model = UserRegistrations


class UserCommentsDAO(BaseDAO):
    model = UserComments
    
    @classmethod
    async def get_comments_for_user(
        cls,
        session: AsyncSession,
        id_user: int,
        limit: int = 5,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Получает последние комментарии, оставленные ДЛЯ пользователя (по id_user),
        с информацией об авторах (LEFT JOIN по id_author).
        Возвращает список словарей с полями:
            - id: ID комментария
            - message: текст комментария (поле data)
            - created_at: дата в UTC (поле datum)
            - author_name: имя автора или None, если не найден
        """


        stmt = (
            select(
                cls.model.id,
                cls.model.data.label("message"),
                cls.model.datum.label("created_at"),
                SkystreamUsers.full_name.label("author_name"),
            )
            .select_from(cls.model)
            .join(
                SkystreamUsers,
                cls.model.id_author == SkystreamUsers.id,
                isouter=True,  # LEFT JOIN
            )
            .where(cls.model.id_user == id_user)
            .order_by(desc(cls.model.datum))
            .offset(offset)
            .limit(limit)
        )

        result = await session.execute(stmt)
        rows = result.fetchall()

        return [
            {
                "id": row.id,
                "message": row.message,
                "created_at": row.created_at,
                "author_name": row.author_name,
            }
            for row in rows
        ]

class UserDetailsDAO(BaseDAO):
    model = UserDetails

class UserServiceDateDAO(BaseDAO):
    model = UserServiceDate

class UsersLkTokensDAO(BaseDAO):
    model = UsersLkTokens

class TemporarySessionsDAO(BaseDAO):
    model = TemporarySessions

class UserFreezeTariffDAO(BaseDAO):
    model = UserFreezeTariff

    @classmethod
    async def find_one_with_reason(
        cls, session: AsyncSession, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Возвращает запись заморозки с подставленным rus_reason (или short_reason) из справочника."""
        from app.models.users import UserFreezeReasonCode
        q = (
            select(cls.model, UserFreezeReasonCode.rus_reason, UserFreezeReasonCode.short_reason)
            .outerjoin(
                UserFreezeReasonCode,
                cls.model.reason_code == UserFreezeReasonCode.id
            )
            .where(cls.model.user_id == user_id)
        )
        result = await session.execute(q)
        row = result.one_or_none()
        if not row:
            return None
        rec, rus_reason, short_reason = row[0], row[1], row[2]
        d = _model_to_dict(rec)
        if d is not None:
            d["reason_short"] = rus_reason if rus_reason else short_reason
            if not d["reason_short"]:
                code = d.get("reason_code")
                if code is None:
                    raw = d.get("reason")
                    if raw is not None and str(raw).strip().isdigit():
                        code = int(str(raw).strip())
                if code is not None:
                    r2 = await session.execute(
                        select(UserFreezeReasonCode.rus_reason, UserFreezeReasonCode.short_reason).where(
                            UserFreezeReasonCode.id == code
                        )
                    )
                    row2 = r2.one_or_none()
                    if row2:
                        d["reason_short"] = row2[0] or row2[1]
        return d

    @classmethod
    async def count_frozen_by_station(cls, session: AsyncSession, station_id: int) -> int:
        """
        Возвращает количество реально замороженных абонентов (is_frozen=True) на станции.
        """
        query = (
            select(func.count())
            .select_from(cls.model)
            .join(User, cls.model.user_id == User.id)
            .where(User.id_grp == station_id, cls.model.is_frozen == True)
        )
        result = await session.execute(query)
        return result.scalar() or 0

    @classmethod
    async def count_planned_freeze_by_station(cls, session: AsyncSession, station_id: int) -> int:
        """
        Возвращает количество абонентов, у которых только запланирована заморозка (is_frozen=False).
        """
        query = (
            select(func.count())
            .select_from(cls.model)
            .join(User, cls.model.user_id == User.id)
            .where(User.id_grp == station_id, cls.model.is_frozen == False)
        )
        result = await session.execute(query)
        return result.scalar() or 0


class UserFreezeReasonCodeDAO(BaseDAO):
    model = UserFreezeReasonCode


class SatelliteDAO(BaseDAO):
    model = Satellite

class ChannelSatelliteDAO(BaseDAO):
    model = ChannelSatellite

#### OSS tables ###

class JurBlankOrderListDAO(BaseDAO):
    model = JurBlankOrderList

class JurClientListDAO(BaseDAO):
    model = JurClientList

class JurContractListDAO(BaseDAO):
    model = JurContractList


class NoteHistoryDAO(BaseDAO):
    model = NoteHistory


class JurMonthlyBillDAO(BaseDAO):
    model = JurMonthlyBill


class JurMonthlyBillV2DAO(BaseDAO):
    model = JurMonthlyBillV2


class TariffConstructorDAO(BaseDAO):
    model = TariffConstructor

class TariffConstructorSpecialDAO(BaseDAO):
    model = TariffConstructorSpecial

class TariffConstructorUnlimDAO(BaseDAO):
    model = TariffConstructorUnlim

#### Service tables ###

class ActivatedDopsDAO(BaseDAO):
    model = ActivatedDops

class ActivatedServicesDAO(BaseDAO):
    model = ActivatedServices
    
    @classmethod
    async def find_many(cls, session: AsyncSession, start_date: str, end_date: str, user_id: int, **additional_filters):
        """
        Поиск активированных услуг за период для пользователя.
        """
        # Проверяем наличие обязательных параметров
        if start_date is None or end_date is None or user_id is None:
            raise ValueError("start_date, end_date, and user_id are required parameters")
        
        # Преобразуем строки в datetime
        start_datetime = datetime.datetime.strptime(start_date, '%Y-%m-%d')  
        end_datetime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        
        # Разворачиваем все колонки модели
        columns = [
            cls.model.activation_timestamp, 
            cls.model.days, 
            cls.model.packet_size, 
            cls.model.price, 
            cls.model.deactivation_date
        ]

        # Формируем основной запрос
        query = select(*columns).where(
            and_(
                cls.model.activation_timestamp >= start_datetime,
                cls.model.activation_timestamp < end_datetime,
                cls.model.uid == user_id
            )
        )
        
        # Добавляем дополнительные фильтры
        for key, value in additional_filters.items():
            if hasattr(cls.model, key):
                query = query.where(getattr(cls.model, key) == value)
        
        # Сортировка по убыванию даты активации
        query = query.order_by(desc(cls.model.activation_timestamp))

        try:
            result = await session.execute(query)
            return [dict(row) for row in result.mappings()]
        except DBAPIError as e:
            if "InvalidTextRepresentationError" in str(e):
                raise WrongStateParameter
            raise
    
    @classmethod
    async def find_latest(cls, session: AsyncSession, user_id: int, **additional_filters):
        """
        Поиск последней активированной услуги пользователя.
        """
        # Разворачиваем выбранные колонки модели
        columns = [
            cls.model.sname, 
            cls.model.days, 
            cls.model.packet_size, 
            cls.model.price,
            cls.model.activation_timestamp  # Добавил для информации
        ]

        # Формируем основной запрос
        query = select(*columns).where(
            cls.model.uid == user_id
        )
        
        # Добавляем дополнительные фильтры
        for key, value in additional_filters.items():
            if hasattr(cls.model, key):
                query = query.where(getattr(cls.model, key) == value)
        
        # Сортировка по убыванию даты активации и ограничение 1 записью
        query = query.order_by(desc(cls.model.activation_timestamp)).limit(1)

        try:
            result = await session.execute(query)
            row = result.mappings().first()
            return dict(row) if row else None
        except DBAPIError as e:
            if "InvalidTextRepresentationError" in str(e):
                raise WrongStateParameter
            raise

class AutoRenewDAO(BaseDAO):
    model = AutoRenew

class DopsDAO(BaseDAO):
    model = Dops

class LkTariffsLimitedDAO(BaseDAO):
    model = LkTariffsLimited

class LkTariffsUnlimitedDAO(BaseDAO):
    model = LkTariffsUnlimited
    
    @classmethod
    async def find_ordered_list(cls, session: AsyncSession, **filter_by):
        """
        Более компактный вариант с использованием select(cls.model)
        """
        query = select(cls.model).filter_by(**filter_by).order_by(
            cls.model.range_b.asc(),
            cls.model.volume.asc(),
            cls.model.days.asc()
        )
        
        try:
            result = await session.execute(query)
            # Используем _model_to_dict если он определен в BaseDAO
            # Или альтернативный способ преобразования
            return [_model_to_dict(row) if hasattr(cls, '_model_to_dict') 
                    else {column.name: getattr(row, column.name) 
                        for column in cls.model.__table__.columns}
                    for row in result.scalars().all()]
        except DBAPIError as e:
            if "InvalidTextRepresentationError" in str(e):
                raise WrongStateParameter
            raise

# Тарифы и трафик

class UserNetflowDAO(BaseDAO):
    model = UserNetflow
    
    @classmethod
    async def month_consumption(cls, session: AsyncSession, netflow_login: str) -> Optional[int]:
        """
            Возвращает сумму traffic_in + traffic_out за текущий месяц по Netflow абоненту
        """
        # Получаем текущую дату
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        
        # Формируем выражение для суммы трафика
        total_traffic = cls.model.traffic_in + cls.model.traffic_out
        
        # Создаем запрос
        query = select(
            func.sum(total_traffic).label('monthly_traffic')
        ).where(
            and_(
                func.lower(cls.model.netflow_name) == netflow_login.lower(),
                extract('month', cls.model.date) == current_month,
                extract('year', cls.model.date) == current_year
            )
        )
        
        result = await session.execute(query)
        monthly_traffic = result.scalar()
        if monthly_traffic:
            # Передаем в байтах
            monthly_traffic = monthly_traffic * 1024 * 1024
        return monthly_traffic

class PricePer1MbDAO(BaseDAO):
    model = PricePer1Mb

class RadgroupreplyDAO(BaseDAO):
    model = Radgroupreply

class RadreplyUnlimDAO(BaseDAO):
    model = RadreplyUnlim

class RadreplyDAO(BaseDAO):
    model = Radreply

class RadUserGroupDAO(BaseDAO):
    model = RadUserGroup
    
    @classmethod
    async def count_enabled_by_station(cls, session: AsyncSession, station_id: int) -> int:
        """
        Возвращает количество записей в RadUserGroup для конкретной станции,
        у которых группа не 'disabled'.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            station_id: ID станции (id_grp в таблице User)
            
        Returns:
            int: Количество активных (не заблокированных) записей
        """
        # Строим запрос с JOIN
        query = (
            select(func.count())
            .select_from(cls.model)
            .join(User, cls.model.username == User.login) # Связываем по логину
            .where(
                and_(
                    User.id_grp == station_id,
                    cls.model.groupname != 'disabled'
                )
            )
        )
        
        result = await session.execute(query)
        return result.scalar() or 0
    
    @classmethod
    async def get_ids_of_active_phyz_users(cls, session: AsyncSession, station_id: int) -> List[int]:
        """
        Возвращает список ID пользователей (User.id) для конкретной станции,
        у которых группа не 'disabled'.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            station_id: ID станции (id_grp в таблице User)
            
        Returns:
            List[int]: Список ID активных (не заблокированных) пользователей
        """
        query = (
            select(User.id)
            .select_from(cls.model)
            .join(User, cls.model.username == User.login)
            .where(
                and_(
                    User.id_grp == station_id,
                    cls.model.groupname != 'disabled',
                    User.is_juridical == 0
                )
            )
            .order_by(User.id)
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())

class RadacctDAO(BaseDAO):
    model = Radacct

    @classmethod
    async def get_session_summary(
        cls, session: AsyncSession, login: str
    ) -> tuple[bool, int, Optional[datetime]]:
        """
        Активные сессии; при офлайне — последняя активность по acctstarttime
        (не ORDER BY radacctid — полный scan истории).
        """
        login = (login or "").strip()
        if not login:
            return False, 0, None

        r = await session.execute(
            text("""
                SELECT count(*)::int AS open_count
                FROM radius.radacct r
                WHERE lower(r.username) = lower(:login)
                  AND r.acctstoptime IS NULL
            """),
            {"login": login},
        )
        open_count = int(r.scalar_one() or 0)
        if open_count > 0:
            return True, open_count, None

        r2 = await session.execute(
            text("""
                SELECT COALESCE(r.acctstoptime, r.acctupdatetime, r.acctstarttime) AS last_end
                FROM radius.radacct r
                WHERE lower(r.username) = lower(:login)
                ORDER BY r.acctstarttime DESC NULLS LAST
                LIMIT 1
            """),
            {"login": login},
        )
        return False, 0, r2.scalar_one_or_none()

    @classmethod
    async def is_online(cls, session: AsyncSession, login: str) -> bool:
        """
        Проверяет, есть ли у пользователя активные сессии.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            login: Логин пользователя (проверяется без учета регистра)
        
        Returns:
            True - есть активные сессии, False - нет активных сессий
        """
        query = select(func.count()).select_from(cls.model).where(
            and_(
                func.lower(cls.model.username) == login.lower(),
                cls.model.acctstoptime.is_(None)
            )
        )
        
        result = await session.execute(query)
        count = result.scalar()
        
        return count > 0
    
    @classmethod
    async def get_last_session_end_time(cls, session: AsyncSession, login: str) -> Optional[datetime]:
        """Дата завершения последней сессии (предпочтительно get_session_summary)."""
        _online, _open, last_end = await cls.get_session_summary(session, login)
        return last_end
    
    @classmethod
    async def count_online_by_station(cls, session: AsyncSession, station_id: int) -> int:
        """
        Возвращает количество активных сессий (онлайн) для конкретной станции.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            station_id: ID станции из таблицы wifitochka.ip_group
        
        Returns:
            int: Количество активных сессий на данной станции
        """
        query = select(func.count()).select_from(cls.model).where(
            and_(
                cls.model.station_id == station_id,
                cls.model.acctstoptime.is_(None)
            )
        )
        
        result = await session.execute(query)
        return result.scalar() or 0
    
    @classmethod
    async def count_online_by_protocol(
        cls, 
        session: AsyncSession, 
        station_id: int, 
        protocol: str
    ) -> int:
        """
        Возвращает количество активных сессий на станции с фильтрацией по протоколу.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            station_id: ID станции
            protocol: Значение протокола (например, 'PPP' или '')
        
        Returns:
            int: Количество найденных сессий
        """
        if protocol == 'hotspot':
            protocol = ''
        
        # Проверка, что station_id валиден
        if not station_id:
            return 0
        
        query = (
            select(func.count())
            .select_from(cls.model)
            .join(
                User,
                # Безопасный join с lower() для регистронезависимого сравнения
                func.lower(cls.model.username) == func.lower(User.login),
                isouter=True,  # или inner, если нужны только совпадения
            )
            .join(
                IpGroup,
                User.id_grp == IpGroup.id,
                isouter=True,  # зависит от требований
            )
            .where(
                and_(
                    IpGroup.id == station_id,
                    cls.model.framedprotocol == protocol,
                    cls.model.acctstoptime.is_(None),  # активные сессии
                    # Дополнительные проверки для надежности
                    cls.model.username.isnot(None),  # если нужно исключить пустые имена
                )
            )
            # Группировка, если требуется (хотя count() и так вернет одно значение)
        )
        
        try:
            result = await session.execute(query)
            count = result.scalar()
            return count if count is not None else 0
        except Exception as e:
            # Логирование ошибки при необходимости
            # logger.error(f"Error counting online sessions: {e}")
            return 0
    
class ServiceDAO(BaseDAO):
    model = Service
    
    @classmethod
    async def find_by_sname(cls, session: AsyncSession, sname: str):
        columns = [
            cls.model.id,
            cls.model.name,
            cls.model.type,
            cls.model.sname_second,
            cls.model.sname,
            cls.model.price,
            cls.model.limit,
            cls.model.frozen,
            cls.model.real_type,
            cls.model.slider,
        ]
        
        query = (
            select(*columns)
            .where(or_(cls.model.sname == sname, cls.model.sname_second == sname))
        )
        
        result = await session.execute(query)
        row = result.mappings().one_or_none()
        return dict(row) if row else None

class ServiceDopsDAO(BaseDAO):
    model = ServiceDops

class ServiceGroupsDAO(BaseDAO):
    model = ServiceGroups

class ServiceJurDAO(BaseDAO):
    model = ServiceJur

class ServiceJurByMonthsDAO(BaseDAO):
    model = ServiceJurByMonths
    
    @classmethod
    async def delete_many(
        cls, 
        session: AsyncSession, 
        user_id: int, 
        year: int, 
        months: list[int], 
        auto_commit: bool = True
    ) -> int:
        """
        Массовое удаление месяцев из расписания.
        """
        if not months:
            return 0
            
        stmt = (
            delete(cls.model)
            .filter(
                cls.model.user_id == user_id,
                cls.model.year == year,
                cls.model.month.in_(months) # Удаляем только те, что в списке
            )
        )
        
        result = await session.execute(stmt)
        
        if auto_commit:
            await session.commit()
            
        return result.rowcount

class TariffBucketPriceDAO(BaseDAO):
    model = TariffBucketPrice

class TariffDatelecomDAO(BaseDAO):
    model = TariffDatelecom


### Пользователи skystream (users.skystream_users)

class SkystreamUsersDAO(BaseDAO):
    model = SkystreamUsers

    @classmethod
    async def find_all(
        cls,
        session: AsyncSession,
        role: Optional[str] = None,
        login: Optional[str] = None,
        id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        level_in: Optional[List[int]] = None,
    ):
        query = select(cls.model)
        if role:
            query = query.where(cls.model.role == role)
        if login:
            query = query.where(cls.model.login.ilike(f"%{login}%"))
        if id:
            query = query.where(cls.model.id == id)
        if is_active is not None:
            query = query.where(cls.model.is_active == is_active)
        if is_superuser is not None:
            query = query.where(cls.model.is_superuser == is_superuser)
        if email:
            query = query.where(cls.model.email.ilike(f"%{email}%"))
        if full_name:
            query = query.where(cls.model.full_name.ilike(f"%{full_name}%"))
        if level_in is not None:
            query = query.where(cls.model.level.in_(level_in))
        
        query = query.order_by(cls.model.full_name.asc())
        result = await session.execute(query)
        return [_model_to_dict(obj) for obj in result.scalars().all()]

    @classmethod
    async def find_by_lower_login(cls, session: AsyncSession, login: str):
        query = select(cls.model).where(func.lower(cls.model.login) == login.lower())
        result = await session.execute(query)
        obj = result.scalar_one_or_none()
        return _model_to_dict(obj)

class AbsUserTokensDAO(BaseDAO):
    model = AbsUserTokens

    @classmethod
    async def find_by_access_jti(cls, session: AsyncSession, access_jti: str):
        """Найти запись токена по access_jti (для проверки отзыва в middleware)."""
        try:
            if isinstance(access_jti, str):
                access_jti = UUID(access_jti)
            query = select(cls.model).where(cls.model.access_jti == access_jti)
            result = await session.execute(query)
            token_obj = result.scalar_one_or_none()
            if not token_obj:
                return None
            return _model_to_dict(token_obj)
        except Exception as e:
            logger.error(f"Error in find_by_access_jti: {e}")
            return None

    @classmethod
    async def find_by_refresh_jti(cls, session: AsyncSession, refresh_jti: str):
        
        try:
            # Если это строка, конвертируем в объект UUID для корректного поиска в PG
            if isinstance(refresh_jti, str):
                refresh_jti = UUID(refresh_jti)
            
            query = select(cls.model).where(cls.model.refresh_jti == refresh_jti)
            result = await session.execute(query)
            token_obj = result.scalar_one_or_none()
            
            if not token_obj:
                logger.warning("Token record not found in DB")
                return None
                
            return _model_to_dict(token_obj)
        except Exception as e:
            logger.error(f"Error in find_by_refresh_jti: {e}")
            return None

    @classmethod
    async def revoke_sessions(cls, session: AsyncSession, filter_by: dict):
        """Ревокует сессии по фильтру (без коммита!)."""
        # Формируем условия
        conditions = []
        for key, value in filter_by.items():
            column = getattr(cls.model, key)
            conditions.append(column == value if value is not None else column.is_(None))

        stmt = (
            update(cls.model)
            .where(and_(*conditions))
            .values(is_revoked=True, revoked_at=func.now())
        )
        await session.execute(stmt)


    @classmethod
    async def rotate_refresh(
        cls,
        session: AsyncSession,
        old_refresh_jti: str,
        new_access_jti: str,
        new_refresh_jti: str,
        access_expires_at,
        refresh_expires_at,
        ip_address: str | None = None,
        device_info: str | None = None
    ):
        """Обновляет refresh-токен: ревокует старый, создаёт новый."""
        # 1. Найти старую запись
        old_record = await cls.find_by_refresh_jti(session, old_refresh_jti)
        if not old_record:
            raise ValueError("Old refresh token not found or already revoked")

        # 2. Ревокнуть старую
        await cls.revoke_sessions(session, {"refresh_jti": old_refresh_jti})

        # 3. Создать новую запись
        new_record = cls.model(
            user_id=old_record["user_id"],
            access_jti=new_access_jti,
            refresh_jti=new_refresh_jti,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
            ip_address=ip_address or old_record["ip_address"],
            device_info=device_info or old_record["device_info"],
            user_agent=old_record["user_agent"],
        )
        session.add(new_record)
        
    @classmethod
    async def find_latest_active_session(cls, session: AsyncSession, user_id: int):
        """Находит последнюю актуальную сессию пользователя."""
        query = (
            select(cls.model)
            .where(
                cls.model.user_id == user_id,
                cls.model.is_revoked.is_(False),
                cls.model.refresh_expires_at > datetime.now(timezone.utc)
            )
            .order_by(cls.model.created_at.desc())
            .limit(1)
        )
        result = await session.execute(query)
        obj = result.scalar_one_or_none()
        return _model_to_dict(obj) if obj else None

class AbsLoginHistoryDAO(BaseDAO):
    model = AbsLoginHistory

class WhiteIpAddressDAO(BaseDAO):
    model = WhiteIpAddress

    @classmethod
    async def find_active_by_user(cls, session: AsyncSession, user_id: int) -> list[Dict[str, Any]]:
        """Активные белые IP (date_stop IS NULL) для абонента."""
        stmt = (
            select(cls.model)
            .where(
                cls.model.user_id == user_id,
                cls.model.date_stop.is_(None)
            )
            .order_by(cls.model.created_at.asc())
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [_model_to_dict(r) for r in rows]

    @classmethod
    async def add(cls, session: AsyncSession, user_id: int, station_id: int, ip_address: str) -> Dict[str, Any]:
        """Добавить белый IP."""
        obj = cls.model(
            user_id=user_id,
            station_id=station_id,
            ip_address=ip_address,
        )
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return _model_to_dict(obj)

    @classmethod
    async def unbind(cls, session: AsyncSession, record_id: int, user_id: int) -> bool:
        """Отвязать адрес (установить date_stop). Возвращает True при успехе."""
        from datetime import datetime, timezone
        stmt = (
            update(cls.model)
            .where(
                cls.model.id == record_id,
                cls.model.user_id == user_id,
                cls.model.date_stop.is_(None)
            )
            .values(date_stop=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        )
        result = await session.execute(stmt)
        return result.rowcount > 0


class RemoveFromDistributionDAO(BaseDAO):
    model = RemoveFromDistribution
    
class UserArchiveDAO(BaseDAO):
    model = UserArchive
    
class OperatorFavoriteDAO(BaseDAO):
    model = OperatorFavorite
    
class ResetTrafficActionDAO(BaseDAO):
    model = ResetTrafficAction

    @classmethod
    async def find_last_script_reset_at(
        cls, session: AsyncSession, user_id: int
    ) -> Optional[datetime]:
        """Последний автоматический (who=script) сброс суточного трафика."""
        ts = (
            await session.execute(
                select(ResetTrafficAction.timestamp)
                .where(
                    ResetTrafficAction.user_id == user_id,
                    ResetTrafficAction.who == "script",
                )
                .order_by(desc(ResetTrafficAction.timestamp))
                .limit(1)
            )
        ).scalar_one_or_none()
        return ts


class RadgroupcheckDAO(BaseDAO):
    model = Radgroupcheck
    
class DilerDAO(BaseDAO):
    model = Diler


class TechnicianDAO(BaseDAO):
    model = Technician


class TechnicianStationDAO(BaseDAO):
    model = TechnicianStation


class TechnicianPartnerDAO(BaseDAO):
    model = TechnicianPartner

     
class TopActiveSubscriberDAO(BaseDAO):
    model = TopActiveSubscriber
    
    