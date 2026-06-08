
from app.config import MEDIA_DIR_DEFAULT


PRIORITY_DICT = {
    'low': 'Низкий',
    'middle': 'Средний',
    'high': 'Высокий',
    'critical': 'Критический',
}

TICKET_TYPE_DICT = {
    'finance': 'Финансы',
    'network': 'Работа сети',
    'equipment': 'Оборудование',
    'traffic': 'Трафик',
    'other': 'Другое',
}

STATUS_DICT = {
    'pending': 'Ожидает',
    'open': 'Открыт',
    'in_progress': 'В работе',
    'waiting_client': 'Ожидание клиента',
    'waiting_technician': 'Ожидаем партнера',
    'no_technician': 'Нет техника',
    'waiting_parts': 'Ожидание запчастей',
    'waiting_logistics': 'Ожидание логистики',
    'cc_handover': 'Передача в КС',
    'waiting_cs': 'Ожидаем КС',
    'resolved': 'Решён',
    'closed': 'Закрыт',
    'cancelled': 'Отменён',
    'deferred': 'Отложен',
    'not_resolved': 'Нерешён',
}

# Линия техподдержки (users.tracker_tickets.support_line)
SUPPORT_LINE_DISPLAY = {
    1: 'Контактный сервис',
    2: 'Инженеры',
    3: 'Партнёр',
    4: 'Менеджер',
}

# Линия менеджера: тикеты не в очереди КС (список /tickets, «нужен ответ»).
TRACKER_MANAGER_SUPPORT_LINE = 4


def is_manager_support_line(support_line: int | None) -> bool:
    return int(support_line or 1) == TRACKER_MANAGER_SUPPORT_LINE


def is_visible_to_cs_support(support_line: int | None) -> bool:
    """Тикет показывается операторам КС в списке и как требующий их ответа."""
    return not is_manager_support_line(support_line)

# Для карточки тикета и списка: компактные названия статусов
STATUS_DISPLAY = {
    'pending': 'Ожидает',
    'open': 'Открыт',
    'in_progress': 'В работе',
    'waiting_client': 'Ожидание клиента',
    'waiting_technician': 'Ожидаем партнера',
    'no_technician': 'Нет техника',
    'waiting_parts': 'Ожидание запчастей',
    'waiting_logistics': 'Ожидание логистики',
    'cc_handover': 'Передача в КС',
    'waiting_cs': 'Ожидаем КС',
    'resolved': 'Решён',
    'closed': 'Закрыт',
    'cancelled': 'Отменён',
    'deferred': 'Отложен',
    'not_resolved': 'Нерешён',
}

# Незакрытые: SLA тикает (pending, open, in_progress) или на паузе (waiting_*, no_technician, cc_handover)
TRACKER_OPEN_STATUSES = (
    'pending', 'open', 'in_progress',
    'waiting_client', 'waiting_technician', 'no_technician', 'waiting_parts', 'waiting_logistics',
    'cc_handover', 'waiting_cs',
)
# Статусы «ожидание сторонней стороны» (запчасти, партнёр, КС) — ниже в очереди
TRACKER_OPERATIONAL_WAIT_STATUSES = (
    'waiting_technician', 'waiting_parts', 'waiting_logistics',
    'waiting_cs', 'deferred',
)
# Обратная совместимость (waiting_client — коммуникационный, не операционный)
TRACKER_WAITING_OPERATOR_STATUSES = TRACKER_OPERATIONAL_WAIT_STATUSES + ('waiting_client',)

# Коммуникационный слой в колонке «Статус» списка /tickets (v2: chat_turn / action_by):
# — chat_turn=staff и action_by ∈ {cs, engineers, partner} → needs_reply;
# — chat_turn=subscriber → awaiting_subscriber (кроме in_progress на КС — workflow «В работе»);
# — list_highlight=ops → workflow-подпись (handoff на КС).
COMMUNICATION_STATE_LABELS = {
    'needs_reply': 'Нужен ответ',
    'awaiting_subscriber': 'Ждём абонента',
}
# Закрытые / завершённые
TRACKER_CLOSED_STATUSES = (
    'resolved', 'closed', 'cancelled', 'deferred', 'not_resolved')

# ---------------------------------------------------------------------------
# Очередь тикетов v2 (колонки queue_line, action_by, chat_turn, action_since)
# Legacy status / support_line не трогаем — другие проекты.
#
# Исполнители на tracker_tickets (не путать):
#   assigned_to  — оператор КС (регистрация, 1-я линия)
#   engineer_id  — инженер при эскалации
#   Оба NULL допустимы (общая очередь); оба заполнены одновременно — нет.
# ---------------------------------------------------------------------------

TRACKER_QUEUE_LINE_DISPLAY = {
    'cs': 'КС',
    'engineers': 'Инженеры',
    'partner': 'Партнёр',
}

TRACKER_ACTION_BY_DISPLAY = {
    'cs': 'КС',
    'engineers': 'Инженеры',
    'partner': 'Партнёр',
    'subscriber': 'Абонент',
    'external': 'Внешняя сторона',
}

