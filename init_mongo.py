#!/usr/bin/env python3
"""
Script de inicialización para MongoDB - PH Control
Crea datos de ejemplo y usuario administrador
"""
import os
import sys
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models_mongo import init_mongo_db, User, Property, Unit, NotificationDoc, Expense, MaintenanceTask

def create_sample_data():
    """Crear datos de ejemplo en MongoDB"""
    from flask import Flask
    app = Flask(__name__)
    app.config['MONGO_URI'] = 'mongodb+srv://geopublicidad507_db_user:Cdeg14650641*@consultor351.yv7gbsp.mongodb.net/miDB?retryWrites=true&w=majority'
    init_mongo_db(app)

    with app.app_context():
        print("START Inicializando base de datos MongoDB...")

        # Verificar si ya existe el usuario admin
        try:
            admin = User.objects.get(email='admin@phcontrol.com')
            print("OK Usuario administrador ya existe")
        except User.DoesNotExist:
            # Crear usuario administrador
            admin = User(
                email='admin@phcontrol.com',
                first_name='Administrador',
                last_name='General',
                role='admin_general'
            )
            admin.set_password('admin123')
            admin.save()
            print("OK Usuario administrador creado: admin@phcontrol.com / admin123")

        # Crear propiedad de ejemplo
        try:
            property_obj = Property.objects.get(code='PH001')
            print("OK Propiedad de ejemplo ya existe")
        except Property.DoesNotExist:
            property_obj = Property(
                name='Residencial Los Cocos',
                code='PH001',
                address='Calle Principal 123, Ciudad de Panamá',
                total_units=50,
                admin_id=admin,
                monthly_fee=150.00
            )
            property_obj.save()
            print("OK Propiedad de ejemplo creada")

            # Crear unidades de ejemplo
            for i in range(1, 11):  # Crear 10 unidades de ejemplo
                unit = Unit(
                    number=f'10{i}',
                    property_id=property_obj,
                    owner_id=admin if i == 1 else None,  # Primera unidad pertenece al admin
                    unit_type='apartment',
                    area=75.5,
                    monthly_fee=150.00
                )
                unit.save()

            print("OK Unidades de ejemplo creadas")

        # Crear notificaciones de ejemplo
        if NotificationDoc.objects.count() == 0:
            notifications = [
                NotificationDoc(
                    user_id=admin,
                    title='Bienvenido a PH Control',
                    message='Su cuenta ha sido configurada correctamente. Explore las funciones del sistema.',
                    notification_type='success',
                    priority='normal'
                ),
                NotificationDoc(
                    user_id=admin,
                    title='Recordatorio de pago',
                    message='El pago de mantenimiento de enero vence en 5 días.',
                    notification_type='warning',
                    priority='high'
                ),
                NotificationDoc(
                    user_id=admin,
                    title='Nueva función disponible',
                    message='Ya puede gestionar gastos e ingresos desde el panel financiero.',
                    notification_type='info',
                    priority='low'
                )
            ]

            for notification in notifications:
                notification.save()

            print("OK Notificaciones de ejemplo creadas")

        # Crear gastos de ejemplo
        if Expense.objects.count() == 0:
            expenses = [
                Expense(
                    property_id=property_obj,
                    category='maintenance',
                    description='Reparación de ascensor',
                    amount=2500.00,
                    expense_date=datetime.now().date(),
                    vendor='Elevadores S.A.',
                    created_by=admin
                ),
                Expense(
                    property_id=property_obj,
                    category='cleaning',
                    description='Servicio de limpieza mensual',
                    amount=800.00,
                    expense_date=datetime.now().date(),
                    vendor='Limpieza Express',
                    created_by=admin
                )
            ]

            for expense in expenses:
                expense.save()

            print("OK Gastos de ejemplo creados")

        # Crear tareas de mantenimiento de ejemplo
        if MaintenanceTask.objects.count() == 0:
            tasks = [
                MaintenanceTask(
                    property_id=property_obj,
                    title='Revisión mensual de ascensores',
                    description='Inspección rutinaria de los 3 ascensores del edificio',
                    task_type='preventive',
                    priority='medium',
                    scheduled_date=datetime.now().date() + timedelta(days=7),
                    created_by=admin
                ),
                MaintenanceTask(
                    property_id=property_obj,
                    title='Reparar filtración en techo',
                    description='Arreglar gotera en el techo del pasillo del piso 5',
                    task_type='corrective',
                    priority='high',
                    scheduled_date=datetime.now().date() + timedelta(days=2),
                    created_by=admin
                )
            ]

            for task in tasks:
                task.save()

            print("OK Tareas de mantenimiento de ejemplo creadas")

        print("CELEBRATION Inicialización completada exitosamente!")
        print("Resumen:")
        print(f"   USER Usuarios: {User.objects.count()}")
        print(f"   BUILDING Propiedades: {Property.objects.count()}")
        print(f"   HOME Unidades: {Unit.objects.count()}")
        print(f"   BELL Notificaciones: {NotificationDoc.objects.count()}")
        print(f"   MONEY Gastos: {Expense.objects.count()}")
        print(f"   TOOL Tareas de mantenimiento: {MaintenanceTask.objects.count()}")

if __name__ == '__main__':
    create_sample_data()
