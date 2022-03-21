from __future__ import annotations

import uuid

from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from application.handlers.database.base_db_handler import Base
from application.utils.constant import Constant


class LeaveRegistry(Base):
    __tablename__ = Constant.LEAVE_REGISTER_SHEET
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String)
    user_id = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    leave_type = Column(String)
    reason = Column(String)
    created_time = Column(Date)
    status = Column(String)
    approver = Column(String)
    message_ts = Column(String)

    def __repr__(self):
        return f'LeaveRegistry(id={self.id!r}, username={self.username!r}, user_id={self.user_id!r})'


class Team(Base):
    __tablename__ = Constant.TEAM_SHEET
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    announcement_channel_id = Column(String)
    holiday_country = Column(String)
    members = relationship(
        'TeamMember',
        backref='team',
        cascade='all,delete, delete-orphan',
        passive_deletes=True,
    )

    def __repr__(self):
        return f'Team(id={self.id!r}, name={self.name!r}, announcement_channel_id={self.announcement_channel_id!r},' \
               f' holiday_country={self.holiday_country!r})'


class TeamMember(Base):
    __tablename__ = Constant.TEAM_MEMBER_SHEET
    user_id = Column(String, primary_key=True)
    team_id = Column(
        String, ForeignKey(f'{Team.__tablename__}.id', ondelete='cascade'), nullable=False,
        primary_key=True,
    )
    is_manager = Column(String)

    # team = relationship("Team", backref=backref("members", cascade="all, delete-orphan"))

    def __repr__(self):
        return f'TeamMember(id={self.id!r}, user_id={self.user_id!r}, ' \
               f'team_id={self.team_id!r},is_manager={self.is_manager!r})'
