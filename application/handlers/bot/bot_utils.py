from __future__ import annotations

from application.utils.cache import LambdaCache
from application.utils.constant import Constant


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
    def get_value_from_state(state, name, extra_field=None, block_id=None):
        if not state:
            return None
        try:
            values = state['values'][block_id] if block_id else state['values']
            value = values[name][f'{name}_value'] if values[name].get(f'{name}_value') else values[name]
            extra_field_list = extra_field.split('.')
            for field in extra_field_list:
                value = value[field]
        except KeyError:
            return None
        return value

    @staticmethod
    def build_leave_display_list(user_leave_rows):
        user_leaves = []
        for leave_row in user_leave_rows:
            user_leave = {
                'username': leave_row.username,
                'user_id': leave_row.user_id,
                'start_date': leave_row.start_date,
                'end_date': leave_row.end_date,
                'type_icon': Constant.EMOJI_MAPPING[leave_row.leave_type],
                'duration': f"{leave_row.start_date.strftime('%A, %B, %d, %Y')} "
                            f"to {leave_row.end_date.strftime('%A, %B, %d, %Y')}",
                'status_icon': Constant.EMOJI_MAPPING[leave_row.status],
                'reason': leave_row.reason,
                'type': leave_row.leave_type,
                'status': leave_row.status,
                'id': leave_row.id,

            }
            user_leaves.append(user_leave)
        return user_leaves
