from __future__ import annotations

import os


class Constant:
    WAIT_DEFAULT = 30
    SCHEDULER_OOO_TODAY = 'SCHEDULER_OOO_TODAY'
    SCHEDULER_WARM_UP_LAMBDA = 'SCHEDULER_WARM_UP_LAMBDA'
    EMOJI_MAPPING = {
        'Quarter PTO': ':palm_tree:',
        'PTO': ':palm_tree:',
        'UTO': ':money_with_wings:',
        'Sick': ':thermometer:',
        'Approved': ':heavy_check_mark:',
        'Rejected': ':X:',
        'Wait for Approval': ':eye:',

    }

    LEAVE_REQUEST_STATUS_REJECTED = 'Rejected'
    LEAVE_REQUEST_STATUS_APPROVED = 'Approved'
    LEAVE_REQUEST_STATUS_WAIT = 'Wait for Approval'
    LEAVE_REQUEST_STATUS_CANCELED = 'Canceled'

    LEAVE_REQUEST_ACTION_REJECT = 'Reject'
    LEAVE_REQUEST_ACTION_APPROVE = 'Approve'
    LEAVE_REQUEST_ACTION_CANCEL = 'Cancel'

    LEAVE_DECISION_TO_STATUS = {
        LEAVE_REQUEST_ACTION_REJECT: LEAVE_REQUEST_STATUS_REJECTED,
        LEAVE_REQUEST_ACTION_APPROVE: LEAVE_REQUEST_STATUS_APPROVED,
        LEAVE_REQUEST_ACTION_CANCEL: LEAVE_REQUEST_STATUS_CANCELED,
    }
    RE_SQL_SPLIT_STMTS = ''';(?=(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$)'''

    LEAVE_REGISTER_SHEET = os.environ['LEAVE_REGISTER_SHEET']
    TEAM_SHEET = os.environ['TEAM_SHEET']
    TEAM_MEMBER_SHEET = os.environ['TEAM_MEMBER_SHEET']
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
