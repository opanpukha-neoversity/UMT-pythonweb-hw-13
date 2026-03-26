"""Contact CRUD routes limited to the authenticated owner."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.database.models import User
from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactResponse, ContactUpdate
from src.services.auth import get_current_user
from src.database.db import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix='/api/contacts', tags=['contacts'])


@router.post('/', response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(body: ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new contact for the authenticated user."""

    return ContactRepository(db).create_contact(body, current_user)


@router.get('/', response_model=list[ContactResponse])
def get_contacts(
    first_name: str | None = Query(default=None),
    last_name: str | None = Query(default=None),
    email: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List current-user contacts with optional filtering."""

    return ContactRepository(db).get_contacts(current_user, first_name=first_name, last_name=last_name, email=email)


@router.get('/upcoming-birthdays', response_model=list[ContactResponse])
def get_upcoming_birthdays(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return current-user contacts with birthdays in the next seven days."""

    return ContactRepository(db).get_upcoming_birthdays(current_user)


@router.get('/{contact_id}', response_model=ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return a single owned contact by id."""

    contact = ContactRepository(db).get_contact(contact_id, current_user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')
    return contact


@router.put('/{contact_id}', response_model=ContactResponse)
def update_contact(contact_id: int, body: ContactUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update an owned contact."""

    repo = ContactRepository(db)
    contact = repo.get_contact(contact_id, current_user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')
    return repo.update_contact(contact, body)


@router.delete('/{contact_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete an owned contact."""

    repo = ContactRepository(db)
    contact = repo.get_contact(contact_id, current_user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')
    repo.delete_contact(contact)
