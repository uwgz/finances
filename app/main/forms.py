from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from ..models import User


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(1, 120), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Log In")


class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(1, 120), Email()])
    username = StringField("Username", validators=[DataRequired(), Length(1, 64)])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            EqualTo("password2", message="Passwords must match"),
        ],
    )
    password2 = PasswordField("Confirm password", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered.")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already in use.")
