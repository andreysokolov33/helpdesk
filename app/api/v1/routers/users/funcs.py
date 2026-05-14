from datetime import datetime
import logging
import re
from typing import Optional
import phonenumbers
from phonenumbers import NumberParseException

logger = logging.getLogger("oss")


def normalize_phone(phone: str, region: str = "RU") -> str:
    """Normalize a phone number to E.164 format."""
    try:
        parsed = phonenumbers.parse(phone, region)
        if not phonenumbers.is_valid_number(parsed):
            logger.warning(f"Invalid phone number: {phone}")
            return phone
        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        logger.debug(f"Normalized phone number: {phone} -> {formatted}")
        return formatted
    except NumberParseException as e:
        logger.warning(f"Failed to parse phone number {phone}: {str(e)}")
        return phone
    
    
def calculate_reset_times(traffic_update_hour: Optional[str], gmt: int):
        """
        Расчет времени сброса трафика.
        Возвращает кортеж: (local_hour, msk_hour).
        """
        try:
            gmt_int = int(gmt)
        except (TypeError, ValueError):
            gmt_int = 3

        if traffic_update_hour is None or str(traffic_update_hour).strip() == "":
            # Если час в users.userr не задан — считаем, что сброс в 00:00 МСК.
            msk_hour = 0
            local_hour = (msk_hour + (gmt_int - 3) + 24) % 24
            return local_hour, msk_hour

        try:
            hour = int(traffic_update_hour)
        except (TypeError, ValueError):
            hour = 0
        msk_hour = max(0, min(23, hour))
        local_hour = (msk_hour + (gmt_int - 3) + 24) % 24
        return local_hour, msk_hour
    
def get_normal_date_from_timestamp(timestamp):
        """Получить дату в человеческом формате из таймштампа"""
        if not timestamp:
            return timestamp
        dt_object = datetime.fromtimestamp(timestamp)
        return dt_object.strftime('%d.%m.%Y %H:%M')
    
def is_only_russian_letters(text):
    """Проверяет, что строка содержит только русские буквы и не пуста"""
    if not text or not isinstance(text, str):
        return False
    # Регулярное выражение: только русские буквы от начала до конца строки
    pattern = r'^[а-яА-ЯёЁ]+$'
    return bool(re.match(pattern, text))

def validate_fio_parts(surname, name, patronymic):
    """Проверяет, что все части ФИО содержат только русские буквы"""
    errors = []
    
    if not is_only_russian_letters(surname):
        errors.append("Фамилия должна содержать только русские буквы")
    
    if not is_only_russian_letters(name):
        errors.append("Имя должно содержать только русские буквы")
    
    if patronymic and not is_only_russian_letters(patronymic):  # Отчество может быть пустым
        errors.append("Отчество должно содержать только русские буквы или отсутствовать")
    
    return errors

def format_seconds(seconds):
    """
    Преобразует секунды в формат:
    - 'N дней, HH:MM' если есть дни
    - 'HH:MM' если дней нет
    """
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "00:00"
    
    # Вычисляем минуты, часы и дни
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = int(hours // 24)
    
    # Получаем оставшиеся часы и минуты
    remaining_hours = hours % 24
    remaining_minutes = minutes % 60
    
    # Форматируем вывод
    if days > 0:
        # Склонение слова "день"
        if days % 10 == 1 and days % 100 != 11:
            day_word = "день"
        elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
            day_word = "дня"
        else:
            day_word = "дней"
        
        return f"{days} {day_word}, {remaining_hours:02d}:{remaining_minutes:02d}"
    else:
        return f"{remaining_hours:02d}:{remaining_minutes:02d}"

def define_speed(meta: dict, traffic: dict):
    """Определить скорость абонента"""
    unlim_speed = meta['speed'].get('unlimited')
    limit_speed = meta['speed'].get('limited')

    if meta.get('service_type') == 'default' or traffic.get("remain_traffic") is not None and traffic.get("remain_traffic") > 1:
        return unlim_speed
    elif meta['speed'].get('limited') and meta['speed'].get('limited') is not None:
        return limit_speed
    return 'undefined'

def check_if_main_tariff_finished(user_info: dict, meta: dict, traffic: dict):
    """Определить, закончился ли основной пакет трафика"""
    if meta.get('service_type') != 'default':
        return False

    remain_traffic = traffic.get('remain_traffic', 0)
    
    if user_info.get('is_jur'):
        # Для ЮЛ: основной пакет закончен, если мы "залезли" в ДОП или в ноль
        # Учитываем, что в remain_traffic уже сидит и основной, и доп.
        extra_packet = traffic.get('extra_packet', 0)
        return remain_traffic <= extra_packet
    else:
        # Для ФЛ: закончен, если остаток 0 или меньше
        return remain_traffic <= 0

def check_if_dop_tariff_finished(user_info: dict, meta: dict, traffic: dict):
    """Определить, закончился ли дополнительный пакет трафика у ЮЛ"""
    if user_info.get('is_jur') and meta.get('service_type') == 'default':
        extra_packet = traffic.get('extra_packet', 0)
        remain_traffic = traffic.get('remain_traffic', 0)
        
        # Если доп. пакет вообще был и общий остаток стал 0
        if extra_packet > 0 and remain_traffic <= 0:
            return True
            
    return False