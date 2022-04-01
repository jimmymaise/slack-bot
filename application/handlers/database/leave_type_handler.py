from __future__ import annotations

import json

from application.handlers.database.base_db_handler import BaseDBHandler
from application.handlers.database.models import LeaveType
from application.utils.common import uuid_convert


class LeaveTypeDBHandler(BaseDBHandler):
    def __init__(self):
        super().__init__(LeaveType)

    def get_all_leave_types_from_cache(self) -> list[dict]:
        leave_types = self.lambda_cache.get_cache('LEAVE_TYPES')

        if leave_types:
            return json.loads(self.lambda_cache.get_cache('LEAVE_TYPES'))

        leave_types = [dict(item) for item in self.get_all_items()]
        self.lambda_cache.set_cache('LEAVE_TYPES', json.dumps(leave_types, default=uuid_convert))
        return json.loads(self.lambda_cache.get_cache('LEAVE_TYPES'))

    def get_leave_type_detail_from_cache(self, leave_type: str):
        for leave_type_obj in self.get_all_leave_types_from_cache():
            if leave_type_obj['code'] == leave_type:
                return leave_type_obj
