import pytest
from sqlalchemy.sql import text

from app import create_app
from utils.db import db
from utils.redis import flush_redis_db
from utils.rate_limits import RateLimitExceeded, rate_limit_error_handler


@pytest.fixture(scope="session")
def mock_app(request):
    """
    Returns session-wide application.
    """
    app = create_app("testing")
    # register the rate limit exceeded error handler for tests
    app.errorhandler(RateLimitExceeded)(rate_limit_error_handler)
    return app


@pytest.fixture(scope="session")
def init_db(mock_app, request):
    """
    Session-wide database initialization.
    This fixture ensures that the database schema is created before any tests run.
    """
    with mock_app.app_context():
        db.drop_all()
        db.create_all()


@pytest.fixture(scope='function')
def api_client(mock_app):
    """
    Function-scoped fixture for providing a test client.
    This fixture provides a Flask test client for making API requests.
    """
    with mock_app.test_client() as client:
        yield client


@pytest.fixture(scope="function", autouse=True)
def db_session(mock_app, init_db, request):
    """
    Function-scoped session fixture.
    This fixture provides a database session for each test function, ensuring that
    any changes made during a test are rolled back and the psql and redis databases
    are cleaned up.

    - Opens a new database session for each test.
    - Rolls back any commits made during the test.
    - Truncates all tables to ensure a clean state.
    - Closes the session after the test is done.
    - Flushes the Redis test database.
    """
    with mock_app.app_context():
        local_session = db.session(expire_on_commit=False)
        yield local_session

        # Roll back any commits made during the test
        local_session.rollback()

        # Truncate all tables to clean up the database
        local_session.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))
        for table in db.metadata.sorted_tables:
            local_session.execute(text(f'TRUNCATE TABLE {table.name};'))
            local_session.commit()
        local_session.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))

        # Close the session
        local_session.close()

        # Flush redis test database
        flush_redis_db()
