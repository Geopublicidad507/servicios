from flask import Flask, jsonify, request, render_template
from flask_login import LoginManager
import os
from datetime import datetime
from models_mongo import init_mongo_db, User
import bcrypt
import jwt

# Import blueprints
from routes.auth import auth_bp

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

@app.route('/login')
def login_page():
    return jsonify({'message': 'Use POST /api/auth/login for authentication'})

@app.route('/auth/login')
def auth_login_page():
    return render_template('auth/login.html')

@app.route('/login')
def login_redirect():
    return render_template('auth/login.html')

@app.route('/dashboard')
def dashboard():
    return jsonify({'message': 'Dashboard - Requiere autenticación', 'login_url': '/auth/login'})

@app.route('/dashboard/admin')
def dashboard_admin():
    return jsonify({'message': 'Dashboard Admin - Requiere autenticación', 'login_url': '/auth/login'})

@app.route('/dashboard/resident')
def dashboard_resident():
    return jsonify({'message': 'Dashboard Residente - Requiere autenticación', 'login_url': '/auth/login'})

@app.route('/static/<path:filename>')
def static_files(filename):
    from flask import send_from_directory
    return send_from_directory('static', filename)

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
    if filename in ['login', 'dashboard', 'admin']:
        return jsonify({
            'message': 'Esta es una API REST. Use los endpoints disponibles.',
            'login_endpoint': '/api/auth/login',
            'available_endpoints': {
                'auth': '/api/auth/login',
                'users': '/api/users',
                'health': '/health',
                'stats': '/api/users/stats'
            }
        })
    return jsonify({'error': 'Endpoint not found', 'available_endpoints': ['/api/auth/login', '/api/users', '/health']}), 404

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    print(f'🚀 Iniciando PH Control API en puerto {port}')
    print('🌐 MongoDB Cloud conectado')
    print('📋 Credenciales: admin@phcontrol.com / admin123')
    print('🌍 URL: https://printed-binny-consultor351-faafa5db.koyeb.app/')
    app.run(debug=False, host='0.0.0.0', port=port)