from __future__ import annotations

import uuid

from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
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
    updated_by = Column(String)
    message_ts = Column(String)

    def __repr__(self):
        return f'LeaveRegistry(id={self.id!r}, username={self.username!r}, user_id={self.user_id!r})'


class Team(Base):
    __tablename__ = Constant.TEAM_SHEET
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    announcement_channel_id = Column(String)
    holiday_group_id = Column(String)
    # Delete orphan doesn't work as a bug of shillelagh https://github.com/betodealmeida/shillelagh/issues/206
    members = relationship(
        'TeamMember',
        backref='team',
        cascade='all,delete, delete-orphan',
        passive_deletes=True,
    )

    def __repr__(self):
        return f'Team(id={self.id!r}, name={self.name!r}, announcement_channel_id={self.announcement_channel_id!r},' \
               f' holiday_group_id={self.holiday_group_id!r})'


class TeamMember(Base):
    __tablename__ = Constant.TEAM_MEMBER_SHEET
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String)
    team_id = Column(
        String, ForeignKey(f'{Team.__tablename__}.id', ondelete='cascade'), nullable=False,
        primary_key=True,
    )
    # We can't use boolean here as a bug of shillelagh https://github.com/betodealmeida/shillelagh/issues/207
    is_manager = Column(Integer)

    # team = relationship("Team", backref=backref("members", cascade="all, delete-orphan"))

    def __repr__(self):
        return f'TeamMember(id={self.id!r}, user_id={self.user_id!r}, ' \
               f'team_id={self.team_id!r},is_manager={self.is_manager!r})'


class LeaveType(Base):
    __tablename__ = Constant.LEAVE_TYPE_SHEET
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String)
    display_name = Column(String)
    description = Column(String)
    icon = Column(Date)
    day = Column(Float)
    is_default = Column(Integer)

    def __repr__(self):
        return f'LeaveType(id={self.id!r}, name={self.name!r},code={self.code!r} ' \
               f'description={self.description!r},icon={self.icon!r},day={self.day!r})'


class MustReadMessage(Base):
    __tablename__ = Constant.MUST_READ_SHEET
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_ts = Column(String)
    status = Column(String)
    author_user_id = Column(String)
    short_content = Column(String)
    channel = Column(String)
    permalink = Column(String)

    def __repr__(self):
        return f'MustReadMessage(id={self.id!r}, message_ts={self.message_ts!r},status={self.status!r}'


class Weekdays(Base):
    __tablename__ = Constant.WEEKDAYS_SHEET
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True))
    is_mon = Column(Integer)
    is_tue = Column(Integer)
    is_wed = Column(Integer)
    is_thu = Column(Integer)
    is_fri = Column(Integer)
    is_sat = Column(Integer)
    is_sun = Column(Integer)

    def __repr__(self):
        return f'Weekdays(id={self.id!r}'


class Holidays(Base):
    __tablename__ = Constant.HOLIDAYS_SHEET
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    holiday_group_id = Column(String)
    date = Column(Integer)
    description = Column(Integer)
    is_custom = Column(Integer)
    is_enabled = Column(Integer)

    def __repr__(self):
        return f'Holidays(id={self.id!r}'


class HolidayGroups(Base):
    __tablename__ = Constant.HOLIDAY_GROUPS_SHEET
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    country_based_on = Column(String)
    description = Column(Integer)

    def __repr__(self):
        return f'Holidays(id={self.id!r}'
