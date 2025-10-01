"""
Rutas para generación de reportes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from utils.reports import report_generator
from models import Property, db
from datetime import datetime, timedelta
import tempfile
import os
from functools import wraps

reports_bp = Blueprint('reports', __name__)


def admin_required(f):
    """Decorador para requerir permisos de administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin_general', 'admin_ph']:
            flash('No tienes permisos para acceder a esta sección.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


@reports_bp.route('/')
@login_required
@admin_required
def index():
    """Dashboard de reportes."""
    try:
        # Obtener propiedades para filtros
        if current_user.role == 'admin_general':
            properties = Property.query.filter_by(is_active=True).all()
        else:
            properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
        
        # Estadísticas rápidas para el dashboard
        stats = {
            'total_properties': len(properties),
            'available_reports': [
                {
                    'name': 'Reporte Financiero',
                    'description': 'Ingresos, gastos y balance financiero',
                    'icon': 'bi-graph-up',
                    'url': 'reports.financial'
                },
                {
                    'name': 'Reporte de Mantenimiento',
                    'description': 'Estado de tareas de mantenimiento',
                    'icon': 'bi-tools',
                    'url': 'reports.maintenance'
                },
                {
                    'name': 'Reporte de Ocupación',
                    'description': 'Estado de ocupación de unidades',
                    'icon': 'bi-house',
                    'url': 'reports.occupancy'
                },
                {
                    'name': 'Estado de Pagos',
                    'description': 'Estado de pagos por unidad',
                    'icon': 'bi-credit-card',
                    'url': 'reports.payment_status'
                }
            ]
        }
        
        return render_template('reports/index.html', 
                             properties=properties, 
                             stats=stats)
                             
    except Exception as e:
        flash(f'Error cargando reportes: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@reports_bp.route('/financial')
@login_required
@admin_required
def financial():
    """Formulario para reporte financiero."""
    try:
        # Obtener propiedades
        if current_user.role == 'admin_general':
            properties = Property.query.filter_by(is_active=True).all()
        else:
            properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
        
        # Fechas por defecto (último mes)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        return render_template('reports/financial.html',
                             properties=properties,
                             start_date=start_date.strftime('%Y-%m-%d'),
                             end_date=end_date.strftime('%Y-%m-%d'))
                             
    except Exception as e:
        flash(f'Error cargando formulario: {str(e)}', 'error')
        return redirect(url_for('reports.index'))


@reports_bp.route('/financial/generate', methods=['POST'])
@login_required
@admin_required
def generate_financial():
    """Generar reporte financiero."""
    try:
        # Obtener parámetros
        property_id = request.form.get('property_id', type=int)
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        format_type = request.form.get('format', 'pdf')
        
        # Validar fechas
        if not start_date_str or not end_date_str:
            flash('Las fechas son requeridas.', 'error')
            return redirect(url_for('reports.financial'))
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        if start_date > end_date:
            flash('La fecha de inicio debe ser anterior a la fecha de fin.', 'error')
            return redirect(url_for('reports.financial'))
        
        # Generar reporte
        report_buffer = report_generator.generate_financial_report(
            property_id=property_id if property_id else None,
            start_date=start_date,
            end_date=end_date,
            format=format_type
        )
        
        # Determinar nombre del archivo
        property_name = ""
        if property_id:
            property = Property.query.get(property_id)
            if property:
                property_name = f"_{property.name.replace(' ', '_')}"
        
        filename = f"reporte_financiero{property_name}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        
        # Determinar tipo MIME
        if format_type == 'pdf':
            mimetype = 'application/pdf'
            filename += '.pdf'
        elif format_type == 'csv':
            mimetype = 'text/csv'
            filename += '.csv'
        elif format_type == 'json':
            mimetype = 'application/json'
            filename += '.json'
        else:
            flash('Formato no válido.', 'error')
            return redirect(url_for('reports.financial'))
        
        return send_file(
            report_buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error generando reporte: {str(e)}', 'error')
        return redirect(url_for('reports.financial'))


@reports_bp.route('/maintenance')
@login_required
@admin_required
def maintenance():
    """Formulario para reporte de mantenimiento."""
    try:
        # Obtener propiedades
        if current_user.role == 'admin_general':
            properties = Property.query.filter_by(is_active=True).all()
        else:
            properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
        
        # Fechas por defecto (último mes)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        return render_template('reports/maintenance.html',
                             properties=properties,
                             start_date=start_date.strftime('%Y-%m-%d'),
                             end_date=end_date.strftime('%Y-%m-%d'))
                             
    except Exception as e:
        flash(f'Error cargando formulario: {str(e)}', 'error')
        return redirect(url_for('reports.index'))


@reports_bp.route('/maintenance/generate', methods=['POST'])
@login_required
@admin_required
def generate_maintenance():
    """Generar reporte de mantenimiento."""
    try:
        # Obtener parámetros
        property_id = request.form.get('property_id', type=int)
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        format_type = request.form.get('format', 'pdf')
        
        # Validar fechas
        if not start_date_str or not end_date_str:
            flash('Las fechas son requeridas.', 'error')
            return redirect(url_for('reports.maintenance'))
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        if start_date > end_date:
            flash('La fecha de inicio debe ser anterior a la fecha de fin.', 'error')
            return redirect(url_for('reports.maintenance'))
        
        # Generar reporte
        report_buffer = report_generator.generate_maintenance_report(
            property_id=property_id if property_id else None,
            start_date=start_date,
            end_date=end_date,
            format=format_type
        )
        
        # Determinar nombre del archivo
        property_name = ""
        if property_id:
            property = Property.query.get(property_id)
            if property:
                property_name = f"_{property.name.replace(' ', '_')}"
        
        filename = f"reporte_mantenimiento{property_name}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        
        # Determinar tipo MIME
        if format_type == 'pdf':
            mimetype = 'application/pdf'
            filename += '.pdf'
        elif format_type == 'csv':
            mimetype = 'text/csv'
            filename += '.csv'
        elif format_type == 'json':
            mimetype = 'application/json'
            filename += '.json'
        else:
            flash('Formato no válido.', 'error')
            return redirect(url_for('reports.maintenance'))
        
        return send_file(
            report_buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error generando reporte: {str(e)}', 'error')
        return redirect(url_for('reports.maintenance'))


@reports_bp.route('/occupancy')
@login_required
@admin_required
def occupancy():
    """Formulario para reporte de ocupación."""
    try:
        # Obtener propiedades
        if current_user.role == 'admin_general':
            properties = Property.query.filter_by(is_active=True).all()
        else:
            properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
        
        return render_template('reports/occupancy.html', properties=properties)
                             
    except Exception as e:
        flash(f'Error cargando formulario: {str(e)}', 'error')
        return redirect(url_for('reports.index'))


@reports_bp.route('/occupancy/generate', methods=['POST'])
@login_required
@admin_required
def generate_occupancy():
    """Generar reporte de ocupación."""
    try:
        # Obtener parámetros
        property_id = request.form.get('property_id', type=int)
        format_type = request.form.get('format', 'pdf')
        
        # Generar reporte
        report_buffer = report_generator.generate_occupancy_report(
            property_id=property_id if property_id else None,
            format=format_type
        )
        
        # Determinar nombre del archivo
        property_name = ""
        if property_id:
            property = Property.query.get(property_id)
            if property:
                property_name = f"_{property.name.replace(' ', '_')}"
        
        filename = f"reporte_ocupacion{property_name}_{datetime.now().strftime('%Y%m%d')}"
        
        # Determinar tipo MIME
        if format_type == 'pdf':
            mimetype = 'application/pdf'
            filename += '.pdf'
        elif format_type == 'csv':
            mimetype = 'text/csv'
            filename += '.csv'
        elif format_type == 'json':
            mimetype = 'application/json'
            filename += '.json'
        else:
            flash('Formato no válido.', 'error')
            return redirect(url_for('reports.occupancy'))
        
        return send_file(
            report_buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error generando reporte: {str(e)}', 'error')
        return redirect(url_for('reports.occupancy'))


@reports_bp.route('/payment-status')
@login_required
@admin_required
def payment_status():
    """Formulario para reporte de estado de pagos."""
    try:
        # Obtener propiedades
        if current_user.role == 'admin_general':
            properties = Property.query.filter_by(is_active=True).all()
        else:
            properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
        
        return render_template('reports/payment_status.html', properties=properties)
                             
    except Exception as e:
        flash(f'Error cargando formulario: {str(e)}', 'error')
        return redirect(url_for('reports.index'))


@reports_bp.route('/payment-status/generate', methods=['POST'])
@login_required
@admin_required
def generate_payment_status():
    """Generar reporte de estado de pagos."""
    try:
        # Obtener parámetros
        property_id = request.form.get('property_id', type=int)
        format_type = request.form.get('format', 'pdf')
        
        # Generar reporte
        report_buffer = report_generator.generate_payment_status_report(
            property_id=property_id if property_id else None,
            format=format_type
        )
        
        # Determinar nombre del archivo
        property_name = ""
        if property_id:
            property = Property.query.get(property_id)
            if property:
                property_name = f"_{property.name.replace(' ', '_')}"
        
        filename = f"estado_pagos{property_name}_{datetime.now().strftime('%Y%m%d')}"
        
        # Determinar tipo MIME
        if format_type == 'pdf':
            mimetype = 'application/pdf'
            filename += '.pdf'
        elif format_type == 'csv':
            mimetype = 'text/csv'
            filename += '.csv'
        elif format_type == 'json':
            mimetype = 'application/json'
            filename += '.json'
        else:
            flash('Formato no válido.', 'error')
            return redirect(url_for('reports.payment_status'))
        
        return send_file(
            report_buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error generando reporte: {str(e)}', 'error')
        return redirect(url_for('reports.payment_status'))


@reports_bp.route('/api/quick-stats')
@login_required
@admin_required
def api_quick_stats():
    """API endpoint para estadísticas rápidas."""
    try:
        # Obtener propiedades del usuario
        if current_user.role == 'admin_general':
            properties = Property.query.filter_by(is_active=True).all()
        else:
            properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
        
        property_ids = [p.id for p in properties]
        
        # Estadísticas del mes actual
        current_month = datetime.utcnow().replace(day=1)
        
        # Ingresos del mes
        from models import Payment, Unit
        from sqlalchemy import func
        monthly_income = db.session.query(func.sum(Payment.amount)).join(Unit).filter(
            Unit.property_id.in_(property_ids),
            Payment.payment_date >= current_month
        ).scalar() or 0
        
        # Gastos del mes
        from models import Expense
        monthly_expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.property_id.in_(property_ids),
            Expense.expense_date >= current_month
        ).scalar() or 0
        
        # Tareas de mantenimiento pendientes
        from models import MaintenanceTask
        pending_tasks = MaintenanceTask.query.filter(
            MaintenanceTask.property_id.in_(property_ids),
            MaintenanceTask.status.in_(['pending', 'in_progress'])
        ).count()
        
        # Tasa de ocupación
        from models import Unit
        total_units = Unit.query.filter(Unit.property_id.in_(property_ids)).count()
        occupied_units = Unit.query.filter(
            Unit.property_id.in_(property_ids),
            Unit.owner_id.isnot(None)
        ).count()
        
        occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
        
        return jsonify({
            'monthly_income': float(monthly_income),
            'monthly_expenses': float(monthly_expenses),
            'net_income': float(monthly_income - monthly_expenses),
            'pending_tasks': pending_tasks,
            'occupancy_rate': round(occupancy_rate, 1),
            'total_properties': len(properties),
            'total_units': total_units,
            'occupied_units': occupied_units
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/custom')
@login_required
@admin_required
def custom():
    """Formulario para reportes personalizados."""
    try:
        # Obtener propiedades
        if current_user.role == 'admin_general':
            properties = Property.query.filter_by(is_active=True).all()
        else:
            properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
        
        return render_template('reports/custom.html', properties=properties)
                             
    except Exception as e:
        flash(f'Error cargando formulario: {str(e)}', 'error')
        return redirect(url_for('reports.index'))


@reports_bp.route('/schedule')
@login_required
@admin_required
def schedule():
    """Programar reportes automáticos."""
    try:
        # Obtener propiedades
        if current_user.role == 'admin_general':
            properties = Property.query.filter_by(is_active=True).all()
        else:
            properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
        
        # Aquí se implementaría la lógica para reportes programados
        # Por ahora solo mostramos la interfaz
        
        return render_template('reports/schedule.html', properties=properties)
                             
    except Exception as e:
        flash(f'Error cargando programación: {str(e)}', 'error')
        return redirect(url_for('reports.index'))