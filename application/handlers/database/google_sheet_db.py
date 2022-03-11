from __future__ import annotations

import base64
import datetime

from sqlalchemy import create_engine


class GoogleSheetDB:
    def __init__(self, service_account_file_content, is_encode_base_64=False):
        if is_encode_base_64:
            service_account_file_content = base64.b64decode(service_account_file_content).decode('utf-8')
        file_path = f'/tmp/file_{datetime.datetime.now().timestamp() * 1000}'
        with open(file_path, 'w') as f:
            f.write(service_account_file_content)
        self.engine = create_engine('gsheets://', service_account_file=file_path)
        self.connection = self.engine.connect()
