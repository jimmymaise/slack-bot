from __future__ import annotations

import os


class Constant:
    WAIT_DEFAULT = 30
    SCHEDULER_OOO_TODAY = 'SCHEDULER_OOO_TODAY'
    SCHEDULER_MUST_READ = 'SCHEDULER_MUST_READ'
    SCHEDULER_WARM_UP_LAMBDA = 'SCHEDULER_WARM_UP_LAMBDA'
    EMOJI_MAPPING = {
        'Rejected': ':X:',
        'Wait for Approval': ':eye:',
    }

    MUST_READ_STATUS_IN_PROGRESS = 'In-progress'
    MUST_READ_STATUS_COMPLETED = 'Completed'

    LEAVE_REQUEST_STATUS_REJECTED = 'Rejected'
    LEAVE_REQUEST_STATUS_APPROVED = 'Approved'
    LEAVE_REQUEST_STATUS_WAIT = 'Wait for Approval'
    LEAVE_REQUEST_STATUS_CANCELED = 'Canceled'

    LEAVE_REQUEST_ACTION_REJECT = 'Reject'
    LEAVE_REQUEST_ACTION_APPROVE = 'Approve'
    LEAVE_REQUEST_ACTION_CANCEL = 'Cancel'
    LEAVE_REQUEST_ACTION_EDIT = 'Edit'

    LEAVE_DECISION_TO_STATUS = {
        LEAVE_REQUEST_ACTION_REJECT: LEAVE_REQUEST_STATUS_REJECTED,
        LEAVE_REQUEST_ACTION_APPROVE: LEAVE_REQUEST_STATUS_APPROVED,
        LEAVE_REQUEST_ACTION_CANCEL: LEAVE_REQUEST_STATUS_CANCELED,
        LEAVE_REQUEST_ACTION_EDIT: LEAVE_REQUEST_STATUS_WAIT,

    }
    RE_SQL_SPLIT_STMTS = ''';(?=(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$)'''

    GOOGLE_SERVICE_BASE64_FILE_CONTENT = os.environ['GOOGLE_SERVICE_BASE64_FILE_CONTENT']
    DATE_FORMAT = '%Y-%m-%d'

    REJECT_MESSAGE_TO_MANAGER = ':x:Leave Request for {requester_name}<@{requester_user_id}>  (From {start_date} ' \
                                'To {end_date}) has been rejected by {changed_by_name} <@{changed_by_user_id}> .. ' \
                                'Leave Id: {leave_id}'
    REJECT_MESSAGE_TO_REQUESTER = ':x:Your leave request (From {start_date} To {end_date}) has been rejected ' \
                                  'by {changed_by_name} <@{changed_by_user_id}> :cry: . Leave Id: {leave_id}'
    APPROVE_MESSAGE_TO_MANAGER = ':tada:Leave Request for {requester_name}<@{requester_user_id}>  (From {start_date} ' \
                                 'To {end_date}) has been approved by {changed_by_name} <@{changed_by_user_id}> .. ' \
                                 'Leave Id: {leave_id}'
    APPROVE_MESSAGE_TO_REQUESTER = ':tada:Your leave request (From {start_date} to {end_date}) has been approved ' \
                                   'by {changed_by_name} <@{changed_by_user_id}> :smiley: . Leave Id: {leave_id}'
    CANCEL_MESSAGE_TO_REQUESTER = ':x:Your leave Request (From {start_date} To {end_date}) ' \
                                  'has been canceled by {changed_by_name} <@{changed_by_user_id}> ' \
                                  '. Leave Id: {leave_id}'
    CANCEL_MESSAGE_TO_MANAGER = ':x:Leave Request for {requester_name}<@{requester_user_id}> ' \
                                '(From {start_date} To {end_date}) ' \
                                'has been canceled by {changed_by_name} <@{changed_by_user_id}> . Leave Id: {leave_id}'

    BLOCK_TEMPLATE_PATH = './application/handlers/bot/block_templates'
    ACK_EMOJI = 'white_check_mark'

    LEAVE_TYPE_SHEET = os.environ['LEAVE_TYPE_SHEET']
    LEAVE_REGISTER_SHEET = os.environ['LEAVE_REGISTER_SHEET']
    TEAM_SHEET = os.environ['TEAM_SHEET']
    TEAM_MEMBER_SHEET = os.environ['TEAM_MEMBER_SHEET']
    MUST_READ_SHEET = os.environ['MUST_READ_SHEET']

    HOLIDAYS_SHEET = os.environ['HOLIDAYS_SHEET']
    WEEKDAYS_SHEET = os.environ['WEEKDAYS_SHEET']
    HOLIDAY_GROUPS_SHEET = os.environ['HOLIDAY_GROUPS_SHEET']
    DEFAULT_HOLIDAY_GROUP_ID = '5b150047-ff50-438f-ad81-8dabks31edc3'
