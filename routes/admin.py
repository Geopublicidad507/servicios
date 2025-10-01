from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import User, Property, Unit, Payment, Expense, MaintenanceTask, Document, Assembly, Ticket, VisitorLog, Budget, db
from sqlalchemy import func, extract, and_
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash
import calendar

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    if current_user.role != 'admin_general':
        return redirect(url_for('dashboard.index'))
    
    # System-wide statistics
    total_properties = Property.query.filter_by(is_active=True).count()
    total_units = db.session.query(func.sum(Property.total_units)).filter_by(is_active=True).scalar() or 0
    total_users = User.query.filter_by(is_active=True).count()
    
    # Financial overview (current month)
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_income = db.session.query(func.sum(Payment.amount)).filter(
        extract('month', Payment.payment_date) == current_month,
        extract('year', Payment.payment_date) == current_year
    ).scalar() or 0
    
    monthly_expenses = db.session.query(func.sum(Expense.amount)).filter(
        extract('month', Expense.expense_date) == current_month,
        extract('year', Expense.expense_date) == current_year
    ).scalar() or 0
    
    # Recent activity
    recent_properties = Property.query.order_by(Property.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Pending tasks across all properties
    pending_tasks = MaintenanceTask.query.filter_by(status='pending').count()
    
    # Open tickets
    open_tickets = Ticket.query.filter(Ticket.status.in_(['open', 'in_progress'])).count()
    
    # Monthly growth data (last 12 months)
    growth_data = []
    for i in range(12):
        date_obj = datetime.now() - timedelta(days=30*i)
        month = date_obj.month
        year = date_obj.year
        month_name = calendar.month_abbr[month]
        
        # Properties created in this month
        properties_count = Property.query.filter(
            extract('month', Property.created_at) == month,
            extract('year', Property.created_at) == year
        ).count()
        
        # Users registered in this month
        users_count = User.query.filter(
            extract('month', User.created_at) == month,
            extract('year', User.created_at) == year
        ).count()
        
        growth_data.insert(0, {
            'month': f"{month_name} {year}",
            'properties': properties_count,
            'users': users_count
        })
    
    return render_template('admin/dashboard.html',
                         total_properties=total_properties,
                         total_units=total_units,
                         total_users=total_users,
                         monthly_income=monthly_income,
                         monthly_expenses=monthly_expenses,
                         recent_properties=recent_properties,
                         recent_users=recent_users,
                         pending_tasks=pending_tasks,
                         open_tickets=open_tickets,
                         growth_data=growth_data)

@admin_bp.route('/properties')
@login_required
def properties():
    """Properties management"""
    if current_user.role != 'admin_general':
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search')
    status = request.args.get('status')
    
    # Build query
    query = Property.query
    
    if search:
        query = query.filter(
            db.or_(
                Property.name.ilike(f'%{search}%'),
                Property.code.ilike(f'%{search}%'),
                Property.address.ilike(f'%{search}%')
            )
        )
    
    if status == 'active':
        query = query.filter(Property.is_active == True)
    elif status == 'inactive':
        query = query.filter(Property.is_active == False)
    
    properties = query.order_by(Property.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/properties.html',
                         properties=properties,
                         filters={'search': search, 'status': status})

@admin_bp.route('/properties/create', methods=['GET', 'POST'])
@login_required
def create_property():
    """Create new property"""
    if current_user.role != 'admin_general':
        flash('No tienes permisos para crear propiedades.', 'error')
        return redirect(url_for('admin.properties'))
    
    # Get available administrators
    admins = User.query.filter(User.role.in_(['admin_ph', 'admin_general'])).all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        address = request.form.get('address')
        total_units = request.form.get('total_units', type=int)
        admin_id = request.form.get('admin_id', type=int)
        monthly_fee = request.form.get('monthly_fee', type=float)
        
        # Validation
        if not all([name, code, address, total_units, admin_id]):
            flash('Por favor completa todos los campos obligatorios.', 'error')
            return render_template('admin/create_property.html', admins=admins)
        
        # Check if code already exists
        if Property.query.filter_by(code=code).first():
            flash('Ya existe una propiedad con este código.', 'error')
            return render_template('admin/create_property.html', admins=admins)
        
        # Check if admin exists
        admin = User.query.get(admin_id)
        if not admin or admin.role not in ['admin_ph', 'admin_general']:
            flash('Administrador no válido.', 'error')
            return render_template('admin/create_property.html', admins=admins)
        
        property_obj = Property(
            name=name,
            code=code,
            address=address,
            total_units=total_units,
            admin_id=admin_id,
            monthly_fee=monthly_fee or 0.00
        )
        
        try:
            db.session.add(property_obj)
            db.session.commit()
            flash('Propiedad creada exitosamente.', 'success')
            return redirect(url_for('admin.view_property', property_id=property_obj.id))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la propiedad.', 'error')
    
    return render_template('admin/create_property.html', admins=admins)

@admin_bp.route('/properties/<int:property_id>')
@login_required
def view_property(property_id):
    """View property details"""
    if current_user.role != 'admin_general':
        return redirect(url_for('dashboard.index'))
    
    property_obj = Property.query.get_or_404(property_id)
    
    # Get property statistics
    total_units = property_obj.total_units
    occupied_units = Unit.query.filter_by(property_id=property_id, is_occupied=True).count()
    occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
    
    # Financial data (current month)
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_income = db.session.query(func.sum(Payment.amount)).join(Unit).filter(
        Unit.property_id == property_id,
        extract('month', Payment.payment_date) == current_month,
        extract('year', Payment.payment_date) == current_year
    ).scalar() or 0
    
    monthly_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.property_id == property_id,
        extract('month', Expense.expense_date) == current_month,
        extract('year', Expense.expense_date) == current_year
    ).scalar() or 0
    
    # Recent activity
    recent_payments = Payment.query.join(Unit).filter(
        Unit.property_id == property_id
    ).order_by(Payment.created_at.desc()).limit(5).all()
    
    recent_expenses = Expense.query.filter_by(
        property_id=property_id
    ).order_by(Expense.created_at.desc()).limit(5).all()
    
    pending_tasks = MaintenanceTask.query.filter_by(
        property_id=property_id,
        status='pending'
    ).count()
    
    return render_template('admin/view_property.html',
                         property=property_obj,
                         occupancy_rate=occupancy_rate,
                         occupied_units=occupied_units,
                         monthly_income=monthly_income,
                         monthly_expenses=monthly_expenses,
                         recent_payments=recent_payments,
                         recent_expenses=recent_expenses,
                         pending_tasks=pending_tasks)

