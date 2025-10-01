"""
Rutas para visualización de logs de auditoría
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from utils.audit import audit_logger, AuditLog
from models import User, db
from datetime import datetime, timedelta
import json
from functools import wraps

audit_bp = Blueprint('audit', __name__)


def admin_required(f):
    """Decorador para requerir permisos de administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin_general']:
            flash('No tienes permisos para acceder a esta sección.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


@audit_bp.route('/')
@login_required
@admin_required
def index():
    """Dashboard de auditoría."""
    try:
        # Obtener estadísticas generales
        total_logs = AuditLog.query.count()
        
        # Logs de las últimas 24 horas
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_logs = AuditLog.query.filter(
            AuditLog.timestamp >= yesterday
        ).count()
        
        # Logs fallidos de las últimas 24 horas
        failed_logs = AuditLog.query.filter(
            AuditLog.timestamp >= yesterday,
            AuditLog.success == False
        ).count()
        
        # Usuarios más activos (últimos 7 días)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_users = db.session.query(
            AuditLog.user_email,
            db.func.count(AuditLog.id).label('activity_count')
        ).filter(
            AuditLog.timestamp >= week_ago,
            AuditLog.user_email.isnot(None)
        ).group_by(AuditLog.user_email).order_by(
            db.func.count(AuditLog.id).desc()
        ).limit(10).all()
        
        # Acciones más comunes (últimos 7 días)
        common_actions = db.session.query(
            AuditLog.action,
            db.func.count(AuditLog.id).label('action_count')
        ).filter(
            AuditLog.timestamp >= week_ago
        ).group_by(AuditLog.action).order_by(
            db.func.count(AuditLog.id).desc()
        ).limit(10).all()
        
        # Logs recientes
        recent_audit_logs = audit_logger.get_logs(limit=20)
        
        stats = {
            'total_logs': total_logs,
            'recent_logs': recent_logs,
            'failed_logs': failed_logs,
            'active_users': active_users,
            'common_actions': common_actions
        }
        
        return render_template('audit/index.html', 
                             stats=stats, 
                             recent_logs=recent_audit_logs)
                             
    except Exception as e:
        flash(f'Error cargando información de auditoría: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@audit_bp.route('/logs')
@login_required
@admin_required
def logs():
    """Lista de logs de auditoría con filtros."""
    try:
        # Obtener parámetros de filtro
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        user_id = request.args.get('user_id', type=int)
        action = request.args.get('action')
        resource_type = request.args.get('resource_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        success_filter = request.args.get('success')
        
        # Construir query
        query = AuditLog.query
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(AuditLog.timestamp < end_dt)
        
        if success_filter:
            success_bool = success_filter.lower() == 'true'
            query = query.filter(AuditLog.success == success_bool)
        
        # Ordenar y paginar
        query = query.order_by(AuditLog.timestamp.desc())
        logs = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Obtener listas para filtros
        users = User.query.filter(User.is_active == True).all()
        
        actions = db.session.query(AuditLog.action).distinct().all()
        actions = [action[0] for action in actions if action[0]]
        
        resource_types = db.session.query(AuditLog.resource_type).distinct().all()
        resource_types = [rt[0] for rt in resource_types if rt[0]]
        
        return render_template('audit/logs.html',
                             logs=logs,
                             users=users,
                             actions=actions,
                             resource_types=resource_types,
                             filters={
                                 'user_id': user_id,
                                 'action': action,
                                 'resource_type': resource_type,
                                 'start_date': start_date,
                                 'end_date': end_date,
                                 'success': success_filter
                             })
                             
    except Exception as e:
        flash(f'Error cargando logs: {str(e)}', 'error')
        return redirect(url_for('audit.index'))


@audit_bp.route('/security')
@login_required
@admin_required
def security():
    """Dashboard de eventos de seguridad."""
    try:
        # Obtener eventos de seguridad recientes
        security_logs = audit_logger.get_security_events(days=30)
        
        # Estadísticas de seguridad
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        login_attempts = AuditLog.query.filter(
            AuditLog.action == 'login_attempt',
            AuditLog.timestamp >= week_ago
        ).count()
        
        failed_logins = AuditLog.query.filter(
            AuditLog.action == 'login_attempt',
            AuditLog.success == False,
            AuditLog.timestamp >= week_ago
        ).count()
        
        permission_denials = AuditLog.query.filter(
            AuditLog.action == 'permission_denied',
            AuditLog.timestamp >= week_ago
        ).count()
        
        # IPs más activas
        active_ips = db.session.query(
            AuditLog.ip_address,
            db.func.count(AuditLog.id).label('request_count')
        ).filter(
            AuditLog.timestamp >= week_ago,
            AuditLog.ip_address.isnot(None)
        ).group_by(AuditLog.ip_address).order_by(
            db.func.count(AuditLog.id).desc()
        ).limit(10).all()
        
        # Intentos de login fallidos por IP
        failed_by_ip = db.session.query(
            AuditLog.ip_address,
            db.func.count(AuditLog.id).label('failed_count')
        ).filter(
            AuditLog.action == 'login_attempt',
            AuditLog.success == False,
            AuditLog.timestamp >= week_ago,
            AuditLog.ip_address.isnot(None)
        ).group_by(AuditLog.ip_address).order_by(
            db.func.count(AuditLog.id).desc()
        ).limit(10).all()
        
        security_stats = {
            'login_attempts': login_attempts,
            'failed_logins': failed_logins,
            'permission_denials': permission_denials,
            'active_ips': active_ips,
            'failed_by_ip': failed_by_ip
        }
        
        return render_template('audit/security.html',
                             security_logs=security_logs,
                             stats=security_stats)
                             
    except Exception as e:
        flash(f'Error cargando información de seguridad: {str(e)}', 'error')
        return redirect(url_for('audit.index'))


@audit_bp.route('/user/<int:user_id>')
@login_required
@admin_required
def user_activity(user_id):
    """Actividad de un usuario específico."""
    try:
        user = User.query.get_or_404(user_id)
        
        # Obtener actividad del usuario
        days = request.args.get('days', 30, type=int)
        user_logs = audit_logger.get_user_activity(user_id, days=days)
        
        # Estadísticas del usuario
        total_actions = len(user_logs)
        
        actions_by_type = {}
        for log in user_logs:
            action = log.action
            if action in actions_by_type:
                actions_by_type[action] += 1
            else:
                actions_by_type[action] = 1
        
        # Último login
        last_login = AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.action == 'login_attempt',
            AuditLog.success == True
        ).order_by(AuditLog.timestamp.desc()).first()
        
        user_stats = {
            'total_actions': total_actions,
            'actions_by_type': actions_by_type,
            'last_login': last_login
        }
        
        return render_template('audit/user_activity.html',
                             user=user,
                             logs=user_logs,
                             stats=user_stats,
                             days=days)
                             
    except Exception as e:
        flash(f'Error cargando actividad del usuario: {str(e)}', 'error')
        return redirect(url_for('audit.logs'))


@audit_bp.route('/export')
@login_required
@admin_required
def export_logs():
    """Exportar logs de auditoría."""
    try:
        # Obtener parámetros
        format_type = request.args.get('format', 'json')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Construir query
        query = AuditLog.query
        
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(AuditLog.timestamp < end_dt)
        
        logs = query.order_by(AuditLog.timestamp.desc()).limit(10000).all()
        
        if format_type == 'json':
            # Exportar como JSON
            from flask import Response
            
            logs_data = [log.to_dict() for log in logs]
            
            response = Response(
                json.dumps(logs_data, indent=2, default=str),
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=audit_logs_{datetime.now().strftime("%Y%m%d")}.json'
                }
            )
            
            return response
        
        elif format_type == 'csv':
            # Exportar como CSV
            import csv
            import io
            from flask import Response
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Headers
            writer.writerow([
                'ID', 'User Email', 'Action', 'Resource Type', 'Resource ID',
                'IP Address', 'Success', 'Error Message', 'Timestamp'
            ])
            
            # Data
            for log in logs:
                writer.writerow([
                    log.id,
                    log.user_email or '',
                    log.action,
                    log.resource_type or '',
                    log.resource_id or '',
                    log.ip_address or '',
                    'Yes' if log.success else 'No',
                    log.error_message or '',
                    log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=audit_logs_{datetime.now().strftime("%Y%m%d")}.csv'
                }
            )
            
            return response
        
        else:
            flash('Formato de exportación no válido.', 'error')
            return redirect(url_for('audit.logs'))
            
    except Exception as e:
        flash(f'Error exportando logs: {str(e)}', 'error')
        return redirect(url_for('audit.logs'))


