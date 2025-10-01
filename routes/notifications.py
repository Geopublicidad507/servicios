"""
Rutas para gestión de notificaciones
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from utils.notifications import notification_manager, NotificationType, NotificationPriority
from models import Notification, User, db
from datetime import datetime, timedelta
from functools import wraps

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/')
@login_required
def index():
    """Lista de notificaciones del usuario."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Obtener notificaciones del usuario
        notifications_query = Notification.query.filter_by(user_id=current_user.id)
        
        # Filtrar notificaciones expiradas
        notifications_query = notifications_query.filter(
            db.or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )
        
        notifications_query = notifications_query.order_by(
            Notification.is_read.asc(),  # No leídas primero
            Notification.created_at.desc()
        )
        
        notifications = notifications_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Estadísticas
        total_notifications = Notification.query.filter_by(user_id=current_user.id).count()
        unread_count = notification_manager.get_unread_count(current_user.id)
        
        stats = {
            'total': total_notifications,
            'unread': unread_count,
            'read': total_notifications - unread_count
        }
        
        return render_template('notifications/index.html',
                             notifications=notifications,
                             stats=stats)
                             
    except Exception as e:
        flash(f'Error cargando notificaciones: {str(e)}', 'error')
        return redirect(url_for('dashboard.index'))


@notifications_bp.route('/api/list')
@login_required
def api_list():
    """API endpoint para obtener notificaciones."""
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        notifications = notification_manager.get_user_notifications(
            user_id=current_user.id,
            unread_only=unread_only,
            limit=limit,
            offset=offset
        )
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'priority': notification.priority,
                'is_read': notification.is_read,
                'action_url': notification.action_url,
                'created_at': notification.created_at.isoformat(),
                'expires_at': notification.expires_at.isoformat() if notification.expires_at else None
            })
        
        return jsonify({
            'notifications': notifications_data,
            'unread_count': notification_manager.get_unread_count(current_user.id)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/api/unread-count')
@login_required
def api_unread_count():
    """API endpoint para obtener número de notificaciones no leídas."""
    try:
        count = notification_manager.get_unread_count(current_user.id)
        return jsonify({'count': count})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Marcar notificación como leída."""
    try:
        success = notification_manager.mark_as_read(notification_id, current_user.id)
        
        if success:
            if request.is_json:
                return jsonify({'success': True})
            else:
                flash('Notificación marcada como leída.', 'success')
        else:
            if request.is_json:
                return jsonify({'error': 'Notificación no encontrada'}), 404
            else:
                flash('Notificación no encontrada.', 'error')
        
        return redirect(request.referrer or url_for('notifications.index'))
        
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Error marcando notificación: {str(e)}', 'error')
            return redirect(url_for('notifications.index'))


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Marcar todas las notificaciones como leídas."""
    try:
        count = notification_manager.mark_all_as_read(current_user.id)
        
        if request.is_json:
            return jsonify({'success': True, 'count': count})
        else:
            flash(f'{count} notificaciones marcadas como leídas.', 'success')
            return redirect(url_for('notifications.index'))
        
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Error marcando notificaciones: {str(e)}', 'error')
            return redirect(url_for('notifications.index'))


@notifications_bp.route('/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete(notification_id):
    """Eliminar notificación."""
    try:
        success = notification_manager.delete_notification(notification_id, current_user.id)
        
        if success:
            if request.is_json:
                return jsonify({'success': True})
            else:
                flash('Notificación eliminada.', 'success')
        else:
            if request.is_json:
                return jsonify({'error': 'Notificación no encontrada'}), 404
            else:
                flash('Notificación no encontrada.', 'error')
        
        return redirect(request.referrer or url_for('notifications.index'))
        
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Error eliminando notificación: {str(e)}', 'error')
            return redirect(url_for('notifications.index'))


@notifications_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Configurar preferencias de notificaciones."""
    if request.method == 'POST':
        try:
            # Aquí se implementarían las preferencias de notificaciones
            # Por ahora, solo mostramos un mensaje
            flash('Preferencias de notificaciones guardadas.', 'success')
            return redirect(url_for('notifications.preferences'))
            
        except Exception as e:
            flash(f'Error guardando preferencias: {str(e)}', 'error')
    
    # Obtener preferencias actuales (simuladas)
    preferences = {
        'email_notifications': True,
        'payment_reminders': True,
        'maintenance_alerts': True,
        'assembly_reminders': True,
        'security_alerts': True,
        'system_updates': False
    }
    
    return render_template('notifications/preferences.html', preferences=preferences)


# Rutas administrativas
def admin_required(f):
    """Decorador para requerir permisos de administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin_general', 'admin_ph']:
            flash('No tienes permisos para acceder a esta sección.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


@notifications_bp.route('/admin')
@login_required
@admin_required
def admin_index():
    """Panel administrativo de notificaciones."""
    try:
        # Estadísticas generales
        total_notifications = Notification.query.count()
        
        # Notificaciones por tipo
        notifications_by_type = db.session.query(
            Notification.notification_type,
            db.func.count(Notification.id).label('count')
        ).group_by(Notification.notification_type).all()
        
        # Notificaciones recientes
        recent_notifications = Notification.query.order_by(
            Notification.created_at.desc()
        ).limit(10).all()
        
        # Usuarios con más notificaciones no leídas
        users_with_unread = db.session.query(
            User.first_name,
            User.last_name,
            User.email,
            db.func.count(Notification.id).label('unread_count')
        ).join(Notification).filter(
            Notification.is_read == False
        ).group_by(User.id).order_by(
            db.func.count(Notification.id).desc()
        ).limit(10).all()
        
        stats = {
            'total_notifications': total_notifications,
            'notifications_by_type': notifications_by_type,
            'users_with_unread': users_with_unread
        }
        
        return render_template('notifications/admin.html',
                             stats=stats,
                             recent_notifications=recent_notifications)
                             
    except Exception as e:
        flash(f'Error cargando panel administrativo: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@notifications_bp.route('/admin/send', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_send():
    """Enviar notificación administrativa."""
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            message = request.form.get('message')
            notification_type = request.form.get('notification_type', 'info')
            priority = request.form.get('priority', 'normal')
            target_type = request.form.get('target_type')  # all, role, specific
            target_roles = request.form.getlist('target_roles')
            target_users = request.form.getlist('target_users')
            action_url = request.form.get('action_url')
            expires_days = request.form.get('expires_days', type=int)
            
            if not title or not message:
                flash('Título y mensaje son requeridos.', 'error')
                return redirect(url_for('notifications.admin_send'))
            
            # Calcular fecha de expiración
            expires_at = None
            if expires_days and expires_days > 0:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)
            
            # Determinar destinatarios
            if target_type == 'all':
                # Todos los usuarios
                count = notification_manager.create_system_notification(
                    title=title,
                    message=message,
                    notification_type=NotificationType(notification_type),
                    priority=NotificationPriority(priority),
                    action_url=action_url if action_url else None,
                    expires_at=expires_at
                )
            elif target_type == 'role' and target_roles:
                # Usuarios por rol
                count = notification_manager.create_system_notification(
                    title=title,
                    message=message,
                    notification_type=NotificationType(notification_type),
                    priority=NotificationPriority(priority),
                    target_roles=target_roles,
                    action_url=action_url if action_url else None,
                    expires_at=expires_at
                )
            elif target_type == 'specific' and target_users:
                # Usuarios específicos
                user_ids = [int(uid) for uid in target_users if uid.isdigit()]
                count = notification_manager.create_bulk_notification(
                    user_ids=user_ids,
                    title=title,
                    message=message,
                    notification_type=NotificationType(notification_type),
                    priority=NotificationPriority(priority),
                    action_url=action_url if action_url else None,
                    expires_at=expires_at
                )
            else:
                flash('Debes seleccionar destinatarios válidos.', 'error')
                return redirect(url_for('notifications.admin_send'))
            
            flash(f'Notificación enviada a {count} usuarios.', 'success')
            return redirect(url_for('notifications.admin_index'))
            
        except Exception as e:
            flash(f'Error enviando notificación: {str(e)}', 'error')
    
    # Obtener usuarios para el formulario
    users = User.query.filter(User.is_active == True).order_by(User.first_name, User.last_name).all()
    
    return render_template('notifications/admin_send.html', users=users)


@notifications_bp.route('/admin/cleanup', methods=['POST'])
@login_required
@admin_required
def admin_cleanup():
    """Limpiar notificaciones antiguas."""
    try:
        cleanup_type = request.form.get('cleanup_type')
        
        if cleanup_type == 'expired':
            count = notification_manager.cleanup_expired_notifications()
            flash(f'Se eliminaron {count} notificaciones expiradas.', 'success')
        elif cleanup_type == 'old':
            days = request.form.get('days', 90, type=int)
            count = notification_manager.cleanup_old_notifications(days=days)
            flash(f'Se eliminaron {count} notificaciones antiguas.', 'success')
        else:
            flash('Tipo de limpieza no válido.', 'error')
        
    except Exception as e:
        flash(f'Error en limpieza: {str(e)}', 'error')
    
    return redirect(url_for('notifications.admin_index'))