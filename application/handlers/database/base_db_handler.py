from __future__ import annotations

import re

import tenacity
from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from application.handlers.database.db_connection import DBConnection
from application.utils.cache import LambdaCache
from application.utils.constant import Constant
from application.utils.logger import Logger

Base = declarative_base()


class BaseDBHandler:
    def __init__(self, table):
        self.db = DBConnection.get_db()
        self.session = scoped_session(sessionmaker(bind=self.db.engine))
        self.table = table
        self.logger = Logger.get_logger()

    def execute(self, query, **data):
        is_select_query = True
        str_query = str(query)
        print(str_query)
        executed_list = self.get_query_list_from_sql_command(str_query)
        for command in executed_list:
            if not command.strip().lower().startswith('select'):
                is_select_query = False
                break
        if not is_select_query:
            LambdaCache.reset_all_db_cache()
        self.logger.info(str_query)
        if getattr(query, 'statement', None) is not None:
            query = query.statement
        return self.db.connection.execute(query, data)

    def update_item_with_retry(self, _id, update_data: dict, wait_fixed=Constant.WAIT_DEFAULT, stop_after_attempt=2):
        retry = tenacity.Retrying(
            wait=tenacity.wait_fixed(wait_fixed),
            stop=tenacity.stop_after_attempt(stop_after_attempt),
            reraise=True,
        )
        retry(self.update_item_by_id_and_verify_success, _id, update_data)

    def add_item_with_retry(self, data: dict, wait_fixed=Constant.WAIT_DEFAULT, stop_after_attempt=2):
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
        _id = self.add_item(data)
        self._verify_operation_success_by_lookup_with_retry({'id': _id})
        return _id

    def _verify_operation_success_by_lookup_with_retry(
            self, data, wait_fixed=Constant.WAIT_DEFAULT,
            stop_after_attempt=4,
    ):
        LambdaCache.reset_all_db_cache()
        retry = tenacity.Retrying(
            wait=tenacity.wait_fixed(wait_fixed),
            stop=tenacity.stop_after_attempt(stop_after_attempt),
            reraise=True,
        )
        return retry(self.find_item_by_multi_keys, data)

    def update_item_by_id(self, _id, update_data: dict):

        update_query = update(self.table).where(self.table.id == _id).values(**update_data)
        self.execute(update_query)

    def add_item(self, data: dict):
        result = self.execute(insert(self.table).values(**data))
        return getattr(result.inserted_primary_key, '_data')[0]

    def delete_item_by_id(self, _id: str):
        # user = self.session.query(self.table).filter(self.table.id == _id).one()
        # self.session.delete(user)
        self.session.remove()
        result = self.execute(delete(self.table).where(self.table.id == _id))
        return result

    def add_many_items(self, item_list: list):
        # `executemany`` is not supported, use ``execute`` instead
        for item in item_list:
            self.add_item(item)

    def remove_item_by_id(self, _id):
        return self.execute(self.session.delete(self.table).where(self.table.id == _id))

    def find_item_by_id(self, _id):

        q = self.session.query(self.table). \
            filter(self.table.id == _id)
        result = self.execute(q)
        if not result.rowcount:
            self.logger.error(f'Cannot find item {_id}')
            raise Exception(f'Cannot find item {_id}')
        self.logger.info('find item successfully')
        return result.first()

    def find_item_by_multi_keys(self, key_value_dict: dict):
        q = self.session.query(self.table).filter_by(
            **key_value_dict,
        )
        result = self.execute(q)
        if not result.rowcount:
            self.logger.error(f'Cannot find item {key_value_dict}')
            raise Exception(f'Cannot find item {key_value_dict}')
        self.logger.info('find item successfully')
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

    def get_all_items(self):
        q = self.session.query(self.table)
        result = self.execute(q)
        return result if result.rowcount else []
