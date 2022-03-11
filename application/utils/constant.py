from __future__ import annotations

import os


class Constant:
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
    LEAVE_REQUEST_ACTION_REJECT = 'Reject'
    LEAVE_REQUEST_ACTION_APPROVE = 'Approve'
    LEAVE_DECISION_TO_STATUS = {
        LEAVE_REQUEST_ACTION_REJECT: LEAVE_REQUEST_STATUS_REJECTED,
        LEAVE_REQUEST_ACTION_APPROVE: LEAVE_REQUEST_STATUS_APPROVED,
    }
    RE_SQL_SPLIT_STMTS = ''';(?=(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$)'''

    LEAVE_REGISTER_SHEET = os.environ['LEAVE_REGISTER_SHEET']
    TEAM_SHEET = os.environ['TEAM_SHEET']
    TEAM_MEMBER_SHEET = os.environ['TEAM_MEMBER_SHEET']
    GOOGLE_SERVICE_BASE64_FILE_CONTENT = os.environ['GOOGLE_SERVICE_BASE64_FILE_CONTENT']
