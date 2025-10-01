from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='resident')  # admin_general, admin_ph, resident, provider, visitor
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    properties = db.relationship('Property', backref='admin', lazy=True)
    units = db.relationship('Unit', backref='owner', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)
    tickets = db.relationship('Ticket', foreign_keys='Ticket.user_id', backref='user', lazy=True)
    assigned_tickets = db.relationship('Ticket', foreign_keys='Ticket.assigned_to', backref='assigned_user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.email}>'

class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    address = db.Column(db.Text, nullable=False)
    total_units = db.Column(db.Integer, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    monthly_fee = db.Column(db.Numeric(10, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    units = db.relationship('Unit', backref='property', lazy=True, cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='property', lazy=True)
    maintenance_tasks = db.relationship('MaintenanceTask', backref='property', lazy=True)
    documents = db.relationship('Document', backref='property', lazy=True)
    assemblies = db.relationship('Assembly', backref='property', lazy=True)
    
    def __repr__(self):
        return f'<Property {self.name}>'

class Unit(db.Model):
    __tablename__ = 'units'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    unit_type = db.Column(db.String(50), default='apartment')  # apartment, parking, storage
    area = db.Column(db.Numeric(8, 2))
    monthly_fee = db.Column(db.Numeric(10, 2), default=0.00)
    is_occupied = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='unit', lazy=True)
    
    @property
    def unit_identifier(self):
        return f"{self.property.code}-{self.number}"
    
    def __repr__(self):
        return f'<Unit {self.unit_identifier}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_type = db.Column(db.String(50), nullable=False)  # maintenance, penalty, rent, other
    payment_method = db.Column(db.String(50), default='cash')  # cash, transfer, check, card
    payment_date = db.Column(db.Date, nullable=False, index=True)
    due_date = db.Column(db.Date)
    description = db.Column(db.Text)
    receipt_number = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(20), default='paid')  # paid, pending, overdue
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.receipt_number}>'

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # maintenance, cleaning, security, utilities, other
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False, index=True)
    vendor = db.Column(db.String(200))
    invoice_number = db.Column(db.String(100))
    payment_method = db.Column(db.String(50), default='cash')
    status = db.Column(db.String(20), default='paid')  # paid, pending, approved
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.description[:50]}>'

class MaintenanceTask(db.Model):
    __tablename__ = 'maintenance_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    task_type = db.Column(db.String(50), nullable=False)  # preventive, corrective, emergency
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    assigned_to = db.Column(db.String(200))  # Provider/technician name
    scheduled_date = db.Column(db.Date)
    completed_date = db.Column(db.Date)
    estimated_cost = db.Column(db.Numeric(10, 2))
    actual_cost = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MaintenanceTask {self.title}>'

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    document_type = db.Column(db.String(50), nullable=False)  # contract, act, regulation, plan, report, other
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    version = db.Column(db.String(20), default='1.0')
    is_public = db.Column(db.Boolean, default=False)  # Visible to all residents
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Document {self.title}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='info')  # info, warning, success, error, etc.
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    action_url = db.Column(db.String(500))  # URL opcional para acción
    expires_at = db.Column(db.DateTime)  # Fecha de expiración opcional
    extra_data = db.Column(db.Text)  # JSON con datos adicionales
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.title}>'

class Assembly(db.Model):
    __tablename__ = 'assemblies'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assembly_type = db.Column(db.String(50), default='ordinary')  # ordinary, extraordinary, emergency
    scheduled_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    agenda = db.Column(db.Text)
    minutes = db.Column(db.Text)  # Meeting minutes
    quorum_required = db.Column(db.Integer, default=50)  # Percentage
    quorum_achieved = db.Column(db.Integer)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed, cancelled
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Assembly {self.title}>'

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # maintenance, complaint, request, suggestion
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved, closed
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolution = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Ticket {self.title}>'

class VisitorLog(db.Model):
    __tablename__ = 'visitor_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    visitor_name = db.Column(db.String(200), nullable=False)
    visitor_id = db.Column(db.String(50))  # ID document number
    unit_visited = db.Column(db.String(20), nullable=False)
    purpose = db.Column(db.String(200))
    entry_time = db.Column(db.DateTime, nullable=False)
    exit_time = db.Column(db.DateTime)
    authorized_by = db.Column(db.String(200))  # Resident who authorized
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VisitorLog {self.visitor_name}>'

class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer)  # NULL for annual budget
    category = db.Column(db.String(100), nullable=False)
    budgeted_amount = db.Column(db.Numeric(10, 2), nullable=False)
    actual_amount = db.Column(db.Numeric(10, 2), default=0.00)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def variance(self):
        return self.actual_amount - self.budgeted_amount
    
    @property
    def variance_percentage(self):
        if self.budgeted_amount == 0:
            return 0
        return (self.variance / self.budgeted_amount) * 100
    
    def __repr__(self):
        return f'<Budget {self.category} {self.year}>'