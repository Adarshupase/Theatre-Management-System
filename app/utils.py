#contains the sql triggers and functions for handling the database
from sqlalchemy import text,func 
from app import db
from app.models import Shows,Customer,Payment,Booking,StatusEnum,Movie
from datetime import datetime,timedelta,timezone
from sqlalchemy.orm import joinedload
def get_total_booked_seats(show_id):
    total_booked = db.session.execute(
        text("""
            SELECT COALESCE(SUM(p.amount), 0) / (SELECT price FROM shows WHERE id = :show_id) AS total_booked_seats
            FROM booking b
            JOIN payment p ON b.id = p.booking_id
            WHERE b.show_id = :show_id
        """),
        {"show_id": show_id}
    ).scalar() or 0  # Return 0 if no bookings exist

    return total_booked

def check_show_conflict(screen_id, show_time,duration, exclude_show_id=None):
    conflict_exists = db.session.execute(
    text("""
        SELECT COUNT(*) > 0
FROM SHOWS 
WHERE screen_id = :screen_id
    AND (:exclude_show_id IS NULL OR id != :exclude_show_id)
    AND (
        (show_time < :show_time AND DATE_ADD(show_time, INTERVAL :duration MINUTE) > :show_time)
    OR 
    (show_time >= :show_time AND show_time < DATE_ADD(:show_time, INTERVAL :duration MINUTE))
)

         """),{
              "screen_id": screen_id,
            "show_time": show_time,
            "duration": duration,
            "exclude_show_id": exclude_show_id
         }
    ).scalar()

    return conflict_exists

def update_show(show_id,new_show_time):
    """
    Deletes all entries in the database that are related to the specified show.
    This includes bookings and payments associated with the show.
    """
    # Delete payments linked to bookings for the show
    show = Shows.query.get(show_id)
    if show:
        
        show.show_time= new_show_time

    
        db.session.commit()
        # payments_to_delete = db.session.query(Payment).join(Booking).filter(Booking.show_id == show_id).all()
        # for payment in payments_to_delete:
        #     db.session.delete(payment)
    
    # Delete bookings associated with the show
        # bookings_to_delete = Booking.query.filter_by(show_id=show_id).all()
        # for booking in bookings_to_delete:
        #     customer = booking.customer
        #     db.session.delete(booking)
        #     other_bookings = Booking.query.filter_by(customer_id=customer.id).all()
        #     if len(other_bookings) == 1:  # This means the customer has no other bookings
        #         db.session.delete(customer)
        # db.session.commit()
        
    

    # Finally, delete the show entry itself (optional, depending on use case)
    


def refreshBookings():
    now  = datetime.now(timezone.utc)

    expired_bookings = (
        db.session.query(Booking)
        .join(Shows)
        .filter(Shows.show_time < now)
        .options(joinedload(Booking.show))  # Optional: load associated show if needed
        .all()
    )
    # Update status of all expired bookings
    for booking in expired_bookings:
        booking.status = StatusEnum.expired

    # Commit the changes to the database
    db.session.commit()
def check_user_exists(username,email):
    result_username = db.session.execute(text('''SELECT 1 FROM user WHERE username = :username'''), {"username": username}).fetchone()
    result_email = db.session.execute(text('''SELECT 1 FROM user WHERE email = :email'''), {"email": email}).fetchone()
    if result_username:
        return "username"  # Username is taken
    elif result_email:
        return "email"  # Email is taken
    return None  #Both are available