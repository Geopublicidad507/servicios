import pytest
from models import User, Property, Unit, Payment, Expense, MaintenanceTask, Document, Notification, Assembly, Ticket, VisitorLog, Budget
from datetime import datetime, timedelta
from decimal import Decimal

def test_user_model(db):
    """Probar modelo de Usuario"""
    # Crear usuario
    user = User(
        email='test_model@phcontrol.com',
        first_name='Test',
        last_name='Model',
        phone='555-1234',
        role='resident',
        is_active=True
    )
    user.set_password('password123')
    
    db.session.add(user)
    db.session.commit()
    
    # Recuperar usuario
    saved_user = User.query.filter_by(email='test_model@phcontrol.com').first()
    
    assert saved_user is not None
    assert saved_user.email == 'test_model@phcontrol.com'
    assert saved_user.first_name == 'Test'
    assert saved_user.last_name == 'Model'
    assert saved_user.full_name == 'Test Model'
    assert saved_user.role == 'resident'
    assert saved_user.is_active is True
    assert saved_user.check_password('password123') is True
    assert saved_user.check_password('wrongpassword') is False

def test_property_model(db):
    """Probar modelo de Propiedad"""
    # Obtener un administrador
    admin = User.query.filter_by(role='admin_general').first()
    assert admin is not None
    
    # Crear propiedad
    property_obj = Property(
        name='Propiedad Modelo Test',
        code='PMT-001',
        address='Dirección de prueba para modelo',
        total_units=15,
        admin_id=admin.id,
        monthly_fee=Decimal('120.00'),
        is_active=True
    )
    
    db.session.add(property_obj)
    db.session.commit()
    
    # Recuperar propiedad
    saved_property = Property.query.filter_by(code='PMT-001').first()
    
    assert saved_property is not None
    assert saved_property.name == 'Propiedad Modelo Test'
    assert saved_property.code == 'PMT-001'
    assert saved_property.total_units == 15
    assert float(saved_property.monthly_fee) == 120.00
    assert saved_property.is_active is True

def test_unit_model(db):
    """Probar modelo de Unidad"""
    # Obtener una propiedad
    property_obj = Property.query.first()
    assert property_obj is not None
    
    # Obtener un propietario
    owner = User.query.filter_by(role='resident').first()
    assert owner is not None
    
    # Crear unidad
    unit = Unit(
        number='T01',
        property_id=property_obj.id,
        owner_id=owner.id,
        unit_type='apartment',
        area=Decimal('85.50'),
        monthly_fee=Decimal('130.00'),
        is_occupied=True
    )
    
    db.session.add(unit)
    db.session.commit()
    
    # Recuperar unidad
    saved_unit = Unit.query.filter_by(number='T01', property_id=property_obj.id).first()
    
    assert saved_unit is not None
    assert saved_unit.number == 'T01'
    assert saved_unit.property_id == property_obj.id
    assert saved_unit.owner_id == owner.id
    assert saved_unit.unit_type == 'apartment'
    assert float(saved_unit.area) == 85.50
    assert float(saved_unit.monthly_fee) == 130.00
    assert saved_unit.is_occupied is True
    assert saved_unit.unit_identifier == f"{property_obj.code}-T01"

def test_payment_model(db):
    """Probar modelo de Pago"""
    # Obtener una unidad
    unit = Unit.query.first()
    assert unit is not None
    
    # Obtener un usuario
    user = User.query.first()
    assert user is not None
    
    # Crear pago
    payment = Payment(
        unit_id=unit.id,
        user_id=user.id,
        amount=Decimal('100.00'),
        payment_type='maintenance',
        payment_method='transfer',
        payment_date=datetime.now().date(),
        description='Pago de prueba para modelo',
        receipt_number='REC-TEST-001',
        status='paid'
    )
    
    db.session.add(payment)
    db.session.commit()
    
    # Recuperar pago
    saved_payment = Payment.query.filter_by(receipt_number='REC-TEST-001').first()
    
    assert saved_payment is not None
    assert saved_payment.unit_id == unit.id
    assert saved_payment.user_id == user.id
    assert float(saved_payment.amount) == 100.00
    assert saved_payment.payment_type == 'maintenance'
    assert saved_payment.payment_method == 'transfer'
    assert saved_payment.status == 'paid'