TRACKER_CHAT_TURN_DISPLAY = {
    'staff': 'Нужен ответ staff',
    'subscriber': 'Ждём абонента',
}

# Список тикетов helpdesk (/tickets): только эти источники (users.tracker_tickets.source)
TRACKER_HELPDESK_LIST_SOURCES = ('lk', 'call_center', 'abs')

# Внутренний чат staff↔staff (без абонента в цепочке v2)
TRACKER_INTERNAL_STAFF_CHAT_SOURCES = ('call_center', 'abs')


def is_subscriber_chat_source(source: str | None) -> bool:
    return (source or '').strip() == 'lk'


def is_internal_staff_chat_source(source: str | None) -> bool:
    return (source or '').strip() in TRACKER_INTERNAL_STAFF_CHAT_SOURCES

# Вкладка «Закрытые» в блоке инцидентов на профиле абонента (без «отложен»)
PROFILE_INCIDENT_CLOSED_STATUSES = (
    'closed', 'cancelled', 'not_resolved', 'resolved')

# Источник обращения (tracker_tickets.source) для страницы траблтикетов
SOURCE_DISPLAY = {
    'lk': 'Личный кабинет',
    'partner': 'Кабинет партнёра',
    'abs': 'АБС',
    'tech': 'Прямое обращение',
    'call_center': 'Колл-центр',
    'ks': 'По звонку',
    'chat': 'Чат',
    'technician': 'Техник',
    'internal': 'Внутренний',
}

# Справочник причин RADIUS
RADIUS_CAUSES = {
    "Admin-Reboot": "Администратор перезагрузил сетевое оборудование (NAS).",
    "Admin-Reset": "Сессия была сброшена администратором вручную.",
    "Hung-Session": "Зависшая сессия: от оборудования долго не поступало обновлений по сессии.",
    "Idle-Timeout": "Тайм-аут простоя: со стороны абонента долго не было активного трафика.",
    "Lost-Carrier": "Потеря несущей: обрыв кабеля, выключение роутера абонента, слабый сигнал от абонента.",
    "Lost-Service": "Какие-то проблемы со стороны клиентского устройства.",
    "NAS-Error": "Внутренняя ошибка на стороне сервера (NAS).",
    "NAS-Reboot": "Внеплановая перезагрузка сервера NAS.",
    "NAS-Request": "Сервер NAS сам инициировал разрыв соединения.",
    "Port-Error": "Ошибка порта на сетевом оборудовании.",
    "Session-Timeout": "Истекло время сессии (закончился лимит времени или трафика по тарифу).",
    "User-Request": "Пользователь сам разорвал соединение (нажал 'Отключить' или выключил ПК/роутер)."
}

# Для страницы спутников и хотспотов
FREQUENCY_MAP = {
    'Ка': 'ka',
    'Ку': 'ku',
    'ka': 'ka',
    'ku': 'ku',
    'KA': 'ka',
    'KU': 'ku',
}
FREQUENCY_TO_RU = {
    'ka': 'Ка',
    'ku': 'Ку'
}

# SNMP OIDs
MODEM_REBOOT_OID = ".1.3.6.1.4.1.5835.5.2.10300.1.2.1.0"
MIKROTIK_REBOOT_OID = ".1.3.6.1.4.1.14988.1.1.7.1.0"
GILAT_REBOOT_OID = ".1.3.6.1.4.1.7352.3.5.10.32.2.0"
# Для логирования в stations.operations
FIELD_NAMES = {
    # IpGroup
    "name":            "Системное имя (eng)",
    "rus_name":        "Название станции (рус)",
    "id_diler":        "Партнёр / дилер",
    "vno":             "VNO",
    "channel_id":      "Канал",
    "id_hotspot":      "ID Hotspot",
    "modem":           "IP модема",
    "login":           "Логин (модем)",
    "router_ip":       "IP роутера",
    "network_hotspot": "Подсеть Hotspot",
    "network_pppoe":   "Подсеть PPPoE",
    "gmt":             "Часовой пояс",
    "region":          "Регион",
    "ip":              "Network address",
    "mask":            "Маска подсети",
    "active":          "Статус (active)",

    # StationForms
    "station_name":    "Название станции (рус)",
    "partner":         "Партнёр (forms)",
    "router_exists":   "Наличие роутера",
}

# Для Бит/Гц
ROLL_OFF = 0.93

# Фотографии
STATIONS_DIR = MEDIA_DIR_DEFAULT / "stations"
if not STATIONS_DIR.exists():
    STATIONS_DIR.mkdir(parents=True)

PUBLIC_PREFIX = "/media"
THUMB_SIZE = (300, 300)
WEBP_QUALITY = 80
WEBP_LOSSLESS = False
WEBP_METHOD = 4

# Файлы на станцию
LAYOUTS_DIR = MEDIA_DIR_DEFAULT / "stations" / "layout"
