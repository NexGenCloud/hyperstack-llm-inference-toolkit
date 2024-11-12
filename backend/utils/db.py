"""Database utility functions."""

import functools

from contextlib import contextmanager

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = db.session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def with_session(func):
    """Decorator to provide a session to a caller function."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with session_scope() as session:
            return func(session, *args, **kwargs)

    return wrapper
