"""
Sistema de auditoría y logs para PH Control
"""
import logging
import json
from datetime import datetime
from functools import wraps
from flask import request, current_app, g
from flask_login import current_user
from models import db
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean


class AuditLog(db.Model):
    """Modelo para logs de auditoría."""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)  # Puede ser None para acciones del sistema
    user_email = Column(String(120), nullable=True)
    action = Column(String(100), nullable=False)  # login, logout, create_user, delete_payment, etc.
    resource_type = Column(String(50), nullable=True)  # user, property, payment, etc.
    resource_id = Column(String(50), nullable=True)  # ID del recurso afectado
    details = Column(Text, nullable=True)  # JSON con detalles adicionales
    ip_address = Column(String(45), nullable=True)  # IPv4 o IPv6
    user_agent = Column(String(500), nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_email} at {self.timestamp}>'
    
    def to_dict(self):
        """Convertir a diccionario para JSON."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': json.loads(self.details) if self.details else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'success': self.success,
            'error_message': self.error_message,
            'timestamp': self.timestamp.isoformat()
        }


class AuditLogger:
    """Gestor de logs de auditoría."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar con la aplicación Flask."""
        self.app = app
        
        # Configurar logging
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # Handler para archivo
        if not self.logger.handlers:
            handler = logging.FileHandler('logs/audit.log')
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log(self, action, resource_type=None, resource_id=None, details=None, 
            success=True, error_message=None):
        """
        Registrar una acción en el log de auditoría.
        
        Args:
            action: Acción realizada (ej: 'login', 'create_payment')
            resource_type: Tipo de recurso (ej: 'user', 'payment')
            resource_id: ID del recurso afectado
            details: Diccionario con detalles adicionales
            success: Si la acción fue exitosa
            error_message: Mensaje de error si la acción falló
        """
        try:
            # Obtener información del usuario actual
            user_id = None
            user_email = None
            if current_user and current_user.is_authenticated:
                user_id = current_user.id
                user_email = current_user.email
            
            # Obtener información de la request
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                               request.environ.get('REMOTE_ADDR'))
                user_agent = request.headers.get('User-Agent', '')[:500]
            
            # Crear entrada de log
            audit_entry = AuditLog(
                user_id=user_id,
                user_email=user_email,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                details=json.dumps(details) if details else None,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message
            )
            
            db.session.add(audit_entry)
            db.session.commit()
            
            # Log también en archivo
            log_message = f"Action: {action}"
            if user_email:
                log_message += f" | User: {user_email}"
            if resource_type and resource_id:
                log_message += f" | Resource: {resource_type}#{resource_id}"
            if not success and error_message:
                log_message += f" | Error: {error_message}"
            
            if success:
                self.logger.info(log_message)
            else:
                self.logger.error(log_message)
                
        except Exception as e:
            # No fallar si el logging falla
            if self.logger:
                self.logger.error(f"Failed to log audit entry: {str(e)}")
    
    def get_logs(self, user_id=None, action=None, resource_type=None, 
                 start_date=None, end_date=None, limit=100, offset=0):
        """
        Obtener logs de auditoría con filtros.
        
        Args:
            user_id: Filtrar por usuario
            action: Filtrar por acción
            resource_type: Filtrar por tipo de recurso
            start_date: Fecha de inicio
            end_date: Fecha de fin
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            Lista de logs de auditoría
        """
        try:
            query = AuditLog.query
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if action:
                query = query.filter(AuditLog.action == action)
            
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            query = query.order_by(AuditLog.timestamp.desc())
            query = query.offset(offset).limit(limit)
            
            return query.all()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get audit logs: {str(e)}")
            return []
    
    def get_user_activity(self, user_id, days=30):
        """Obtener actividad reciente de un usuario."""
        try:
            from datetime import timedelta
            start_date = datetime.utcnow() - timedelta(days=days)
            
            return self.get_logs(
                user_id=user_id,
                start_date=start_date,
                limit=1000
            )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get user activity: {str(e)}")
            return []
    
    def get_security_events(self, days=7):
        """Obtener eventos de seguridad recientes."""
        try:
            from datetime import timedelta
            start_date = datetime.utcnow() - timedelta(days=days)
            
            security_actions = [
                'login_failed', 'login_success', 'logout', 
                'password_change', 'user_created', 'user_deleted',
                'permission_denied', 'backup_created', 'backup_restored'
            ]
            
            logs = []
            for action in security_actions:
                action_logs = self.get_logs(
                    action=action,
                    start_date=start_date,
                    limit=100
                )
                logs.extend(action_logs)
            
            # Ordenar por timestamp
            logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            return logs[:100]  # Limitar a 100 eventos más recientes
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get security events: {str(e)}")
            return []
    
    def cleanup_old_logs(self, days=365):
        """Limpiar logs antiguos."""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            deleted_count = AuditLog.query.filter(
                AuditLog.timestamp < cutoff_date
            ).delete()
            
            db.session.commit()
            
            self.log('audit_cleanup', details={
                'deleted_logs': deleted_count,
                'cutoff_date': cutoff_date.isoformat()
            })
            
            return deleted_count
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to cleanup old logs: {str(e)}")
            return 0


def audit_action(action, resource_type=None):
    """
    Decorador para auditar automáticamente acciones.
    
    Usage:
        @audit_action('create_payment', 'payment')
        def create_payment():
            # función que crea un pago
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Ejecutar la función
                result = f(*args, **kwargs)
                
                # Determinar resource_id del resultado si es posible
                resource_id = None
                if hasattr(result, 'id'):
                    resource_id = result.id
                elif isinstance(result, dict) and 'id' in result:
                    resource_id = result['id']
                
                # Log exitoso
                audit_logger.log(
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Log de error
                audit_logger.log(
                    action=action,
                    resource_type=resource_type,
                    success=False,
                    error_message=str(e)
                )
                raise
        
        return decorated_function
    return decorator


def log_login_attempt(email, success, error_message=None):
    """Log específico para intentos de login."""
    audit_logger.log(
        action='login_attempt',
        resource_type='user',
        details={'email': email},
        success=success,
        error_message=error_message
    )


def log_permission_denied(action, resource_type=None, resource_id=None):
    """Log específico para denegación de permisos."""
    audit_logger.log(
        action='permission_denied',
        resource_type=resource_type,
        resource_id=resource_id,
        details={'attempted_action': action},
        success=False
    )


def log_data_change(action, resource_type, resource_id, old_data=None, new_data=None):
    """Log específico para cambios de datos."""
    details = {}
    if old_data:
        details['old_data'] = old_data
    if new_data:
        details['new_data'] = new_data
    
    audit_logger.log(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        success=True
    )


# Instancia global del logger de auditoría
audit_logger = AuditLogger()