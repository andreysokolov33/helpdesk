from typing import Any
from fastapi import HTTPException, status

class AppException(Exception):
    """Базовое исключение приложения"""
    pass

class DatabaseError(AppException):
    """
    Исключение для ошибок базы данных.
    Сохраняет контекст DAO и оригинальную ошибку.
    """
    def __init__(
        self,
        dao_name: str,
        method: str,
        message: str | None = None,
        original_error: Exception | None = None,
    ):
        self.dao_name = dao_name
        self.method = method
        self.original_error = original_error
        self.detail = message or "Неизвестная ошибка базы данных"

        # Формируем читаемое сообщение
        msg = f"[DAO {dao_name}.{method}] {self.detail}"
        if original_error:
            msg += f" (причина: {type(original_error).__name__}: {original_error})"
        super().__init__(msg)
        
class WrongStateParameter(AppException):
    """
    Исключение для ошибок неверного состояния/параметров,
    например, некорректный формат данных для DAO-метода.
    """

    def __init__(
        self,
        dao_name: str,
        method: str,
        message: str | None = None,
        original_error: Exception | None = None,
    ):
        self.dao_name = dao_name
        self.method = method
        self.original_error = original_error
        self.detail = message or "Передан некорректный параметр состояния"

        # Формируем читаемое сообщение
        msg = f"[DAO {dao_name}.{method}] {self.detail}"
        if original_error:
            msg += (
                f" (причина: {type(original_error).__name__}: {original_error})"
            )

        super().__init__(msg)

def raise_wrong_site() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Это не личный кабинет абонента! Вам надо авторизоваться на сайте lk.wifitochka.ru"
    )

def raise_wrong_login_or_password() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неправильно введен логин или пароль, попробуйте еще раз"
    )