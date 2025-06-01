from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from app.models import Transaction
import calendar

# class FinancialGoalOptimizer:
#     def __init__(self, transactions):
#         self.transactions = transactions
#         self.period_factors = {
#             'daily': 365,
#             'weekly': 52,
#             'monthly': 12,
#             'yearly': 1
#         }

#     def calculate_total_net(self, years):
#         """Calculate the TOTAL net savings (income - expenses) over N years"""
#         total = 0
#         for period, annual_factor in self.period_factors.items():
#             income = sum(self.transactions['income'].get(period, [])) * annual_factor * years
#             expense = sum(self.transactions['expense'].get(period, [])) * annual_factor * years
#             total += (income - expense)
#         return total

#     def find_optimal_years(self, goalamount, learning_rate=0.0001, max_iter=1000, tolerance=1.0):
#         """Find years required to minimize |goalamount - total_net|"""
#         years = 1.0  # Initial guess
#         prev_error = float('inf')

#         for iteration in range(max_iter):
#             total_net = self.calculate_total_net(years)
#             error = goalamount - total_net

#             if abs(error) < tolerance:
#                 break

#             # Calculate gradient
#             delta = 0.001 * years
#             perturbed_net = self.calculate_total_net(years + delta)
#             gradient = (perturbed_net - total_net) / delta
#             gradient = max(min(gradient, 1e6), -1e6)

#             # Update years
#             years += learning_rate * error * gradient
#             years = max(0.1, min(years, 100))  # Keep within reasonable bounds

#             # Adjust learning rate if error increases
#             if abs(error) > prev_error:
#                 learning_rate *= 0.9

#             prev_error = abs(error)

#             if iteration % 100 == 0:
#                 print(f"Iter {iteration}: years={years:.3f}, net=${total_net:,.2f}, error=${error:,.2f}")

#         return years


def calculate_frequency_multiplier(frequency):
    """Convert frequency to annual multiplier for calculations"""
    multipliers = {
        "Daily": 365,
        "Weekly": 52,
        "Monthly": 12,
        "Quarterly": 4,
        "Yearly": 1,
        "One-Time": 0,  # Special case
    }
    return multipliers.get(frequency, 1)


def get_next_occurrence_date(start_date, frequency):
    """Calculate next occurrence based on frequency"""
    if frequency == "Daily":
        return start_date + timedelta(days=1)
    elif frequency == "Weekly":
        return start_date + timedelta(weeks=1)
    elif frequency == "Monthly":
        return start_date + relativedelta(months=1)
    elif frequency == "Quarterly":
        return start_date + relativedelta(months=3)
    elif frequency == "Yearly":
        return start_date + relativedelta(years=1)
    else:  # One-Time
        return None


def calculate_monthly_cash_flow(user_id, start_date=None):
    """Calculate monthly net cash flow based on recurring transactions"""
    if start_date is None:
        start_date = date.today()

    # Get all recurring transactions for the user
    transactions = Transaction.query.filter_by(user_id=user_id).all()

    monthly_income = 0
    monthly_expenses = 0
    monthly_assets = 0

    for transaction in transactions:
        if transaction.frequency == "One-Time":
            continue

        multiplier = calculate_frequency_multiplier(transaction.frequency)
        monthly_amount = (transaction.amount * multiplier) / 12

        if transaction.transaction_type == "Income":
            monthly_income += monthly_amount
        elif transaction.transaction_type == "Expenses":
            monthly_expenses += monthly_amount
        elif transaction.transaction_type == "Assets":
            monthly_assets += monthly_amount

    net_monthly_flow = monthly_income - monthly_expenses - monthly_assets

    return {
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_assets": monthly_assets,
        "net_monthly_flow": net_monthly_flow,
    }


