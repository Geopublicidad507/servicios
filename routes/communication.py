from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from flask_mail import Message, Mail
from models import Property, Unit, User, Notification, Ticket, db
import threading

communication_bp = Blueprint('communication', __name__)

@communication_bp.route('/')
@login_required
def index():
    """Communication dashboard"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('dashboard.resident'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    # Recent notifications
    recent_notifications = Notification.query.join(User).join(Unit).join(Property).filter(
        Property.id.in_([p.id for p in properties])
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    # Open tickets
    open_tickets = Ticket.query.filter(
        Ticket.status.in_(['open', 'in_progress'])
    ).count()
    
    return render_template('communication/index.html',
                         properties=properties,
                         recent_notifications=recent_notifications,
                         open_tickets=open_tickets)

@communication_bp.route('/notifications')
@login_required
def notifications():
    """Notifications management"""
    page = request.args.get('page', 1, type=int)
    
    if current_user.role in ['admin_general', 'admin_ph']:
        # Admin view - all notifications
        if current_user.role == 'admin_general':
            properties = Property.query.filter_by(is_active=True).all()
        else:
            properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
        
        notifications = Notification.query.join(User).join(Unit).join(Property).filter(
            Property.id.in_([p.id for p in properties])
        ).order_by(Notification.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
    else:
        # Resident view - only their notifications
        notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
    
    return render_template('communication/notifications.html', notifications=notifications)

@communication_bp.route('/notifications/send', methods=['GET', 'POST'])
@login_required
def send_notification():
    """Send notification to residents"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        flash('No tienes permisos para enviar notificaciones.', 'error')
        return redirect(url_for('communication.notifications'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        notification_type = request.form.get('notification_type', 'info')
        property_ids = request.form.getlist('property_ids')
        send_email = request.form.get('send_email') == 'on'
        
        if not all([title, message]):
            flash('Por favor completa todos los campos obligatorios.', 'error')
            return render_template('communication/send_notification.html', properties=properties)
        
        # Get recipients
        recipients = []
        if property_ids:
            # Send to specific properties
            for prop_id in property_ids:
                if int(prop_id) in [p.id for p in properties]:
                    units = Unit.query.filter_by(property_id=int(prop_id)).all()
                    for unit in units:
                        if unit.owner:
                            recipients.append(unit.owner)
        else:
            # Send to all residents
            for prop in properties:
                units = Unit.query.filter_by(property_id=prop.id).all()
                for unit in units:
                    if unit.owner:
                        recipients.append(unit.owner)
        
        # Remove duplicates
        recipients = list(set(recipients))
        
        # Create notifications
        notifications_created = 0
        for recipient in recipients:
            notification = Notification(
                user_id=recipient.id,
                title=title,
                message=message,
                notification_type=notification_type
            )
            db.session.add(notification)
            notifications_created += 1
        
        try:
            db.session.commit()
            
            # Send emails if requested
            if send_email and recipients:
                send_bulk_email(recipients, title, message)
            
            flash(f'Notificación enviada a {notifications_created} residentes.', 'success')
            return redirect(url_for('communication.notifications'))
        except Exception as e:
            db.session.rollback()
            flash('Error al enviar la notificación.', 'error')
    
    return render_template('communication/send_notification.html', properties=properties)

@communication_bp.route('/tickets')
@login_required
def tickets():
    """Tickets management"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    category = request.args.get('category')
    
    # Build query based on user role
    if current_user.role in ['admin_general', 'admin_ph']:
        query = Ticket.query
        if status:
            query = query.filter(Ticket.status == status)
        if category:
            query = query.filter(Ticket.category == category)
    else:
        # Residents see only their tickets
        query = Ticket.query.filter_by(user_id=current_user.id)
        if status:
            query = query.filter(Ticket.status == status)
        if category:
            query = query.filter(Ticket.category == category)
    
    tickets = query.order_by(Ticket.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get categories for filter
    categories = db.session.query(Ticket.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('communication/tickets.html',
                         tickets=tickets,
                         categories=categories,
                         filters={'status': status, 'category': category})

@communication_bp.route('/tickets/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    """Create new ticket"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        priority = request.form.get('priority', 'medium')
        
        if not all([title, description, category]):
            flash('Por favor completa todos los campos obligatorios.', 'error')
            return render_template('communication/create_ticket.html')
        
        ticket = Ticket(
            user_id=current_user.id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            status='open'
        )
        
        try:
            db.session.add(ticket)
            db.session.commit()
            
            # Notify administrators
            if current_user.role == 'resident':
                notify_admins_new_ticket(ticket)
            
            flash('Ticket creado exitosamente.', 'success')
            return redirect(url_for('communication.tickets'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el ticket.', 'error')
    
    return render_template('communication/create_ticket.html')

@communication_bp.route('/tickets/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    """View ticket details"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check permissions
    if current_user.role == 'resident' and ticket.user_id != current_user.id:
        flash('No tienes permisos para ver este ticket.', 'error')
        return redirect(url_for('communication.tickets'))
    
    return render_template('communication/view_ticket.html', ticket=ticket)

@communication_bp.route('/tickets/<int:ticket_id>/update', methods=['POST'])
@login_required
def update_ticket(ticket_id):
    """Update ticket status/resolution"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    ticket = Ticket.query.get_or_404(ticket_id)
    
    status = request.form.get('status')
    resolution = request.form.get('resolution')
    assigned_to = request.form.get('assigned_to', type=int)
    
    if status:
        ticket.status = status
    if resolution:
        ticket.resolution = resolution
    if assigned_to:
        ticket.assigned_to = assigned_to
    
    ticket.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        
        # Notify ticket creator
        if status or resolution:
            notify_ticket_update(ticket)
        
        flash('Ticket actualizado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar el ticket.', 'error')
    
    return redirect(url_for('communication.view_ticket', ticket_id=ticket_id))

@communication_bp.route('/announcements')
@login_required
def announcements():
    """Public announcements board"""
    page = request.args.get('page', 1, type=int)
    
    # Get recent announcements (public notifications)
    announcements = Notification.query.filter_by(
        notification_type='announcement'
    ).order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('communication/announcements.html', announcements=announcements)

def send_bulk_email(recipients, subject, message):
    """Send bulk email in background thread"""
    def send_async_email(recipients, subject, message):
        try:
            mail = Mail(current_app)
            with mail.connect() as conn:
                for recipient in recipients:
                    msg = Message(
                        subject=f"[PH Control] {subject}",
                        recipients=[recipient.email],
                        body=message,
                        sender=current_app.config['MAIL_USERNAME']
                    )
                    conn.send(msg)
        except Exception as e:
            print(f"Error sending bulk email: {e}")
    
    thread = threading.Thread(target=send_async_email, args=(recipients, subject, message))
    thread.start()

def notify_admins_new_ticket(ticket):
    """Notify administrators about new ticket"""
    admins = User.query.filter(User.role.in_(['admin_general', 'admin_ph'])).all()
    
    for admin in admins:
        notification = Notification(
            user_id=admin.id,
            title=f"Nuevo Ticket: {ticket.title}",
            message=f"Se ha creado un nuevo ticket por {ticket.user.full_name}. Categoría: {ticket.category}",
            notification_type='info'
        )
        db.session.add(notification)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()

def notify_ticket_update(ticket):
    """Notify ticket creator about updates"""
    notification = Notification(
        user_id=ticket.user_id,
        title=f"Actualización de Ticket: {ticket.title}",
        message=f"Tu ticket ha sido actualizado. Estado: {ticket.status}",
        notification_type='info'
    )
    db.session.add(notification)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
