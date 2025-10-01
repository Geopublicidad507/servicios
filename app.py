from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from flask_mail import Mail
from models import db, User
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Import blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.financial import financial_bp
from routes.communication import communication_bp
from routes.maintenance import maintenance_bp
from routes.security import security_bp
from routes.legal import legal_bp
from routes.documents import documents_bp
from routes.admin import admin_bp
from routes.backup import backup_bp
from routes.audit import audit_bp
from routes.notifications import notifications_bp
from routes.api import api_bp
from routes.reports import reports_bp

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ph_control.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Upload configuration
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Backup configuration
    app.config['BACKUP_DIR'] = os.path.join(app.root_path, 'backups')
    app.config['MAX_BACKUPS'] = int(os.environ.get('MAX_BACKUPS', 30))
    
    # Mail configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize Flask-Mail
    mail = Mail(app)
    
    # Initialize Backup Manager
    from utils.backup import backup_manager
    backup_manager.init_app(app)
    
    # Initialize Audit Logger
    from utils.audit import audit_logger
    audit_logger.init_app(app)
    
    # Initialize Notification Manager
    from utils.notifications import notification_manager
    notification_manager.init_app(app, mail)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(financial_bp, url_prefix='/financial')
    app.register_blueprint(communication_bp, url_prefix='/communication')
    app.register_blueprint(maintenance_bp, url_prefix='/maintenance')
    app.register_blueprint(security_bp, url_prefix='/security')
    app.register_blueprint(legal_bp, url_prefix='/legal')
    app.register_blueprint(documents_bp, url_prefix='/documents')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(backup_bp, url_prefix='/backup')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    # Root route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'resident':
                return redirect(url_for('dashboard.resident'))
            else:
                return redirect(url_for('dashboard.index'))
        return render_template('landing.html')

    # Favicon route
    @app.route('/favicon.ico')
    def favicon():
        return '', 204
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    # Template filters
    @app.template_filter('datetime')
    def datetime_filter(value, format='%d/%m/%Y %H:%M'):
        if value is None:
            return ""
        return value.strftime(format)
    
    @app.template_filter('date')
    def date_filter(value, format='%d/%m/%Y'):
        if value is None:
            return ""
        return value.strftime(format)
    
    @app.template_filter('currency')
    def currency_filter(value):
        if value is None:
            return "$0.00"
        return "${:,.2f}".format(float(value))
    
    @app.template_filter('status_badge')
    def status_badge_filter(status):
        status_classes = {
            'active': 'success',
            'inactive': 'secondary',
            'pending': 'warning',
            'completed': 'success',
            'cancelled': 'danger',
            'open': 'primary',
            'in_progress': 'info',
            'resolved': 'success',
            'closed': 'secondary',
            'paid': 'success',
            'overdue': 'danger',
            'scheduled': 'primary'
        }
        css_class = status_classes.get(status, 'secondary')
        display_text = status.replace('_', ' ').title()
        return f'<span class="badge bg-{css_class}">{display_text}</span>'
    
    # Context processors
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    @app.context_processor
    def inject_user_notifications():
        if current_user.is_authenticated:
            from models import Notification
            unread_notifications = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()
            return {'unread_notifications_count': unread_notifications}
        return {'unread_notifications_count': 0}
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if it doesn't exist
        admin_user = User.query.filter_by(email='admin@phcontrol.com').first()
        if not admin_user:
            admin_user = User(
                email='admin@phcontrol.com',
                first_name='Administrador',
                last_name='General',
                role='admin_general'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created: admin@phcontrol.com / admin123")
    
    return app

# Create the app instance
app = create_app()

# Make mail available globally for routes
mail = Mail(app)

if __name__ == '__main__':
    try:
        # Inicializar sistema primero
        print("🚀 Iniciando PH Control...")
        
        # Verificar y crear base de datos
        with app.app_context():
            print("🔧 Inicializando sistema...")
            
            # Probar conexión
            try:
                db.create_all()
                print("🧪 Probando conexión a la base de datos...")
                print(f"🔍 Probando conexión a: {app.config['SQLALCHEMY_DATABASE_URI']}")
                print("✅ Conexión exitosa a la base de datos")
                
                # Crear usuario administrador si no existe
                admin_user = User.query.filter_by(email='admin@phcontrol.com').first()
                if not admin_user:
                    admin_user = User(
                        email='admin@phcontrol.com',
                        first_name='Administrador',
                        last_name='General',
                        role='admin_general',
                        is_active=True
                    )
                    admin_user.set_password('admin123')
                    db.session.add(admin_user)
                    db.session.commit()
                    print("👤 Usuario administrador creado")
                else:
                    # Verificar contraseña
                    if not admin_user.check_password('admin123'):
                        admin_user.set_password('admin123')
                        db.session.commit()
                        print("🔧 Contraseña de administrador corregida")
                
                print("✅ Sistema inicializado correctamente")
                
            except Exception as e:
                print(f"❌ Error en inicialización: {e}")
        
        print("✅ Sistema inicializado")
        
        # Development server
        port = int(os.environ.get('PORT', 5003))
        debug = os.environ.get('DEBUG', 'True').lower() == 'true'
        
        print("🌐 Iniciando aplicación Flask...")
        print(f"Disponible en: http://localhost:{port}")
        
        from utils.backup import backup_manager
        backup_manager.start_scheduler()
        
        print(f"🚀 Iniciando PH Control en puerto {port}")
        print(f"🐛 Debug mode: {debug}")
        print(f"🌐 Accesible en: http://0.0.0.0:{port}")
        print("=" * 50)
        
        app.run(debug=debug, host='0.0.0.0', port=port, threaded=True)
    except Exception as e:
        print(f"❌ Error iniciando la aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)session.commit()
                        print("🔧 Contraseña de administrador corregida")
                
                print("✅ Sistema inicializado correctamente")
                
            except Exception as e:
                print(f"❌ Error en inicialización: {e}")
        
        print("✅ Sistema inicializado")
        
        # Development server
        port = int(os.environ.get('PORT', 5003))
        debug = os.environ.get('DEBUG', 'True').lower() == 'true'
        
        print("🌐 Iniciando aplicación Flask...")
        print(f"Disponible en: http://localhost:{port}")
        
        from utils.backup import backup_manager
        backup_manager.start_scheduler()
        
        print(f"🚀 Iniciando PH Control en puerto {port}")
        print(f"🐛 Debug mode: {debug}")
        print(f"🌐 Accesible en: http://0.0.0.0:{port}")
        print("=" * 50)
        
        app.run(debug=debug, host='0.0.0.0', port=port, threaded=True)
    except Exception as e:
        print(f"❌ Error iniciando la aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)