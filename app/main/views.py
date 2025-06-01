from flask import flash, redirect, render_template, url_for, request, jsonify, session
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
import json
from . import main
from .. import db
from ..models import User, Transaction
from .forms import (
    LoginForm,
    RegistrationForm,
    TransactionForm,
    GoalForecastForm,
    ForecastScenarioForm,
)
from sqlalchemy import func, extract, case
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .utils import (
    forecast_goal_achievement,
    calculate_current_balance,
    generate_forecast_milestones,
    analyze_spending_categories,
    get_optimization_suggestions,
    calculate_monthly_cash_flow,
)


@main.route("/")
def index():
    return render_template("index.html", current_time=datetime.utcnow())


@main.route("/dashboard", methods=["GET", "POST"])
@main.route("/dashboard/feeds", methods=["GET", "POST"])
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
            user_id=current_user.id,
        )
        db.session.add(new_transaction)
        db.session.commit()
        flash("Transaction added successfully!", "success")
        return redirect(url_for("main.dashboard"))

    # Get all transactions
    all_tx = (
        Transaction.query.filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.date.desc())
        .all()
    )

    # Convert transactions to serializable format
    tx_data = [
        {
            "type": tx.transaction_type,
            "amount": float(tx.amount),
            "date": tx.date.isoformat(),
            "category": tx.category,
            "description": tx.description,
            "frequency": tx.frequency,
        }
        for tx in all_tx
    ]

    # Keep all your existing calculations (unchanged)
    total_income = (
        db.session.query(func.sum(Transaction.amount))
        .filter_by(transaction_type="income", user_id=current_user.id)
        .scalar()
        or 0.0
    )

    total_expense = (
        db.session.query(func.sum(Transaction.amount))
        .filter_by(transaction_type="expense", user_id=current_user.id)
        .scalar()
        or 0.0
    )

    net_balance = total_income - total_expense

    assets = (
        db.session.query(func.sum(Transaction.amount))
        .filter_by(transaction_type="assets", user_id=current_user.id)
        .scalar()
        or 0.0
    )

    expected_income = (
        db.session.query(
            func.sum(
                case(
                    (
                        Transaction.frequency == "daily",
                        Transaction.amount * days_remaining,
                    ),
                    (
                        Transaction.frequency == "weekly",
                        Transaction.amount * weeks_remaining,
                    ),
                    (
                        Transaction.frequency.in_(["monthly", "yearly"]),
                        Transaction.amount,
                    ),
                    else_=0.0,
                )
            )
        )
        .filter(
            (Transaction.frequency != "one-time")
            & (Transaction.transaction_type == "income")
            & (
                (Transaction.frequency == "daily")
                | (Transaction.frequency == "weekly")
                | (
                    (Transaction.frequency == "monthly")
                    & (extract("month", Transaction.date) == today.month)
                    & (
                        (extract("day", Transaction.date) >= today.day)
                        | (extract("year", Transaction.date) > today.year)
                    )
                )
                | (
                    (Transaction.frequency == "yearly")
                    & (extract("month", Transaction.date) == today.month)
                    & (
                        (extract("day", Transaction.date) >= today.day)
                        | (extract("year", Transaction.date) > today.year)
                    )
                )
            )
        )
        .scalar()
        or 0.0
    )

    recurring_tx = (
        db.session.query(
            func.sum(
                case(
                    (
                        Transaction.frequency == "daily",
                        Transaction.amount * days_remaining,
                    ),
                    (
                        Transaction.frequency == "weekly",
                        Transaction.amount * weeks_remaining,
                    ),
                    (
                        Transaction.frequency.in_(["monthly", "yearly"]),
                        Transaction.amount,
                    ),
                    else_=0.0,
                )
            )
        )
        .filter(
            (Transaction.frequency != "one-time")
            & (Transaction.transaction_type != "assets")
            & (
                (Transaction.frequency == "daily")
                | (Transaction.frequency == "weekly")
                | (
                    (Transaction.frequency == "monthly")
                    & (extract("month", Transaction.date) == today.month)
                    & (
                        (extract("day", Transaction.date) >= today.day)
                        | (extract("year", Transaction.date) > today.year)
                    )
                )
                | (
                    (Transaction.frequency == "yearly")
                    & (extract("month", Transaction.date) == today.month)
                    & (
                        (extract("day", Transaction.date) >= today.day)
                        | (extract("year", Transaction.date) > today.year)
                    )
                )
            )
        )
        .scalar()
        or 0.0
    )

    return render_template(
        "dashboard.html",
        form=form,
        total_income=total_income,
        total_expense=total_expense,
        net_balance=net_balance,
        recurring_tx=recurring_tx,
        assets=assets,
        expected_income=expected_income,
        all_tx=tx_data,
    )


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash("Login successful! Welcome back.", "success")
            next_page = request.args.get("next")
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
            last_name=form.last_name.data,
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for(".login"))

    return render_template("auth/register.html", form=form)


