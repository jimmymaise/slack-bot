from __future__ import annotations


class LambdaCache:
    _lambda_cache = {}

    @classmethod
    def get_cache(cls, key, is_delete_after_get=False):
        value = cls._lambda_cache.get(key)
        if is_delete_after_get:
            del cls._lambda_cache[key]
        return value

    @classmethod
    def is_exist_cache(cls, key):
        if key in cls._lambda_cache:
            return True
        return False

    @classmethod
    def set_cache(cls, key, value):
        cls._lambda_cache[key] = value

    @classmethod
    def reset_all_db_cache(cls):
        for key in cls._lambda_cache.keys():
            if key.startswith('db_cache'):
                del cls._lambda_cache[key]
