# app/core/logger.py
import logging
import sys
import re
import traceback
from typing import Optional, Set, Pattern, Dict, Any
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Импортируем контекстные переменные
from .context import request_id_ctx_var, user_id_ctx_var


class SensitiveDataFilter(logging.Filter):
    """Фильтр для маскирования чувствительных данных в логах"""

    PATTERNS: Dict[str, Pattern] = {
        'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
        'phone': re.compile(r'(\+7|8)[- _]*\d{3}[- _]*\d{3}[- _]*\d{2}[- _]*\d{2}'),
        'password': re.compile(r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+["\']?', re.IGNORECASE),
        'token': re.compile(r'token["\']?\s*[:=]\s*["\']?[^"\'\s]+["\']?', re.IGNORECASE),
        'secret': re.compile(r'secret["\']?\s*[:=]\s*["\']?[^"\'\s]+["\']?', re.IGNORECASE),
    }

    SENSITIVE_KEYS: Set[str] = {
        'password', 'token', 'secret', 'api_key',
        'oss_acc_token', 'oss_ref_token',
        'private_key', 'email', 'phone', 'cvv', 'card_number'
    }

    def __init__(self):
        super().__init__()
        self.replacement = '***MASKED***'

    def _mask_sensitive_data(self, text: str) -> str:
        for pattern in self.PATTERNS.values():
            text = pattern.sub(self.replacement, text)
        return text

    def _mask_dict_values(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: self.replacement if k.lower() in self.SENSITIVE_KEYS else self._mask_dict_values(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [self._mask_dict_values(item) for item in obj]
        return obj

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, (dict, list)):
            record.msg = self._mask_dict_values(record.msg)
        elif isinstance(record.msg, str):
            record.msg = self._mask_sensitive_data(record.msg)

        if record.args:
            record.args = tuple(
                self._mask_dict_values(arg) if isinstance(arg, (dict, list)) else
                self._mask_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


class ContextFilter(logging.Filter):
    """Фильтр для добавления контекстных переменных в логи"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Добавляем request_id из контекста
        if not hasattr(record, 'request_id'):
            record.request_id = request_id_ctx_var.get() or 'no-request-id'
        
        # Опционально: добавляем user_id
        if not hasattr(record, 'user_id'):
            record.user_id = user_id_ctx_var.get() or 'anonymous'
        
        return True


class ProjectPathFormatter(logging.Formatter):
    """Форматтер с относительными путями и расширенной информацией об ошибках"""
    
    def __init__(self, fmt=None, datefmt=None, style="%", project_root=None):
        super().__init__(fmt, datefmt, style)
        self.project_root = Path(project_root or Path.cwd()).resolve()

    def format(self, record):
        # Относительный путь от корня проекта
        try:
            rel_path = Path(record.pathname).resolve().relative_to(self.project_root)
            record.relpath = str(rel_path)
        except (ValueError, Exception):
            record.relpath = record.pathname

        # Короткое имя файла
        record.filename_short = Path(record.pathname).name

        # Для исключений добавляем полный traceback
        if record.exc_info:
            record.exc_text = self._format_exception(record.exc_info)
        
        # Добавляем стек вызовов для ERROR/CRITICAL без exc_info
        if record.levelno >= logging.ERROR and not record.exc_info:
            record.stack_info = self._get_caller_stack()

        return super().format(record)

    def _format_exception(self, exc_info) -> str:
        """Форматирует исключение с относительными путями"""
        if not exc_info:
            return ""
        
        tb_lines = traceback.format_exception(*exc_info)
        formatted_lines = []
        
        for line in tb_lines:
            try:
                for part in line.split('"'):
                    if '/' in part or '\\' in part:
                        try:
                            abs_path = Path(part).resolve()
                            rel_path = abs_path.relative_to(self.project_root)
                            line = line.replace(part, str(rel_path))
                        except (ValueError, Exception):
                            pass
            except Exception:
                pass
            formatted_lines.append(line)
        
        return ''.join(formatted_lines)

    def _get_caller_stack(self, depth: int = 5) -> str:
        """Получает стек вызовов для отладки"""
        stack = traceback.extract_stack()[:-depth]
        formatted = []
        
        for frame in stack[-5:]:
            try:
                rel_path = Path(frame.filename).resolve().relative_to(self.project_root)
                formatted.append(f"  {rel_path}:{frame.lineno} in {frame.name}")
            except (ValueError, Exception):
                formatted.append(f"  {frame.filename}:{frame.lineno} in {frame.name}")
        
        return "\n" + "\n".join(formatted) if formatted else ""


class CustomFormatter(ProjectPathFormatter):
    """Цветной вывод в консоль"""

    grey = "\033[90m"
    blue = "\033[94m"
    cyan = "\033[96m"
    yellow = "\033[93m"
    red = "\033[91m"
    bold_red = "\033[91;1m"
    reset = "\033[0m"

    EMOJI = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️ ",
        logging.WARNING: "⚠️ ",
        logging.ERROR: "❌",
        logging.CRITICAL: "🔥",
    }

    def __init__(self, fmt: str, project_root: Optional[Path] = None, use_emoji: bool = True):
        super().__init__(fmt, project_root=project_root)
        self.fmt = fmt
        self.use_emoji = use_emoji
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.cyan + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset,
        }

    def format(self, record):
        # Добавляем эмодзи
        if self.use_emoji:
            record.emoji = self.EMOJI.get(record.levelno, "")
        else:
            record.emoji = ""

        log_fmt = self.FORMATS.get(record.levelno, self.fmt)
        formatter = ProjectPathFormatter(log_fmt, project_root=self.project_root)
        
        result = formatter.format(record)
        
        # Добавляем стек вызовов для ошибок
        if hasattr(record, 'stack_info') and record.stack_info:
            result += f"\n{self.grey}Call stack:{self.reset}{record.stack_info}"
        
        return result


def setup_logger(
    name: str,
    level: int = logging.DEBUG,
    log_dir: Optional[str | Path] = None,
    log_to_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    log_format: Optional[str] = None,
    project_root: Optional[str | Path] = None,
    use_emoji: bool = True,
    propagate: bool = False
) -> logging.Logger:
    """
    Создаёт и настраивает логгер с расширенной информацией об ошибках.
    """
    
    log_format = log_format or (
        "%(emoji)s %(asctime)s | %(levelname)-8s | [%(request_id)s] | "
        "%(relpath)s:%(lineno)d | %(funcName)s() | %(message)s"
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []
    logger.propagate = propagate
    
    # Добавляем фильтры
    logger.addFilter(ContextFilter())  # ← Добавляем request_id автоматически
    logger.addFilter(SensitiveDataFilter())

    # Консольный вывод
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(
            CustomFormatter(log_format, project_root=project_root, use_emoji=use_emoji)
        )
        logger.addHandler(console_handler)

    # Файловые хендлеры
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        file_format = (
            "%(asctime)s | %(levelname)-8s | [%(request_id)s] | "
            "%(relpath)s:%(lineno)d | %(funcName)s() | %(message)s"
        )
        formatter = ProjectPathFormatter(file_format, project_root=project_root)

        # DEBUG лог
        debug_handler = RotatingFileHandler(
            filename=log_dir / f"{name}.debug.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        logger.addHandler(debug_handler)

        # INFO лог
        info_handler = RotatingFileHandler(
            filename=log_dir / f"{name}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(formatter)
        logger.addHandler(info_handler)

        # ERROR лог
        error_handler = RotatingFileHandler(
            filename=log_dir / f"{name}.error.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

    return logger


def log_exception(logger: logging.Logger, exc: Exception, message: str = "Exception occurred"):
    """Логирует исключение с полным traceback"""
    logger.error(message, exc_info=(type(exc), exc, exc.__traceback__))


def log_errors(logger: logging.Logger, reraise: bool = True):
    """Декоратор для автоматического логирования ошибок"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error in {func.__name__}: {str(e)}",
                    exc_info=True
                )
                if reraise:
                    raise
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error in {func.__name__}: {str(e)}",
                    exc_info=True
                )
                if reraise:
                    raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator