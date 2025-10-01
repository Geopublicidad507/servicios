"""
Modelos de datos para MongoDB usando MongoEngine
PH Control - Sistema de Gestión de Propiedades Horizontales
"""
from mongoengine import Document, EmbeddedDocument, fields, connect
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# Conectar a MongoDB
def init_mongo_db(app):
    """Inicializar conexión a MongoDB"""
    mongo_uri = app.config.get('MONGO_URI', 'mongodb+srv://geopublicidad507_db_user:Cdeg14650641*@consultor351.yv7gbsp.mongodb.net/miDB?retryWrites=true&w=majority')
    connect(host=mongo_uri, db='ph_control_db')

class User(Document, UserMixin):
    """Modelo de Usuario"""
    meta = {'collection': 'users'}

    email = fields.EmailField(required=True, unique=True)
    first_name = fields.StringField(required=True, max_length=80)
    last_name = fields.StringField(required=True, max_length=80)
    phone = fields.StringField(max_length=20)
    password_hash = fields.StringField(required=True, max_length=255)
    role = fields.StringField(required=True, default='resident',
                             choices=['admin_general', 'admin_ph', 'resident', 'provider', 'visitor'])
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    last_login = fields.DateTimeField()

    # Referencias a otros documentos (serán pobladas dinámicamente)
    property_ids = fields.ListField(fields.ReferenceField('Property'))
    unit_ids = fields.ListField(fields.ReferenceField('Unit'))
    payment_ids = fields.ListField(fields.ReferenceField('Payment'))
    ticket_ids = fields.ListField(fields.ReferenceField('Ticket'))
    assigned_ticket_ids = fields.ListField(fields.ReferenceField('Ticket'))
    notification_ids = fields.ListField(fields.ReferenceField('Notification'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f'<User {self.email}>'

class Property(Document):
    """Modelo de Propiedad Horizontal"""
    meta = {'collection': 'properties'}

    name = fields.StringField(required=True, max_length=200)
    code = fields.StringField(required=True, unique=True, max_length=20)
    address = fields.StringField(required=True)
    total_units = fields.IntField(required=True, min_value=1)
    admin_id = fields.ReferenceField(User, required=True)
    monthly_fee = fields.DecimalField(default=0.00, precision=2)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    is_active = fields.BooleanField(default=True)

    # Referencias
    unit_ids = fields.ListField(fields.ReferenceField('Unit'))
    expense_ids = fields.ListField(fields.ReferenceField('Expense'))
    maintenance_task_ids = fields.ListField(fields.ReferenceField('MaintenanceTask'))
    document_ids = fields.ListField(fields.ReferenceField('Document'))
    assembly_ids = fields.ListField(fields.ReferenceField('Assembly'))

    def __str__(self):
        return f'<Property {self.name}>'

class Unit(Document):
    """Modelo de Unidad"""
    meta = {'collection': 'units'}

    number = fields.StringField(required=True, max_length=20)
    property_id = fields.ReferenceField(Property, required=True)
    owner_id = fields.ReferenceField(User)
    unit_type = fields.StringField(default='apartment',
                                  choices=['apartment', 'parking', 'storage'])
    area = fields.DecimalField(precision=2)
    monthly_fee = fields.DecimalField(default=0.00, precision=2)
    is_occupied = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.utcnow)

    # Referencias
    payment_ids = fields.ListField(fields.ReferenceField('Payment'))

    @property
    def unit_identifier(self):
        return f"{self.property_id.code}-{self.number}"

    def __str__(self):
        return f'<Unit {self.unit_identifier}>'

class Payment(Document):
    """Modelo de Pago"""
    meta = {'collection': 'payments'}

    unit_id = fields.ReferenceField(Unit, required=True)
    user_id = fields.ReferenceField(User, required=True)
    amount = fields.DecimalField(required=True, precision=2)
    payment_type = fields.StringField(required=True,
                                     choices=['maintenance', 'penalty', 'rent', 'other'])
    payment_method = fields.StringField(default='cash',
                                       choices=['cash', 'transfer', 'check', 'card'])
    payment_date = fields.DateField(required=True)
    due_date = fields.DateField()
    description = fields.StringField()
    receipt_number = fields.StringField(unique=True)
    status = fields.StringField(default='paid',
                               choices=['paid', 'pending', 'overdue'])
    created_at = fields.DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return f'<Payment {self.receipt_number}>'

class Expense(Document):
    """Modelo de Gasto"""
    meta = {'collection': 'expenses'}

    property_id = fields.ReferenceField(Property, required=True)
    category = fields.StringField(required=True,
                                 choices=['maintenance', 'cleaning', 'security', 'utilities', 'other'])
    description = fields.StringField(required=True)
    amount = fields.DecimalField(required=True, precision=2)
    expense_date = fields.DateField(required=True)
    vendor = fields.StringField(max_length=200)
    invoice_number = fields.StringField(max_length=100)
    payment_method = fields.StringField(default='cash')
    status = fields.StringField(default='paid',
                               choices=['paid', 'pending', 'approved'])
    created_by = fields.ReferenceField(User)
    created_at = fields.DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return f'<Expense {self.description[:50]}>'

class MaintenanceTask(Document):
    """Modelo de Tarea de Mantenimiento"""
    meta = {'collection': 'maintenance_tasks'}

    property_id = fields.ReferenceField(Property, required=True)
    title = fields.StringField(required=True, max_length=200)
    description = fields.StringField()
    task_type = fields.StringField(required=True,
                                  choices=['preventive', 'corrective', 'emergency'])
    priority = fields.StringField(default='medium',
                                 choices=['low', 'medium', 'high', 'urgent'])
    status = fields.StringField(default='pending',
                               choices=['pending', 'in_progress', 'completed', 'cancelled'])
    assigned_to = fields.StringField(max_length=200)  # Provider/technician name
    scheduled_date = fields.DateField()
    completed_date = fields.DateField()
    estimated_cost = fields.DecimalField(precision=2)
    actual_cost = fields.DecimalField(precision=2)
    notes = fields.StringField()
    created_by = fields.ReferenceField(User)
    created_at = fields.DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return f'<MaintenanceTask {self.title}>'

class Document(Document):
    """Modelo de Documento"""
    meta = {'collection': 'documents'}

    property_id = fields.ReferenceField(Property, required=True)
    title = fields.StringField(required=True, max_length=200)
    description = fields.StringField()
    document_type = fields.StringField(required=True,
                                      choices=['contract', 'act', 'regulation', 'plan', 'report', 'other'])
    file_path = fields.StringField(required=True, max_length=500)
    file_size = fields.IntField()
    mime_type = fields.StringField(max_length=100)
    version = fields.StringField(default='1.0', max_length=20)
    is_public = fields.BooleanField(default=False)  # Visible to all residents
    uploaded_by = fields.ReferenceField(User)
    created_at = fields.DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return f'<Document {self.title}>'

class Notification(Document):
    """Modelo de Notificación"""
    meta = {'collection': 'notifications'}

    user_id = fields.ReferenceField(User, required=True)
    title = fields.StringField(required=True, max_length=200)
    message = fields.StringField(required=True)
    notification_type = fields.StringField(default='info',
                                          choices=['info', 'warning', 'success', 'error'])
    priority = fields.StringField(default='normal',
                                 choices=['low', 'normal', 'high', 'urgent'])
    action_url = fields.StringField(max_length=500)  # URL opcional para acción
    expires_at = fields.DateTimeField()  # Fecha de expiración opcional
    extra_data = fields.DictField()  # JSON con datos adicionales
    is_read = fields.BooleanField(default=False)
    read_at = fields.DateTimeField()
    email_sent = fields.BooleanField(default=False)
    email_sent_at = fields.DateTimeField()
    created_at = fields.DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return f'<Notification {self.title}>'

class Assembly(Document):
    """Modelo de Asamblea"""
    meta = {'collection': 'assemblies'}

    property_id = fields.ReferenceField(Property, required=True)
    title = fields.StringField(required=True, max_length=200)
    description = fields.StringField()
    assembly_type = fields.StringField(default='ordinary',
                                      choices=['ordinary', 'extraordinary', 'emergency'])
    scheduled_date = fields.DateTimeField(required=True)
    location = fields.StringField(max_length=200)
    agenda = fields.StringField()
    minutes = fields.StringField()  # Meeting minutes
    quorum_required = fields.IntField(default=50)  # Percentage
    quorum_achieved = fields.IntField()
    status = fields.StringField(default='scheduled',
                               choices=['scheduled', 'in_progress', 'completed', 'cancelled'])
    created_by = fields.ReferenceField(User)
    created_at = fields.DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return f'<Assembly {self.title}>'

class Ticket(Document):
    """Modelo de Ticket/Solicitud"""
    meta = {'collection': 'tickets'}

    user_id = fields.ReferenceField(User, required=True)
    title = fields.StringField(required=True, max_length=200)
    description = fields.StringField(required=True)
    category = fields.StringField(required=True,
                                 choices=['maintenance', 'complaint', 'request', 'suggestion'])
    priority = fields.StringField(default='medium',
                                 choices=['low', 'medium', 'high', 'urgent'])
    status = fields.StringField(default='open',
                               choices=['open', 'in_progress', 'resolved', 'closed'])
    assigned_to = fields.ReferenceField(User)
    resolution = fields.StringField()
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return f'<Ticket {self.title}>'

class VisitorLog(Document):
    """Modelo de Registro de Visitantes"""
    meta = {'collection': 'visitor_logs'}

    visitor_name = fields.StringField(required=True, max_length=200)
    visitor_id = fields.StringField(max_length=50)  # ID document number
    unit_visited = fields.StringField(required=True, max_length=20)
    purpose = fields.StringField(max_length=200)
    entry_time = fields.DateTimeField(required=True)
    exit_time = fields.DateTimeField()
    authorized_by = fields.StringField(max_length=200)  # Resident who authorized
    notes = fields.StringField()
    created_at = fields.DateTimeField(default=datetime.utcnow)

    def __str__(self):
        return f'<VisitorLog {self.visitor_name}>'

class Budget(Document):
    """Modelo de Presupuesto"""
    meta = {'collection': 'budgets'}

    property_id = fields.ReferenceField(Property, required=True)
    year = fields.IntField(required=True)
    month = fields.IntField()  # NULL for annual budget
    category = fields.StringField(required=True, max_length=100)
    budgeted_amount = fields.DecimalField(required=True, precision=2)
    actual_amount = fields.DecimalField(default=0.00, precision=2)
    description = fields.StringField()
    created_by = fields.ReferenceField(User)
    created_at = fields.DateTimeField(default=datetime.utcnow)

    @property
    def variance(self):
        return float(self.actual_amount - self.budgeted_amount)

    @property
    def variance_percentage(self):
        if self.budgeted_amount == 0:
            return 0
        return (self.variance / float(self.budgeted_amount)) * 100

    def __str__(self):
        return f'<Budget {self.category} {self.year}>'