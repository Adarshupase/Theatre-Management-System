from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
import enum


class StatusEnum(enum.Enum):
    active="active"
    cancelled="cancelled"
    expired="expired"

# User model
class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    is_admin: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)

    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author')

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

# Post model
class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    author: so.Mapped[User] = so.relationship(back_populates='posts')

    def __repr__(self):
        return '<Post {}>'.format(self.body)

# Theatre model
class Theatre(db.Model):
    __tablename__ = 'theatre'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64))
    location: so.Mapped[str] = so.mapped_column(sa.String(64))
    screens: so.WriteOnlyMapped['Screen'] = so.relationship('Screen', back_populates='theatre')

# Screen model
class Screen(db.Model):
    __tablename__ = 'screen'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    screen_number: so.Mapped[int] = so.mapped_column()
    seating_capacity: so.Mapped[int] = so.mapped_column()
    theatre_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('theatre.id'))

    theatre: so.Mapped[Theatre] = so.relationship('Theatre', back_populates='screens')
    shows: so.WriteOnlyMapped['Shows'] = so.relationship('Shows', back_populates='screen')

# Movie model
class Movie(db.Model):
    __tablename__ = 'movie'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(128))
    duration: so.Mapped[int] = so.mapped_column()  # Duration in minutes
    genre: so.Mapped[str] = so.mapped_column(sa.String(64))
    language: so.Mapped[str] = so.mapped_column(sa.String(32))
    rating: so.Mapped[float] = so.mapped_column()

    shows: so.WriteOnlyMapped['Shows'] = so.relationship('Shows', back_populates='movie')

# Shows model

class Shows(db.Model):
    __tablename__ = 'shows'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    screen_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('screen.id'))
    movie_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('movie.id'))
    show_time: so.Mapped[datetime] = so.mapped_column()
    date: so.Mapped[datetime] = so.mapped_column()
    price: so.Mapped[float] = so.mapped_column()
    status: so.Mapped[StatusEnum] = so.mapped_column(sa.Enum(StatusEnum), default=StatusEnum.active)
    screen: so.Mapped[Screen] = so.relationship('Screen', back_populates='shows')
    movie: so.Mapped[Movie] = so.relationship('Movie', back_populates='shows')
    bookings: so.WriteOnlyMapped['Booking'] = so.relationship('Booking', back_populates='show')

# Customer model
class Customer(db.Model):
    __tablename__ = 'customer'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64))
    email: so.Mapped[str] = so.mapped_column(sa.String(120), unique=True)
    phone_number: so.Mapped[str] = so.mapped_column(sa.String(15))

    bookings: so.WriteOnlyMapped['Booking'] = so.relationship('Booking', back_populates='customer')

# Booking model
class Booking(db.Model):
    __tablename__ = 'booking'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    customer_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('customer.id'))
    show_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('shows.id'))
    booking_date: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    status:so.Mapped[StatusEnum] = so.mapped_column(sa.Enum(StatusEnum),default=StatusEnum.active)

    customer: so.Mapped[Customer] = so.relationship('Customer', back_populates='bookings')
    show: so.Mapped[Shows] = so.relationship('Shows', back_populates='bookings')
    payments: so.WriteOnlyMapped['Payment'] = so.relationship('Payment', back_populates='booking')

# Payment model
class Payment(db.Model):
    __tablename__ = 'payment'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    booking_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('booking.id'))
    payment_method: so.Mapped[str] = so.mapped_column(sa.String(20))  # e.g., 'credit_card', 'cash'
    amount: so.Mapped[float] = so.mapped_column()

    booking: so.Mapped[Booking] = so.relationship('Booking', back_populates='payments')
