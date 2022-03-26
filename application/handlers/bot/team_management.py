from __future__ import annotations

import datetime
import json

from slack_bolt import App
from slack_bolt import BoltContext
from slack_sdk import WebClient

from application.handlers.bot.base_management import BaseManagement


class TeamManagement(BaseManagement):
    def __init__(self, app: App, client: WebClient):
        super().__init__(app, client)

        app.view('create_team_view')(
            ack=lambda ack: ack(response_action='clear'),
            lazy=[self.create_team_lazy],
        )
        app.view('update_team_view')(
            ack=lambda ack: ack(response_action='clear'),
            lazy=[self.update_team_lazy],
        )
        app.action('switch_personal')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_personal_view_by_user_id],
        )
        app.action('back_to_personal_home')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_personal_view_by_user_id],
        )
        app.action('back_to_manager_home')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_manager_view_by_user_id],
        )

        app.action('switch_manager')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_manager_view_by_user_id],
        )
        app.action('team_actions')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.process_team_actions_lazy],
        )
        app.event('team_join')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.process_new_user_join_work_space],
        )
        app.action('new_crew_member_approve')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.add_or_decline_new_member_to_the_team_lazy],
        )

        app.action('new_crew_member_decline')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.add_or_decline_new_member_to_the_team_lazy],
        )

    def process_new_user_join_work_space(self, body, event, context):
        workspace_name = self.client.team_info()['team']['name']

        team_managers = self.team_member_db_handler.get_team_managers_from_all_teams()

        for team_manager in team_managers:
            number_of_members = self.team_member_db_handler.count_number_of_team_members(team_manager.team_id)
            team_name = self.team_db_handler.get_team_by_id(team_manager.team_id).name
            self.client.chat_postMessage(
                channel=team_manager.user_id,
                blocks=json.loads(
                    self.block_kit.new_member_to_add_message(
                        workspace_name=workspace_name,
                        user_id=context.user_id,
                        number_of_members=number_of_members,
                        team_name=team_name,
                        team_id=team_manager.team_id,

                    ),
                ),
            )

    def add_or_decline_new_member_to_the_team_lazy(self, event, context: BoltContext, client: WebClient, body):

        data = body.get('actions')[0].get('value')
        member_user_id, team_id = data.split(':')

        message_ts = body['message']['ts']
        team_managers = self.team_member_db_handler.get_team_managers_by_team_id(team_id=team_id)

        action_id = body.get('actions')[0].get('action_id')
        if action_id == 'new_crew_member_approve':
            self.team_member_db_handler.add_user_to_team(
                user_id=member_user_id,
                team_id=team_id, is_manager=False,
            )
            message = '<@{member_user_id}> has been successfully added to {team_name} by <@{manager_user_id}>!'
        else:
            message = '<@{member_user_id}> has been rejected to be added to {team_name} by <@{manager_user_id}>!'

        for team_manager in team_managers:
            channel = client.conversations_open(users=[team_manager.user_id])['channel']['id']
            team_name = self.team_db_handler.get_team_by_id(team_manager.team_id).name
            client.chat_update(
                channel=channel,
                ts=message_ts,
                blocks=[],
                text=message.format(
                    team_name=team_name,
                    member_user_id=member_user_id,
                    manager_user_id=team_manager.user_id,

                ),
            )

    def get_create_team_view_lazy(self, event, context: BoltContext, client: WebClient, body):
        user_name = self.get_username_by_user_id(context.user_id)
        client.views_open(
            trigger_id=body.get('trigger_id'),
            view=json.loads(
                self.block_kit.create_update_team_view(
                    callback_id='create_team_view',
                    initial_team_name=f"{user_name}'s team",

                    initial_normal_members=[
                    ],
                    initial_managers=[context.user_id],
                    title='Create a team',
                    submit_type='Create',
                ),
            ),
        )

    def get_update_team_view_lazy(self, event, context: BoltContext, client: WebClient, body):
        team_id = self.get_team_id_by_user_id(context.user_id)
        team_info = self.get_team_by_team_id(team_id)
        all_team_members = self.team_member_db_handler.get_all_team_members_by_team_id(team_id=team_id)
        update_team_view = json.loads(
            self.block_kit.create_update_team_view(
                callback_id='update_team_view',
                initial_team_name=team_info.name,
                initial_managers=[
                    member.user_id for member in all_team_members if
                    member.is_manager
                ],
                initial_normal_members=[
                    member.user_id for member in all_team_members if
                    not member.is_manager
                ],
                initial_conversation=team_info.announcement_channel_id,
                title='Update team',
                submit_type='Update',
            ),
        )
        update_team_view['private_metadata'] = json.dumps({'team_id': team_id})
        client.views_open(
            trigger_id=body.get('trigger_id'),
            view=update_team_view,
        )

    def create_team_lazy(self, client, body, ack):
        user_id = body['user']['id']
        data = self._parse_data_from_create_update_team_view(body)
        team_id = self.team_db_handler.add_item(
            data={
                'announcement_channel_id': data.get('announcement_channel_id'),
                'name': data['team_name'],
                'holiday_country': 'US',

            },
        )

        all_team_members = [{'user_id': member['user_id'], 'is_manager': member['is_manager'], 'team_id': team_id} for
                            member in
                            data['all_team_members']]

        self.team_member_db_handler.add_many_items(
            all_team_members,
        )
        self.get_manager_view_by_user_id(user_id)

    def update_team_lazy(self, client, body, ack):
        private_metadata = json.loads(body['view']['private_metadata'])
        team_id = private_metadata['team_id']
        user_id = body['user']['id']

        data = self._parse_data_from_create_update_team_view(body)

        all_team_members = [{'user_id': member['user_id'], 'is_manager': member['is_manager'], 'team_id': team_id} for
                            member in
                            data['all_team_members']]

        self.team_db_handler.update_item_by_id(
            update_data={
                'announcement_channel_id': data['announcement_channel_id'],
                'name': data['team_name'],
                'holiday_country': 'US',
            },
            _id=team_id,
        )
        self.team_member_db_handler.replace_members_from_team(team_id, all_team_members)
        self.get_manager_view_by_user_id(user_id)

    def get_personal_view_lazy(self, body):
        self.get_personal_view_by_user_id(body['user']['id'])

    def get_manager_view_by_user_id(self, user_id):
        team_id = self.get_team_id_by_user_id(user_id)
        if not team_id:
            return self.get_personal_view_by_user_id(user_id)
        team_info = self.get_team_by_team_id(team_id)
        announcement_channel_name = ''
        if team_info.announcement_channel_id:
            announcement_channel_name = \
                self.client.conversations_info(channel=team_info.announcement_channel_id)['channel']['name']
        all_team_members = self.team_member_db_handler.get_all_team_members_by_team_id(team_id=team_id)
        num_of_all_team_member = len(all_team_members)
        num_of_manager = sum(1 for team_member in all_team_members if team_member.is_manager)
        num_of_normal_member = num_of_all_team_member - num_of_manager
        slack_users = self.get_slack_users_by_user_ids(
            [team_member.user_id for team_member in all_team_members],
        )
        wait_for_approval_leaves_rows = self.leave_register_db_handler.get_leaves(
            team_id=team_id,
            statuses=[self.constant.LEAVE_REQUEST_STATUS_WAIT],
        )
        wait_for_approval_leaves = self.build_leave_display_list(wait_for_approval_leaves_rows, True)

        current_leaves_rows = self.leave_register_db_handler.get_leaves(
            start_date=datetime.datetime.now().strftime('%Y-%m-%d'),
            end_date=datetime.datetime.now().strftime('%Y-%m-%d'),
            team_id=team_id,
            statuses=[self.constant.LEAVE_REQUEST_STATUS_WAIT, self.constant.LEAVE_REQUEST_STATUS_APPROVED],
        )
        current_leaves = self.build_leave_display_list(current_leaves_rows, True)
        up_coming_leaves_rows = self.leave_register_db_handler.get_leaves(
            start_date=datetime.datetime.now().strftime('%Y-%m-%d'),
            team_id=team_id,
            statuses=[self.constant.LEAVE_REQUEST_STATUS_WAIT, self.constant.LEAVE_REQUEST_STATUS_APPROVED],
            is_exclude_request_time_off_before_start_date=True,
        )
        up_coming_leaves = self.build_leave_display_list(up_coming_leaves_rows, True)
        self.client.views_publish(
            user_id=user_id,
            view={

                'type': 'home',
                'blocks': json.loads(
                    self.block_kit.manager_panel(
                        team_info=team_info,
                        announcement_channel_name=announcement_channel_name,
                        num_of_normal_member=num_of_normal_member,
                        num_of_manager=num_of_manager,
                        all_team_members=all_team_members,
                        slack_users=slack_users,
                        up_coming_leaves=up_coming_leaves,
                        wait_for_approval_leaves=wait_for_approval_leaves,
                        current_leaves=current_leaves,

                    ),
                ), },
        )

    def get_personal_view_by_user_id(self, user_id):
        user = self.client.users_info(user=user_id).data['user']
        is_admin_or_owner = user['is_admin'] or user['is_owner']
        current_team = self.get_team_member_by_user_id(user_id)
        team_name = self.get_team_by_team_id(team_id=current_team.team_id).name if current_team else None
        is_able_to_create_team = current_team is None and is_admin_or_owner
        is_already_manager = current_team and current_team.is_manager
        is_not_have_team = not (current_team or is_admin_or_owner)

        user_leave_rows = self.leave_register_db_handler.get_leaves(
            start_date=datetime.datetime.now().strftime('%Y-%m-%d'),
            user_id=user_id,
        )

        user_leaves = self.build_leave_display_list(user_leave_rows)

        blocks = json.loads(
            self.block_kit.personal_view(
                is_able_to_create_team=is_able_to_create_team,
                is_already_manager=is_already_manager,
                is_not_have_team=is_not_have_team,
                user_leaves=user_leaves,
                team_name=team_name,
            ),
        )

        self.client.views_publish(
            user_id=user_id, view={
                'type': 'home',
                'blocks': blocks,
            },
        )

    def process_team_actions_lazy(self, event, context: BoltContext, client: WebClient, body):
        action_data = body['actions'][0]['selected_option']['value'].split(',')
        if action_data[0] == 'destroy':
            self.team_db_handler.delete_team_by_id(action_data[1])
            self.team_member_db_handler.delete_team_members_by_team_id(team_id=action_data[1])
        return self.get_manager_view_by_user_id(user_id=body['user']['id'])

    def _parse_data_from_create_update_team_view(self, body):
        return_data = {}
        user_id = body['user']['id']
        state = body['view']['state']

        team_name = self.get_value_from_state(state, 'name', 'value')
        announcement_channel_id = self.get_value_from_state(state, 'channel', 'selected_conversation')

        managers = self.get_value_from_state(state, 'managers', 'selected_users')
        if user_id not in managers:
            managers.append(user_id)
        normal_members = self.get_value_from_state(state, 'members', 'selected_users')
        slack_users = self.get_slack_users_by_user_ids(list(set(managers + normal_members)))
        slack_bots = [user['id'] for user in slack_users if user['is_bot']]
        managers = list(set(managers) - set(slack_bots))
        normal_members = list(set(normal_members) - set(managers) - set(slack_bots))

        all_team_members = [{'user_id': manager, 'is_manager': True} for manager in managers]
        all_team_members += [
            {'user_id': normal_member, 'is_manager': False} for normal_member in
            normal_members
        ]
        return_data.update({
            'team_name': team_name,
            'announcement_channel_id': announcement_channel_id,
            'name': team_name,
            'all_team_members': all_team_members,
        })
        return return_data
