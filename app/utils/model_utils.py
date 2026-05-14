# app/utils/model_utils.py
from typing import Any, Dict, Optional
from sqlalchemy.inspection import inspect

def _model_to_dict(instance: Any) -> Optional[Dict[str, Any]]:
    if instance is None:
        return None
    return {column.key: getattr(instance, column.key) for column in inspect(instance).mapper.column_attrs}