from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myfinances.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return redirect(url_for('register'))
        
        # hashed_password = generate_password_hash(password, method='sha256')
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access this page', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Get totals
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter_by(
        user_id=user.id, type='income').scalar() or 0
    total_expenses = db.session.query(db.func.sum(Transaction.amount)).filter_by(
        user_id=user.id, type='expense').scalar() or 0
    balance = total_income - total_expenses
    
    # Get data for charts
    income_by_category = db.session.query(
        Transaction.category,
        db.func.sum(Transaction.amount).label('total')
    ).filter_by(
        user_id=user.id, type='income'
    ).group_by(Transaction.category).all()
    
    expenses_by_category = db.session.query(
        Transaction.category,
        db.func.sum(Transaction.amount).label('total')
    ).filter_by(
        user_id=user.id, type='expense'
    ).group_by(Transaction.category).all()
    
    # Get monthly trends
    monthly_data = db.session.query(
        db.func.strftime('%Y-%m', Transaction.date).label('month'),
        db.func.sum(db.case((Transaction.type == 'income', Transaction.amount), else_=0)).label('income'),
        db.func.sum(db.case((Transaction.type == 'expense', Transaction.amount), else_=0)).label('expense')
    ).filter_by(
        user_id=user.id
    ).group_by('month').order_by('month').all()
    
    return render_template(
        'dashboard.html',
        balance=balance,
        total_income=total_income,
        total_expenses=total_expenses,
        income_by_category=dict(income_by_category),
        expenses_by_category=dict(expenses_by_category),
        monthly_data=monthly_data,
        recent_transactions=Transaction.query.filter_by(
            user_id=user.id
        ).order_by(Transaction.date.desc()).limit(5).all()
    )



@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        flash('Please log in to access this page', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.date.desc()).all()
    return render_template('transactions.html', transactions=transactions)


@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    if 'user_id' not in session:
        flash('Please log in to access this page', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            category = request.form['category']
            description = request.form['description']
            transaction_type = request.form['type']
            
            # The date will always be in YYYY-MM-DD format from the date input
            date = datetime.fromisoformat(request.form['date'])
            
            new_transaction = Transaction(
                amount=amount,
                category=category,
                description=description,
                type=transaction_type,
                date=date,
                user_id=session['user_id']
            )
            
            db.session.add(new_transaction)
            db.session.commit()
            
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('transactions'))
        
        except ValueError as e:
            db.session.rollback()
            flash(f'Invalid input: {str(e)}', 'danger')
            return redirect(url_for('add_transaction'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect(url_for('add_transaction'))
    
    # For GET request, show the form with today's date as default
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_transaction.html', today=today)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)