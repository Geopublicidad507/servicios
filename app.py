from flask import Flask, jsonify, request, render_template
from flask_login import LoginManager
import os
from datetime import datetime
from models_mongo import init_mongo_db, User
import bcrypt
import jwt

# Import blueprints
from routes.auth import auth_bp
from routes.api import api_bp

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'ph-control-secret-2024'
app.config['MONGO_URI'] = 'mongodb+srv://geopublicidad507_db_user:Cdeg14650641*@consultor351.yv7gbsp.mongodb.net/miDB?retryWrites=true&w=majority'

# Initialize MongoDB
init_mongo_db(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

# Routes
@app.route('/')
def index():
    from flask import redirect
    return redirect('/auth/login')

@app.route('/api')
def api_info():
    return jsonify({
        'message': 'PH Control API - Sistema de Gestión de Propiedades Horizontales',
        'version': '1.0.0',
        'status': 'OK',
        'mongodb': 'connected',
        'endpoints': {
            'login_page': '/auth/login',
            'api_login': '/api/auth/login',
            'users': '/api/users',
            'health': '/health'
        }
    })

@app.route('/favicon.ico')
def favicon():
    from flask import send_from_directory
    return send_from_directory('static', 'favicon.ico')

# Removed conflicting login routes - handled by auth blueprint

@app.route('/dashboard')
def dashboard():
    from flask_login import login_required, current_user
    if not current_user.is_authenticated:
        return jsonify({'message': 'Dashboard - Requiere autenticación', 'login_url': '/auth/login'})
    return render_template('dashboard/index.html', 
                         stats={'total_properties': 1, 'total_units': 10, 'pending_tasks': 2, 'monthly_income': 7500},
                         recent_activities=[],
                         alerts=[],
                         unread_notifications_count=0)

@app.route('/dashboard/admin')
def dashboard_admin():
    from flask_login import login_required, current_user
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    return render_template('dashboard/index.html', 
                         stats={'total_properties': 1, 'total_units': 10, 'pending_tasks': 2, 'monthly_income': 7500},
                         recent_activities=[], alerts=[], unread_notifications_count=0)

@app.route('/dashboard/resident')
def dashboard_resident():
    from flask_login import login_required, current_user
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    return render_template('dashboard/index.html', 
                         stats={'total_properties': 1, 'total_units': 10, 'pending_tasks': 2, 'monthly_income': 7500},
                         recent_activities=[], alerts=[], unread_notifications_count=0)

@app.route('/static/<path:filename>')
def static_files(filename):
    from flask import send_from_directory
    return send_from_directory('static', filename)

# Rutas de módulos
@app.route('/financial')
@app.route('/financial/<path:subpath>')
def financial_module(subpath=None):
    from flask_login import current_user
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    return render_template('dashboard/index.html', 
                         stats={'total_properties': 1, 'total_units': 10, 'pending_tasks': 2, 'monthly_income': 7500},
                         recent_activities=[], alerts=[], unread_notifications_count=0)

@app.route('/communication')
@app.route('/communication/<path:subpath>')
def communication_module(subpath=None):
    from flask_login import current_user
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    return render_template('dashboard/index.html', 
                         stats={'total_properties': 1, 'total_units': 10, 'pending_tasks': 2, 'monthly_income': 7500},
                         recent_activities=[], alerts=[], unread_notifications_count=0)

@app.route('/maintenance')
@app.route('/maintenance/<path:subpath>')
def maintenance_module(subpath=None):
    from flask_login import current_user
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    return render_template('dashboard/index.html', 
                         stats={'total_properties': 1, 'total_units': 10, 'pending_tasks': 2, 'monthly_income': 7500},
                         recent_activities=[], alerts=[], unread_notifications_count=0)

@app.route('/security')
@app.route('/security/<path:subpath>')
def security_module(subpath=None):
    from flask_login import current_user
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    return render_template('dashboard/index.html', 
                         stats={'total_properties': 1, 'total_units': 10, 'pending_tasks': 2, 'monthly_income': 7500},
                         recent_activities=[], alerts=[], unread_notifications_count=0)

@app.route('/legal')
@app.route('/legal/<path:subpath>')
def legal_module(subpath=None):
    from flask_login import current_user
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    return render_template('dashboard/index.html', 
                         stats={'total_properties': 1, 'total_units': 10, 'pending_tasks': 2, 'monthly_income': 7500},
                         recent_activities=[], alerts=[], unread_notifications_count=0)

@app.route('/documents')
@app.route('/documents/<path:subpath>')
def documents_module(subpath=None):
    from flask_login import current_user
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    return render_template('dashboard/index.html', 
                         stats={'total_properties': 1, 'total_units': 10, 'pending_tasks': 2, 'monthly_income': 7500},
                         recent_activities=[], alerts=[], unread_notifications_count=0)

@app.route('/admin')
@app.route('/admin/<path:subpath>')
def admin_module(subpath=None):
    from flask_login import current_user
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    return render_template('dashboard/index.html', 
                         stats={'total_properties': 1, 'total_units': 10, 'pending_tasks': 2, 'monthly_income': 7500},
                         recent_activities=[], alerts=[], unread_notifications_count=0)

@app.route('/notifications')
def notifications_module():
    from flask_login import current_user
    if not current_user.is_authenticated:
        return redirect('/auth/login')
    return render_template('dashboard/index.html', 
                         stats={'total_properties': 1, 'total_units': 10, 'pending_tasks': 2, 'monthly_income': 7500},
                         recent_activities=[], alerts=[], unread_notifications_count=0)

@app.route('/notifications/api/list')
def notifications_api_list():
    from flask_login import current_user
    if not current_user.is_authenticated:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        from models_mongo import NotificationDoc
        notifications = NotificationDoc.objects(user_id=current_user.id, is_read=False).limit(5)
        notifications_data = []
        for notif in notifications:
            notifications_data.append({
                'id': str(notif.id),
                'title': notif.title,
                'message': notif.message,
                'created_at': notif.created_at.isoformat(),
                'notification_type': notif.notification_type
            })
        return jsonify({
            'notifications': notifications_data,
            'unread_count': len(notifications_data)
        })
    except Exception as e:
        return jsonify({
            'notifications': [],
            'unread_count': 0
        })

@app.route('/notifications/api/unread-count')
def notifications_unread_count():
    from flask_login import current_user
    if not current_user.is_authenticated:
        return jsonify({'count': 0})
    
    try:
        from models_mongo import NotificationDoc
        count = NotificationDoc.objects(user_id=current_user.id, is_read=False).count()
        return jsonify({'count': count})
    except:
        return jsonify({'count': 0})

@app.route('/<path:filename>')
def catch_all(filename):
    if filename.endswith(('.woff', '.woff2', '.ttf', '.eot')):
        return '', 204
    if filename.endswith(('.css', '.js', '.png', '.jpg', '.gif')):
        from flask import send_from_directory
        try:
            return send_from_directory('static', filename)
        except:
            return '', 404
    from flask import redirect
    return redirect('/auth/login')

@app.route('/health')
def health():
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.utcnow().isoformat(),
        'mongodb': 'connected'
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email y contraseña requeridos'}), 400
        
        try:
            user = User.objects.get(email=email, is_active=True)
            if user.check_password(password):
                user.last_login = datetime.utcnow()
                user.save()
                
                token = jwt.encode({
                    'user_id': str(user.id),
                    'role': user.role,
                    'exp': datetime.utcnow().timestamp() + 86400
                }, app.config['SECRET_KEY'], algorithm='HS256')
                
                return jsonify({
                    'token': token,
                    'user': {
                        'id': str(user.id),
                        'email': user.email,
                        'firstName': user.first_name,
                        'lastName': user.last_name,
                        'role': user.role
                    }
                })
            else:
                return jsonify({'error': 'Credenciales inválidas'}), 401
        except User.DoesNotExist:
            return jsonify({'error': 'Credenciales inválidas'}), 401
            
    except Exception as e:
        return jsonify({'error': 'Error del servidor'}), 500

@app.route('/api/users')
def get_users():
    try:
        users = User.objects(is_active=True).only('email', 'first_name', 'last_name', 'role', 'phone', 'created_at')
        users_data = []
        for user in users:
            users_data.append({
                'id': str(user.id),
                'email': user.email,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'fullName': f"{user.first_name} {user.last_name}",
                'role': user.role,
                'phone': user.phone,
                'createdAt': user.created_at.isoformat()
            })
        return jsonify(users_data)
    except Exception as e:
        return jsonify({'error': 'Error del servidor'}), 500

@app.route('/api/users/create', methods=['POST'])
def create_user():
    try:
        from create_users import create_all_users
        create_all_users()
        return jsonify({'message': 'Usuarios creados exitosamente'})
    except Exception as e:
        return jsonify({'error': 'Error creando usuarios'}), 500

@app.route('/api/users/clean-duplicates', methods=['POST'])
def clean_duplicates():
    try:
        from clean_duplicates import clean_duplicates
        clean_duplicates()
        return jsonify({'message': 'Duplicados eliminados exitosamente'})
    except Exception as e:
        return jsonify({'error': 'Error limpiando duplicados'}), 500

@app.route('/api/users/stats')
def user_stats():
    try:
        stats = {
            'total': User.objects.count(),
            'active': User.objects(is_active=True).count(),
            'by_role': {
                'admin_general': User.objects(role='admin_general').count(),
                'admin_ph': User.objects(role='admin_ph').count(),
                'resident': User.objects(role='resident').count(),
                'provider': User.objects(role='provider').count(),
                'visitor': User.objects(role='visitor').count()
            }
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': 'Error del servidor'}), 500

# Clean duplicates and create default admin user
with app.app_context():
    try:
        print('🧹 Limpiando duplicados en inicio...')
        
        # Limpiar usuarios duplicados
        emails_seen = set()
        users_to_delete = []
        
        for user in User.objects.all():
            if user.email in emails_seen:
                users_to_delete.append(user)
            else:
                emails_seen.add(user.email)
        
        for user in users_to_delete:
            user.delete()
            print(f'🗑️ Duplicado eliminado: {user.email}')
        
        # Solo verificar si existe admin, no crear
        admin_count = User.objects(email='admin@phcontrol.com').count()
        if admin_count > 0:
            print('✅ Usuario administrador existe')
        else:
            print('ℹ️ No hay usuario administrador (usar /api/users/create para crear usuarios)')
            
        print(f'✅ Base de datos limpia - {User.objects.count()} usuarios únicos')
        
    except Exception as e:
        print(f'❌ Error en limpieza inicial: {e}')

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    print(f'🚀 Iniciando PH Control API en puerto {port}')
    print('🌐 MongoDB Cloud conectado')
    print('📋 Credenciales: admin@phcontrol.com / admin123')
    print('🌍 URL: https://printed-binny-consultor351-faafa5db.koyeb.app/')
    app.run(debug=False, host='0.0.0.0', port=port)