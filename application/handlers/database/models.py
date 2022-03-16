from __future__ import annotations

import uuid

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID

from application.handlers.database.base_db_handler import Base
from application.utils.constant import Constant


class LeaveRegistry(Base):
    __tablename__ = Constant.LEAVE_REGISTER_SHEET
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String())
    user_id = Column(String())
    start_date = Column(String())
    end_date = Column(String())
    leave_type = Column(String())
    reason = Column(String())
    created_time = Column(String())
    status = Column(String())
    approver = Column(String())

    def __repr__(self):
        return f"LeaveRegistry(id={self.id!r}, username={self.username!r}, user_id={self.user_id!r})"


class Team(Base):
    __tablename__ = Constant.TEAM_SHEET
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String())
    announcement_channel_id = (String())
    holiday_country = Column(String())

    def __repr__(self):
        return f"Team(id={self.id!r}, name={self.name!r}, announcement_channel_id={self.announcement_channel_id!r}," \
               f" holiday_country={self.holiday_country!r})"


class TeamMember(Base):
    __tablename__ = Constant.TEAM_MEMBER_SHEET
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String())
    team_id = (String())
    is_manager = Column(Boolean())

    def __repr__(self):
        return f"TeamMember(id={self.id!r}, user_id={self.user_id!r}, " \
               f"team_id={self.team_id!r},is_manager={self.is_manager!r})"
