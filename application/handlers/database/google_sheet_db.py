from __future__ import annotations

import base64
import datetime

import gspread
from sqlalchemy import create_engine


class GoogleSheetDB:
    def __init__(self, service_account_file_content, db_spreadsheet_id, is_encode_base_64=False):
        if is_encode_base_64:
            service_account_file_content = base64.b64decode(service_account_file_content).decode('utf-8')
        file_path = f'/tmp/file_{datetime.datetime.now().timestamp() * 1000}'
        with open(file_path, 'w') as f:
            f.write(service_account_file_content)
        self.engine = create_engine('gsheets://', service_account_file=file_path)
        self.connection = self.engine.connect()
        self.gs_api_client = gspread.service_account(file_path)
        self.spread_sheet = self.gs_api_client.open_by_key(db_spreadsheet_id)
        self.db_spreadsheet_id = db_spreadsheet_id
        self.worksheet_list = self.spread_sheet.worksheets()

    def get_sheet_url_by_name(self, name):
        for ws in self.worksheet_list:
            if ws.title == name:
                return 'https://docs.google.com/spreadsheets/d/' \
                       '{db_spreadsheet_id}' \
                       '/#gid={ws_id}'.format(
                           db_spreadsheet_id=self.db_spreadsheet_id,
                           ws_id=ws.id,
                       )
        raise Exception(f'Cannot get the sheet url with name {name}')
