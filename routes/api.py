"""
API routes for PH Control
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from utils.notifications import notification_manager
from models import Notification, User, db
from datetime import datetime

api_bp = Blueprint('api', __name__)


# Notification API endpoints
@api_bp.route('/notifications/check')
@login_required
def check_notifications():
    """Check for new notifications."""
    try:
        count = notification_manager.get_unread_count(current_user.id)
        return jsonify({'new_notifications': count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/notifications/list')
@login_required
def api_list_notifications():
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


@api_bp.route('/notifications/unread-count')
@login_required
def api_unread_count():
    """API endpoint para obtener número de notificaciones no leídas."""
    try:
        count = notification_manager.get_unread_count(current_user.id)
        return jsonify({'count': count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Marcar notificación como leída."""
    try:
        success = notification_manager.mark_as_read(notification_id, current_user.id)

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Notificación no encontrada'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Marcar todas las notificaciones como leídas."""
    try:
        count = notification_manager.mark_all_as_read(current_user.id)
        return jsonify({'success': True, 'count': count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Eliminar notificación."""
    try:
        success = notification_manager.delete_notification(notification_id, current_user.id)

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Notificación no encontrada'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500