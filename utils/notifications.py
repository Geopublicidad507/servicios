"""
Sistema de notificaciones avanzado para PH Control
"""
from flask import current_app, render_template
from flask_mail import Message
from models import db, Notification, User
from datetime import datetime, timedelta
import json
from enum import Enum
import logging


class NotificationType(Enum):
    """Tipos de notificaciones."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PAYMENT_DUE = "payment_due"
    PAYMENT_OVERDUE = "payment_overdue"
    MAINTENANCE_SCHEDULED = "maintenance_scheduled"
    ASSEMBLY_REMINDER = "assembly_reminder"
    SECURITY_ALERT = "security_alert"
    SYSTEM_UPDATE = "system_update"


class NotificationPriority(Enum):
    """Prioridades de notificaciones."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationManager:
    """Gestor de notificaciones del sistema."""
    
    def __init__(self, app=None, mail=None):
        self.app = app
        self.mail = mail
        self.logger = logging.getLogger(__name__)
        
        if app is not None:
            self.init_app(app, mail)
    
    def init_app(self, app, mail=None):
        """Inicializar con la aplicación Flask."""
        self.app = app
        self.mail = mail
        
        # Configurar logging
        if not self.logger.handlers:
            handler = logging.FileHandler('logs/notifications.log')
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def create_notification(self, user_id, title, message, notification_type=NotificationType.INFO,
                          priority=NotificationPriority.NORMAL, action_url=None, 
                          expires_at=None, metadata=None):
        """
        Crear una nueva notificación.
        
        Args:
            user_id: ID del usuario destinatario
            title: Título de la notificación
            message: Mensaje de la notificación
            notification_type: Tipo de notificación
            priority: Prioridad de la notificación
            action_url: URL de acción opcional
            expires_at: Fecha de expiración opcional
            metadata: Datos adicionales en formato JSON
        
        Returns:
            Notification: La notificación creada
        """
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type.value,
                priority=priority.value,
                action_url=action_url,
                expires_at=expires_at,
                metadata=json.dumps(metadata) if metadata else None
            )
            
            db.session.add(notification)
            db.session.commit()
            
            self.logger.info(f"Notification created for user {user_id}: {title}")
            
            # Enviar email si es de alta prioridad
            if priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]:
                self._send_email_notification(notification)
            
            return notification
            
        except Exception as e:
            self.logger.error(f"Error creating notification: {str(e)}")
            db.session.rollback()
            return None
    
    def create_bulk_notification(self, user_ids, title, message, 
                               notification_type=NotificationType.INFO,
                               priority=NotificationPriority.NORMAL, 
                               action_url=None, expires_at=None, metadata=None):
        """
        Crear notificaciones para múltiples usuarios.
        
        Args:
            user_ids: Lista de IDs de usuarios
            title: Título de la notificación
            message: Mensaje de la notificación
            notification_type: Tipo de notificación
            priority: Prioridad de la notificación
            action_url: URL de acción opcional
            expires_at: Fecha de expiración opcional
            metadata: Datos adicionales
        
        Returns:
            int: Número de notificaciones creadas
        """
        try:
            notifications = []
            
            for user_id in user_ids:
                notification = Notification(
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type=notification_type.value,
                    priority=priority.value,
                    action_url=action_url,
                    expires_at=expires_at,
                    metadata=json.dumps(metadata) if metadata else None
                )
                notifications.append(notification)
            
            db.session.add_all(notifications)
            db.session.commit()
            
            self.logger.info(f"Bulk notification created for {len(user_ids)} users: {title}")
            
            # Enviar emails si es de alta prioridad
            if priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]:
                for notification in notifications:
                    self._send_email_notification(notification)
            
            return len(notifications)
            
        except Exception as e:
            self.logger.error(f"Error creating bulk notifications: {str(e)}")
            db.session.rollback()
            return 0
    
    def create_system_notification(self, title, message, notification_type=NotificationType.INFO,
                                 priority=NotificationPriority.NORMAL, target_roles=None,
                                 action_url=None, expires_at=None, metadata=None):
        """
        Crear notificación del sistema para usuarios específicos por rol.
        
        Args:
            title: Título de la notificación
            message: Mensaje de la notificación
            notification_type: Tipo de notificación
            priority: Prioridad de la notificación
            target_roles: Lista de roles objetivo (None = todos)
            action_url: URL de acción opcional
            expires_at: Fecha de expiración opcional
            metadata: Datos adicionales
        
        Returns:
            int: Número de notificaciones creadas
        """
        try:
            # Obtener usuarios objetivo
            query = User.query.filter(User.is_active == True)
            
            if target_roles:
                query = query.filter(User.role.in_(target_roles))
            
            users = query.all()
            user_ids = [user.id for user in users]
            
            return self.create_bulk_notification(
                user_ids=user_ids,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                action_url=action_url,
                expires_at=expires_at,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error creating system notification: {str(e)}")
            return 0
    
    def mark_as_read(self, notification_id, user_id=None):
        """
        Marcar notificación como leída.
        
        Args:
            notification_id: ID de la notificación
            user_id: ID del usuario (para verificación)
        
        Returns:
            bool: True si se marcó correctamente
        """
        try:
            query = Notification.query.filter_by(id=notification_id)
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            notification = query.first()
            
            if notification:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error marking notification as read: {str(e)}")
            return False
    
    def mark_all_as_read(self, user_id):
        """
        Marcar todas las notificaciones de un usuario como leídas.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            int: Número de notificaciones marcadas
        """
        try:
            count = Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).update({
                'is_read': True,
                'read_at': datetime.utcnow()
            })
            
            db.session.commit()
            return count
            
        except Exception as e:
            self.logger.error(f"Error marking all notifications as read: {str(e)}")
            return 0
    
    def delete_notification(self, notification_id, user_id=None):
        """
        Eliminar notificación.
        
        Args:
            notification_id: ID de la notificación
            user_id: ID del usuario (para verificación)
        
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            query = Notification.query.filter_by(id=notification_id)
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            notification = query.first()
            
            if notification:
                db.session.delete(notification)
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting notification: {str(e)}")
            return False
    
    def get_user_notifications(self, user_id, unread_only=False, limit=50, offset=0):
        """
        Obtener notificaciones de un usuario.
        
        Args:
            user_id: ID del usuario
            unread_only: Solo notificaciones no leídas
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            List[Notification]: Lista de notificaciones
        """
        try:
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            # Filtrar notificaciones expiradas
            query = query.filter(
                db.or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at > datetime.utcnow()
                )
            )
            
            query = query.order_by(Notification.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            return query.all()
            
        except Exception as e:
            self.logger.error(f"Error getting user notifications: {str(e)}")
            return []
    
    def get_unread_count(self, user_id):
        """
        Obtener número de notificaciones no leídas.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            int: Número de notificaciones no leídas
        """
        try:
            return Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).filter(
                db.or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at > datetime.utcnow()
                )
            ).count()
            
        except Exception as e:
            self.logger.error(f"Error getting unread count: {str(e)}")
            return 0
    
    def cleanup_expired_notifications(self):
        """
        Limpiar notificaciones expiradas.
        
        Returns:
            int: Número de notificaciones eliminadas
        """
        try:
            count = Notification.query.filter(
                Notification.expires_at < datetime.utcnow()
            ).delete()
            
            db.session.commit()
            
            self.logger.info(f"Cleaned up {count} expired notifications")
            return count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired notifications: {str(e)}")
            return 0
    
    def cleanup_old_notifications(self, days=90):
        """
        Limpiar notificaciones antiguas leídas.
        
        Args:
            days: Días de antigüedad
        
        Returns:
            int: Número de notificaciones eliminadas
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            count = Notification.query.filter(
                Notification.is_read == True,
                Notification.read_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            self.logger.info(f"Cleaned up {count} old notifications")
            return count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old notifications: {str(e)}")
            return 0
    
    def _send_email_notification(self, notification):
        """
        Enviar notificación por email.
        
        Args:
            notification: Objeto Notification
        """
        try:
            if not self.mail:
                return
            
            user = User.query.get(notification.user_id)
            if not user or not user.email:
                return
            
            # Crear mensaje de email
            msg = Message(
                subject=f"[PH Control] {notification.title}",
                recipients=[user.email],
                html=render_template('emails/notification.html', 
                                   notification=notification, user=user),
                body=f"{notification.title}\n\n{notification.message}"
            )
            
            self.mail.send(msg)
            
            # Marcar como enviado por email
            notification.email_sent = True
            notification.email_sent_at = datetime.utcnow()
            db.session.commit()
            
            self.logger.info(f"Email notification sent to {user.email}")
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {str(e)}")
    
    def create_payment_due_notification(self, user_id, amount, due_date, unit_number=None):
        """Crear notificación de pago pendiente."""
        title = "Pago Pendiente"
        message = f"Tienes un pago pendiente de ${amount:.2f}"
        if unit_number:
            message += f" para la unidad {unit_number}"
        message += f". Fecha de vencimiento: {due_date.strftime('%d/%m/%Y')}"
        
        return self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.PAYMENT_DUE,
            priority=NotificationPriority.HIGH,
            action_url="/financial/payments",
            expires_at=due_date + timedelta(days=30),
            metadata={
                'amount': float(amount),
                'due_date': due_date.isoformat(),
                'unit_number': unit_number
            }
        )
    
    def create_maintenance_notification(self, user_ids, task_title, scheduled_date):
        """Crear notificación de mantenimiento programado."""
        title = "Mantenimiento Programado"
        message = f"Se ha programado: {task_title} para el {scheduled_date.strftime('%d/%m/%Y')}"
        
        return self.create_bulk_notification(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type=NotificationType.MAINTENANCE_SCHEDULED,
            priority=NotificationPriority.NORMAL,
            action_url="/maintenance",
            metadata={
                'task_title': task_title,
                'scheduled_date': scheduled_date.isoformat()
            }
        )
    
    def create_assembly_reminder(self, user_ids, assembly_title, assembly_date):
        """Crear recordatorio de asamblea."""
        title = "Recordatorio de Asamblea"
        message = f"Recordatorio: {assembly_title} el {assembly_date.strftime('%d/%m/%Y a las %H:%M')}"
        
        return self.create_bulk_notification(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type=NotificationType.ASSEMBLY_REMINDER,
            priority=NotificationPriority.HIGH,
            action_url="/communication/assemblies",
            expires_at=assembly_date + timedelta(hours=2),
            metadata={
                'assembly_title': assembly_title,
                'assembly_date': assembly_date.isoformat()
            }
        )
    
    def create_security_alert(self, title, message, target_roles=['admin_general', 'admin_ph']):
        """Crear alerta de seguridad."""
        return self.create_system_notification(
            title=title,
            message=message,
            notification_type=NotificationType.SECURITY_ALERT,
            priority=NotificationPriority.URGENT,
            target_roles=target_roles,
            action_url="/audit/security"
        )


# Instancia global del gestor de notificaciones
notification_manager = NotificationManager()