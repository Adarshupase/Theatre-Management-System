
from app import app
import json
from sqlalchemy import text,desc
from flask import jsonify
from app.forms import RegistrationForm,EditorProfileForm,BookingForm,LoginForm,AddShowForm,AddMovieForm,EditShowForm
from flask import request 
from urllib.parse import urlsplit
from flask_login import logout_user 
from flask import render_template, flash, redirect, url_for
from app.utils import get_total_booked_seats,check_show_conflict,update_show,refreshBookings,check_user_exists
from flask_login import current_user,login_user,login_required
import sqlalchemy as sa
from app import db
from datetime import datetime,timezone
from app.models import User,Customer,Booking,Shows,Payment,Screen,Theatre,StatusEnum
from app.models import Movie

TMDB_API_KEY = ''
@app.route('/')
@app.route('/index')
@login_required
def index():
    
    
    return render_template('index.html', title='Home')

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user_exists = check_user_exists(form.username.data,form.email.data)
        if user_exists =="username":
             flash("This username is already taken. Please choose a different one.", "danger")
             return redirect(url_for('register'))
        if user_exists == "email":
            flash("This email is already taken. Please choose a different one.", "danger")
            return redirect(url_for('register'))
        user = User(username=form.username.data,email = form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congragulation, you are now registered')
        return redirect(url_for('login'))
    return render_template('register.html',title='Register',form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    posts = [
        {'author':user,'body':'Test post #1'},
        {'author':user,'body':'Test post #2'},
        {'author':user,'body':'Test post #2'}
    ]
    return render_template('user.html',user=user,posts=posts)



@app.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('invalid username or password')
            return redirect(url_for('login'))
        
        login_user(user,remember=form.remember_me.data)

        # if user.is_admin:
        #     return render_template('adminpage.html',user=current_user)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')

        return redirect(next_page)
    return render_template('login.html',title='Sign In',form=form)
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
@app.route('/edit_profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditorProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved")
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET' :
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title = 'Edit Profile',form=form)
@app.route('/shows',methods=['GET'])
@login_required
def movies():
    genre_filter = request.args.get('genre')


    current_time = datetime.now(timezone.utc)
    with open('/home/adarshupase/project/flaks/app/templates/movies.json','r') as file:
        movie_data = json.load(file)
    movie_posters =  {movie['title']: movie['posterUrl'] for movie in movie_data['movies']}
    query = Shows.query.filter(Shows.show_time > current_time,
                               Shows.status == StatusEnum.active
                               )
    if genre_filter:
        all_shows = Shows.query.filter(
            Shows.movie.has(Movie.genre == genre_filter),
            Shows.show_time > current_time  # Filter for future shows
        ).all() 
   
    else:
        all_shows = Shows.query.filter(Shows.show_time > current_time,Shows.status == StatusEnum.active).all()
    genres = db.session.query(Movie.genre).distinct().all()
    genres = [g[0] for g in genres]
    return render_template('shows.html',shows=all_shows,genres=genres,movie_posters=movie_posters)
@app.route('/book_movie/<int:show_id>', methods=['GET', 'POST'])
@login_required
def book_movie(show_id):
    show = Shows.query.get_or_404(show_id)  # Fetch the movie by ID
    form = BookingForm()  # Create an instance of the booking form
    
    if form.validate_on_submit():  # Check if the form is submitted and valid
        
        no_of_tickets = form.num_tickets.data
        total_booked = get_total_booked_seats(show_id)
        seating_capacity = show.screen.seating_capacity
        if total_booked + no_of_tickets > seating_capacity and no_of_tickets<0:
            return redirect(url_for('movies'))
        customer = Customer(
            name=form.name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
        )
        db.session.add(customer)  # Add the customer to the session
        db.session.commit()  # Commit the session to save the customer
        booking = Booking(
            customer_id = customer.id,
            show_id = show_id,
            booking_date = datetime.now()
        )
        db.session.add(booking)
        db.session.commit()
        payment = Payment(
            booking_id = booking.id,
            payment_method=form.payment_method.data,
            amount = show.price * no_of_tickets

        )
        db.session.add(payment)
        db.session.commit()

          # Flash a success message
        # return redirect(url_for('movies'))  # Redirect to the movies page
        return render_template('movie_booked.html',booking=booking,payment=payment,no_of_tickets=no_of_tickets)
    # Ensure that a response is returned for GET requests or invalid form submissions
    return render_template('book_movie.html', form=form, show=show)

@app.route('/add_show', methods=['GET', 'POST'])
@login_required
def add_show():
    form = AddShowForm()
    if form.validate_on_submit():
        show_time = form.show_time.data
        movie_id = form.movie_id.data
        screen_id = form.screen_id.data
        date = show_time.date()
        # Fetch the movie duration to check conflicts
        movie = Movie.query.get(movie_id)
        if not movie:
            flash('Movie not found', 'danger')
            return redirect(url_for('add_show'))

        duration = movie.duration  # Duration in minutes

        # Check for conflicting shows
        


        if check_show_conflict(screen_id, show_time, duration):
            flash('There is a scheduling conflict with another show.', 'danger')
            return redirect(url_for('add_show'))

        # If no conflicts, add the new show
        new_show = Shows(
            screen_id=screen_id,
            movie_id=movie_id,
            show_time=show_time,
            date=show_time.date(),
            price=form.price.data
        )
        db.session.add(new_show)
        db.session.commit()
        flash('Show added successfully!', 'success')
        return redirect(url_for('add_show'))  # Redirect to the same page or any other page

    return render_template('add_show.html', form=form)

@app.route('/edit_show/<int:show_id>',methods=['GET','POST'])
@login_required
def edit_shows(show_id):
    show = Shows.query.get_or_404(show_id)
    movies = Movie.query.all()  # Ensure you get all the movies
    #theatres = Theatre.query.all()
    #screens = Screen.query.all()
    form = EditShowForm(obj=show)
    if form.validate_on_submit():
        new_show_time = form.show_time.data
        
        duration = show.movie.duration
        if check_show_conflict(show.screen_id, new_show_time, duration, exclude_show_id=show_id):
            flash('There is a scheduling conflict with another show.', 'danger')
            return redirect(url_for('edit_show', show_id=show_id))
        update_show(show_id,new_show_time)
        db.session.commit()

        flash('Show updated successfully!', 'success')
        return redirect(url_for('index'))
    show_time_str = show.show_time.strftime('%Y-%m-%dT%H:%M')
    return render_template('edit_show.html', form=form,movies=movies, show=show ,show_time_str=show_time_str)


@app.route('/cancel_show/<int:show_id>',methods=['POST'])
@login_required
def cancel_show(show_id):
    show = db.session.get(Shows,show_id)
    if not show:
        return redirect(url_for('index'))
    show.status = StatusEnum.cancelled
    affected_bookings = db.session.query(Booking).filter_by(show_id=show_id).all()
    for booking in affected_bookings:
        booking.status = StatusEnum.cancelled
    db.session.commit()
    flash("Show and associated bookings have been cancelled.", "success")
    return redirect(url_for('movies'))
@app.route('/get_screens/<int:theatre_id>')
@login_required
def get_screens(theatre_id):
    screens = Screen.query.filter_by(theatre_id=theatre_id).all()
    screen_choices = [(screen.id,f'Screen {screen.screen_number}')for screen in screens]
    return jsonify(screen_choices)



@app.route('/show_bookings')
@login_required
def show_bookings():
    refreshBookings()
    # bookings = Booking.query.all()
    bookings = (
    db.session.query(Booking, Payment)
    .join(Payment, Booking.id == Payment.booking_id)
    .order_by(desc(Booking.id))  # Join Payment on Booking ID
    .all()
    )

    return render_template('show_bookings.html',bookings=bookings)



# def get_total_booked_seats(show_id):
#     total_booked = db.session.execute(
#         text("""
#             SELECT COALESCE(SUM(p.amount), 0) / (SELECT price FROM shows WHERE id = :show_id) AS total_booked_seats
#             FROM booking b
#             JOIN payment p ON b.id = p.booking_id
#             WHERE b.show_id = :show_id
#         """),
#         {"show_id": show_id}
#     ).scalar() or 0  # Return 0 if no bookings exist

#     return total_booked
@app.route('/get_available_seats/<int:show_id>', methods=['GET'])
@login_required
def get_available_seats(show_id):
    show = Shows.query.get_or_404(show_id)

    # Count total booked seats for the show
    total_booked = get_total_booked_seats(show_id)


    available_seats = show.screen.seating_capacity - total_booked

    return jsonify({'available_seats': available_seats})

@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie = Movie(
            title=form.title.data,
            duration=form.duration.data,
            genre=form.genre.data,
            language=form.language.data,
            rating=form.rating.data
        )
        db.session.add(movie)
        db.session.commit()
        flash('Movie added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_movie.html', form=form)

