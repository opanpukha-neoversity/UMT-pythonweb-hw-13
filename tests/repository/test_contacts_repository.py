from datetime import date, timedelta


def birthday_with_offset(offset_days: int) -> date:
    target = date.today() + timedelta(days=offset_days)
    return date(2000, target.month, target.day)

from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate


def test_create_filter_update_delete_contact(session, user):
    repo = ContactRepository(session)
    contact = repo.create_contact(
        ContactCreate(
            first_name='Ivan',
            last_name='Petrenko',
            email='ivan@example.com',
            phone_number='+380501112233',
            birthday=date.today(),
            additional_data='friend',
        ),
        user,
    )

    results = repo.get_contacts(user, first_name='Iv')
    assert len(results) == 1
    assert results[0].id == contact.id

    updated = repo.update_contact(contact, ContactUpdate(last_name='Shevchenko'))
    assert updated.last_name == 'Shevchenko'

    assert repo.get_contact(contact.id, user) is not None
    repo.delete_contact(contact)
    assert repo.get_contact(contact.id, user) is None


def test_get_upcoming_birthdays(session, user):
    repo = ContactRepository(session)
    repo.create_contact(
        ContactCreate(
            first_name='Soon',
            last_name='Birthday',
            email='soon@example.com',
            phone_number='+380501112233',
            birthday=birthday_with_offset(2),
            additional_data=None,
        ),
        user,
    )
    repo.create_contact(
        ContactCreate(
            first_name='Later',
            last_name='Birthday',
            email='later@example.com',
            phone_number='+380501112234',
            birthday=birthday_with_offset(20),
            additional_data=None,
        ),
        user,
    )

    upcoming = repo.get_upcoming_birthdays(user)
    assert len(upcoming) == 1
    assert upcoming[0].email == 'soon@example.com'
