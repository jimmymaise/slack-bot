from __future__ import annotations

from application.utils.cache import LambdaCache


class BotUtils:
    @staticmethod
    def get_username_by_user_id(client, user_id):
        user_name = LambdaCache.get_cache(f'slack_cache_{user_id}_user_name', False)
        if user_name:
            return user_name

        user_info = client.users_info(user=user_id)
        user_name = user_info.get('user').get('real_name')
        LambdaCache.set_cache(f'slack_cache_{user_id}_user_name', user_name)
        return user_name

    @staticmethod
    def get_value_from_state(state, name, extra_field=None):
        return state['values'][name][f'{name}_value'][extra_field] \
            if extra_field else state['values'][name][f'{name}_value']
