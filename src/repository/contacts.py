"""Repository functions for contact management."""

from datetime import date, timedelta

from sqlalchemy import and_, extract, or_, select
from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate


class ContactRepository:
    """Data access layer for contacts."""

    def __init__(self, db: Session):
        """Store the database session for repository operations."""

        self.db = db

    def create_contact(self, body: ContactCreate, owner: User) -> Contact:
        """Create a contact bound to the authenticated owner."""

        contact = Contact(**body.model_dump(), owner_id=owner.id)
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def get_contacts(self, owner: User, first_name: str | None = None, last_name: str | None = None, email: str | None = None) -> list[Contact]:
        """Return owner contacts filtered by optional query parameters."""

        stmt = select(Contact).where(Contact.owner_id == owner.id)
        if first_name:
            stmt = stmt.where(Contact.first_name.ilike(f'%{first_name}%'))
        if last_name:
            stmt = stmt.where(Contact.last_name.ilike(f'%{last_name}%'))
        if email:
            stmt = stmt.where(Contact.email.ilike(f'%{email}%'))
        return list(self.db.scalars(stmt).all())

    def get_contact(self, contact_id: int, owner: User) -> Contact | None:
        """Return one owner contact by id."""

        return self.db.scalar(select(Contact).where(and_(Contact.id == contact_id, Contact.owner_id == owner.id)))

    def update_contact(self, contact: Contact, body: ContactUpdate) -> Contact:
        """Apply partial updates to a contact."""

        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(contact, key, value)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def delete_contact(self, contact: Contact) -> None:
        """Delete a contact instance."""

        self.db.delete(contact)
        self.db.commit()

    def get_upcoming_birthdays(self, owner: User, days: int = 7) -> list[Contact]:
        """Return contacts whose birthdays fall within the next given number of days."""

        today = date.today()
        upcoming = {(today + timedelta(days=offset)).strftime('%m-%d') for offset in range(days + 1)}
        contacts = list(self.db.scalars(select(Contact).where(Contact.owner_id == owner.id)).all())
        return [c for c in contacts if c.birthday.strftime('%m-%d') in upcoming]