# Transactions routes
@main.route("/dashboard/feeds/transactions")
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
            user_id=current_user.id,
        )
        db.session.add(new_transaction)
        db.session.commit()
        flash("Transaction added successfully!", "success")
        return redirect(url_for("main.transactions"))

    # Get recurring transactions (non one-time)
    recurring_transactions = (
        Transaction.query.filter(
            Transaction.frequency != "one-time", Transaction.user_id == current_user.id
        )
        .order_by(Transaction.date.asc())
        .all()
    )

    # Get all transactions
    all_tx = (
        Transaction.query.filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.date.desc())
        .all()
    )

    # Get only assets
    all_assets = (
        Transaction.query.filter(
            Transaction.transaction_type == "assets",
            Transaction.user_id == current_user.id,
        )
        .order_by(Transaction.date.desc())
        .all()
    )

    return render_template(
        "transactions.html",
        form=form,
        recurring_transactions=recurring_transactions,
        all_transactions=all_tx,
        all_assets=all_assets,
    )


# Settings routes
@main.route("/dashboard/feeds/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        # Handle form submission for settings
        # Example: Update user preferences
        # currency = request.form.get('currency')
        # theme = request.form.get('theme')
        # Save the settings
        return redirect(url_for("settings"))

    # GET request - show settings
    return render_template("settings.html")


# # Prediction settings
# @main.route("/dashboard/feeds/predictor", methods=["GET", "POST"])
# def predictor():
#     if request.method == "POST":
#         try:
#             data = request.get_json()
#             print(data)
#             if (
#                 not data
#                 or "goal_name" not in data
#                 or "goal_amount" not in data
#                 or "transactions" not in data
#             ):
#                 return (
#                     jsonify({"status": "error", "message": "Invalid data format"}),
#                     400,
#                 )

#             print("Received goal data:", data["transactions"])

#             # Prepare the transactions data for the optimizer
#             transactions = prepare_transactions_data(data["transactions"])

#             print("*" * 1000)

#             goal_amount = data["goal_amount"]

#             # Create and use the optimizer
#             optimizer = FinancialGoalOptimizer(transactions)
#             optimal_years = optimizer.find_optimal_years(goal_amount)
#             projected_savings = optimizer.calculate_total_net(optimal_years)

#             # return jsonify({
#             #     'status': 'success',
#             #     'goal_name': data['goal_name'],
#             #     'goal_amount': goal_amount,
#             #     'optimal_years': optimal_years,
#             #     'projected_savings': projected_savings,
#             #     'monthly_savings_needed': goal_amount / (optimal_years * 12) if optimal_years > 0 else 0,
#             #     'annual_savings_needed': goal_amount / optimal_years if optimal_years > 0 else 0,
#             #     'transactions_summary': {
#             #         'total_income': sum(sum(amounts) for amounts in optimizer.transactions['income'].values()),
#             #         'total_expenses': sum(sum(amounts) for amounts in optimizer.transactions['expenses'].values())
#             #     }
#             # })

#         except Exception as e:
#             return jsonify({"status": "error", "message": str(e)}), 500

#     # Get all recurring transactions EXCLUDING assets
#     all_tx = (
#         Transaction.query.filter(
#             Transaction.user_id == current_user.id,
#             Transaction.frequency != "one-time",
#             Transaction.transaction_type != "assets",  # Explicitly exclude assets
#         )
#         .order_by(Transaction.date.desc())
#         .all()
#     )

#     # Convert transactions to serializable format
#     tx_data = [
#         {
#             "transaction_type": tx.transaction_type,
#             "amount": float(tx.amount),
#             "date": tx.date.isoformat(),
#             "category": tx.category,
#             "description": tx.description,
#             "frequency": tx.frequency,
#         }
#         for tx in all_tx
#     ]

#     # Calculate totals (also excluding assets)
#     total_income = (
#         db.session.query(func.sum(Transaction.amount))
#         .filter(
#             Transaction.transaction_type == "income",
#             Transaction.user_id == current_user.id,
#             Transaction.transaction_type != "assets",
#         )
#         .scalar()
#         or 0.0
#     )

#     total_expense = (
#         db.session.query(func.sum(Transaction.amount))
#         .filter(
#             Transaction.transaction_type == "expense",
#             Transaction.user_id == current_user.id,
#             Transaction.transaction_type != "assets",
#         )
#         .scalar()
#         or 0.0
#     )

#     net_balance = total_income - total_expense

#     return render_template(
#         "predictor.html",
#         transactions=json.dumps(tx_data),
#         total_income=total_income,
#         total_expense=total_expense,
#         net_balance=net_balance,
#     )


# def prepare_transactions_data(raw_transactions):
#     transactions = {
#         "income": {"daily": [], "weekly": [], "monthly": [], "yearly": []},
#         "expenses": {"daily": [], "weekly": [], "monthly": [], "yearly": []},
#     }

#     for tx in raw_transactions:
#         tx_type = tx["transaction_type"]  # 'income' or 'expense'
#         frequency = tx["frequency"]  # 'daily', 'weekly', 'monthly', 'yearly'
#         amount = tx["amount"]

#         # Append the amount to the appropriate list
#         transactions[tx_type][frequency].append(amount)

#     return transactions


@main.route("/forecast", methods=["GET", "POST"])
@login_required
def forecast():
    form = GoalForecastForm()

    if form.validate_on_submit():
        goal_amount = float(form.goal_amount.data)
        goal_type = form.goal_type.data
        goal_description = form.goal_description.data

        # Store goal info in session for use in results
        session["forecast_goal"] = {
            "amount": goal_amount,
            "type": goal_type,
            "description": goal_description,
        }

        return redirect(url_for("main.forecast_results"))

    # Get user's current balance and recent transactions for display
    current_balance = calculate_current_balance(current_user.id)
    cash_flow = calculate_monthly_cash_flow(current_user.id)

    return render_template(
        "forecast/forecast_form.html",
        form=form,
        current_balance=current_balance,
        cash_flow=cash_flow,
    )


@main.route("/forecast/results")
@login_required
def forecast_results():
    goal_info = session.get("forecast_goal")
    if not goal_info:
        flash("Please set a goal first.", "warning")
        return redirect(url_for("main.forecast"))

    goal_amount = goal_info["amount"]

    # Get scenario adjustments if any
    additional_income = float(request.args.get("additional_income", 0))
    reduced_expenses = float(request.args.get("reduced_expenses", 0))

    # Calculate forecast
    forecast_data = forecast_goal_achievement(current_user.id, goal_amount)

    # Apply scenario adjustments
    if additional_income > 0 or reduced_expenses > 0:
        adjusted_monthly_flow = (
            forecast_data["cash_flow_analysis"]["net_monthly_flow"]
            + additional_income
            + reduced_expenses
        )
        if adjusted_monthly_flow > 0 and not forecast_data.get("goal_achieved", False):
            amount_needed = goal_amount - forecast_data["current_balance"]
            adjusted_months = amount_needed / adjusted_monthly_flow

            from dateutil.relativedelta import relativedelta
            from datetime import date, timedelta

            adjusted_date = date.today() + relativedelta(months=int(adjusted_months))
            if adjusted_months % 1 > 0:
                extra_days = int((adjusted_months % 1) * 30)
                adjusted_date += timedelta(days=extra_days)

            forecast_data["scenario_analysis"] = {
                "adjusted_monthly_flow": adjusted_monthly_flow,
                "adjusted_months": adjusted_months,
                "adjusted_date": adjusted_date,
                "time_saved_months": forecast_data.get("months_to_goal", 0)
                - adjusted_months,
            }

    # Generate milestones
    milestones = generate_forecast_milestones(current_user.id, goal_amount)

    # Get optimization suggestions
    suggestions = get_optimization_suggestions(current_user.id, goal_amount)

    # Spending analysis
    spending_analysis = analyze_spending_categories(current_user.id)

    scenario_form = ForecastScenarioForm()

    return render_template(
        "forecast/forecast_results.html",
        goal_info=goal_info,
        forecast=forecast_data,
        milestones=milestones,
        suggestions=suggestions,
        spending_analysis=spending_analysis,
        scenario_form=scenario_form,
    )


@main.route("/forecast/api/scenario", methods=["POST"])
@login_required
def forecast_scenario_api():
    """API endpoint for real-time scenario calculations"""
    data = request.get_json()
    goal_amount = data.get("goal_amount")
    additional_income = data.get("additional_income", 0)
    reduced_expenses = data.get("reduced_expenses", 0)

    if not goal_amount:
        return jsonify({"error": "Goal amount required"}), 400

    # Get base forecast
    forecast_data = forecast_goal_achievement(current_user.id, float(goal_amount))

    if forecast_data.get("goal_achieved"):
        return jsonify(forecast_data)

    # Calculate adjusted scenario
    base_flow = forecast_data["cash_flow_analysis"]["net_monthly_flow"]
    adjusted_flow = base_flow + float(additional_income) + float(reduced_expenses)

    if adjusted_flow <= 0:
        return jsonify(
            {
                "achievable": False,
                "adjusted_monthly_flow": adjusted_flow,
                "message": "Goal still not achievable with these adjustments",
            }
        )

    amount_needed = forecast_data["amount_needed"]
    adjusted_months = amount_needed / adjusted_flow

    from dateutil.relativedelta import relativedelta
    from datetime import date, timedelta

    adjusted_date = date.today() + relativedelta(months=int(adjusted_months))
    if adjusted_months % 1 > 0:
        extra_days = int((adjusted_months % 1) * 30)
        adjusted_date += timedelta(days=extra_days)

    time_saved = forecast_data.get("months_to_goal", 0) - adjusted_months

    return jsonify(
        {
            "achievable": True,
            "adjusted_monthly_flow": adjusted_flow,
            "adjusted_months": round(adjusted_months, 1),
            "adjusted_date": adjusted_date.strftime("%Y-%m-%d"),
            "time_saved_months": round(time_saved, 1),
            "time_saved_days": round(time_saved * 30, 0),
        }
    )


@main.route("/forecast/dashboard")
@login_required
def forecast_dashboard():
    """Dashboard showing overview of all financial forecasts and trends"""
    current_balance = calculate_current_balance(current_user.id)
    cash_flow = calculate_monthly_cash_flow(current_user.id)
    spending_analysis = analyze_spending_categories(current_user.id)

    # Common goal amounts for quick forecasting
    common_goals = [1000, 5000, 10000, 25000, 50000, 100000]
    quick_forecasts = []

    for goal in common_goals:
        if goal > current_balance:
            forecast = forecast_goal_achievement(current_user.id, goal)
            if forecast.get("achievable", False):
                quick_forecasts.append(
                    {
                        "amount": goal,
                        "months": round(forecast.get("months_to_goal", 0), 1),
                        "date": forecast.get("achievement_date"),
                    }
                )

    return render_template(
        "forecast/dashboard.html",
        current_balance=current_balance,
        cash_flow=cash_flow,
        spending_analysis=spending_analysis[:5],  # Top 5 categories
        quick_forecasts=quick_forecasts,
    )
