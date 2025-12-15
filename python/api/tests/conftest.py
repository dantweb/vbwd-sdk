import pytest
import os

# Set test environment BEFORE importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['TESTING'] = 'true'

from src import create_app, db


@pytest.fixture(scope='function')
def app():
    """Create application for testing."""
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Database session for tests."""
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def sample_submission_data():
    """Sample valid submission data."""
    return {
        'email': 'test@example.com',
        'consent': True,
        'images': [
            {'type': 'image/jpeg', 'size': 1000, 'data': 'base64data...'}
        ],
        'comments': 'Test submission'
    }
