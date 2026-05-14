# main.py (корень проекта)
from __future__ import annotations
import uvicorn
from app.config import settings, BASE_DIR
from app.core.logger import setup_logger
from app.fastapi_app import create_app

# === Логгер инициализируется один раз ===
logger = setup_logger(
    name="oss",
    log_dir=settings.LOG_DIR,
    log_to_console=True,
    max_bytes=50 * 1024 * 1024,
    backup_count=14,
    project_root=BASE_DIR,
)

app = create_app()

# === Запуск напрямую через `python main.py` ===
if __name__ == "__main__":
    # Определяем режим
    mode = settings.MODE.upper()
    is_dev = mode == "DEV" or mode == "TEST"
    is_prod = mode == "PROD"

    logger.info(f"Starting application in {mode} mode")
    logger.info(f"FastAPI available at: http://{settings.HOST}:{settings.PORT}/")
    logger.info(f"API docs:             http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"Health check:         /health")
    # print('DATABASE URL:', settings.DATABASE_URL)
    # print('MEDIA DIR:', settings.MEDIA_DIR)
    # print('BASE DIR:', BASE_DIR)

    # === Рекомендации по запуску ===
    if is_prod:
        logger.warning(
            "Запуск в PROD через `python main.py` не рекомендуется!\n"
            "Используй: gunicorn -k uvicorn.workers.UvicornWorker 'main:app' -b 0.0.0.0:8000"
        )
        # Но если всё же запускаешь так — отключаем всё лишнее
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            reload=False,
            workers=1,  # uvicorn.run() не поддерживает multiprocessing — только через Gunicorn
            proxy_headers=settings.PROXY_HEADERS,
            forwarded_allow_ips="*",
            log_level="warning",
            access_log=False,
        )
    else:  # DEV
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=True,
            proxy_headers=settings.PROXY_HEADERS,
            forwarded_allow_ips="*",
            log_level="info",
            access_log=True,
        )