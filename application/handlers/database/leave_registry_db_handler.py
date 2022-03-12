from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID

from application.handlers.database.base_db_handler import BaseDBHandler
from application.utils.constant import Constant


class LeaveRegistryDBHandler(BaseDBHandler):
    def __init__(self):
        table_name = Constant.LEAVE_REGISTER_SHEET
        schema = (
            Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            Column('username', String()),
            Column('user_id', String()),
            Column('start_date', String()),
            Column('end_date', String()),
            Column('leave_type', String()),
            Column('reason', String()),
            Column('created_time', String()),
            Column('status', String()),
            Column('approver', String()),
        )
        super().__init__(table_name, schema)

    def get_today_ooo(self, statuses):
        today_date_str = datetime.now().strftime('%Y-%m-%d')
        return self.get_leaves(
            start_date=today_date_str, end_date=today_date_str,
            statuses=statuses,
        )

    def get_leaves(
            self, *, start_date: str = None, end_date: str = None, statuses: list = None,
            user_id: str = None, leave_type=None,
    ):
        select_query = self.table.select()
        if not start_date:
            start_date = '1900-01-01'
        if not end_date:
            end_date = '9999-01-01'
        select_query = select_query.filter(
            ((self.table.c.start_date <= start_date)
             & (self.table.c.end_date >= start_date))
            | ((self.table.c.start_date <= end_date) & (self.table.c.end_date >= end_date))
            | ((self.table.c.start_date >= start_date) & (self.table.c.end_date <= end_date)),
        )
        if statuses:
            select_query = select_query.filter(
                self.table.c.status.in_(statuses),
            )
        if user_id:
            select_query = select_query.filter(
                self.table.c.user_id == user_id,
            )
        if leave_type:
            select_query = select_query.filter(
                self.table.c.leave_type == leave_type,
            )
        result = self.execute(select_query)

        return result.all() if result.rowcount else []

    def change_leave_status(self, leave_id, manager_name, status):
        update_data = {
            'approver': manager_name,
            'status': status,
        }
        self.update_item_with_retry(_id=leave_id, update_data=update_data)

    def add_a_leave(
            self, leave_type, reason_of_leave, user_name, user_id, start_date,
            end_date,
    ):
        leave_data = {
            'username': user_name,
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date,
            'leave_type': leave_type,
            'reason': reason_of_leave,
            'status': Constant.LEAVE_REQUEST_STATUS_WAIT,
            'created_time': datetime.now(),
        }
        return self.add_item_with_retry(data=leave_data)
