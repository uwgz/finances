from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms import StringField, SelectField, FloatField, DateField
from ..models import User


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(1, 120), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Log In")


class RegistrationForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(1, 64)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(1, 64)])
    email = StringField("Email", validators=[DataRequired(), Length(1, 120), Email()])
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
        

class TransactionForm(FlaskForm):
    transaction_type = SelectField('Transaction Type', choices=[('income', 'Income'), ('expense', 'Expense'), ('assets', 'Assets')], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    frequency = SelectField('Frequency', 
                          choices=[
                              ('one-time', 'One-time'),
                              ('daily', 'Daily'),
                              ('weekly', 'Weekly'),
                              ('monthly', 'Monthly'),
                              ('yearly', 'Yearly')
                          ], 
                          validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])