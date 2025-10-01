import pytest
from flask import url_for
from models import User, Property, Unit

def test_admin_dashboard_access(auth_client):
    """Probar acceso al dashboard administrativo"""
    response = auth_client.get('/dashboard/')
    assert response.status_code == 200
    assert b'Dashboard Administrativo' in response.data

def test_resident_dashboard_redirect(client, db):
    """Probar redirección de residente al dashboard de residentes"""
    # Iniciar sesión como residente
    client.post('/auth/login', data={
        'email': 'resident@phcontrol.com',
        'password': 'resident123'
    }, follow_redirects=True)
    
    # Intentar acceder al dashboard administrativo
    response = client.get('/dashboard/', follow_redirects=True)
    
    # Debería ser redirigido al dashboard de residentes
    assert response.status_code == 200
    assert b'Mi Dashboard' in response.data

def test_resident_dashboard_access(client, db):
    """Probar acceso al dashboard de residentes"""
    # Iniciar sesión como residente
    client.post('/auth/login', data={
        'email': 'resident@phcontrol.com',
        'password': 'resident123'
    }, follow_redirects=True)
    
    # Acceder al dashboard de residentes
    response = client.get('/dashboard/resident')
    
    assert response.status_code == 200
    assert b'Dashboard de Residente' in response.data or b'Mi Dashboard' in response.data

def test_dashboard_unauthenticated(client):
    """Probar acceso al dashboard sin autenticación"""
    response = client.get('/dashboard/', follow_redirects=True)
    
    # Debería ser redirigido a la página de login
    assert response.status_code == 200
    assert b'Iniciar Sesi' in response.data  # 'Iniciar Sesión' en UTF-8

def test_property_stats_api(auth_client, db):
    """Probar API de estadísticas de propiedad"""
    # Obtener una propiedad de prueba
    property_test = Property.query.filter_by(code='TEST-001').first()
    assert property_test is not None
    
    # Acceder a la API de estadísticas
    response = auth_client.get(f'/dashboard/api/stats/property/{property_test.id}')
    
    assert response.status_code == 200
    assert response.json is not None
    
    # Verificar estructura de la respuesta
    assert 'monthly_income' in response.json
    assert 'monthly_expenses' in response.json
    assert 'net_income' in response.json
    assert 'occupancy_rate' in response.json
    assert 'total_units' in response.json

def test_mark_notification_read(auth_client, db):
    """Probar marcar notificación como leída"""
    from models import Notification
    from datetime import datetime
    
    # Crear una notificación de prueba
    admin = User.query.filter_by(email='admin@phcontrol.com').first()
    notification = Notification(
        user_id=admin.id,
        title='Test Notification',
        message='This is a test notification',
        notification_type='info',
        is_read=False
    )
    db.session.add(notification)
    db.session.commit()
    
    # Marcar como leída
    response = auth_client.post(f'/dashboard/api/notifications/mark-read/{notification.id}')
    
    assert response.status_code == 200
    assert response.json['success'] is True
    
    # Verificar que se marcó como leída
    notification = Notification.query.get(notification.id)
    assert notification.is_read is True