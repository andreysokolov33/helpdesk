VISIBLE = {
    "engineer_admin": {
        "*"
    },

    "engineer": {
        "*",        # всё
        "!abs_users"  # кроме пользователей АБС
    },

    "director": {
        "*",
        "!abs_users", "!daemons", "!speed_profiles", "!nas"
    },

    "accountant": {
        "*",
        "!abs_users", "!daemons", "!speed_profiles", "!nas",
        "!subscribers_analyze", "!subscribers_news",
        "!vno", "!media_servers",
        "!partners_questions", "!partners_month",
        "!partners_news", "!partners_logs",
        "!docs", "!cs", "!satellite_hotspot", "!detalisation",
        "!cs_new", "!main_page", "!chat", "!tracker",
        "!stations_list", "!stations_map"
    },

    "manager": {
        "*",
        "!abs_users", "!daemons", "!speed_profiles", "!nas",
        "!subscribers_analyze", "!subscribers_news",
        "!vno", "!media_servers",
        "!partners_questions", "!partners_month",
        "!partners_news", "!partners_logs",
        "!docs", "!cs", "!satellite_hotspot", "!detalisation",
        "!cs_new", "!main_page", "!chat", "!tracker"
    },
    "marketing": "accountant",

    "support": {
        "*",
        "!abs_users", "!daemons", "!speed_profiles", "!nas",
        "!subscribers_analyze", "!subscribers_news",
        "!vno", "!media_servers",
        "!partners_questions", "!partners_month",
        "!partners_news", "!partners_logs",
        "!docs", "!satellite_hotspot",
        "!station_list", "!station_map", "!frozen_users",
        "!tariff_list", "!tariff_dop", "!tariff_net", "!partners_list",
        "!profile", "!favorite", "!main_page", '!descriptions'
    },

    "default": {},
}

def normalize_scope(scope: str, priv: bool) -> str:
    if scope == "engineer" and priv:
        return "engineer_admin"
    return scope


def expand_role(scope: str):
    role = VISIBLE.get(scope)

    if isinstance(role, str):
        # alias, например "manager": "accountant"
        return VISIBLE[role]

    return role or VISIBLE["default"]


def resolve_allowed(scope: str, priv: bool) -> set:
    role = normalize_scope(scope, priv)
    rules = expand_role(role)

    if "*" in rules:
        # глобальный доступ с исключениями
        disallowed = {x[1:] for x in rules if x.startswith("!")}
        return {"*"} | {"!"+d for d in disallowed}

    return rules