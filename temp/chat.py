from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel


class Chat(BaseModel):  
    chat_id: int  
    fullname: str  
    station_name: Optional[str] = None  
    formatted_date: Optional[str] = None  # deprecated, use last_message_date_iso
    last_message_date_iso: Optional[str] = None
    last_message_text: Optional[str] = None
    is_jur: Optional[bool] = False
    is_online: Optional[int] = 0
    has_unread: Optional[bool] = False
    unread_count: int = 0
    top_subscriber_rank: Optional[int] = None
    
class MessageAttachment(BaseModel):
    id: int
    file_path: str
    original_filename: str
    file_ext: Optional[str] = None
    file_size_bytes: Optional[int] = None


class Message(BaseModel):
    msg_id: int
    date: str  # legacy formatted
    date_iso: Optional[str] = None
    file_path: Optional[str] = None
    text: str
    answer: bool
    whose_message: str
    has_read: bool
    user_id: int
    # ЛК-тикеты: время прочтения абонентом (user_mail_reads.person_type = 'user')
    subscriber_read_at: Optional[str] = None
    relay_msg_id: Optional[str] = None
    relay_author: Optional[str] = None
    relay_snippet: Optional[str] = None
    attachments: List[MessageAttachment] = []

class MessageCreate(BaseModel):
    text: str
    
class UserInfo(BaseModel):
    id: int
    fullname: str
    station_name: str | None = None
    
# Pydantic схемы
class ProposalChat(BaseModel):
    msg_id: int
    proposal_id: int
    date: str
    text: str
    answer: bool
    user_id: int
    files: List[str] = []  # Список путей к файлам

    class Config:
        from_attributes = True  # Для совместимости с SQLAlchemy
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Сериализация TIMESTAMP в ISO формат
        }

class ProposalChatFiles(BaseModel):
    id: int
    msg_id: int
    file_path: str
    created_at: str

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
class MessagesResponse(BaseModel):
    messages: List[Message]
    total: int
    
class ChatMessage(BaseModel):
    msg_id: int
    proposal_id: int
    date: str
    text: str
    answer: bool
    user_id: int
    read: bool
    created_at: str
    files: Optional[List[Dict[str, str]]] = None