from sqlalchemy import Column, Index, text
from sqlalchemy.dialects.mysql import INTEGER, DOUBLE
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class BaseTableMixin(object):
    __table_args__ = (
        {
            'mysql_charset': 'utf8mb4',
            'mysql_engine': 'InnoDB'
        },
    )


class WindMeasurement(Base, BaseTableMixin):

    __tablename__ = 'measurement_wind'

    epoch = Column('epoch', INTEGER(11, unsigned=True), nullable=False, primary_key=True)
    mph = Column('mph', DOUBLE(unsigned=True), nullable=False, default=0.0, server_default=text('0'))

    idx_epoch_mph = Index('epoch_mph', epoch, mph)
