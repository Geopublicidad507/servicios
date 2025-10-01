"""
Sistema de reportes avanzado para PH Control
"""
import io
import csv
from datetime import datetime, timedelta
from flask import current_app
from models import db, Property, Unit, User, Payment, Expense, MaintenanceTask, Ticket, Notification
from sqlalchemy import func, and_, or_
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64


class ReportGenerator:
    """Generador de reportes del sistema."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12
        )
    
    def generate_financial_report(self, property_id=None, start_date=None, end_date=None, format='pdf'):
        """
        Generar reporte financiero.
        
        Args:
            property_id: ID de la propiedad (None para todas)
            start_date: Fecha de inicio
            end_date: Fecha de fin
            format: Formato del reporte ('pdf', 'csv', 'json')
        
        Returns:
            BytesIO: Buffer con el reporte generado
        """
        try:
            # Configurar fechas por defecto
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Obtener datos financieros
            data = self._get_financial_data(property_id, start_date, end_date)
            
            if format == 'pdf':
                return self._generate_financial_pdf(data, start_date, end_date)
            elif format == 'csv':
                return self._generate_financial_csv(data)
            elif format == 'json':
                return self._generate_financial_json(data)
            else:
                raise ValueError(f"Formato no soportado: {format}")
                
        except Exception as e:
            current_app.logger.error(f"Error generating financial report: {str(e)}")
            raise
    
    def generate_maintenance_report(self, property_id=None, start_date=None, end_date=None, format='pdf'):
        """Generar reporte de mantenimiento."""
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            data = self._get_maintenance_data(property_id, start_date, end_date)
            
            if format == 'pdf':
                return self._generate_maintenance_pdf(data, start_date, end_date)
            elif format == 'csv':
                return self._generate_maintenance_csv(data)
            elif format == 'json':
                return self._generate_maintenance_json(data)
            else:
                raise ValueError(f"Formato no soportado: {format}")
                
        except Exception as e:
            current_app.logger.error(f"Error generating maintenance report: {str(e)}")
            raise
    
    def generate_occupancy_report(self, property_id=None, format='pdf'):
        """Generar reporte de ocupación."""
        try:
            data = self._get_occupancy_data(property_id)
            
            if format == 'pdf':
                return self._generate_occupancy_pdf(data)
            elif format == 'csv':
                return self._generate_occupancy_csv(data)
            elif format == 'json':
                return self._generate_occupancy_json(data)
            else:
                raise ValueError(f"Formato no soportado: {format}")
                
        except Exception as e:
            current_app.logger.error(f"Error generating occupancy report: {str(e)}")
            raise
    
    def generate_payment_status_report(self, property_id=None, format='pdf'):
        """Generar reporte de estado de pagos."""
        try:
            data = self._get_payment_status_data(property_id)
            
            if format == 'pdf':
                return self._generate_payment_status_pdf(data)
            elif format == 'csv':
                return self._generate_payment_status_csv(data)
            elif format == 'json':
                return self._generate_payment_status_json(data)
            else:
                raise ValueError(f"Formato no soportado: {format}")
                
        except Exception as e:
            current_app.logger.error(f"Error generating payment status report: {str(e)}")
            raise
    
    def _get_financial_data(self, property_id, start_date, end_date):
        """Obtener datos financieros."""
        # Query base para pagos
        payments_query = Payment.query.filter(
            Payment.payment_date.between(start_date, end_date)
        )
        
        # Query base para gastos
        expenses_query = Expense.query.filter(
            Expense.expense_date.between(start_date, end_date)
        )
        
        if property_id:
            payments_query = payments_query.join(Unit).filter(Unit.property_id == property_id)
            expenses_query = expenses_query.filter(Expense.property_id == property_id)
        
        # Obtener datos
        payments = payments_query.all()
        expenses = expenses_query.all()
        
        # Calcular totales
        total_income = sum(p.amount for p in payments)
        total_expenses = sum(e.amount for e in expenses)
        net_income = total_income - total_expenses
        
        # Ingresos por mes
        income_by_month = db.session.query(
            func.date_trunc('month', Payment.payment_date).label('month'),
            func.sum(Payment.amount).label('total')
        ).filter(
            Payment.payment_date.between(start_date, end_date)
        ).group_by(func.date_trunc('month', Payment.payment_date)).all()
        
        # Gastos por categoría
        expenses_by_category = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.expense_date.between(start_date, end_date)
        ).group_by(Expense.category).all()
        
        return {
            'summary': {
                'total_income': float(total_income),
                'total_expenses': float(total_expenses),
                'net_income': float(net_income),
                'period': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
            },
            'payments': payments,
            'expenses': expenses,
            'income_by_month': income_by_month,
            'expenses_by_category': expenses_by_category
        }
    
    def _get_maintenance_data(self, property_id, start_date, end_date):
        """Obtener datos de mantenimiento."""
        query = MaintenanceTask.query.filter(
            MaintenanceTask.created_at.between(start_date, end_date)
        )
        
        if property_id:
            query = query.filter(MaintenanceTask.property_id == property_id)
        
        tasks = query.all()
        
        # Estadísticas
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == 'completed'])
        pending_tasks = len([t for t in tasks if t.status in ['pending', 'in_progress']])
        
        # Tareas por estado
        tasks_by_status = db.session.query(
            MaintenanceTask.status,
            func.count(MaintenanceTask.id).label('count')
        ).filter(
            MaintenanceTask.created_at.between(start_date, end_date)
        ).group_by(MaintenanceTask.status).all()
        
        # Tareas por categoría
        tasks_by_category = db.session.query(
            MaintenanceTask.category,
            func.count(MaintenanceTask.id).label('count')
        ).filter(
            MaintenanceTask.created_at.between(start_date, end_date)
        ).group_by(MaintenanceTask.category).all()
        
        return {
            'summary': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'pending_tasks': pending_tasks,
                'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                'period': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
            },
            'tasks': tasks,
            'tasks_by_status': tasks_by_status,
            'tasks_by_category': tasks_by_category
        }
    
    def _get_occupancy_data(self, property_id):
        """Obtener datos de ocupación."""
        query = Unit.query
        
        if property_id:
            query = query.filter(Unit.property_id == property_id)
        
        units = query.all()
        
        total_units = len(units)
        occupied_units = len([u for u in units if u.owner_id is not None])
        vacant_units = total_units - occupied_units
        
        occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
        
        # Ocupación por propiedad
        occupancy_by_property = db.session.query(
            Property.name,
            func.count(Unit.id).label('total_units'),
            func.count(Unit.owner_id).label('occupied_units')
        ).join(Unit).group_by(Property.id, Property.name).all()
        
        return {
            'summary': {
                'total_units': total_units,
                'occupied_units': occupied_units,
                'vacant_units': vacant_units,
                'occupancy_rate': occupancy_rate
            },
            'units': units,
            'occupancy_by_property': occupancy_by_property
        }
    
    def _get_payment_status_data(self, property_id):
        """Obtener datos de estado de pagos."""
        current_month = datetime.utcnow().replace(day=1)
        
        query = Unit.query
        if property_id:
            query = query.filter(Unit.property_id == property_id)
        
        units = query.all()
        
        payment_status = []
        for unit in units:
            if unit.owner:
                # Verificar pagos del mes actual
                current_payment = Payment.query.filter(
                    Payment.unit_id == unit.id,
                    Payment.payment_date >= current_month
                ).first()
                
                status = 'paid' if current_payment else 'pending'
                
                payment_status.append({
                    'unit': unit,
                    'owner': unit.owner,
                    'status': status,
                    'amount_due': unit.monthly_fee,
                    'last_payment': Payment.query.filter_by(unit_id=unit.id).order_by(Payment.payment_date.desc()).first()
                })
        
        # Estadísticas
        total_units = len(payment_status)
        paid_units = len([p for p in payment_status if p['status'] == 'paid'])
        pending_units = total_units - paid_units
        
        return {
            'summary': {
                'total_units': total_units,
                'paid_units': paid_units,
                'pending_units': pending_units,
                'collection_rate': (paid_units / total_units * 100) if total_units > 0 else 0,
                'month': current_month.strftime('%B %Y')
            },
            'payment_status': payment_status
        }
    
    def _generate_financial_pdf(self, data, start_date, end_date):
        """Generar PDF del reporte financiero."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Título
        title = Paragraph("Reporte Financiero", self.title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Período
        period = Paragraph(f"Período: {data['summary']['period']}", self.styles['Normal'])
        story.append(period)
        story.append(Spacer(1, 12))
        
        # Resumen
        summary_data = [
            ['Concepto', 'Monto'],
            ['Ingresos Totales', f"${data['summary']['total_income']:,.2f}"],
            ['Gastos Totales', f"${data['summary']['total_expenses']:,.2f}"],
            ['Ingreso Neto', f"${data['summary']['net_income']:,.2f}"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Detalle de pagos
        if data['payments']:
            story.append(Paragraph("Detalle de Ingresos", self.heading_style))
            
            payments_data = [['Fecha', 'Unidad', 'Concepto', 'Monto']]
            for payment in data['payments'][:20]:  # Limitar a 20 registros
                payments_data.append([
                    payment.payment_date.strftime('%d/%m/%Y'),
                    payment.unit.unit_number if payment.unit else 'N/A',
                    payment.concept,
                    f"${payment.amount:,.2f}"
                ])
            
            payments_table = Table(payments_data)
            payments_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(payments_table)
            story.append(Spacer(1, 20))
        
        # Detalle de gastos
        if data['expenses']:
            story.append(Paragraph("Detalle de Gastos", self.heading_style))
            
            expenses_data = [['Fecha', 'Categoría', 'Descripción', 'Monto']]
            for expense in data['expenses'][:20]:  # Limitar a 20 registros
                expenses_data.append([
                    expense.expense_date.strftime('%d/%m/%Y'),
                    expense.category,
                    expense.description[:30] + '...' if len(expense.description) > 30 else expense.description,
                    f"${expense.amount:,.2f}"
                ])
            
            expenses_table = Table(expenses_data)
            expenses_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(expenses_table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _generate_financial_csv(self, data):
        """Generar CSV del reporte financiero."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        # Resumen
        writer.writerow(['RESUMEN FINANCIERO'])
        writer.writerow(['Concepto', 'Monto'])
        writer.writerow(['Ingresos Totales', data['summary']['total_income']])
        writer.writerow(['Gastos Totales', data['summary']['total_expenses']])
        writer.writerow(['Ingreso Neto', data['summary']['net_income']])
        writer.writerow([])
        
        # Pagos
        writer.writerow(['DETALLE DE INGRESOS'])
        writer.writerow(['Fecha', 'Unidad', 'Concepto', 'Monto'])
        for payment in data['payments']:
            writer.writerow([
                payment.payment_date.strftime('%d/%m/%Y'),
                payment.unit.unit_number if payment.unit else 'N/A',
                payment.concept,
                payment.amount
            ])
        
        writer.writerow([])
        
        # Gastos
        writer.writerow(['DETALLE DE GASTOS'])
        writer.writerow(['Fecha', 'Categoría', 'Descripción', 'Monto'])
        for expense in data['expenses']:
            writer.writerow([
                expense.expense_date.strftime('%d/%m/%Y'),
                expense.category,
                expense.description,
                expense.amount
            ])
        
        output = io.BytesIO()
        output.write(buffer.getvalue().encode('utf-8'))
        output.seek(0)
        return output
    
    def _generate_financial_json(self, data):
        """Generar JSON del reporte financiero."""
        # Convertir objetos SQLAlchemy a diccionarios
        payments_data = []
        for payment in data['payments']:
            payments_data.append({
                'date': payment.payment_date.isoformat(),
                'unit': payment.unit.unit_number if payment.unit else None,
                'concept': payment.concept,
                'amount': float(payment.amount)
            })
        
        expenses_data = []
        for expense in data['expenses']:
            expenses_data.append({
                'date': expense.expense_date.isoformat(),
                'category': expense.category,
                'description': expense.description,
                'amount': float(expense.amount)
            })
        
        report_data = {
            'summary': data['summary'],
            'payments': payments_data,
            'expenses': expenses_data,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        output = io.BytesIO()
        output.write(json.dumps(report_data, indent=2).encode('utf-8'))
        output.seek(0)
        return output
    
    def _generate_maintenance_pdf(self, data, start_date, end_date):
        """Generar PDF del reporte de mantenimiento."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Título
        title = Paragraph("Reporte de Mantenimiento", self.title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Período
        period = Paragraph(f"Período: {data['summary']['period']}", self.styles['Normal'])
        story.append(period)
        story.append(Spacer(1, 12))
        
        # Resumen
        summary_data = [
            ['Concepto', 'Cantidad'],
            ['Total de Tareas', data['summary']['total_tasks']],
            ['Tareas Completadas', data['summary']['completed_tasks']],
            ['Tareas Pendientes', data['summary']['pending_tasks']],
            ['Tasa de Completitud', f"{data['summary']['completion_rate']:.1f}%"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Detalle de tareas
        if data['tasks']:
            story.append(Paragraph("Detalle de Tareas", self.heading_style))
            
            tasks_data = [['Fecha', 'Título', 'Categoría', 'Estado', 'Prioridad']]
            for task in data['tasks'][:20]:  # Limitar a 20 registros
                tasks_data.append([
                    task.created_at.strftime('%d/%m/%Y'),
                    task.title[:30] + '...' if len(task.title) > 30 else task.title,
                    task.category,
                    task.status,
                    task.priority
                ])
            
            tasks_table = Table(tasks_data)
            tasks_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(tasks_table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _generate_maintenance_csv(self, data):
        """Generar CSV del reporte de mantenimiento."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        # Resumen
        writer.writerow(['RESUMEN DE MANTENIMIENTO'])
        writer.writerow(['Concepto', 'Cantidad'])
        writer.writerow(['Total de Tareas', data['summary']['total_tasks']])
        writer.writerow(['Tareas Completadas', data['summary']['completed_tasks']])
        writer.writerow(['Tareas Pendientes', data['summary']['pending_tasks']])
        writer.writerow(['Tasa de Completitud (%)', data['summary']['completion_rate']])
        writer.writerow([])
        
        # Detalle de tareas
        writer.writerow(['DETALLE DE TAREAS'])
        writer.writerow(['Fecha', 'Título', 'Descripción', 'Categoría', 'Estado', 'Prioridad'])
        for task in data['tasks']:
            writer.writerow([
                task.created_at.strftime('%d/%m/%Y'),
                task.title,
                task.description,
                task.category,
                task.status,
                task.priority
            ])
        
        output = io.BytesIO()
        output.write(buffer.getvalue().encode('utf-8'))
        output.seek(0)
        return output
    
    def _generate_maintenance_json(self, data):
        """Generar JSON del reporte de mantenimiento."""
        tasks_data = []
        for task in data['tasks']:
            tasks_data.append({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'category': task.category,
                'status': task.status,
                'priority': task.priority,
                'created_at': task.created_at.isoformat(),
                'scheduled_date': task.scheduled_date.isoformat() if task.scheduled_date else None,
                'completed_date': task.completed_date.isoformat() if task.completed_date else None
            })
        
        report_data = {
            'summary': data['summary'],
            'tasks': tasks_data,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        output = io.BytesIO()
        output.write(json.dumps(report_data, indent=2).encode('utf-8'))
        output.seek(0)
        return output
    
    def _generate_occupancy_pdf(self, data):
        """Generar PDF del reporte de ocupación."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Título
        title = Paragraph("Reporte de Ocupación", self.title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Resumen
        summary_data = [
            ['Concepto', 'Cantidad'],
            ['Total de Unidades', data['summary']['total_units']],
            ['Unidades Ocupadas', data['summary']['occupied_units']],
            ['Unidades Vacantes', data['summary']['vacant_units']],
            ['Tasa de Ocupación', f"{data['summary']['occupancy_rate']:.1f}%"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Detalle por propiedad
        if data['occupancy_by_property']:
            story.append(Paragraph("Ocupación por Propiedad", self.heading_style))
            
            property_data = [['Propiedad', 'Total Unidades', 'Unidades Ocupadas', 'Tasa de Ocupación']]
            for prop in data['occupancy_by_property']:
                occupancy_rate = (prop.occupied_units / prop.total_units * 100) if prop.total_units > 0 else 0
                property_data.append([
                    prop.name,
                    str(prop.total_units),
                    str(prop.occupied_units),
                    f"{occupancy_rate:.1f}%"
                ])
            
            property_table = Table(property_data)
            property_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(property_table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _generate_occupancy_csv(self, data):
        """Generar CSV del reporte de ocupación."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        # Resumen
        writer.writerow(['RESUMEN DE OCUPACIÓN'])
        writer.writerow(['Concepto', 'Cantidad'])
        writer.writerow(['Total de Unidades', data['summary']['total_units']])
        writer.writerow(['Unidades Ocupadas', data['summary']['occupied_units']])
        writer.writerow(['Unidades Vacantes', data['summary']['vacant_units']])
        writer.writerow(['Tasa de Ocupación (%)', data['summary']['occupancy_rate']])
        writer.writerow([])
        
        # Detalle por unidad
        writer.writerow(['DETALLE POR UNIDAD'])
        writer.writerow(['Propiedad', 'Unidad', 'Propietario', 'Estado'])
        for unit in data['units']:
            writer.writerow([
                unit.property.name if unit.property else 'N/A',
                unit.unit_number,
                unit.owner.full_name if unit.owner else 'Vacante',
                'Ocupada' if unit.owner else 'Vacante'
            ])
        
        output = io.BytesIO()
        output.write(buffer.getvalue().encode('utf-8'))
        output.seek(0)
        return output
    
    def _generate_occupancy_json(self, data):
        """Generar JSON del reporte de ocupación."""
        units_data = []
        for unit in data['units']:
            units_data.append({
                'property': unit.property.name if unit.property else None,
                'unit_number': unit.unit_number,
                'owner': unit.owner.full_name if unit.owner else None,
                'occupied': unit.owner is not None,
                'monthly_fee': float(unit.monthly_fee) if unit.monthly_fee else 0
            })
        
        report_data = {
            'summary': data['summary'],
            'units': units_data,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        output = io.BytesIO()
        output.write(json.dumps(report_data, indent=2).encode('utf-8'))
        output.seek(0)
        return output
    
    def _generate_payment_status_pdf(self, data):
        """Generar PDF del reporte de estado de pagos."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Título
        title = Paragraph("Reporte de Estado de Pagos", self.title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Mes
        month = Paragraph(f"Mes: {data['summary']['month']}", self.styles['Normal'])
        story.append(month)
        story.append(Spacer(1, 12))
        
        # Resumen
        summary_data = [
            ['Concepto', 'Cantidad'],
            ['Total de Unidades', data['summary']['total_units']],
            ['Unidades al Día', data['summary']['paid_units']],
            ['Unidades Pendientes', data['summary']['pending_units']],
            ['Tasa de Cobranza', f"{data['summary']['collection_rate']:.1f}%"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Detalle de pagos
        if data['payment_status']:
            story.append(Paragraph("Detalle por Unidad", self.heading_style))
            
            status_data = [['Unidad', 'Propietario', 'Cuota', 'Estado', 'Último Pago']]
            for status in data['payment_status'][:30]:  # Limitar a 30 registros
                last_payment_date = status['last_payment'].payment_date.strftime('%d/%m/%Y') if status['last_payment'] else 'Nunca'
                status_data.append([
                    status['unit'].unit_number,
                    status['owner'].full_name if status['owner'] else 'N/A',
                    f"${status['amount_due']:,.2f}",
                    'Al día' if status['status'] == 'paid' else 'Pendiente',
                    last_payment_date
                ])
            
            status_table = Table(status_data)
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(status_table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _generate_payment_status_csv(self, data):
        """Generar CSV del reporte de estado de pagos."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        # Resumen
        writer.writerow(['ESTADO DE PAGOS'])
        writer.writerow(['Mes', data['summary']['month']])
        writer.writerow(['Concepto', 'Cantidad'])
        writer.writerow(['Total de Unidades', data['summary']['total_units']])
        writer.writerow(['Unidades al Día', data['summary']['paid_units']])
        writer.writerow(['Unidades Pendientes', data['summary']['pending_units']])
        writer.writerow(['Tasa de Cobranza (%)', data['summary']['collection_rate']])
        writer.writerow([])
        
        # Detalle
        writer.writerow(['DETALLE POR UNIDAD'])
        writer.writerow(['Unidad', 'Propietario', 'Cuota Mensual', 'Estado', 'Último Pago'])
        for status in data['payment_status']:
            last_payment_date = status['last_payment'].payment_date.strftime('%d/%m/%Y') if status['last_payment'] else 'Nunca'
            writer.writerow([
                status['unit'].unit_number,
                status['owner'].full_name if status['owner'] else 'N/A',
                status['amount_due'],
                'Al día' if status['status'] == 'paid' else 'Pendiente',
                last_payment_date
            ])
        
        output = io.BytesIO()
        output.write(buffer.getvalue().encode('utf-8'))
        output.seek(0)
        return output
    
    def _generate_payment_status_json(self, data):
        """Generar JSON del reporte de estado de pagos."""
        status_data = []
        for status in data['payment_status']:
            status_data.append({
                'unit_number': status['unit'].unit_number,
                'owner': status['owner'].full_name if status['owner'] else None,
                'amount_due': float(status['amount_due']),
                'status': status['status'],
                'last_payment_date': status['last_payment'].payment_date.isoformat() if status['last_payment'] else None,
                'last_payment_amount': float(status['last_payment'].amount) if status['last_payment'] else None
            })
        
        report_data = {
            'summary': data['summary'],
            'payment_status': status_data,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        output = io.BytesIO()
        output.write(json.dumps(report_data, indent=2).encode('utf-8'))
        output.seek(0)
        return output


# Instancia global del generador de reportes
report_generator = ReportGenerator()