def calculate_current_balance(user_id):
    """Calculate current balance based on all past transactions"""
    # Get all transactions up to today
    transactions = Transaction.query.filter(
        Transaction.user_id == user_id, Transaction.date <= date.today()
    ).all()

    balance = 0
    for transaction in transactions:
        # Calculate how many times this transaction has occurred
        if transaction.frequency == "One-Time":
            occurrences = 1
        else:
            # Calculate occurrences from transaction date to today
            days_passed = (date.today() - transaction.date).days

            if transaction.frequency == "daily":
                occurrences = max(1, days_passed + 1)
            elif transaction.frequency == "weekly":
                occurrences = max(1, (days_passed // 7) + 1)
            elif transaction.frequency == "monthly":
                months_passed = (date.today().year - transaction.date.year) * 12 + (
                    date.today().month - transaction.date.month
                )
                occurrences = max(1, months_passed + 1)
            elif transaction.frequency == "quarterly":
                months_passed = (date.today().year - transaction.date.year) * 12 + (
                    date.today().month - transaction.date.month
                )
                occurrences = max(1, (months_passed // 3) + 1)
            elif transaction.frequency == "yearly":
                years_passed = date.today().year - transaction.date.year
                occurrences = max(1, years_passed + 1)

        total_amount = transaction.amount * occurrences

        if transaction.transaction_type == "income":
            balance += total_amount
        elif transaction.transaction_type in ["expenses"]:
            balance -= total_amount

    return balance


def forecast_goal_achievement(user_id, goal_amount, current_balance=None):
    """
    Forecast when a financial goal will be achieved
    Returns detailed forecast information
    """
    if current_balance is None:
        current_balance = calculate_current_balance(user_id)

    cash_flow = calculate_monthly_cash_flow(user_id)

    # If goal is already achieved
    if current_balance >= goal_amount:
        return {
            "goal_achieved": True,
            "current_balance": current_balance,
            "goal_amount": goal_amount,
            "surplus": current_balance - goal_amount,
            "achievement_date": date.today(),
            "months_to_goal": 0,
            "cash_flow_analysis": cash_flow,
        }

    # If no positive cash flow, goal cannot be achieved
    if cash_flow["net_monthly_flow"] <= 0:
        return {
            "goal_achieved": False,
            "achievable": False,
            "current_balance": current_balance,
            "goal_amount": goal_amount,
            "amount_needed": goal_amount - current_balance,
            "monthly_deficit": abs(cash_flow["net_monthly_flow"]),
            "recommendation": "Increase income or reduce expenses to achieve this goal",
            "cash_flow_analysis": cash_flow,
        }

    # Calculate months needed
    amount_needed = goal_amount - current_balance
    months_needed = amount_needed / cash_flow["net_monthly_flow"]

    # Calculate achievement date
    achievement_date = date.today() + relativedelta(months=int(months_needed))
    if months_needed % 1 > 0:  # Add extra days for partial month
        extra_days = int((months_needed % 1) * 30)
        achievement_date += timedelta(days=extra_days)

    return {
        "goal_achieved": False,
        "achievable": True,
        "current_balance": current_balance,
        "goal_amount": goal_amount,
        "amount_needed": amount_needed,
        "months_to_goal": months_needed,
        "achievement_date": achievement_date,
        "cash_flow_analysis": cash_flow,
        "weekly_savings": cash_flow["net_monthly_flow"] / 4.33,
        "daily_savings": cash_flow["net_monthly_flow"] / 30,
    }


def generate_forecast_milestones(user_id, goal_amount, current_balance=None):
    """Generate milestone predictions (25%, 50%, 75%, 100%)"""
    if current_balance is None:
        current_balance = calculate_current_balance(user_id)

    cash_flow = calculate_monthly_cash_flow(user_id)

    if cash_flow["net_monthly_flow"] <= 0:
        return []

    milestones = []
    percentages = [25, 50, 75, 100]

    for percentage in percentages:
        milestone_amount = (goal_amount * percentage) / 100

        if current_balance >= milestone_amount:
            milestones.append(
                {
                    "percentage": percentage,
                    "amount": milestone_amount,
                    "achieved": True,
                    "achievement_date": date.today(),
                }
            )
        else:
            amount_needed = milestone_amount - current_balance
            months_needed = amount_needed / cash_flow["net_monthly_flow"]
            achievement_date = date.today() + relativedelta(months=int(months_needed))

            if months_needed % 1 > 0:
                extra_days = int((months_needed % 1) * 30)
                achievement_date += timedelta(days=extra_days)

            milestones.append(
                {
                    "percentage": percentage,
                    "amount": milestone_amount,
                    "achieved": False,
                    "months_to_achieve": months_needed,
                    "achievement_date": achievement_date,
                }
            )

    return milestones


def analyze_spending_categories(user_id):
    """Analyze spending by category for optimization suggestions"""
    from sqlalchemy import func

    # Get expense transactions grouped by category
    expense_analysis = (
        Transaction.query.filter(
            Transaction.user_id == user_id, Transaction.transaction_type == "Expenses"
        )
        .with_entities(
            Transaction.category,
            func.sum(Transaction.amount).label("total_amount"),
            func.count(Transaction.id).label("transaction_count"),
            func.avg(Transaction.amount).label("avg_amount"),
        )
        .group_by(Transaction.category)
        .all()
    )

    categories = []
    for category, total, count, avg in expense_analysis:
        categories.append(
            {
                "category": category,
                "total_amount": total,
                "transaction_count": count,
                "average_amount": avg,
                "monthly_estimate": total
                * 12
                / max(1, count),  # Rough monthly estimate
            }
        )

    # Sort by total amount descending
    categories.sort(key=lambda x: x["total_amount"], reverse=True)

    return categories


def get_optimization_suggestions(user_id, goal_amount):
    """Provide suggestions to achieve goal faster"""
    forecast = forecast_goal_achievement(user_id, goal_amount)
    spending_analysis = analyze_spending_categories(user_id)

    suggestions = []

    if not forecast.get("achievable", True):
        suggestions.append(
            {
                "type": "critical",
                "title": "Goal Currently Not Achievable",
                "description": "Your current expenses exceed your income. Consider increasing income or reducing expenses.",
                "priority": 1,
            }
        )

    # Suggest reducing top spending categories
    if spending_analysis:
        top_category = spending_analysis[0]
        monthly_savings_needed = forecast.get("amount_needed", 0) / 12

        if top_category["monthly_estimate"] > monthly_savings_needed * 0.1:
            suggestions.append(
                {
                    "type": "optimization",
                    "title": f'Reduce {top_category["category"]} Spending',
                    "description": f'You spend ${top_category["total_amount"]:.2f} monthly on {top_category["category"]}. Reducing this by 20% could save ${top_category["total_amount"] * 0.2:.2f}/month.',
                    "priority": 2,
                    "potential_savings": top_category["total_amount"] * 0.2,
                }
            )

    # Suggest increasing income
    current_income = forecast["cash_flow_analysis"]["monthly_income"]
    suggestions.append(
        {
            "type": "income",
            "title": "Increase Monthly Income",
            "description": f"Increasing your income by even $100/month could significantly accelerate your goal achievement.",
            "priority": 3,
        }
    )

    return suggestions
