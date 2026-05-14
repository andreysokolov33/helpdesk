from sqlalchemy import BigInteger, DateTime, Index, PrimaryKeyConstraint, SmallInteger, Text
from sqlalchemy.orm import mapped_column


from app.database import Base


class TmChat(Base):
    __tablename__ = 'tm_chat'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90937_primary'),
        Index('idx_90937_tm_chat_chat_creator_idx', 'chat_creator'),
        {'schema': 'task_manager'}
    )

    id = mapped_column(BigInteger)
    chat_type = mapped_column(Text)
    chat_custom_name = mapped_column(Text)
    chat_creator = mapped_column(BigInteger)
    date_of_create = mapped_column(DateTime(True))
    active = mapped_column(BigInteger)
    user_list = mapped_column(Text)


class TmMessage(Base):
    __tablename__ = 'tm_message'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90944_primary'),
        {'schema': 'task_manager'}
    )

    id = mapped_column(BigInteger)
    author = mapped_column(BigInteger)
    original_author = mapped_column(BigInteger)
    chat = mapped_column(BigInteger)
    original_chat = mapped_column(BigInteger)
    text = mapped_column(Text)
    attachments = mapped_column(Text)
    date_of_create = mapped_column(DateTime(True))
    date_last_change = mapped_column(DateTime(True))
    hidden = mapped_column(SmallInteger)
    user_list = mapped_column(Text)


class TmTask(Base):
    __tablename__ = 'tm_task'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='idx_90951_primary'),
        {'schema': 'task_manager'}
    )

    id = mapped_column(BigInteger)
    author = mapped_column(BigInteger)
    name = mapped_column(Text)
    description = mapped_column(Text)
    date_of_create = mapped_column(DateTime(True))
    deadline = mapped_column(DateTime(True))
    chat = mapped_column(BigInteger)
    status = mapped_column(Text)
    responsible = mapped_column(Text)
    object_list = mapped_column(Text)
