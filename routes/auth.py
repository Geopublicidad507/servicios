from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db
from datetime import datetime
from utils.audit import audit_logger, log_login_attempt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash('Por favor completa todos los campos.', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
        
        if user:
            
            # Log successful login
            log_login_attempt(email, success=True)
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # Redirect based on user role
            if user.role == 'admin_general':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'admin_ph':
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('dashboard.resident'))
        else:
            # Log failed login attempt
            log_login_attempt(email, success=False, error_message='Invalid credentials')
            flash('Email o contraseña incorrectos.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([email, first_name, last_name, password, confirm_password]):
            flash('Por favor completa todos los campos obligatorios.', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Ya existe un usuario con este email.', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='resident'  # Default role
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registro exitoso. Puedes iniciar sesión ahora.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la cuenta. Intenta nuevamente.', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    # Log logout before actually logging out
    audit_logger.log('logout', resource_type='user', resource_id=current_user.id)
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # TODO: Implement password reset email functionality
            flash('Se ha enviado un enlace de recuperación a tu email.', 'info')
        else:
            flash('No se encontró una cuenta con ese email.', 'error')
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.phone = request.form.get('phone')
        
        # Change password if provided
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password:
            if not current_user.check_password(current_password):
                flash('Contraseña actual incorrecta.', 'error')
                return render_template('auth/profile.html')
            
            if new_password != confirm_password:
                flash('Las nuevas contraseñas no coinciden.', 'error')
                return render_template('auth/profile.html')
            
            if len(new_password) < 6:
                flash('La nueva contraseña debe tener al menos 6 caracteres.', 'error')
                return render_template('auth/profile.html')
            
            current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Perfil actualizado exitosamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el perfil.', 'error')
    
    return render_template('auth/profile.html')
