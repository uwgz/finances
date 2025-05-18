from flask import flash, redirect, render_template, url_for
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
from . import main
from .. import db
from ..models import User
from .forms import LoginForm, RegistrationForm


@main.route("/")
def index():
    return render_template("index.html", current_time=datetime.utcnow())


@main.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for("main.dashboard"))  # <- HERE
        flash("Invalid email or password.")
    return render_template("auth/login.html", form=form)


@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("main.index"))


@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for(".index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! You can now log in.")
        return redirect(url_for(".login"))
    return render_template("auth/register.html", form=form)
