from flask import Flask, render_template, request, send_file, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import emoji

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cgpa_records.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'
db = SQLAlchemy(app)

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# Grade to weight mapping
grade_weights = {
    'S': 10,
    'A': 9,
    'B': 8,
    'C': 7,
    'D': 6,
    'E': 5,
    'U': 0,
    'AB': 0
}

# Database models
class CGPARecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    regno = db.Column(db.String(50))
    cgpa = db.Column(db.Float)
    grades = db.Column(db.String(200))
    credits = db.Column(db.String(200))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(100))
    content = db.Column(db.String(2000))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Dummy Admin user
class AdminUser(UserMixin):
    def __init__(self, id):
        self.id = id
        self.username = 'admin'
        self.password = 'admin123'

@login_manager.user_loader
def load_user(user_id):
    return AdminUser(user_id)

# Routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    grades = request.form.getlist('grade')
    credits = request.form.getlist('credit')
    name = request.form.get('name')
    regno = request.form.get('regno')

    total_score = 0
    total_credits = 0
    suggestions = []
    detailed_data = []

    for grade, credit in zip(grades, credits):
        try:
            weight = grade_weights[grade.upper()]
            credit = float(credit)
            total_score += weight * credit
            total_credits += credit
            detailed_data.append((grade.upper(), credit, weight))
            if grade.upper() in ['C', 'D', 'E', 'U', 'AB']:
                suggestions.append(f"Improve in subject with grade '{grade.upper()}'")
        except (KeyError, ValueError):
            continue

    cgpa = round(total_score / total_credits, 2) if total_credits > 0 else 0

    # Save to database
    new_record = CGPARecord(
        name=name,
        regno=regno,
        cgpa=cgpa,
        grades=",".join(grades),
        credits=",".join(credits)
    )
    db.session.add(new_record)
    db.session.commit()

    return render_template('index.html', cgpa=cgpa, data=zip(grades, credits),
                           detailed_data=detailed_data, suggestions=set(suggestions),
                           regno=regno, name=name)

@app.route('/export', methods=['POST'])
def export():
    grades = request.form.getlist('grade')
    credits = request.form.getlist('credit')
    regno = request.form.get('regno')

    total_score = 0
    total_credits = 0
    detailed_data = []

    for grade, credit in zip(grades, credits):
        try:
            weight = grade_weights[grade.upper()]
            credit = float(credit)
            total_score += weight * credit
            total_credits += credit
            detailed_data.append((grade.upper(), credit, weight))
        except (KeyError, ValueError):
            continue

    cgpa = round(total_score / total_credits, 2) if total_credits > 0 else 0

    rendered = render_template('report.html', cgpa=cgpa, detailed_data=detailed_data, regno=regno)
    return rendered

# -----------------------
# ✅ Admin Login System
# -----------------------

@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin123':
            user = AdminUser(id=1)
            login_user(user)
            return redirect(url_for('admin_panel'))
        else:
            error = 'Invalid credentials'
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_panel():
    records = CGPARecord.query.all()
    return render_template('admin.html', records=records)

@app.route('/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    record = CGPARecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for('admin_panel'))

# -----------------------
# 💬 Messaging System
# -----------------------

@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if request.method == 'POST':
        alias = request.form.get('alias')
        content = request.form.get('message')
        if alias and content and len(content.split()) <= 200:
            content = emoji.emojize(content, language='alias')
            msg = Message(alias=alias.strip(), content=content.strip())
            db.session.add(msg)
            db.session.commit()
        return redirect(url_for('messages'))

    # Clean up messages older than 16 hours
    time_limit = datetime.utcnow() - timedelta(hours=16)
    old_msgs = Message.query.filter(Message.timestamp < time_limit).all()
    for msg in old_msgs:
        db.session.delete(msg)
    db.session.commit()

    msgs = Message.query.order_by(Message.timestamp.desc()).all()
    return render_template('messages.html', messages=msgs)

# -----------------------
# Run
# -----------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