def test_expense_model(db):
    """Probar modelo de Gasto"""
    # Obtener una propiedad
    property_obj = Property.query.first()
    assert property_obj is not None
    
    # Obtener un usuario
    user = User.query.first()
    assert user is not None
    
    # Crear gasto
    expense = Expense(
        property_id=property_obj.id,
        category='maintenance',
        description='Gasto de prueba para modelo',
        amount=Decimal('150.00'),
        expense_date=datetime.now().date(),
        vendor='Proveedor Test',
        invoice_number='INV-TEST-001',
        payment_method='transfer',
        status='paid',
        created_by=user.id
    )
    
    db.session.add(expense)
    db.session.commit()
    
    # Recuperar gasto
    saved_expense = Expense.query.filter_by(invoice_number='INV-TEST-001').first()
    
    assert saved_expense is not None
    assert saved_expense.property_id == property_obj.id
    assert saved_expense.category == 'maintenance'
    assert float(saved_expense.amount) == 150.00
    assert saved_expense.vendor == 'Proveedor Test'
    assert saved_expense.status == 'paid'

def test_maintenance_task_model(db):
    """Probar modelo de Tarea de Mantenimiento"""
    # Obtener una propiedad
    property_obj = Property.query.first()
    assert property_obj is not None
    
    # Obtener un usuario
    user = User.query.first()
    assert user is not None
    
    # Crear tarea
    task = MaintenanceTask(
        property_id=property_obj.id,
        title='Tarea de prueba',
        description='Descripción de tarea de prueba',
        task_type='preventive',
        priority='medium',
        status='pending',
        assigned_to='Técnico de prueba',
        scheduled_date=(datetime.now() + timedelta(days=7)).date(),
        estimated_cost=Decimal('200.00'),
        created_by=user.id
    )
    
    db.session.add(task)
    db.session.commit()
    
    # Recuperar tarea
    saved_task = MaintenanceTask.query.filter_by(title='Tarea de prueba').first()
    
    assert saved_task is not None
    assert saved_task.property_id == property_obj.id
    assert saved_task.task_type == 'preventive'
    assert saved_task.priority == 'medium'
    assert saved_task.status == 'pending'
    assert saved_task.assigned_to == 'Técnico de prueba'
    assert float(saved_task.estimated_cost) == 200.00

def test_budget_model(db):
    """Probar modelo de Presupuesto"""
    # Obtener una propiedad
    property_obj = Property.query.first()
    assert property_obj is not None
    
    # Obtener un usuario
    user = User.query.first()
    assert user is not None
    
    # Crear presupuesto
    current_year = datetime.now().year
    budget = Budget(
        property_id=property_obj.id,
        year=current_year,
        category='maintenance',
        budgeted_amount=Decimal('1200.00'),
        actual_amount=Decimal('800.00'),
        description='Presupuesto de prueba',
        created_by=user.id
    )
    
    db.session.add(budget)
    db.session.commit()
    
    # Recuperar presupuesto
    saved_budget = Budget.query.filter_by(
        property_id=property_obj.id,
        year=current_year,
        category='maintenance'
    ).first()
    
    assert saved_budget is not None
    assert saved_budget.property_id == property_obj.id
    assert saved_budget.year == current_year
    assert float(saved_budget.budgeted_amount) == 1200.00
    assert float(saved_budget.actual_amount) == 800.00
    assert float(saved_budget.variance) == -400.00
    assert saved_budget.variance_percentage == -33.33333333333333