from __future__ import annotations

import re

import tenacity
from sqlalchemy import Table

from application.utils.cache import LambdaCache
from application.utils.constant import Constant


class BaseDBHandler:
    def __init__(self, google_sheet_db, google_sheet, table_schema):
        self.google_sheet_db = google_sheet_db
        self.table_schema = table_schema
        self.google_sheet = google_sheet
        self.table: Table = self.create_table_from_google_sheet()

    def create_table_from_google_sheet(self) -> Table:
        from sqlalchemy import MetaData
        return Table(
            self.google_sheet,
            MetaData(bind=self.google_sheet_db.engine), *self.table_schema,
        )

    def execute(self, query, **data):
        is_select_query = True
        str_query = str(query)
        executed_list = self.get_query_list_from_sql_command(str_query)
        for command in executed_list:
            if not command.strip().lower().startswith('select'):
                is_select_query = False
                break
        if not is_select_query:
            LambdaCache.reset_all_db_cache()
        print(str_query)
        return self.google_sheet_db.cursor.execute(query, data)

    def update_item_with_retry(self, _id, update_data: dict, wait_fixed=10, stop_after_attempt=2):
        retry = tenacity.Retrying(
            wait=tenacity.wait_fixed(wait_fixed),
            stop=tenacity.stop_after_attempt(stop_after_attempt),
            reraise=True,
        )
        retry(self.update_item_by_id_and_verify_success, _id, update_data)

    def add_item_with_retry(self, data: dict, wait_fixed=10, stop_after_attempt=2):
        retry = tenacity.Retrying(
            wait=tenacity.wait_fixed(wait_fixed),
            stop=tenacity.stop_after_attempt(stop_after_attempt),
            reraise=True,
        )
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
            reraise=True,
        )
        return retry(self.find_item_by_multi_keys, data)

    def update_item_by_id(self, _id, update_data: dict):

        update_query = self.table.update().where(self.table.c.id == _id).values(**update_data)
        self.execute(update_query)

    def add_item(self, data: dict):
        result = self.execute(self.table.insert(), **data)
        return getattr(result.inserted_primary_key, '_data')[0]

    def add_many_items(self, item_list: list):
        # `executemany`` is not supported, use ``execute`` instead
        for item in item_list:
            self.execute(self.table.insert(), **item)

    def remove_item_by_id(self, _id):
        return self.execute(self.table.delete().where(self.table.c.id == _id))

    def find_item_by_id(self, _id):

        q = self.table.select(). \
            filter(self.table.c.id == _id)
        result = self.execute(q)
        if not result.rowcount:
            print('Cannot find item')
            raise Exception('Cannot find item')
        print('find item successfully')

    def find_item_by_multi_keys(self, key_value_dict: dict):
        q = self.table.select().filter_by(
            **key_value_dict,
        )
        result = self.execute(q)
        if not result.rowcount:
            print('Cannot find item')
            raise Exception('Cannot find item')
        print('find item successfully')
        return result

    @staticmethod
    def get_query_list_from_sql_command(sql_command):
        sql_split_regex = re.compile(Constant.RE_SQL_SPLIT_STMTS)
        executed_list = sql_split_regex.split(sql_command)
        while '' in executed_list:
            executed_list.remove('')
        if executed_list:
            executed_list[-1] = f'{executed_list[-1]};'
        return executed_list
