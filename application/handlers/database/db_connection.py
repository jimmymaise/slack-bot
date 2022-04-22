from __future__ import annotations

from application.handlers.database.google_sheet_db import GoogleSheetDB
from application.utils.constant import Constant


class DBConnection:
    @staticmethod
    def get_db() -> GoogleSheetDB:
        return GoogleSheetDB(
            service_account_file_content=Constant.GOOGLE_SERVICE_BASE64_FILE_CONTENT,
            is_encode_base_64=True,
            db_spreadsheet_id=Constant.DB_SPREADSHEET_ID,
        )
