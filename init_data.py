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

def load_initial_data():
    """Cargar datos iniciales para el sistema"""
    print("📊 Cargando datos iniciales...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar si ya hay datos
            if Property.query.count() > 0:
                print("✅ Ya existen datos en el sistema")
                return True
            
            # Obtener usuario administrador
            admin = User.query.filter_by(role='admin_general').first()
            if not admin:
                print("❌ No se encontró usuario administrador")
                return False
            
            # Crear propiedad de ejemplo
            property1 = Property(
                name='Torre Marina Bay',
                code='TMB-001',
                address='Avenida Balboa #500, Ciudad de Panamá',
                total_units=50,
                admin_id=admin.id,
                monthly_fee=Decimal('150.00'),
                is_active=True
            )
            db.session.add(property1)
            db.session.flush()
            
            # Crear unidades
            for i in range(1, 51):
                unit = Unit(
                    number=f"{i:02d}",
                    property_id=property1.id,
                    unit_type='apartment' if i <= 45 else 'parking',
                    area=Decimal('100.00') if i <= 45 else Decimal('12.00'),
                    monthly_fee=Decimal('150.00') if i <= 45 else Decimal('30.00'),
                    is_occupied=True if i <= 40 else False
                )
                db.session.add(unit)
            
            # Crear presupuesto anual
            current_year = datetime.now().year
            budget_categories = {
                'maintenance': 25000,
                'cleaning': 15000,
                'security': 30000,
                'utilities': 18000,
                'administration': 12000,
                'reserve': 10000
            }
            
            for category, amount in budget_categories.items():
                budget = Budget(
                    property_id=property1.id,
                    year=current_year,
                    category=category,
                    budgeted_amount=Decimal(str(amount)),
                    actual_amount=Decimal('0.00'),
                    description=f'Presupuesto anual {current_year} - {category}',
                    created_by=admin.id
                )
                db.session.add(budget)
            
            # Crear documentos legales
            legal_docs = [
                ('Reglamento Interno', 'regulation', 'Reglamento interno de la propiedad horizontal'),
                ('Ley 284 de Propiedad Horizontal', 'legal', 'Texto completo de la Ley 284'),
                ('Planos Arquitectónicos', 'plan', 'Planos arquitectónicos del edificio'),
                ('Manual de Convivencia', 'regulation', 'Normas de convivencia para residentes')
            ]
            
            for title, doc_type, desc in legal_docs:
                doc = Document(
                    property_id=property1.id,
                    title=title,
                    description=desc,
                    document_type=doc_type,
                    file_path=f'uploads/documents/{doc_type}_{title.lower().replace(" ", "_")}.pdf',
                    file_size=1024 * 10,
                    mime_type='application/pdf',
                    is_public=True,
                    uploaded_by=admin.id
                )
                db.session.add(doc)
            
            db.session.commit()
            print("✅ Datos iniciales cargados correctamente")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error cargando datos iniciales: {e}")
            return False

if __name__ == "__main__":
    success = load_initial_data()
    sys.exit(0 if success else 1)