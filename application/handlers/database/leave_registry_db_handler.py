from datetime import datetime

from pypika import Query

from application.handlers.database.base_db_handler import BaseDBHandler
from application.utils.constant import Constant


class LeaveRegistryDBHandler(BaseDBHandler):
    def __init__(self, google_sheet_db, leave_register_sheet):
        super().__init__(google_sheet_db, leave_register_sheet)

    def get_today_ooo(self, statuses):
        today_date_str = datetime.now().strftime('%Y-%m-%d')
        return self.get_leaves_by_date_range(start_date=today_date_str, end_date=today_date_str,
                                             statuses=statuses)

    def get_leaves_by_date_range(self, start_date: str, end_date: str, statuses: list):
        select_query = Query.from_(self.table).select('*') \
            .where(self.table["start_date"] <= start_date) \
            .where(self.table["end_date"] >= end_date)
        if statuses:
            select_query = select_query.where(self.table["status"].isin(statuses))
        select_query = select_query.get_sql()
        return self.google_sheet_db.cursor.execute(select_query)

    def change_leave_status(self, leave_id, manager_name, status):
        update_data = {
            'approver': manager_name,
            'status': status
        }
        self.update_item_with_retry(_id=leave_id, update_data=update_data)

    def add_a_leave(self, leave_type, reason_of_leave, user_name, start_date,
                    end_date):
        leave_data = {
            'username': user_name,
            'start_date': start_date,
            'end_date': end_date,
            'leave_type': leave_type,
            'reason': reason_of_leave,
            'status': Constant.LEAVE_REQUEST_STATUS_WAIT,
            'created_time': datetime.now()
        }
        return self.add_item_with_retry(data=leave_data)
