from __future__ import annotations

from datetime import datetime
from datetime import timedelta

from sqlalchemy import select

from application.handlers.database.base_db_handler import BaseDBHandler
from application.handlers.database.models import LeaveRegistry
from application.handlers.database.team_member_db_handler import TeamMember
from application.utils.constant import Constant


class LeaveRegistryDBHandler(BaseDBHandler):
    def __init__(self):

        super().__init__(LeaveRegistry)

    def get_today_ooo(self, statuses, team_id=None):
        today_date_str = datetime.now().strftime('%Y-%m-%d')
        return self.get_leaves(
            start_date=today_date_str, end_date=today_date_str,
            statuses=statuses,
            team_id=team_id,
        )

    def get_upcoming_ooo(self, statuses, team_id=None):
        start_date_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        end_date_str = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        return self.get_leaves(
            start_date=start_date_str,
            end_date=end_date_str,
            statuses=statuses,
            team_id=team_id,
            is_exclude_request_time_off_before_start_date=True,
        )

    def get_leaves(
            self, *, start_date: str = None, end_date: str = None, statuses: list = None,
            user_id: str = None, leave_type=None, team_id=None, is_exclude_request_time_off_before_start_date=False,
    ):
        select_query = select(self.table)
        if not start_date:
            start_date = '1900-01-01'
        if not end_date:
            end_date = '9999-01-01'
        select_query = select_query.filter(
            ((start_date >= self.table.start_date) & (start_date <= self.table.end_date))
            | ((end_date >= self.table.start_date) & (end_date <= self.table.end_date))
            | ((start_date <= self.table.start_date) & (end_date >= self.table.end_date)),
        )
        if statuses:
            select_query = select_query.filter(
                self.table.status.in_(statuses),
            )
        if user_id:
            select_query = select_query.filter(
                self.table.user_id == user_id,
            )
        if leave_type:
            select_query = select_query.filter(
                self.table.leave_type == leave_type,
            )
        if team_id:
            select_query = select_query. \
                join(TeamMember, self.table.user_id == TeamMember.user_id). \
                where(TeamMember.team_id == team_id)

        if is_exclude_request_time_off_before_start_date:
            select_query = select_query.where(self.table.start_date >= start_date)

        result = self.execute(select_query)

        return result.all() if result.rowcount else []

    def change_leave_status(self, leave_id, updated_by, status):
        update_data = {
            'updated_by': updated_by,
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

    def update_a_leave(self, _id, update_data):
        return self.update_item_with_retry(_id=_id, update_data=update_data)

    def cancel_a_leave(self, leave_id, updated_by):
        return self.change_leave_status(
            leave_id=leave_id,
            updated_by=updated_by,
            status=self.constant.LEAVE_REQUEST_STATUS_CANCELED,
        )

    def update_leave_dates(self, leave_id, start_date, end_date, update_by):
        update_data = {
            'start_date': start_date,
            'end_date': end_date,
            'update_by': update_by,
        }
        self.update_item_with_retry(_id=leave_id, update_data=update_data)
