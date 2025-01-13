from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField
from wtforms import StringField, PasswordField, BooleanField, SubmitField,SelectField
from wtforms.validators import DataRequired,ValidationError,Email,EqualTo
import sqlalchemy as sa
from app import db
from app.models import User,Theatre,Screen,Movie
from wtforms import TextAreaField,IntegerField,DateTimeField,DecimalField
from wtforms.validators import Length, NumberRange

class RegistrationForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired()])
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password',validators=[DataRequired(), EqualTo('password')]
    )
    submit  = SubmitField('Register')

    def validate_username(self,username):
        user = db.session.scalar(sa.select(User).where(
            User.email == self.email.data))
        if user is not None:
            raise ValidationError('Please Use different email address')
class LoginForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired()])
    password = PasswordField('Password',validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in')
class EditorProfileForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired()])
    about_me = TextAreaField('About me',validators=[Length(min=0,max=140)])
    submit = SubmitField('Submit')
class BookingForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=15)])
    num_tickets = IntegerField('Number of Tickets', validators=[DataRequired(), NumberRange(min=1, message="Must be a positive integer.")])
    payment_method = SelectField(
    'Choose a payment method', 
    choices=[
        ('1', 'UPI'),
        ('2', 'Credit-card'),
        ('3', 'BitCoin')
    ]
)

    submit = SubmitField('Book Now')
class AddShowForm(FlaskForm):
    theatre_id = SelectField('Theatre', coerce=int, validators=[DataRequired()])
    screen_id = SelectField('Screen', coerce=int, validators=[DataRequired()])
    movie_id = SelectField('Movie', coerce=int, validators=[DataRequired()])
    show_time = DateTimeLocalField('Show Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    price = DecimalField('Price', places=2, validators=[DataRequired()])
    def __init__(self,*args,**kwargs):
        super(AddShowForm,self).__init__(*args,**kwargs)
        self.theatre_id.choices = [(theatre.id, theatre.name) for theatre in Theatre.query.all()]
        self.screen_id.choices = [(screen.id, f'Screen {screen.screen_number}') for screen in Screen.query.all()]
        self.movie_id.choices = [(movie.id, movie.title) for movie in Movie.query.all()]
class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    duration = IntegerField('Duration (minutes)', validators=[DataRequired()])
    
    genre = SelectField('Genre', choices=[
        ('Action', 'Action'), 
        ('Comedy', 'Comedy'), 
        ('Drama', 'Drama'), 
        ('Horror', 'Horror'),
        ('Romance', 'Romance')
    ], validators=[DataRequired()])
    
    language = SelectField('Language', choices=[
        ('English', 'English'), 
        ('Hindi', 'Hindi'), 
        ('Spanish', 'Spanish'),
        ('French', 'French'),
        ('Mandarin', 'Mandarin')
    ], validators=[DataRequired()])
    
    # Rating field with a range between 0 and 10 and limited to one decimal place
    rating = DecimalField('Rating', places=1, validators=[
        DataRequired(),
        NumberRange(min=0, max=10, message="Rating must be between 0 and 10.")
    ])
    
    submit = SubmitField('Add Movie')
class EditShowForm(FlaskForm):
    movie_id = SelectField('Movie',coerce=int,validators=[DataRequired()])
    show_time = DateTimeLocalField('Show Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    price = DecimalField('Price', places=2, validators=[DataRequired()])
    submit = SubmitField('Update Show')

    def __init__(self, *args, **kwargs):
        super(EditShowForm, self).__init__(*args, **kwargs)
        self.movie_id.choices = [(movie.id, movie.title) for movie in Movie.query.all()]