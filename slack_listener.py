from __future__ import annotations

import os

from application.handlers.bot.home_tab import HomeTab
from application.handlers.bot.leave_lookup import LeaveLookup
from application.handlers.bot.leave_register import LeaveRegister
from application.handlers.bot.team_management import TeamManagement


class SlackListener:
    def __init__(self, bolt_app, client):
        leave_register = LeaveRegister(
            bolt_app, client,
            approval_channel=os.getenv('MANAGER_LEAVE_APPROVAL_CHANNEL'),
        )
        self.leave_lookup = LeaveLookup(bolt_app, client)
        self.team_management = TeamManagement(bolt_app, client)
        self.home_tab = HomeTab(bolt_app, client, self.leave_lookup, leave_register, self.team_management)
