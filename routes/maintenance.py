from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Property, MaintenanceTask, User, Notification, db
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
import os

maintenance_bp = Blueprint('maintenance', __name__)

@maintenance_bp.route('/')
@login_required
def index():
    """Maintenance dashboard"""
    if current_user.role not in ['admin_general', 'admin_ph', 'provider']:
        return redirect(url_for('dashboard.resident'))
    
    # Get properties based on user role
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    elif current_user.role == 'admin_ph':
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    else:  # provider
        properties = Property.query.filter_by(is_active=True).all()
    
    # Get maintenance statistics
    total_tasks = MaintenanceTask.query.filter(
        MaintenanceTask.property_id.in_([p.id for p in properties])
    ).count()
    
    pending_tasks = MaintenanceTask.query.filter(
        MaintenanceTask.property_id.in_([p.id for p in properties]),
        MaintenanceTask.status == 'pending'
    ).count()
    
    in_progress_tasks = MaintenanceTask.query.filter(
        MaintenanceTask.property_id.in_([p.id for p in properties]),
        MaintenanceTask.status == 'in_progress'
    ).count()
    
    completed_tasks = MaintenanceTask.query.filter(
        MaintenanceTask.property_id.in_([p.id for p in properties]),
        MaintenanceTask.status == 'completed'
    ).count()
    
    # Overdue tasks
    overdue_tasks = MaintenanceTask.query.filter(
        MaintenanceTask.property_id.in_([p.id for p in properties]),
        MaintenanceTask.status.in_(['pending', 'in_progress']),
        MaintenanceTask.scheduled_date < date.today()
    ).all()
    
    # Upcoming tasks (next 7 days)
    next_week = date.today() + timedelta(days=7)
    upcoming_tasks = MaintenanceTask.query.filter(
        MaintenanceTask.property_id.in_([p.id for p in properties]),
        MaintenanceTask.status.in_(['pending', 'in_progress']),
        MaintenanceTask.scheduled_date.between(date.today(), next_week)
    ).all()
    
    # Recent tasks
    recent_tasks = MaintenanceTask.query.filter(
        MaintenanceTask.property_id.in_([p.id for p in properties])
    ).order_by(MaintenanceTask.created_at.desc()).limit(10).all()
    
    return render_template('maintenance/index.html',
                         properties=properties,
                         total_tasks=total_tasks,
                         pending_tasks=pending_tasks,
                         in_progress_tasks=in_progress_tasks,
                         completed_tasks=completed_tasks,
                         overdue_tasks=overdue_tasks,
                         upcoming_tasks=upcoming_tasks,
                         recent_tasks=recent_tasks)

