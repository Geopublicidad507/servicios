from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Property, VisitorLog, User, Notification, db
from datetime import datetime, date, timedelta

security_bp = Blueprint('security', __name__)

@security_bp.route('/')
@login_required
def index():
    """Security dashboard"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('dashboard.resident'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    # Today's statistics
    today = date.today()
    
    # Visitors today
    visitors_today = VisitorLog.query.filter(
        VisitorLog.entry_time >= datetime.combine(today, datetime.min.time())
    ).count()
    
    # Active visitors (not exited)
    active_visitors = VisitorLog.query.filter(
        VisitorLog.exit_time.is_(None),
        VisitorLog.entry_time >= datetime.combine(today - timedelta(days=1), datetime.min.time())
    ).count()
    
    # Recent visitor logs
    recent_logs = VisitorLog.query.order_by(
        VisitorLog.entry_time.desc()
    ).limit(10).all()
    
    # Weekly visitor statistics
    week_ago = today - timedelta(days=7)
    weekly_visitors = []
    
    for i in range(7):
        day = week_ago + timedelta(days=i)
        count = VisitorLog.query.filter(
            VisitorLog.entry_time >= datetime.combine(day, datetime.min.time()),
            VisitorLog.entry_time < datetime.combine(day + timedelta(days=1), datetime.min.time())
        ).count()
        weekly_visitors.append({
            'date': day.strftime('%Y-%m-%d'),
            'day': day.strftime('%a'),
            'count': count
        })
    
    return render_template('security/index.html',
                         properties=properties,
                         visitors_today=visitors_today,
                         active_visitors=active_visitors,
                         recent_logs=recent_logs,
                         weekly_visitors=weekly_visitors)

@security_bp.route('/visitors')
@login_required
def visitors():
    """Visitor logs management"""
    page = request.args.get('page', 1, type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    unit_visited = request.args.get('unit_visited')
    status = request.args.get('status')  # active, exited, all
    
    # Build query
    query = VisitorLog.query
    
    # Apply filters
    if date_from:
        query = query.filter(VisitorLog.entry_time >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(VisitorLog.entry_time <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    if unit_visited:
        query = query.filter(VisitorLog.unit_visited.contains(unit_visited))
    if status == 'active':
        query = query.filter(VisitorLog.exit_time.is_(None))
    elif status == 'exited':
        query = query.filter(VisitorLog.exit_time.isnot(None))
    
    visitors = query.order_by(VisitorLog.entry_time.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('security/visitors.html',
                         visitors=visitors,
                         filters={
                             'date_from': date_from,
                             'date_to': date_to,
                             'unit_visited': unit_visited,
                             'status': status
                         })

@security_bp.route('/visitors/register', methods=['GET', 'POST'])
@login_required
def register_visitor():
    """Register new visitor entry"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        flash('No tienes permisos para registrar visitantes.', 'error')
        return redirect(url_for('security.visitors'))
    
    if request.method == 'POST':
        visitor_name = request.form.get('visitor_name')
        visitor_id = request.form.get('visitor_id')
        unit_visited = request.form.get('unit_visited')
        purpose = request.form.get('purpose')
        authorized_by = request.form.get('authorized_by')
        notes = request.form.get('notes')
        
        # Validation
        if not all([visitor_name, unit_visited]):
            flash('Por favor completa todos los campos obligatorios.', 'error')
            return render_template('security/register_visitor.html')
        
        visitor_log = VisitorLog(
            visitor_name=visitor_name,
            visitor_id=visitor_id,
            unit_visited=unit_visited,
            purpose=purpose,
            authorized_by=authorized_by,
            notes=notes,
            entry_time=datetime.now()
        )
        
        try:
            db.session.add(visitor_log)
            db.session.commit()
            flash(f'Visitante {visitor_name} registrado exitosamente.', 'success')
            return redirect(url_for('security.visitors'))
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar el visitante.', 'error')
    
    return render_template('security/register_visitor.html')

