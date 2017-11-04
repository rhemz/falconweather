from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


class SessionManager(object):

    _engine = None
    _db_config = None
    _pool_args = None

    def __init__(self, db_config, pool_args=None, **kwargs):
        """
        Parent initializer.  Takes SQLAlchemy database config parameters.
        :param db_config: Database config, consisting of known SQLAlchemy
        config key/values
        :type db_config: dict
        :return: self
        """
        self._db_config = db_config
        self._pool_args = pool_args

        engine_string = self.build_db_engine_string(
            user=self._db_config['user'],
            password=self._db_config['password'],
            host=self._db_config['host'],
            port=self._db_config['port'],
            db=self._db_config['db']
        )
        self._engine = create_engine(engine_string, **self._pool_args)

    @staticmethod
    def build_db_engine_string(user, password, host, port=3306, engine='mysql',
                               db=None, charset=None):
        """
        Create a SQLAlchemy-compliant engine string from provided parameters.
        :param user: The username to authenticate with
        :type user: str
        :param password: The password
        :type password: str
        :param host: Hostname of the DB instance
        :type host: str
        :param port: Port of the DB instance
        :type port: int
        :param engine: Which SQLAlchemy DB Engine to use (default mysql)
        :type engine: str
        :param db: DB to use when sessions are opened (optional)
        :type db: str
        :param charset: Force the characterset (override SQLA's autodiscover)
        :type charset: str
        :return: str
        """
        conn_string = '{engine}://{user}:{password}@{host}:{port}'.format(
            engine=engine,
            user=user,
            password=password,
            host=host,
            port=port
        )

        if db is not None:
            conn_string += '/{db}'.format(db=db)

        if charset is not None:
            if db is None:
                # empty db name, parameters cannot directly follow port
                conn_string += '/'

            # append charset param
            conn_string += '?charset={}'.format(charset)

        return conn_string

    @contextmanager
    def get_session(self, autoflush=True, autocommit=False):
        """
        Check out a SQLAlchemy DB session.
        :param autoflush: Check out an auto-flushing session. (default=True)
        :type autoflush: bool
        :param autocommit: Check out an auto-committing session. (default=False)
        :type autocommit: bool
        :return: sqlalchemy.orm.scoping.scoped_session
        """
        session = scoped_session(
            sessionmaker(
                autoflush=autoflush,
                autocommit=autocommit,
                bind=self._engine
            ))

        try:
            yield session
        finally:
            session.remove()  # always return the session to the pool
