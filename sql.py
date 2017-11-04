from falconweather.models import WindMeasurement

from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import mysql


tables = (
    WindMeasurement,
)


if __name__ == '__main__':
    for model in tables:
        print('{};\n\n\n'.format(
            CreateTable(model.__table__).compile(dialect=mysql.dialect()))
        )