@audit_bp.route('/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_logs():
    """Limpiar logs antiguos."""
    try:
        days = request.form.get('days', 365, type=int)
        
        if days < 30:
            flash('No se pueden eliminar logs de menos de 30 días.', 'error')
            return redirect(url_for('audit.index'))
        
        deleted_count = audit_logger.cleanup_old_logs(days=days)
        
        flash(f'Se eliminaron {deleted_count} logs antiguos.', 'success')
        
    except Exception as e:
        flash(f'Error limpiando logs: {str(e)}', 'error')
    
    return redirect(url_for('audit.index'))


@audit_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API endpoint para estadísticas de auditoría."""
    try:
        days = request.args.get('days', 7, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Actividad por día
        daily_activity = db.session.query(
            db.func.date(AuditLog.timestamp).label('date'),
            db.func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.timestamp >= start_date
        ).group_by(
            db.func.date(AuditLog.timestamp)
        ).order_by('date').all()
        
        # Acciones más comunes
        top_actions = db.session.query(
            AuditLog.action,
            db.func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.timestamp >= start_date
        ).group_by(AuditLog.action).order_by(
            db.func.count(AuditLog.id).desc()
        ).limit(10).all()
        
        # Errores por día
        daily_errors = db.session.query(
            db.func.date(AuditLog.timestamp).label('date'),
            db.func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.timestamp >= start_date,
            AuditLog.success == False
        ).group_by(
            db.func.date(AuditLog.timestamp)
        ).order_by('date').all()
        
        return jsonify({
            'daily_activity': [
                {'date': str(item.date), 'count': item.count}
                for item in daily_activity
            ],
            'top_actions': [
                {'action': item.action, 'count': item.count}
                for item in top_actions
            ],
            'daily_errors': [
                {'date': str(item.date), 'count': item.count}
                for item in daily_errors
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500