@security_bp.route('/visitors/<int:log_id>/exit', methods=['POST'])
@login_required
def exit_visitor(log_id):
    """Register visitor exit"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    visitor_log = VisitorLog.query.get_or_404(log_id)
    
    if visitor_log.exit_time:
        return jsonify({'success': False, 'message': 'El visitante ya ha salido'}), 400
    
    visitor_log.exit_time = datetime.now()
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Salida registrada para {visitor_log.visitor_name}',
            'exit_time': visitor_log.exit_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error al registrar la salida'}), 500

@security_bp.route('/visitors/<int:log_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_visitor_log(log_id):
    """Edit visitor log"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        flash('No tienes permisos para editar registros.', 'error')
        return redirect(url_for('security.visitors'))
    
    visitor_log = VisitorLog.query.get_or_404(log_id)
    
    if request.method == 'POST':
        visitor_log.visitor_name = request.form.get('visitor_name')
        visitor_log.visitor_id = request.form.get('visitor_id')
        visitor_log.unit_visited = request.form.get('unit_visited')
        visitor_log.purpose = request.form.get('purpose')
        visitor_log.authorized_by = request.form.get('authorized_by')
        visitor_log.notes = request.form.get('notes')
        
        # Update entry time if provided
        entry_time = request.form.get('entry_time')
        if entry_time:
            visitor_log.entry_time = datetime.strptime(entry_time, '%Y-%m-%dT%H:%M')
        
        # Update exit time if provided
        exit_time = request.form.get('exit_time')
        if exit_time:
            visitor_log.exit_time = datetime.strptime(exit_time, '%Y-%m-%dT%H:%M')
        elif request.form.get('clear_exit_time'):
            visitor_log.exit_time = None
        
        try:
            db.session.commit()
            flash('Registro actualizado exitosamente.', 'success')
            return redirect(url_for('security.visitors'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el registro.', 'error')
    
    return render_template('security/edit_visitor_log.html', visitor_log=visitor_log)

@security_bp.route('/access-control')
@login_required
def access_control():
    """Access control management"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('security.index'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    # Current active visitors
    active_visitors = VisitorLog.query.filter(
        VisitorLog.exit_time.is_(None)
    ).order_by(VisitorLog.entry_time.desc()).all()
    
    return render_template('security/access_control.html',
                         properties=properties,
                         active_visitors=active_visitors)

@security_bp.route('/incidents')
@login_required
def incidents():
    """Security incidents management"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('security.index'))
    
    # This would integrate with a separate incidents model
    # For now, we'll show a placeholder
    return render_template('security/incidents.html')

@security_bp.route('/reports')
@login_required
def reports():
    """Security reports"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('security.index'))
    
    # Get date range from request
    date_from = request.args.get('date_from', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', date.today().strftime('%Y-%m-%d'))
    
    # Parse dates
    start_date = datetime.strptime(date_from, '%Y-%m-%d')
    end_date = datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    
    # Get visitor statistics
    total_visitors = VisitorLog.query.filter(
        VisitorLog.entry_time.between(start_date, end_date)
    ).count()
    
    # Daily visitor counts
    daily_counts = []
    current_date = start_date.date()
    end_date_only = end_date.date()
    
    while current_date <= end_date_only:
        count = VisitorLog.query.filter(
            VisitorLog.entry_time >= datetime.combine(current_date, datetime.min.time()),
            VisitorLog.entry_time < datetime.combine(current_date + timedelta(days=1), datetime.min.time())
        ).count()
        
        daily_counts.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'day': current_date.strftime('%a'),
            'count': count
        })
        current_date += timedelta(days=1)
    
    # Most visited units
    unit_stats = db.session.query(
        VisitorLog.unit_visited,
        db.func.count(VisitorLog.id).label('visit_count')
    ).filter(
        VisitorLog.entry_time.between(start_date, end_date)
    ).group_by(VisitorLog.unit_visited).order_by(
        db.func.count(VisitorLog.id).desc()
    ).limit(10).all()
    
    # Average visit duration (for visitors who have exited)
    avg_duration_query = db.session.query(
        db.func.avg(
            db.func.extract('epoch', VisitorLog.exit_time - VisitorLog.entry_time) / 3600
        ).label('avg_hours')
    ).filter(
        VisitorLog.entry_time.between(start_date, end_date),
        VisitorLog.exit_time.isnot(None)
    ).first()
    
    avg_duration = round(avg_duration_query.avg_hours or 0, 2)
    
    return render_template('security/reports.html',
                         date_from=date_from,
                         date_to=date_to,
                         total_visitors=total_visitors,
                         daily_counts=daily_counts,
                         unit_stats=unit_stats,
                         avg_duration=avg_duration)

@security_bp.route('/api/visitors/search')
@login_required
def search_visitors():
    """Search visitors for autocomplete"""
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify([])
    
    visitors = VisitorLog.query.filter(
        VisitorLog.visitor_name.ilike(f'%{query}%')
    ).distinct(VisitorLog.visitor_name).limit(10).all()
    
    results = [{'name': visitor.visitor_name, 'id': visitor.visitor_id} for visitor in visitors]
    
    return jsonify(results)

@security_bp.route('/api/visitors/active')
@login_required
def active_visitors_api():
    """Get active visitors for real-time updates"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    active_visitors = VisitorLog.query.filter(
        VisitorLog.exit_time.is_(None)
    ).order_by(VisitorLog.entry_time.desc()).all()
    
    visitors_data = []
    for visitor in active_visitors:
        duration = datetime.now() - visitor.entry_time
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, _ = divmod(remainder, 60)
        
        visitors_data.append({
            'id': visitor.id,
            'name': visitor.visitor_name,
            'unit': visitor.unit_visited,
            'entry_time': visitor.entry_time.strftime('%H:%M'),
            'duration': f"{int(hours):02d}:{int(minutes):02d}",
            'purpose': visitor.purpose or 'No especificado'
        })
    
    return jsonify(visitors_data)
