from flask import flash, redirect, render_template, url_for, request
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
from . import main
from .. import db
from ..models import User, Transaction
from .forms import LoginForm, RegistrationForm, TransactionForm
from sqlalchemy import func, extract, case, and_, or_
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta



@main.route("/")
def index():
    return render_template("index.html", current_time=datetime.utcnow())


@main.route("/dashboard", methods=['GET', 'POST'])
@main.route('/dashboard/feeds', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = TransactionForm()
    today = datetime.now().date()
    
    # Date calculations
    end_of_month = today + relativedelta(day=31)
    days_remaining = (end_of_month - today).days + 1
    weeks_remaining = days_remaining / 7

    if form.validate_on_submit():
        new_transaction = Transaction(
            transaction_type=form.transaction_type.data,
            amount=form.amount.data,
            category=form.category.data,
            date=form.date.data,
            frequency=form.frequency.data,
            description=form.description.data,
            user_id=current_user.id
        )
        db.session.add(new_transaction)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    all_tx = Transaction.query.filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc()).all()
    
    # Summarize totals (keep your existing calculations)
    total_income = db.session.query(func.sum(Transaction.amount)).filter_by(
        transaction_type='income', user_id=current_user.id
    ).scalar() or 0.0


    total_expense = db.session.query(func.sum(Transaction.amount)).filter_by(
        transaction_type='expense', user_id=current_user.id
    ).scalar() or 0.0


    net_balance = total_income - total_expense


    assets = db.session.query(func.sum(Transaction.amount)).filter_by(
        transaction_type='assets', user_id=current_user.id
    ).scalar() or 0.0
    
    expected_income = db.session.query(
            func.sum(
                case(
                    # Daily transactions: amount * remaining days
                    (Transaction.frequency == 'daily', Transaction.amount * days_remaining),
                    # Weekly transactions: amount * remaining weeks
                    (Transaction.frequency == 'weekly', Transaction.amount * weeks_remaining),
                    # For monthly/yearly: use amount as-is
                    (Transaction.frequency.in_(['monthly', 'yearly']), Transaction.amount),
                    else_=0.0
                )
            )
        ).filter(
            (Transaction.frequency != 'one-time') &
            (Transaction.transaction_type == 'income') &
            (
                (Transaction.frequency == 'daily') |
                (Transaction.frequency == 'weekly') |
                (
                    (Transaction.frequency == 'monthly') &
                    (extract('month', Transaction.date) == today.month) &
                    (
                        (extract('day', Transaction.date) >= today.day) |
                        (extract('year', Transaction.date) > today.year)
                    )
                ) |
                (
                    (Transaction.frequency == 'yearly') &
                    (extract('month', Transaction.date) == today.month) &
                    (
                        (extract('day', Transaction.date) >= today.day) |
                        (extract('year', Transaction.date) > today.year)
                    )
                )
            )
        ).scalar() or 0.0

    # Recurring transactions query
    recurring_tx = db.session.query(
        func.sum(
            case(
                (Transaction.frequency == 'daily', Transaction.amount * days_remaining),
                (Transaction.frequency == 'weekly', Transaction.amount * weeks_remaining),
                (Transaction.frequency.in_(['monthly', 'yearly']), Transaction.amount),
                else_=0.0
            )
        )
    ).filter(
        (Transaction.frequency != 'one-time') &
        (Transaction.transaction_type != 'assets') &
        (
            (Transaction.frequency == 'daily') |
            (Transaction.frequency == 'weekly') |
            (
                (Transaction.frequency == 'monthly') &
                (extract('month', Transaction.date) == today.month) &
                (
                    (extract('day', Transaction.date) >= today.day) |
                    (extract('year', Transaction.date) > today.year)
                )
            ) |
            (
                (Transaction.frequency == 'yearly') &
                (extract('month', Transaction.date) == today.month) &
                (
                    (extract('day', Transaction.date) >= today.day) |
                    (extract('year', Transaction.date) > today.year)
                )
            )
        )
    ).scalar() or 0.0



    return render_template(
        "dashboard.html",
        form=form,
        total_income=total_income,
        total_expense=total_expense,
        net_balance=net_balance,
        recurring_tx=recurring_tx,
        assets=assets,
        expected_income=expected_income,
        all_tx = all_tx
    )


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash("Login successful! Welcome back.", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for("main.dashboard"))
        flash("Invalid email or password.", "danger")
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
        user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for(".login"))

    return render_template("auth/register.html", form=form)


# Transactions routes
@main.route('/dashboard/feeds/transactions')
@login_required
def transactions():
    # Get recurring transactions (non one-time)
    recurring_transactions = Transaction.query.filter(
        Transaction.frequency != 'one-time',
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.asc()).all()

    # Get all transactions
    all_tx = Transaction.query.filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc()).all()

    # Get only assets
    all_assets = Transaction.query.filter(
        Transaction.transaction_type == 'assets',
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc()).all()

    return render_template('transactions.html',
        recurring_transactions=recurring_transactions,
        all_transactions=all_tx,
        all_assets=all_assets
    )

# Analysis routes
@main.route('/dashboard/feeds/analysis', methods=['GET', 'POST'])
def analysis():
    if request.method == 'POST':
        # Handle form submission for analysis
        # Example: Update analysis filters
        # start_date = request.form.get('start_date')
        # end_date = request.form.get('end_date')
        # Process the filters
        return redirect(url_for('analysis'))
    
    # GET request - show analysis
    return render_template('analysis.html')

# Settings routes
@main.route('/dashboard/feeds/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # Handle form submission for settings
        # Example: Update user preferences
        # currency = request.form.get('currency')
        # theme = request.form.get('theme')
        # Save the settings
        return redirect(url_for('settings'))
    
    # GET request - show settings
    return render_template('settings.html')