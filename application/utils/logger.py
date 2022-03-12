from __future__ import annotations

import logging
import os
import sys


class Logger:

    @classmethod
    def get_logger(cls):
        logger = logging.getLogger()
        return logger

    @staticmethod
    def _setup_logger_console(logger):
        # Just need to display in console when running task file directly
        # define a Handler which writes INFO messages or higher to the sys.stderr

        console = logging.StreamHandler(sys.stdout)

        console.setLevel(logging.INFO)
        logger.addHandler(console)
