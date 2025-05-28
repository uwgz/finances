from flask import flash, redirect, render_template, url_for, request, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
import json
from . import main
from .. import db
from ..models import User, Transaction
from .forms import LoginForm, RegistrationForm, TransactionForm
from sqlalchemy import func, extract, case
from datetime import datetime
from dateutil.relativedelta import relativedelta
from ..utils import FinancialGoalOptimizer


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
    
    # Get all transactions
    all_tx = Transaction.query.filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc()).all()
    
    # Convert transactions to serializable format
    tx_data = [{
        'type': tx.transaction_type,
        'amount': float(tx.amount),
        'date': tx.date.isoformat(),
        'category': tx.category,
        'description': tx.description,
        'frequency': tx.frequency
    } for tx in all_tx]

    # Keep all your existing calculations (unchanged)
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
                    (Transaction.frequency == 'daily', Transaction.amount * days_remaining),
                    (Transaction.frequency == 'weekly', Transaction.amount * weeks_remaining),
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
        all_tx=tx_data
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
    form = TransactionForm()
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
        return redirect(url_for('main.transactions'))
    
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
        form=form,
        recurring_transactions=recurring_transactions,
        all_transactions=all_tx,
        all_assets=all_assets
    )

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




# Prediction settings
@main.route('/dashboard/feeds/predictor', methods=['GET', 'POST'])
def predictor():
    if request.method == 'POST':
        try:
            data = request.get_json()
            print(data)
            if not data or 'goal_name' not in data or 'goal_amount' not in data or 'transactions' not in data:
                return jsonify({'status': 'error', 'message': 'Invalid data format'}), 400
            
            print("Received goal data:", data['transactions'])
            
            
            # Prepare the transactions data for the optimizer
            transactions = prepare_transactions_data(data['transactions'])

            print("*"*1000)
           
            goal_amount = data['goal_amount']



            # Create and use the optimizer
            optimizer = FinancialGoalOptimizer(transactions)
            optimal_years = optimizer.find_optimal_years(goal_amount)
            projected_savings = optimizer.calculate_total_net(optimal_years)
            
            # return jsonify({
            #     'status': 'success',
            #     'goal_name': data['goal_name'],
            #     'goal_amount': goal_amount,
            #     'optimal_years': optimal_years,
            #     'projected_savings': projected_savings,
            #     'monthly_savings_needed': goal_amount / (optimal_years * 12) if optimal_years > 0 else 0,
            #     'annual_savings_needed': goal_amount / optimal_years if optimal_years > 0 else 0,
            #     'transactions_summary': {
            #         'total_income': sum(sum(amounts) for amounts in optimizer.transactions['income'].values()),
            #         'total_expenses': sum(sum(amounts) for amounts in optimizer.transactions['expenses'].values())
            #     }
            # })
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # Get all recurring transactions EXCLUDING assets
    all_tx = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.frequency != 'one-time',
        Transaction.transaction_type != 'assets'  # Explicitly exclude assets
    ).order_by(Transaction.date.desc()).all()
    
    # Convert transactions to serializable format
    tx_data = [{
        'transaction_type': tx.transaction_type,
        'amount': float(tx.amount),
        'date': tx.date.isoformat(),
        'category': tx.category,
        'description': tx.description,
        'frequency': tx.frequency
    } for tx in all_tx]


    # Calculate totals (also excluding assets)
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'income',
        Transaction.user_id == current_user.id,
        Transaction.transaction_type != 'assets'
    ).scalar() or 0.0

    total_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'expense', 
        Transaction.user_id == current_user.id,
        Transaction.transaction_type != 'assets'
    ).scalar() or 0.0

    net_balance = total_income - total_expense


    return render_template('predictor.html',
        transactions=json.dumps(tx_data),
        total_income=total_income,
        total_expense=total_expense,
        net_balance=net_balance
    )



def prepare_transactions_data(raw_transactions):
    transactions = {
        "income": {
            "daily": [],
            "weekly": [],
            "monthly": [],
            "yearly": []
        },
        "expenses": {
            "daily": [],
            "weekly": [],
            "monthly": [],
            "yearly": []
        }
    }
    
    for tx in raw_transactions:
        tx_type = tx['transaction_type']  # 'income' or 'expense'
        frequency = tx['frequency']  # 'daily', 'weekly', 'monthly', 'yearly'
        amount = tx['amount']
        
        # Append the amount to the appropriate list
        transactions[tx_type][frequency].append(amount)
    
    return transactions