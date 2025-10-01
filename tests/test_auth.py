import pytest
from flask import url_for
from models import User

def test_login_page(client):
    """Probar que la página de login se carga correctamente"""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Iniciar Sesi' in response.data  # 'Iniciar Sesión' en UTF-8

def test_login_success(client, db):
    """Probar login exitoso"""
    response = client.post('/auth/login', data={
        'email': 'admin@phcontrol.com',
        'password': 'admin123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Dashboard' in response.data

def test_login_invalid_credentials(client):
    """Probar login con credenciales inválidas"""
    response = client.post('/auth/login', data={
        'email': 'admin@phcontrol.com',
        'password': 'wrong_password'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Credenciales inv' in response.data  # 'Credenciales inválidas' en UTF-8

def test_logout(auth_client):
    """Probar logout"""
    response = auth_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Iniciar Sesi' in response.data  # 'Iniciar Sesión' en UTF-8

def test_register_page(client):
    """Probar que la página de registro se carga correctamente"""
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b'Registro' in response.data

def test_register_user(client, db):
    """Probar registro de usuario"""
    # Verificar que el usuario no existe
    user = User.query.filter_by(email='nuevo@phcontrol.com').first()
    if user:
        db.session.delete(user)
        db.session.commit()
    
    response = client.post('/auth/register', data={
        'email': 'nuevo@phcontrol.com',
        'first_name': 'Nuevo',
        'last_name': 'Usuario',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verificar que el usuario fue creado
    user = User.query.filter_by(email='nuevo@phcontrol.com').first()
    assert user is not None
    assert user.first_name == 'Nuevo'
    assert user.last_name == 'Usuario'
    assert user.role == 'resident'  # Rol por defecto

def test_profile_page(auth_client):
    """Probar que la página de perfil se carga correctamente"""
    response = auth_client.get('/auth/profile')
    assert response.status_code == 200
    assert b'Perfil' in response.data

def test_change_password(auth_client, db):
    """Probar cambio de contraseña"""
    # Obtener usuario
    user = User.query.filter_by(email='admin@phcontrol.com').first()
    old_password_hash = user.password_hash
    
    response = auth_client.post('/auth/change_password', data={
        'current_password': 'admin123',
        'new_password': 'newpassword123',
        'confirm_password': 'newpassword123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verificar que la contraseña cambió
    user = User.query.filter_by(email='admin@phcontrol.com').first()
    assert user.password_hash != old_password_hash
    
    # Restaurar contraseña original
    user.set_password('admin123')
    db.session.commit()