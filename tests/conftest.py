import os
import pytest
from app import create_app
from models import db as _db, User, Property, Unit

@pytest.fixture(scope='session')
def app():
    """Crear instancia de la aplicación para pruebas"""
    # Configurar la aplicación para pruebas
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    os.environ['DATABASE_URL'] = 'postgresql://phcontrol:phcontrol123@ph-database:5432/phcontrol_test'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    app = create_app()
    
    # Configuración específica para pruebas
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'DEBUG': False,
        'SERVER_NAME': 'localhost.localdomain',
    })
    
    # Establecer contexto de aplicación
    with app.app_context():
        yield app

@pytest.fixture(scope='session')
def db(app):
    """Configurar la base de datos para pruebas"""
    with app.app_context():
        # Crear todas las tablas
        _db.create_all()
        
        # Crear datos de prueba
        create_test_data()
        
        yield _db
        
        # Limpiar después de las pruebas
        _db.session.remove()
        _db.drop_all()

@pytest.fixture(scope='function')
def session(db):
    """Crear una nueva sesión de base de datos para cada prueba"""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # Opciones para usar una sesión separada para cada prueba
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    
    # Establecer la sesión
    db.session = session
    
    yield session
    
    # Rollback y cerrar la sesión después de cada prueba
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture(scope='function')
def client(app):
    """Cliente de prueba para la aplicación Flask"""
    with app.test_client() as client:
        yield client

@pytest.fixture(scope='function')
def auth_client(app, client):
    """Cliente autenticado para pruebas"""
    with app.test_request_context():
        # Iniciar sesión
        client.post('/auth/login', data={
            'email': 'admin@phcontrol.com',
            'password': 'admin123'
        }, follow_redirects=True)
        
        yield client

def create_test_data():
    """Crear datos de prueba para las pruebas"""
    # Crear usuario administrador si no existe
    admin = User.query.filter_by(email='admin@phcontrol.com').first()
    if not admin:
        admin = User(
            email='admin@phcontrol.com',
            first_name='Admin',
            last_name='Test',
            role='admin_general'
        )
        admin.set_password('admin123')
        _db.session.add(admin)
    
    # Crear usuario residente si no existe
    resident = User.query.filter_by(email='resident@phcontrol.com').first()
    if not resident:
        resident = User(
            email='resident@phcontrol.com',
            first_name='Resident',
            last_name='Test',
            role='resident'
        )
        resident.set_password('resident123')
        _db.session.add(resident)
    
    # Crear propiedad de prueba si no existe
    property_test = Property.query.filter_by(code='TEST-001').first()
    if not property_test:
        property_test = Property(
            name='Propiedad Test',
            code='TEST-001',
            address='Dirección de prueba',
            total_units=10,
            admin_id=admin.id,
            monthly_fee=100.00,
            is_active=True
        )
        _db.session.add(property_test)
        _db.session.flush()  # Para obtener el ID
        
        # Crear unidades de prueba
        for i in range(1, 6):
            unit = Unit(
                number=f"{i:02d}",
                property_id=property_test.id,
                owner_id=resident.id if i <= 3 else None,
                unit_type='apartment',
                area=75.00,
                monthly_fee=100.00,
                is_occupied=True if i <= 3 else False
            )
            _db.session.add(unit)
    
    _db.session.commit()