@maintenance_bp.route('/tasks')
@login_required
def tasks():
    """Maintenance tasks list"""
    page = request.args.get('page', 1, type=int)
    property_id = request.args.get('property_id', type=int)
    status = request.args.get('status')
    task_type = request.args.get('task_type')
    priority = request.args.get('priority')
    
    # Get properties based on user role
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    elif current_user.role == 'admin_ph':
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    else:
        properties = Property.query.filter_by(is_active=True).all()
    
    # Build query
    query = MaintenanceTask.query.filter(
        MaintenanceTask.property_id.in_([p.id for p in properties])
    )
    
    # Apply filters
    if property_id:
        query = query.filter(MaintenanceTask.property_id == property_id)
    if status:
        query = query.filter(MaintenanceTask.status == status)
    if task_type:
        query = query.filter(MaintenanceTask.task_type == task_type)
    if priority:
        query = query.filter(MaintenanceTask.priority == priority)
    
    tasks = query.order_by(MaintenanceTask.scheduled_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('maintenance/tasks.html',
                         tasks=tasks,
                         properties=properties,
                         filters={
                             'property_id': property_id,
                             'status': status,
                             'task_type': task_type,
                             'priority': priority
                         })

@maintenance_bp.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    """Create new maintenance task"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        flash('No tienes permisos para crear tareas de mantenimiento.', 'error')
        return redirect(url_for('maintenance.tasks'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        property_id = request.form.get('property_id', type=int)
        title = request.form.get('title')
        description = request.form.get('description')
        task_type = request.form.get('task_type')
        priority = request.form.get('priority', 'medium')
        assigned_to = request.form.get('assigned_to')
        scheduled_date = request.form.get('scheduled_date')
        estimated_cost = request.form.get('estimated_cost', type=float)
        
        # Validation
        if not all([property_id, title, task_type]):
            flash('Por favor completa todos los campos obligatorios.', 'error')
            return render_template('maintenance/create_task.html', properties=properties)
        
        if property_id not in [p.id for p in properties]:
            flash('Propiedad no válida.', 'error')
            return render_template('maintenance/create_task.html', properties=properties)
        
        task = MaintenanceTask(
            property_id=property_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            assigned_to=assigned_to,
            scheduled_date=datetime.strptime(scheduled_date, '%Y-%m-%d').date() if scheduled_date else None,
            estimated_cost=estimated_cost,
            created_by=current_user.id,
            status='pending'
        )
        
        try:
            db.session.add(task)
            db.session.commit()
            
            # Create notification for assigned provider if specified
            if assigned_to:
                create_task_notification(task, 'created')
            
            flash('Tarea de mantenimiento creada exitosamente.', 'success')
            return redirect(url_for('maintenance.tasks'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la tarea de mantenimiento.', 'error')
    
    return render_template('maintenance/create_task.html', properties=properties)

@maintenance_bp.route('/tasks/<int:task_id>')
@login_required
def view_task(task_id):
    """View task details"""
    task = MaintenanceTask.query.get_or_404(task_id)
    
    # Check permissions
    if current_user.role == 'admin_ph' and task.property.admin_id != current_user.id:
        flash('No tienes permisos para ver esta tarea.', 'error')
        return redirect(url_for('maintenance.tasks'))
    
    return render_template('maintenance/view_task.html', task=task)

@maintenance_bp.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Edit maintenance task"""
    task = MaintenanceTask.query.get_or_404(task_id)
    
    # Check permissions
    if current_user.role not in ['admin_general', 'admin_ph']:
        flash('No tienes permisos para editar tareas.', 'error')
        return redirect(url_for('maintenance.view_task', task_id=task_id))
    
    if current_user.role == 'admin_ph' and task.property.admin_id != current_user.id:
        flash('No tienes permisos para editar esta tarea.', 'error')
        return redirect(url_for('maintenance.view_task', task_id=task_id))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.task_type = request.form.get('task_type')
        task.priority = request.form.get('priority')
        task.assigned_to = request.form.get('assigned_to')
        
        scheduled_date = request.form.get('scheduled_date')
        if scheduled_date:
            task.scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
        
        estimated_cost = request.form.get('estimated_cost')
        if estimated_cost:
            task.estimated_cost = float(estimated_cost)
        
        actual_cost = request.form.get('actual_cost')
        if actual_cost:
            task.actual_cost = float(actual_cost)
        
        task.notes = request.form.get('notes')
        
        # Update status if provided
        new_status = request.form.get('status')
        if new_status and new_status != task.status:
            old_status = task.status
            task.status = new_status
            
            if new_status == 'completed':
                task.completed_date = date.today()
            
            # Create notification for status change
            create_task_notification(task, 'status_changed', old_status)
        
        try:
            db.session.commit()
            flash('Tarea actualizada exitosamente.', 'success')
            return redirect(url_for('maintenance.view_task', task_id=task_id))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la tarea.', 'error')
    
    return render_template('maintenance/edit_task.html', task=task, properties=properties)

@maintenance_bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """Delete maintenance task"""
    task = MaintenanceTask.query.get_or_404(task_id)
    
    # Check permissions
    if current_user.role not in ['admin_general', 'admin_ph']:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    if current_user.role == 'admin_ph' and task.property.admin_id != current_user.id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        db.session.delete(task)
        db.session.commit()
        flash('Tarea eliminada exitosamente.', 'success')
        return redirect(url_for('maintenance.tasks'))
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error al eliminar la tarea'}), 500

@maintenance_bp.route('/schedule')
@login_required
def schedule():
    """Maintenance schedule calendar view"""
    if current_user.role not in ['admin_general', 'admin_ph', 'provider']:
        return redirect(url_for('dashboard.resident'))
    
    # Get properties based on user role
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    elif current_user.role == 'admin_ph':
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    else:  # provider
        properties = Property.query.filter_by(is_active=True).all()
    
    # Get tasks for calendar
    tasks = MaintenanceTask.query.filter(
        MaintenanceTask.property_id.in_([p.id for p in properties]),
        MaintenanceTask.scheduled_date.isnot(None)
    ).all()
    
    # Format tasks for calendar
    calendar_events = []
    for task in tasks:
        color = {
            'pending': '#ffc107',
            'in_progress': '#17a2b8',
            'completed': '#28a745',
            'cancelled': '#dc3545'
        }.get(task.status, '#6c757d')
        
        calendar_events.append({
            'id': task.id,
            'title': task.title,
            'start': task.scheduled_date.isoformat(),
            'backgroundColor': color,
            'borderColor': color,
            'url': url_for('maintenance.view_task', task_id=task.id)
        })
    
    return render_template('maintenance/schedule.html',
                         properties=properties,
                         calendar_events=calendar_events)

@maintenance_bp.route('/preventive')
@login_required
def preventive():
    """Preventive maintenance management"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('maintenance.index'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    # Get preventive maintenance tasks
    preventive_tasks = MaintenanceTask.query.filter(
        MaintenanceTask.property_id.in_([p.id for p in properties]),
        MaintenanceTask.task_type == 'preventive'
    ).order_by(MaintenanceTask.scheduled_date.desc()).all()
    
    return render_template('maintenance/preventive.html',
                         properties=properties,
                         preventive_tasks=preventive_tasks)

@maintenance_bp.route('/api/tasks/status/<int:task_id>', methods=['POST'])
@login_required
def update_task_status(task_id):
    """Update task status via AJAX"""
    task = MaintenanceTask.query.get_or_404(task_id)
    
    # Check permissions
    if current_user.role == 'admin_ph' and task.property.admin_id != current_user.id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    new_status = request.json.get('status')
    if new_status not in ['pending', 'in_progress', 'completed', 'cancelled']:
        return jsonify({'success': False, 'message': 'Estado no válido'}), 400
    
    old_status = task.status
    task.status = new_status
    
    if new_status == 'completed':
        task.completed_date = date.today()
    
    try:
        db.session.commit()
        
        # Create notification
        create_task_notification(task, 'status_changed', old_status)
        
        return jsonify({'success': True, 'message': 'Estado actualizado'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error al actualizar'}), 500

def create_task_notification(task, action, old_status=None):
    """Create notification for task events"""
    try:
        if action == 'created':
            title = f"Nueva tarea de mantenimiento: {task.title}"
            message = f"Se ha creado una nueva tarea en {task.property.name}. Tipo: {task.task_type}, Prioridad: {task.priority}"
        elif action == 'status_changed':
            title = f"Tarea actualizada: {task.title}"
            message = f"El estado de la tarea ha cambiado de {old_status} a {task.status}"
        else:
            return
        
        # Notify property admin
        if task.property.admin:
            notification = Notification(
                user_id=task.property.admin.id,
                title=title,
                message=message,
                notification_type='info'
            )
            db.session.add(notification)
        
        # Notify task creator if different from admin
        if task.created_by and task.created_by != task.property.admin_id:
            creator = User.query.get(task.created_by)
            if creator:
                notification = Notification(
                    user_id=creator.id,
                    title=title,
                    message=message,
                    notification_type='info'
                )
                db.session.add(notification)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error creating task notification: {e}")
