import os
from sqlalchemy import Column, Boolean, ForeignKey, Integer, Sequence, String, UniqueConstraint, Text
from sqlalchemy.orm import relationship

from ..modules import get_module
from ..settings import DATA_PATH
from .errors import GroupNotFound, SourceNotFound
from .utils import Base


def get_group(db, id):
    group = db.query(Group).get(id)
    if group is None:
        raise GroupNotFound(id)
    return group


class Group(Base):
    __tablename__ = 'group'
    __table_args__ = (
        UniqueConstraint('parent_id', 'name'),
    )

    id = Column(Integer, Sequence('group_id_seq'), primary_key=True)
    parent_id = Column(Integer, ForeignKey('group.id'))
    name = Column(String(50), nullable=False)

    parent = relationship('Group', remote_side=id, back_populates='children')
    children = relationship('Group', remote_side=parent_id, order_by='Group.name', back_populates='parent')
    sources = relationship('Source', order_by='Source.name', back_populates='group')

    def __repr__(self):
        return '<Group "%s">' % self.path_name

    @property
    def path_ids(self):
        if self.parent_id is None:
            return [self]
        return self.parent.path_ids + [self]

    @property
    def path_name(self):
        return '/'.join(group.name for group in self.path_ids)


def get_source(db, module_id, id):
    source = db.query(Source).get((module_id, id))
    if source is None:
        raise SourceNotFound('%s:%s' % (module_id, id))
    return source


class Source(Base):
    __tablename__ = 'source'

    module_id = Column(String(50), primary_key=True)
    id = Column(String(50), primary_key=True)
    group_id = Column(Integer, ForeignKey('group.id'))
    url = Column(String(256), nullable=False)
    options = Column(Text, nullable=False, default='')
    name = Column(String(50), nullable=False)
    thumbnail_url = Column(String(256), nullable=False, default='')
    web_url = Column(String(256), nullable=False, default='')
    auto_download_media = Column(Boolean, nullable=False, default=False)

    group = relationship('Group', back_populates='sources')

    def __repr__(self):
        return '<Source "%s:%s">' % (self.module_id, self.id)

    @property
    def module(self):
        return get_module(self.module_id)

    @property
    def group_path_name(self):
        if self.group:
            return self.group.path_name
        return ''

    @property
    def thumbnail_path(self):
        return os.path.join(DATA_PATH, 'thumbnail', 'source', self.module_id, self.id)
