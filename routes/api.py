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
def check_notifications():
    """Check for new notifications."""
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({'new_notifications': 0, 'authenticated': False})

        # Count unread notifications for current user
        count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return jsonify({'new_notifications': count, 'authenticated': True})

    except Exception as e:
        return jsonify({'error': str(e), 'authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False}), 500


@api_bp.route('/notifications/list')
@login_required
def api_list_notifications():
    """API endpoint para obtener notificaciones."""
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)

        # Build query
        query = {'user_id': current_user.id}
        if unread_only:
            query['is_read'] = False

        # Get notifications with pagination
        notifications_query = Notification.query.filter_by(**query)
        notifications_query = notifications_query.order_by(Notification.created_at.desc())
        notifications = notifications_query.offset(offset).limit(limit).all()

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

        # Get total unread count
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

        return jsonify({
            'notifications': notifications_data,
            'unread_count': unread_count
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/notifications/unread-count')
@login_required
def api_unread_count():
    """API endpoint para obtener número de notificaciones no leídas."""
    try:
        count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return jsonify({'count': count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/notifications/mark-read/<notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Marcar notificación como leída."""
    try:
        # Find and update notification
        notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
        if not notification:
            return jsonify({'error': 'Notificación no encontrada'}), 404

        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'success': True})

    except Notification.DoesNotExist:
        return jsonify({'error': 'Notificación no encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Marcar todas las notificaciones como leídas."""
    try:
        # Update all unread notifications for current user
        count = Notification.query.filter_by(user_id=current_user.id, is_read=False).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        db.session.commit()
        return jsonify({'success': True, 'count': count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/notifications/delete/<notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Eliminar notificación."""
    try:
        # Find and delete notification
        notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Notificación no encontrada'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
