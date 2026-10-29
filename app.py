import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import FileSystemLoader

class RobustFileSystemLoader(FileSystemLoader):
    def get_source(self, environment, template):
        path = os.path.join(self.searchpath[0], template)
        for enc in ('utf-8', 'windows-1252', 'latin-1'):
            try:
                with open(path, 'r', encoding=enc) as f:
                    contents = f.read()
                return contents, path, lambda: True
            except UnicodeDecodeError:
                continue
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            contents = f.read()
        return contents, path, lambda: True

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'apex-enterprise-secure-key-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///apex_cris.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.jinja_loader = RobustFileSystemLoader("templates")

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user') # 'user', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    records = db.relationship('CrisisRecord', backref='citizen', lazy=True, cascade='all, delete-orphan')

class CrisisRecord(db.Model):
    __tablename__ = 'crisis_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False) # 'EMPLOYMENT', 'GBV_ALERT', 'EL_NINO_RELIEF'
    details = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(40), default='SUBMITTED')
    assigned_partner = db.Column(db.String(120), default='Unassigned National Queue')
    next_action = db.Column(db.String(200), default='Awaiting triage and administrative review')
    aws_region = db.Column(db.String(20), default='af-south-1')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    audit_logs = db.relationship('AuditLog', backref='record', lazy=True, cascade='all, delete-orphan')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('crisis_records.id'), nullable=False)
    actor = db.Column(db.String(120), nullable=False)
    previous_status = db.Column(db.String(40), nullable=False)
    new_status = db.Column(db.String(40), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='admin@apex.gov.za').first():
        default_admin = User(
            full_name='Apex National Administrator',
            email='admin@apex.gov.za',
            password_hash=generate_password_hash('Admin@2026'),
            role='admin'
        )
        db.session.add(default_admin)
        db.session.commit()

# --- ROUTES: AUTHENTICATION ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        flash('Invalid email or password credentials.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email address is already registered in the APEX network.', 'error')
            return redirect(url_for('register'))
            
        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            role='user'
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Citizen account successfully created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# --- ROUTES: USER DASHBOARD & CASE TRACKING ---
@app.route('/dashboard')
@login_required
def user_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    user_records = CrisisRecord.query.filter_by(user_id=current_user.id).order_by(CrisisRecord.timestamp.desc()).all()
    return render_template('user_dashboard.html', records=user_records)

@app.route('/submit-record', methods=['POST'])
@login_required
def submit_record():
    category = request.form.get('category')
    details = request.form.get('details')
    
    if not details or not details.strip():
        flash('Please provide details for the crisis module dispatch.', 'error')
        return redirect(url_for('user_dashboard'))

    record = CrisisRecord(
        user_id=current_user.id,
        category=category,
        details=details.strip(),
        status='SUBMITTED',
        assigned_partner='Unassigned National Queue',
        next_action='Awaiting triage and administrative review',
        aws_region='af-south-1'
    )
    db.session.add(record)
    db.session.commit()

    audit = AuditLog(
        record_id=record.id,
        actor=current_user.full_name,
        previous_status='NONE',
        new_status='SUBMITTED',
        reason='Initial citizen case submission'
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'APEX Case #{record.id} [{category}] successfully submitted and logged to AWS RDS (af-south-1).', 'success')
    return redirect(url_for('user_dashboard'))

# --- ROUTES: ADMIN SITE & COMMAND CENTER ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, role='admin').first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Authenticated into Admin Command Center.', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid Administrator Credentials.', 'error')
    return render_template('admin_login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        secret_code = request.form.get('secret_code')
        
        if secret_code != 'APEX-SA-2026':
            flash('Unauthorized Administrator Secret Access Code.', 'error')
            return redirect(url_for('admin_register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('admin_register'))
            
        admin_user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        flash('Admin account created successfully. Please login.', 'success')
        return redirect(url_for('admin_login'))
    return render_template('admin_register.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access restricted to administrators.', 'error')
        return redirect(url_for('user_dashboard'))
    
    filter_cat = request.args.get('category', 'ALL')
    if filter_cat != 'ALL':
        records = CrisisRecord.query.filter_by(category=filter_cat).order_by(CrisisRecord.timestamp.desc()).all()
    else:
        records = CrisisRecord.query.order_by(CrisisRecord.timestamp.desc()).all()
        
    stats = {
        'total_users': User.query.filter_by(role='user').count(),
        'total_cases': CrisisRecord.query.count(),
        'pending_cases': CrisisRecord.query.filter(CrisisRecord.status.in_(['SUBMITTED', 'UNDER REVIEW'])).count(),
        'resolved_cases': CrisisRecord.query.filter_by(status='RESOLVED').count()
    }
    
    return render_template('admin_dashboard.html', records=records, stats=stats, selected_cat=filter_cat)

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    if current_user.role != 'admin':
        return redirect(url_for('user_dashboard'))
    
    total_cases = CrisisRecord.query.count()
    resolved_cases = CrisisRecord.query.filter_by(status='RESOLVED').count()
    emp_count = CrisisRecord.query.filter_by(category='EMPLOYMENT').count()
    gbv_count = CrisisRecord.query.filter_by(category='GBV_ALERT').count()
    drought_count = CrisisRecord.query.filter_by(category='EL_NINO_RELIEF').count()
    
    analytics_data = {
        'total_cases': total_cases,
        'resolved_cases': resolved_cases,
        'resolution_rate': round((resolved_cases / total_cases * 100) if total_cases > 0 else 0, 1),
        'emp_count': emp_count,
        'gbv_count': gbv_count,
        'drought_count': drought_count
    }
    return render_template('admin_analytics.html', data=analytics_data)

@app.route('/admin/update-status/<int:record_id>', methods=['POST'])
@login_required
def update_status(record_id):
    if current_user.role != 'admin':
        return redirect(url_for('user_dashboard'))
        
    record = CrisisRecord.query.get_or_404(record_id)
    new_status = request.form.get('status')
    assigned_partner = request.form.get('assigned_partner', record.assigned_partner)
    next_action = request.form.get('next_action', record.next_action)
    reason = request.form.get('reason', 'Status updated by Command Center operator')

    valid_statuses = ['SUBMITTED', 'UNDER REVIEW', 'ASSIGNED', 'ACKNOWLEDGED', 'IN PROGRESS', 'RESOLVED']
    if new_status in valid_statuses:
        prev_status = record.status
        record.status = new_status
        record.assigned_partner = assigned_partner
        record.next_action = next_action
        
        audit = AuditLog(
            record_id=record.id,
            actor=current_user.full_name,
            previous_status=prev_status,
            new_status=new_status,
            reason=reason
        )
        db.session.add(audit)
        db.session.commit()
        flash(f'Case #{record.id} successfully updated to [{new_status}].', 'success')
    else:
        flash('Invalid status selection.', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)