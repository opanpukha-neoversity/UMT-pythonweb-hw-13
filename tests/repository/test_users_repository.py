from src.database.models import UserRole
from src.repository.users import UserRepository
from src.schemas import UserCreate


def test_create_get_confirm_and_update_password(session):
    repo = UserRepository(session)
    body = UserCreate(username='alice', email='alice@example.com', password='secret123')

    user = repo.create_user(body, 'hashed', UserRole.ADMIN)

    assert user.id is not None
    assert repo.get_by_email('alice@example.com').email == 'alice@example.com'
    assert repo.get_by_id(user.id).role == UserRole.ADMIN

    repo.confirm_email(user)
    assert repo.get_by_id(user.id).confirmed is True

    repo.update_password(user, 'new-hash')
    assert repo.get_by_id(user.id).hashed_password == 'new-hash'