@admin_bp.route('/users')
@login_required
def users():
    """Users management"""
    if current_user.role != 'admin_general':
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search')
    role = request.args.get('role')
    status = request.args.get('status')
    
    # Build query
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if status == 'active':
        query = query.filter(User.is_active == True)
    elif status == 'inactive':
        query = query.filter(User.is_active == False)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html',
                         users=users,
                         filters={'search': search, 'role': role, 'status': status})

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    """Create new user"""
    if current_user.role != 'admin_general':
        flash('No tienes permisos para crear usuarios.', 'error')
        return redirect(url_for('admin.users'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        role = request.form.get('role')
        password = request.form.get('password')
        
        # Validation
        if not all([email, first_name, last_name, role, password]):
            flash('Por favor completa todos los campos obligatorios.', 'error')
            return render_template('admin/create_user.html')
        
        if role not in ['admin_general', 'admin_ph', 'resident', 'provider']:
            flash('Rol no válido.', 'error')
            return render_template('admin/create_user.html')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Ya existe un usuario con este email.', 'error')
            return render_template('admin/create_user.html')
        
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Usuario creado exitosamente.', 'success')
            return redirect(url_for('admin.view_user', user_id=user.id))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el usuario.', 'error')
    
    return render_template('admin/create_user.html')

@admin_bp.route('/users/<int:user_id>')
@login_required
def view_user(user_id):
    """View user details"""
    if current_user.role != 'admin_general':
        return redirect(url_for('dashboard.index'))
    
    user = User.query.get_or_404(user_id)
    
    # Get user statistics
    user_units = Unit.query.filter_by(owner_id=user_id).all()
    user_payments = Payment.query.filter_by(user_id=user_id).count()
    user_tickets = Ticket.query.filter_by(user_id=user_id).count()
    
    # Recent activity
    recent_payments = Payment.query.filter_by(user_id=user_id).order_by(
        Payment.created_at.desc()
    ).limit(5).all()
    
    recent_tickets = Ticket.query.filter_by(user_id=user_id).order_by(
        Ticket.created_at.desc()
    ).limit(5).all()
    
    return render_template('admin/view_user.html',
                         user=user,
                         user_units=user_units,
                         user_payments=user_payments,
                         user_tickets=user_tickets,
                         recent_payments=recent_payments,
                         recent_tickets=recent_tickets)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit user"""
    if current_user.role != 'admin_general':
        flash('No tienes permisos para editar usuarios.', 'error')
        return redirect(url_for('admin.view_user', user_id=user_id))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        user.role = request.form.get('role')
        user.is_active = request.form.get('is_active') == 'on'
        
        # Update password if provided
        new_password = request.form.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Usuario actualizado exitosamente.', 'success')
            return redirect(url_for('admin.view_user', user_id=user_id))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el usuario.', 'error')
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/system')
@login_required
def system():
    """System settings and information"""
    if current_user.role != 'admin_general':
        return redirect(url_for('dashboard.index'))
    
    # System statistics
    system_stats = {
        'total_properties': Property.query.count(),
        'active_properties': Property.query.filter_by(is_active=True).count(),
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_units': db.session.query(func.sum(Property.total_units)).scalar() or 0,
        'total_payments': Payment.query.count(),
        'total_expenses': Expense.query.count(),
        'total_documents': Document.query.count(),
        'total_assemblies': Assembly.query.count(),
        'total_tickets': Ticket.query.count(),
        'total_maintenance_tasks': MaintenanceTask.query.count(),
        'total_visitor_logs': VisitorLog.query.count()
    }
    
    # Database size (approximate)
    db_size = "N/A"  # Would need specific database queries
    
    # Recent system activity
    recent_logins = User.query.filter(
        User.last_login.isnot(None)
    ).order_by(User.last_login.desc()).limit(10).all()
    
    return render_template('admin/system.html',
                         system_stats=system_stats,
                         db_size=db_size,
                         recent_logins=recent_logins)

@admin_bp.route('/reports')
@login_required
def reports():
    """System reports"""
    if current_user.role != 'admin_general':
        return redirect(url_for('dashboard.index'))
    
    return render_template('admin/reports.html')

@admin_bp.route('/api/stats/overview')
@login_required
def stats_overview():
    """Get system overview statistics for AJAX"""
    if current_user.role != 'admin_general':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Current month statistics
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    stats = {
        'properties': Property.query.filter_by(is_active=True).count(),
        'users': User.query.filter_by(is_active=True).count(),
        'monthly_income': float(db.session.query(func.sum(Payment.amount)).filter(
            extract('month', Payment.payment_date) == current_month,
            extract('year', Payment.payment_date) == current_year
        ).scalar() or 0),
        'monthly_expenses': float(db.session.query(func.sum(Expense.amount)).filter(
            extract('month', Expense.expense_date) == current_month,
            extract('year', Expense.expense_date) == current_year
        ).scalar() or 0),
        'pending_tasks': MaintenanceTask.query.filter_by(status='pending').count(),
        'open_tickets': Ticket.query.filter(Ticket.status.in_(['open', 'in_progress'])).count()
    }
    
    stats['net_income'] = stats['monthly_income'] - stats['monthly_expenses']
    
    return jsonify(stats)

@admin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    if current_user.role != 'admin_general':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow deactivating yourself
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'No puedes desactivar tu propia cuenta'}), 400
    
    user.is_active = not user.is_active
    
    try:
        db.session.commit()
        status = 'activado' if user.is_active else 'desactivado'
        return jsonify({'success': True, 'message': f'Usuario {status} exitosamente', 'is_active': user.is_active})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error al actualizar el usuario'}), 500

@admin_bp.route('/api/properties/<int:property_id>/toggle-status', methods=['POST'])
@login_required
def toggle_property_status(property_id):
    """Toggle property active status"""
    if current_user.role != 'admin_general':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    property_obj = Property.query.get_or_404(property_id)
    property_obj.is_active = not property_obj.is_active
    
    try:
        db.session.commit()
        status = 'activada' if property_obj.is_active else 'desactivada'
        return jsonify({'success': True, 'message': f'Propiedad {status} exitosamente', 'is_active': property_obj.is_active})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error al actualizar la propiedad'}), 500