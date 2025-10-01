import pytest
from flask import url_for
from models import Property, Unit, Payment, Expense
from datetime import datetime, timedelta
from decimal import Decimal

def test_financial_index_access(auth_client):
    """Probar acceso al índice financiero"""
    response = auth_client.get('/financial/')
    assert response.status_code == 200
    assert b'Resumen Financiero' in response.data

def test_payments_page_access(auth_client):
    """Probar acceso a la página de pagos"""
    response = auth_client.get('/financial/payments')
    assert response.status_code == 200
    assert b'Pagos' in response.data

def test_expenses_page_access(auth_client):
    """Probar acceso a la página de gastos"""
    response = auth_client.get('/financial/expenses')
    assert response.status_code == 200
    assert b'Gastos' in response.data

def test_reports_page_access(auth_client):
    """Probar acceso a la página de reportes"""
    response = auth_client.get('/financial/reports')
    assert response.status_code == 200
    assert b'Reportes Financieros' in response.data

def test_add_payment(auth_client, db):
    """Probar agregar un pago"""
    # Obtener una unidad de prueba
    unit = Unit.query.first()
    assert unit is not None
    
    # Datos del pago
    payment_data = {
        'unit_id': unit.id,
        'amount': 100.00,
        'payment_type': 'maintenance',
        'payment_method': 'cash',
        'payment_date': datetime.now().strftime('%Y-%m-%d'),
        'description': 'Pago de prueba'
    }
    
    # Enviar formulario
    response = auth_client.post('/financial/payments/add', 
                              data=payment_data, 
                              follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Pago registrado exitosamente' in response.data
    
    # Verificar que el pago se creó
    payment = Payment.query.filter_by(unit_id=unit.id, description='Pago de prueba').first()
    assert payment is not None
    assert float(payment.amount) == 100.00
    assert payment.payment_type == 'maintenance'

def test_add_expense(auth_client, db):
    """Probar agregar un gasto"""
    # Obtener una propiedad de prueba
    property_test = Property.query.first()
    assert property_test is not None
    
    # Datos del gasto
    expense_data = {
        'property_id': property_test.id,
        'category': 'maintenance',
        'description': 'Gasto de prueba',
        'amount': 150.00,
        'expense_date': datetime.now().strftime('%Y-%m-%d'),
        'vendor': 'Proveedor de prueba',
        'invoice_number': 'INV-TEST-001',
        'payment_method': 'transfer'
    }
    
    # Enviar formulario
    response = auth_client.post('/financial/expenses/add', 
                              data=expense_data, 
                              follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Gasto registrado exitosamente' in response.data
    
    # Verificar que el gasto se creó
    expense = Expense.query.filter_by(property_id=property_test.id, description='Gasto de prueba').first()
    assert expense is not None
    assert float(expense.amount) == 150.00
    assert expense.category == 'maintenance'

def test_income_statement_report(auth_client, db):
    """Probar generación de estado de resultados"""
    # Obtener una propiedad de prueba
    property_test = Property.query.first()
    assert property_test is not None
    
    # Crear algunos pagos y gastos para el reporte
    create_test_financial_data(db, property_test.id)
    
    # Acceder al reporte
    response = auth_client.get(f'/financial/reports/income-statement?property_id={property_test.id}')
    
    assert response.status_code == 200
    assert b'Estado de Resultados' in response.data

def test_get_units_api(auth_client, db):
    """Probar API para obtener unidades de una propiedad"""
    # Obtener una propiedad de prueba
    property_test = Property.query.first()
    assert property_test is not None
    
    # Acceder a la API
    response = auth_client.get(f'/financial/api/units/{property_test.id}')
    
    assert response.status_code == 200
    assert response.json is not None
    assert len(response.json) > 0
    
    # Verificar estructura de la respuesta
    unit = response.json[0]
    assert 'id' in unit
    assert 'number' in unit
    assert 'monthly_fee' in unit

def create_test_financial_data(db, property_id):
    """Crear datos financieros de prueba"""
    # Obtener unidades de la propiedad
    units = Unit.query.filter_by(property_id=property_id).all()
    
    if not units:
        return
    
    # Crear pagos
    for unit in units[:3]:  # Solo para algunas unidades
        payment = Payment(
            unit_id=unit.id,
            user_id=unit.owner_id if unit.owner_id else 1,
            amount=Decimal('100.00'),
            payment_type='maintenance',
            payment_method='cash',
            payment_date=datetime.now().date(),
            description='Pago de prueba para reporte',
            receipt_number=f'TEST-{unit.id}',
            status='paid'
        )
        db.session.add(payment)
    
    # Crear gastos
    categories = ['maintenance', 'cleaning', 'security']
    for i, category in enumerate(categories):
        expense = Expense(
            property_id=property_id,
            category=category,
            description=f'Gasto de {category} para reporte',
            amount=Decimal(str(50 * (i + 1))),
            expense_date=datetime.now().date(),
            vendor='Proveedor de prueba',
            invoice_number=f'TEST-EXP-{i+1}',
            payment_method='transfer',
            status='paid',
            created_by=1
        )
        db.session.add(expense)
    
    db.session.commit()