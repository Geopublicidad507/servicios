import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv
from flask import Flask
from models import db, User, Property, Unit, Payment, Expense, MaintenanceTask, Document, Notification, Assembly, Ticket, VisitorLog, Budget

# Cargar variables de entorno
load_dotenv()

def create_app():
    """Crear una instancia de la aplicación Flask para inicialización"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ph_control.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def initialize_system():
    """Inicializar el sistema con datos básicos"""
    print("🔧 Inicializando sistema...")
    
    app = create_app()
    
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()
        
        # Verificar si ya hay datos
        if User.query.count() > 1:
            print("✅ El sistema ya está inicializado")
            return True
        
        try:
            # Crear usuario administrador general
            admin = User.query.filter_by(email='admin@phcontrol.com').first()
            if not admin:
                admin = User(
                    email='admin@phcontrol.com',
                    first_name='Administrador',
                    last_name='General',
                    role='admin_general',
                    is_active=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()  # Commit para obtener el ID
                print("👤 Usuario administrador creado")
            
            # Crear datos de muestra si está habilitado
            if os.environ.get('CREATE_SAMPLE_DATA', 'false').lower() == 'true':
                create_sample_data(admin.id)
                print("📊 Datos de muestra creados")
            
            db.session.commit()
            print("✅ Sistema inicializado correctamente")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error inicializando el sistema: {e}")
            return False

def create_sample_data(admin_id):
    """Crear datos de muestra para el sistema"""
    # Crear administrador de PH
    admin_ph = User(
        email='adminph@phcontrol.com',
        first_name='Administrador',
        last_name='PH',
        role='admin_ph',
        is_active=True
    )
    admin_ph.set_password('admin123')
    db.session.add(admin_ph)
    db.session.flush()  # Para obtener el ID
    
    # Crear residente
    resident = User(
        email='residente@phcontrol.com',
        first_name='Usuario',
        last_name='Residente',
        phone='555-1234',
        role='resident',
        is_active=True
    )
    resident.set_password('resident123')
    db.session.add(resident)
    db.session.flush()  # Para obtener el ID
    
    # Crear proveedor
    provider = User(
        email='proveedor@phcontrol.com',
        first_name='Proveedor',
        last_name='Mantenimiento',
        phone='555-5678',
        role='provider',
        is_active=True
    )
    provider.set_password('provider123')
    db.session.add(provider)
    db.session.flush()  # Para obtener el ID
    
    # Crear propiedad
    property1 = Property(
        name='Edificio Modelo',
        code='EM-001',
        address='Calle Principal #123, Ciudad de Panamá',
        total_units=20,
        admin_id=admin_ph.id,  # Usar el ID del administrador de PH
        monthly_fee=Decimal('100.00'),
        is_active=True
    )
    db.session.add(property1)
    db.session.flush()  # Para obtener el ID
    
    # Crear unidades
    for i in range(1, 21):
        unit = Unit(
            number=f"{i:02d}",
            property_id=property1.id,
            owner_id=resident.id if i <= 3 else None,
            unit_type='apartment',
            area=Decimal('75.00'),
            monthly_fee=Decimal('100.00'),
            is_occupied=True if i <= 15 else False
        )
        db.session.add(unit)
    
    db.session.flush()
    
    # Obtener unidades para pagos
    units = Unit.query.filter_by(property_id=property1.id).all()
    
    # Crear pagos
    for month in range(1, 7):
        payment_date = datetime.now() - timedelta(days=30 * (6 - month))
        for unit in units[:15]:  # Solo unidades ocupadas
            payment = Payment(
                unit_id=unit.id,
                user_id=unit.owner_id or admin_ph.id,
                amount=unit.monthly_fee,
                payment_type='maintenance',
                payment_method='transfer',
                payment_date=payment_date.date(),
                description=f'Cuota de mantenimiento {payment_date.strftime("%B %Y")}',
                receipt_number=f'REC-{payment_date.year}-{month:02d}-{unit.number}',
                status='paid'
            )
            db.session.add(payment)
    
    # Crear pagos vencidos
    for unit in units[3:6]:
        payment = Payment(
            unit_id=unit.id,
            user_id=unit.owner_id or admin_ph.id,
            amount=unit.monthly_fee,
            payment_type='maintenance',
            payment_method='transfer',
            payment_date=datetime.now().date(),
            due_date=(datetime.now() - timedelta(days=15)).date(),
            description='Cuota de mantenimiento vencida',
            receipt_number=f'REC-{datetime.now().year}-LATE-{unit.number}',
            status='overdue'
        )
        db.session.add(payment)
    
    # Crear gastos
    expense_categories = ['maintenance', 'cleaning', 'security', 'utilities', 'other']
    for month in range(1, 7):
        expense_date = datetime.now() - timedelta(days=30 * (6 - month))
        for category in expense_categories:
            expense = Expense(
                property_id=property1.id,
                category=category,
                description=f'Gasto de {category} - {expense_date.strftime("%B %Y")}',
                amount=Decimal(str(50 + (month * 10))),
                expense_date=expense_date.date(),
                vendor='Proveedor Ejemplo',
                invoice_number=f'INV-{expense_date.year}-{month:02d}-{category[:3].upper()}',
                payment_method='transfer',
                status='paid',
                created_by=admin_ph.id
            )
            db.session.add(expense)
    
    # Crear tareas de mantenimiento
    task_types = ['preventive', 'corrective', 'emergency']
    task_statuses = ['pending', 'in_progress', 'completed']
    for i in range(10):
        task = MaintenanceTask(
            property_id=property1.id,
            title=f'Tarea de mantenimiento #{i+1}',
            description=f'Descripción de la tarea de mantenimiento #{i+1}',
            task_type=task_types[i % len(task_types)],
            priority='medium',
            status=task_statuses[i % len(task_statuses)],
            assigned_to='Técnico de Mantenimiento',
            scheduled_date=(datetime.now() + timedelta(days=i*3)).date(),
            estimated_cost=Decimal('100.00'),
            created_by=admin_ph.id
        )
        db.session.add(task)
    
    # Crear documentos
    doc_types = ['contract', 'act', 'regulation', 'plan', 'report']
    for i in range(5):
        doc = Document(
            property_id=property1.id,
            title=f'Documento {doc_types[i]}',
            description=f'Descripción del documento {doc_types[i]}',
            document_type=doc_types[i],
            file_path=f'uploads/documents/sample_{doc_types[i]}.pdf',
            file_size=1024 * (i+1),
            mime_type='application/pdf',
            is_public=True,
            uploaded_by=admin_ph.id
        )
        db.session.add(doc)
    
    # Crear notificaciones
    notification = Notification(
        user_id=resident.id,
        title='Bienvenido a PH Control',
        message='Gracias por usar nuestro sistema de gestión de propiedades horizontales.',
        notification_type='info',
        priority='normal',
        action_url='/dashboard/resident',
        is_read=False
    )
    db.session.add(notification)
    
    # Crear asamblea
    assembly = Assembly(
        property_id=property1.id,
        title='Asamblea Ordinaria Anual',
        description='Asamblea ordinaria para discutir presupuesto y elección de junta directiva',
        assembly_type='ordinary',
        scheduled_date=datetime.now() + timedelta(days=30),
        location='Salón de eventos del edificio',
        agenda='1. Apertura\n2. Informe financiero\n3. Elección de junta directiva\n4. Cierre',
        quorum_required=50,
        status='scheduled',
        created_by=admin_ph.id
    )
    db.session.add(assembly)
    
    # Crear tickets
    ticket_categories = ['maintenance', 'complaint', 'request', 'suggestion']
    for i in range(5):
        ticket = Ticket(
            user_id=resident.id,
            title=f'Ticket #{i+1}',
            description=f'Descripción del ticket #{i+1}',
            category=ticket_categories[i % len(ticket_categories)],
            priority='medium',
            status='open' if i < 3 else 'resolved',
            assigned_to=admin_ph.id if i < 3 else None,
            resolution='Problema resuelto' if i >= 3 else None
        )
        db.session.add(ticket)
    
    # Crear registro de visitantes
    visitor = VisitorLog(
        visitor_name='Juan Pérez',
        visitor_id='8-123-456',
        unit_visited='01',
        purpose='Visita social',
        entry_time=datetime.now() - timedelta(hours=3),
        exit_time=datetime.now() - timedelta(hours=1),
        authorized_by='Propietario Unidad 01',
        notes='Visita registrada correctamente'
    )
    db.session.add(visitor)
    
    # Crear presupuesto
    current_year = datetime.now().year
    budget_categories = ['maintenance', 'cleaning', 'security', 'utilities', 'administration', 'reserve']
    for category in budget_categories:
        budget = Budget(
            property_id=property1.id,
            year=current_year,
            category=category,
            budgeted_amount=Decimal('1200.00'),
            actual_amount=Decimal('600.00'),
            description=f'Presupuesto anual para {category}',
            created_by=admin_ph.id
        )
        db.session.add(budget)

if __name__ == "__main__":
    success = initialize_system()
    sys.exit(0 if success else 1)