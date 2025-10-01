from flask import Flask, jsonify, request
from flask_login import LoginManager
import os
from datetime import datetime
from models_mongo import init_mongo_db, User
import bcrypt
import jwt

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
    return jsonify({
        'message': 'PH Control API - Sistema de Gestión de Propiedades Horizontales',
        'version': '1.0.0',
        'status': 'OK',
        'mongodb': 'connected',
        'endpoints': {
            'login': '/api/auth/login',
            'users': '/api/users',
            'health': '/health'
        }
    })

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
        users = User.objects(is_active=True).only('email', 'first_name', 'last_name', 'role', 'created_at')
        users_data = []
        for user in users:
            users_data.append({
                'id': str(user.id),
                'email': user.email,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'role': user.role,
                'createdAt': user.created_at.isoformat()
            })
        return jsonify(users_data)
    except Exception as e:
        return jsonify({'error': 'Error del servidor'}), 500

# Create default admin user
with app.app_context():
    try:
        admin = User.objects.get(email='admin@phcontrol.com')
        print('✅ Usuario administrador existe')
    except User.DoesNotExist:
        admin = User(
            email='admin@phcontrol.com',
            first_name='Administrador',
            last_name='General',
            role='admin_general',
            is_active=True
        )
        admin.set_password('admin123')
        admin.save()
        print('✅ Usuario administrador creado: admin@phcontrol.com / admin123')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    print(f'🚀 Iniciando PH Control API en puerto {port}')
    print('🌐 MongoDB Cloud conectado')
    print('📋 Credenciales: admin@phcontrol.com / admin123')
    app.run(debug=False, host='0.0.0.0', port=port)