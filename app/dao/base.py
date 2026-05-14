# app/dao/base.py

from typing import Any, TypeVar, Generic, Optional, Dict, List
from sqlalchemy import Select, delete, update, select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.model_utils import _model_to_dict

ModelType = TypeVar("ModelType")

class BaseDAO(Generic[ModelType]):
    model: type[ModelType]  # Обязательно переопределять в наследниках

    @classmethod
    def _get_dao_name(cls) -> str:
        return cls.__name__

    # ==============================================================================
    # ПОИСК
    # ==============================================================================
    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, **filter_by: Any) -> Optional[Dict[str, Any]]:
        stmt = select(cls.model).filter_by(**filter_by)
        result = await session.execute(stmt)
        instance = result.scalar_one_or_none()
        return _model_to_dict(instance)

    @classmethod
    async def find_one(cls, session: AsyncSession, **filter_by: Any) -> Dict[str, Any]:
        stmt = select(cls.model).filter_by(**filter_by)
        result = await session.execute(stmt)
        instance = result.scalar_one()
        return _model_to_dict(instance)

    @classmethod
    async def find_all(
        cls,
        session: AsyncSession,
        order_by: Any | None = None,
        limit: int | None = None,
        offset: int | None = None,
        **filter_by: Any,
    ) -> List[Dict[str, Any]]:
        stmt: Select = select(cls.model)
        if filter_by:
            stmt = stmt.filter_by(**filter_by)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        instances = result.scalars().all()
        return [_model_to_dict(obj) for obj in instances]

    @classmethod
    async def find_last(cls, session: AsyncSession, pk_field: str = "id", **filter_by: Any) -> Optional[Dict[str, Any]]:
        column = getattr(cls.model, pk_field, None)
        if column is None:
            raise AttributeError(f"Поле '{pk_field}' не существует в {cls.model.__name__}")

        stmt = (
            select(cls.model)
            .filter_by(**filter_by)
            .order_by(desc(column))
            .limit(1)
        )
        result = await session.execute(stmt)
        instance = result.scalar_one_or_none()
        return _model_to_dict(instance)

    @classmethod
    async def count(cls, session: AsyncSession, **filter_by: Any) -> int:
        stmt = select(func.count()).select_from(cls.model)
        if filter_by:
            stmt = stmt.filter_by(**filter_by)
        result = await session.execute(stmt)
        return result.scalar_one()

    # ==============================================================================
    # ДОБАВЛЕНИЕ
    # ==============================================================================
    @classmethod
    async def add(cls, session: AsyncSession, auto_commit: bool = True, **data: Any) -> Dict[str, Any]:
        obj = cls.model(**data)
        session.add(obj)
        if auto_commit:
            await session.commit()
            await session.refresh(obj)
        else:
            # Отправляем в БД, чтобы сгенерировались ID, но не закрываем транзакцию
            await session.flush() 
        return _model_to_dict(obj)

    # ==============================================================================
    # ОБНОВЛЕНИЕ
    # ==============================================================================
    @classmethod
    async def update(
        cls,
        session: AsyncSession,
        filter_by: dict[str, Any],
        auto_commit: bool = True,
        **update_data: Any
    ) -> int:
        if not update_data:
            return 0

        stmt = (
            update(cls.model)
            .filter_by(**filter_by)
            .values(**update_data)
            .execution_options(synchronize_session="fetch")
        )
        result = await session.execute(stmt)
        if auto_commit:
            await session.commit()
        return result.rowcount

    # ==============================================================================
    # УДАЛЕНИЕ
    # ==============================================================================
    @classmethod
    async def delete(cls, session: AsyncSession, auto_commit: bool = True, **filter_by: Any) -> int:
        stmt = delete(cls.model).filter_by(**filter_by)
        result = await session.execute(stmt)
        if auto_commit:
            await session.commit()
        return result.rowcount