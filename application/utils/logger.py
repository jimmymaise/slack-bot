from __future__ import annotations

import logging
import os
import sys


class Logger:

    @classmethod
    def get_logger(cls):
        logging.basicConfig(level=logging.INFO)
        is_running_lambda_logging = os.environ.get('AWS_EXECUTION_ENV') is not None
        logger = logging.getLogger()
        if not is_running_lambda_logging:
            cls._setup_logger_console(logger)
        return logging.getLogger()

    @staticmethod
    def _setup_logger_console(logger):
        # Just need to display in console when running task file directly
        # define a Handler which writes INFO messages or higher to the sys.stderr

        console = logging.StreamHandler(sys.stdout)

        console.setLevel(logging.INFO)
        logger.addHandler(console)

    # logger in a global context
# requires importing logging
