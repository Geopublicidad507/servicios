from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User, Property, Unit, Payment, Expense, MaintenanceTask, Notification, db
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import calendar

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard for admin users"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('dashboard.resident'))
    
    # Get properties managed by current user
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    # Calculate KPIs
    total_properties = len(properties)
    total_units = sum(prop.total_units for prop in properties)
    
    # Financial KPIs for current month
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_income = db.session.query(func.sum(Payment.amount)).join(Unit).join(Property).filter(
        Property.id.in_([p.id for p in properties]),
        extract('month', Payment.payment_date) == current_month,
        extract('year', Payment.payment_date) == current_year
    ).scalar() or 0
    
    monthly_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.property_id.in_([p.id for p in properties]),
        extract('month', Expense.expense_date) == current_month,
        extract('year', Expense.expense_date) == current_year
    ).scalar() or 0
    
    # Pending maintenance tasks
    pending_tasks = MaintenanceTask.query.filter(
        MaintenanceTask.property_id.in_([p.id for p in properties]),
        MaintenanceTask.status.in_(['pending', 'in_progress'])
    ).count()
    
    # Recent payments (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_payments = Payment.query.join(Unit).join(Property).filter(
        Property.id.in_([p.id for p in properties]),
        Payment.created_at >= week_ago
    ).order_by(Payment.created_at.desc()).limit(10).all()
    
    # Overdue payments
    overdue_payments = Payment.query.join(Unit).join(Property).filter(
        Property.id.in_([p.id for p in properties]),
        Payment.status == 'overdue'
    ).count()
    
    # Monthly income chart data (last 12 months)
    income_data = []
    expense_data = []
    months = []
    
    for i in range(12):
        date = datetime.now() - timedelta(days=30*i)
        month = date.month
        year = date.year
        month_name = calendar.month_abbr[month]
        
        income = db.session.query(func.sum(Payment.amount)).join(Unit).join(Property).filter(
            Property.id.in_([p.id for p in properties]),
            extract('month', Payment.payment_date) == month,
            extract('year', Payment.payment_date) == year
        ).scalar() or 0
        
        expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.property_id.in_([p.id for p in properties]),
            extract('month', Expense.expense_date) == month,
            extract('year', Expense.expense_date) == year
        ).scalar() or 0
        
        income_data.insert(0, float(income))
        expense_data.insert(0, float(expenses))
        months.insert(0, f"{month_name} {year}")
    
    return render_template('dashboard/admin.html',
                         properties=properties,
                         total_properties=total_properties,
                         total_units=total_units,
                         monthly_income=monthly_income,
                         monthly_expenses=monthly_expenses,
                         pending_tasks=pending_tasks,
                         recent_payments=recent_payments,
                         overdue_payments=overdue_payments,
                         income_data=income_data,
                         expense_data=expense_data,
                         months=months)

@dashboard_bp.route('/resident')
@login_required
def resident():
    """Dashboard for residents"""
    if current_user.role not in ['resident']:
        return redirect(url_for('dashboard.index'))
    
    # Get user's units
    units = Unit.query.filter_by(owner_id=current_user.id).all()
    
    if not units:
        flash('No tienes unidades asignadas. Contacta al administrador.', 'warning')
        return render_template('dashboard/resident.html', units=[])
    
    # Calculate resident KPIs
    total_units = len(units)
    
    # Current month payments
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_payments = Payment.query.filter(
        Payment.unit_id.in_([u.id for u in units]),
        extract('month', Payment.payment_date) == current_month,
        extract('year', Payment.payment_date) == current_year
    ).all()
    
    monthly_total = sum(p.amount for p in monthly_payments)
    
    # Pending payments
    pending_payments = Payment.query.filter(
        Payment.unit_id.in_([u.id for u in units]),
        Payment.status.in_(['pending', 'overdue'])
    ).all()
    
    # Recent notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Payment history (last 6 months)
    payment_history = []
    for i in range(6):
        date = datetime.now() - timedelta(days=30*i)
        month = date.month
        year = date.year
        month_name = calendar.month_abbr[month]
        
        payments = Payment.query.filter(
            Payment.unit_id.in_([u.id for u in units]),
            extract('month', Payment.payment_date) == month,
            extract('year', Payment.payment_date) == year
        ).all()
        
        total = sum(p.amount for p in payments)
        payment_history.insert(0, {
            'month': f"{month_name} {year}",
            'total': float(total),
            'payments': len(payments)
        })
    
    return render_template('dashboard/resident.html',
                         units=units,
                         total_units=total_units,
                         monthly_total=monthly_total,
                         pending_payments=pending_payments,
                         notifications=notifications,
                         payment_history=payment_history)

@dashboard_bp.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()
    
    if notification:
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 404

@dashboard_bp.route('/api/stats/property/<int:property_id>')
@login_required
def property_stats(property_id):
    """Get property statistics for AJAX requests"""
    property_obj = Property.query.get_or_404(property_id)
    
    # Check permissions
    if current_user.role == 'admin_ph' and property_obj.admin_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Monthly stats
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
    
    # Unit occupancy
    total_units = property_obj.total_units
    occupied_units = Unit.query.filter_by(property_id=property_id, is_occupied=True).count()
    occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
    
    # Maintenance tasks
    pending_tasks = MaintenanceTask.query.filter_by(
        property_id=property_id,
        status='pending'
    ).count()
    
    return jsonify({
        'monthly_income': float(monthly_income),
        'monthly_expenses': float(monthly_expenses),
        'net_income': float(monthly_income - monthly_expenses),
        'occupancy_rate': round(occupancy_rate, 1),
        'occupied_units': occupied_units,
        'total_units': total_units,
        'pending_tasks': pending_tasks
    })