import uuid

import tenacity
from pypika import Table, Query


class BaseDBHandler:
    def __init__(self, google_sheet_db, google_sheet):
        self.table = Table(google_sheet)
        self.google_sheet_db = google_sheet_db

    def update_item_with_retry(self, _id, update_data: dict, wait_fixed=10, stop_after_attempt=2):
        retry = tenacity.Retrying(
            wait=tenacity.wait_fixed(wait_fixed),
            stop=tenacity.stop_after_attempt(stop_after_attempt),
            reraise=True)
        retry(self.update_item_by_id_and_verify_success, _id, update_data)

    def add_item_with_retry(self, data: dict, wait_fixed=10, stop_after_attempt=2):
        retry = tenacity.Retrying(
            wait=tenacity.wait_fixed(wait_fixed),
            stop=tenacity.stop_after_attempt(stop_after_attempt),
            reraise=True)
        return retry(self.add_item_and_verify_success, data)

    def update_item_by_id_and_verify_success(self, _id, update_data: dict):
        self.update_item_by_id(_id, update_data)
        update_data['id'] = _id
        return self._verify_operation_success_by_lookup_with_retry(update_data)

    def add_item_and_verify_success(self, data: dict):
        leave_id = self.add_item(data)
        self._verify_operation_success_by_lookup_with_retry(data)
        return leave_id

    def _verify_operation_success_by_lookup_with_retry(self, data, wait_fixed=30, stop_after_attempt=4):
        retry = tenacity.Retrying(
            wait=tenacity.wait_fixed(wait_fixed),
            stop=tenacity.stop_after_attempt(stop_after_attempt),
            reraise=True)
        return retry(self.find_item_by_multi_keys, data)

    def update_item_by_id(self, _id, update_data: dict):
        update_query = Query.update(self.table)
        for column, value in update_data.items():
            update_query = update_query.set(
                self.table[column], value
            )
        update_query = update_query.where(self.table['id'] == _id).get_sql()
        self.google_sheet_db.cursor.execute(update_query)

    def add_item(self, data: dict):
        data['id'] = str(uuid.uuid4())
        keys = data.keys()
        values = data.values()

        q = Query.into(self.table). \
            columns(*keys). \
            insert(*values).get_sql()
        self.google_sheet_db.cursor.execute(q)
        return data['id']

    def find_item_by_id(self, _id):

        q = Query.from_(self.table).select('*'). \
            where(self.table["id"] == _id).get_sql()
        result = self.google_sheet_db.cursor.execute(q)
        if not result.rowcount:
            print("Cannot find item")
            raise Exception(f"Cannot find item")
        print('find item successfully')

    def find_item_by_multi_keys(self, key_value_dict: dict):
        q = Query.from_(self.table).select('*')
        for key, value in key_value_dict.items():
            q = q.where(self.table[key] == value)
        q = q.get_sql()
        result = self.google_sheet_db.cursor.execute(q)
        if not result.rowcount:
            print("Cannot find item")
            raise Exception(f"Cannot find item")
        print('find item successfully')
        return result
