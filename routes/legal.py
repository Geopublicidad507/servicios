from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from models import Property, Assembly, User, Document, Notification, db
from datetime import datetime, date
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io

legal_bp = Blueprint('legal', __name__)

@legal_bp.route('/')
@login_required
def index():
    """Legal compliance dashboard"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('dashboard.resident'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    # Assembly statistics
    total_assemblies = Assembly.query.filter(
        Assembly.property_id.in_([p.id for p in properties])
    ).count()
    
    upcoming_assemblies = Assembly.query.filter(
        Assembly.property_id.in_([p.id for p in properties]),
        Assembly.scheduled_date > datetime.now(),
        Assembly.status == 'scheduled'
    ).count()
    
    completed_assemblies = Assembly.query.filter(
        Assembly.property_id.in_([p.id for p in properties]),
        Assembly.status == 'completed'
    ).count()
    
    # Recent assemblies
    recent_assemblies = Assembly.query.filter(
        Assembly.property_id.in_([p.id for p in properties])
    ).order_by(Assembly.scheduled_date.desc()).limit(5).all()
    
    # Legal documents count
    legal_documents = Document.query.filter(
        Document.property_id.in_([p.id for p in properties]),
        Document.document_type.in_(['contract', 'act', 'regulation'])
    ).count()
    
    return render_template('legal/index.html',
                         properties=properties,
                         total_assemblies=total_assemblies,
                         upcoming_assemblies=upcoming_assemblies,
                         completed_assemblies=completed_assemblies,
                         recent_assemblies=recent_assemblies,
                         legal_documents=legal_documents)

@legal_bp.route('/assemblies')
@legal_bp.route('/assemblies/<string:status>')
@login_required
def assemblies(status=None):
    """Assemblies management"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('legal.index'))
    
    page = request.args.get('page', 1, type=int)
    property_id = request.args.get('property_id', type=int)
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    # Build query
    query = Assembly.query.filter(
        Assembly.property_id.in_([p.id for p in properties])
    )
    
    # Apply filters
    if status:
        query = query.filter(Assembly.status == status)
    if property_id:
        query = query.filter(Assembly.property_id == property_id)
    
    assemblies = query.order_by(Assembly.scheduled_date.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    return render_template('legal/assemblies.html',
                         assemblies=assemblies,
                         properties=properties,
                         current_status=status,
                         filters={'property_id': property_id})

@legal_bp.route('/assemblies/create', methods=['GET', 'POST'])
@login_required
def create_assembly():
    """Create new assembly"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        flash('No tienes permisos para crear asambleas.', 'error')
        return redirect(url_for('legal.assemblies'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        property_id = request.form.get('property_id', type=int)
        title = request.form.get('title')
        description = request.form.get('description')
        assembly_type = request.form.get('assembly_type', 'ordinary')
        scheduled_date = request.form.get('scheduled_date')
        scheduled_time = request.form.get('scheduled_time')
        location = request.form.get('location')
        agenda = request.form.get('agenda')
        quorum_required = request.form.get('quorum_required', 50, type=int)
        
        # Validation
        if not all([property_id, title, scheduled_date, scheduled_time]):
            flash('Por favor completa todos los campos obligatorios.', 'error')
            return render_template('legal/create_assembly.html', properties=properties)
        
        if property_id not in [p.id for p in properties]:
            flash('Propiedad no válida.', 'error')
            return render_template('legal/create_assembly.html', properties=properties)
        
        # Combine date and time
        scheduled_datetime = datetime.strptime(f"{scheduled_date} {scheduled_time}", '%Y-%m-%d %H:%M')
        
        assembly = Assembly(
            property_id=property_id,
            title=title,
            description=description,
            assembly_type=assembly_type,
            scheduled_date=scheduled_datetime,
            location=location,
            agenda=agenda,
            quorum_required=quorum_required,
            created_by=current_user.id,
            status='scheduled'
        )
        
        try:
            db.session.add(assembly)
            db.session.commit()
            
            # Notify residents
            notify_assembly_created(assembly)
            
            flash('Asamblea creada exitosamente.', 'success')
            return redirect(url_for('legal.view_assembly', assembly_id=assembly.id))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la asamblea.', 'error')
    
    return render_template('legal/create_assembly.html', properties=properties)

@legal_bp.route('/assemblies/<int:assembly_id>')
@login_required
def view_assembly(assembly_id):
    """View assembly details"""
    assembly = Assembly.query.get_or_404(assembly_id)
    
    # Check permissions
    if current_user.role == 'admin_ph' and assembly.property.admin_id != current_user.id:
        flash('No tienes permisos para ver esta asamblea.', 'error')
        return redirect(url_for('legal.assemblies'))
    
    return render_template('legal/view_assembly.html', assembly=assembly)

@legal_bp.route('/assemblies/<int:assembly_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_assembly(assembly_id):
    """Edit assembly"""
    assembly = Assembly.query.get_or_404(assembly_id)
    
    # Check permissions
    if current_user.role not in ['admin_general', 'admin_ph']:
        flash('No tienes permisos para editar asambleas.', 'error')
        return redirect(url_for('legal.view_assembly', assembly_id=assembly_id))
    
    if current_user.role == 'admin_ph' and assembly.property.admin_id != current_user.id:
        flash('No tienes permisos para editar esta asamblea.', 'error')
        return redirect(url_for('legal.view_assembly', assembly_id=assembly_id))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        assembly.title = request.form.get('title')
        assembly.description = request.form.get('description')
        assembly.assembly_type = request.form.get('assembly_type')
        assembly.location = request.form.get('location')
        assembly.agenda = request.form.get('agenda')
        assembly.quorum_required = request.form.get('quorum_required', type=int)
        
        # Update scheduled date/time
        scheduled_date = request.form.get('scheduled_date')
        scheduled_time = request.form.get('scheduled_time')
        if scheduled_date and scheduled_time:
            assembly.scheduled_date = datetime.strptime(f"{scheduled_date} {scheduled_time}", '%Y-%m-%d %H:%M')
        
        # Update status
        new_status = request.form.get('status')
        if new_status:
            assembly.status = new_status
        
        # Update quorum achieved
        quorum_achieved = request.form.get('quorum_achieved', type=int)
        if quorum_achieved is not None:
            assembly.quorum_achieved = quorum_achieved
        
        # Update minutes
        minutes = request.form.get('minutes')
        if minutes:
            assembly.minutes = minutes
        
        try:
            db.session.commit()
            flash('Asamblea actualizada exitosamente.', 'success')
            return redirect(url_for('legal.view_assembly', assembly_id=assembly_id))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la asamblea.', 'error')
    
    return render_template('legal/edit_assembly.html', assembly=assembly, properties=properties)

@legal_bp.route('/assemblies/<int:assembly_id>/convocation')
@login_required
def generate_convocation(assembly_id):
    """Generate assembly convocation document"""
    assembly = Assembly.query.get_or_404(assembly_id)
    
    # Check permissions
    if current_user.role == 'admin_ph' and assembly.property.admin_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Generate PDF convocation
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Header
    title = Paragraph("CONVOCATORIA A ASAMBLEA", title_style)
    story.append(title)
    
    # Property info
    property_info = f"""
    <b>Propiedad Horizontal:</b> {assembly.property.name}<br/>
    <b>Dirección:</b> {assembly.property.address}<br/>
    <b>Código:</b> {assembly.property.code}
    """
    story.append(Paragraph(property_info, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Assembly details
    assembly_details = f"""
    <b>Tipo de Asamblea:</b> {assembly.assembly_type.title()}<br/>
    <b>Fecha:</b> {assembly.scheduled_date.strftime('%d de %B de %Y')}<br/>
    <b>Hora:</b> {assembly.scheduled_date.strftime('%H:%M')}<br/>
    <b>Lugar:</b> {assembly.location or 'Por definir'}<br/>
    <b>Quórum Requerido:</b> {assembly.quorum_required}%
    """
    story.append(Paragraph(assembly_details, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Description
    if assembly.description:
        story.append(Paragraph("<b>Descripción:</b>", styles['Heading3']))
        story.append(Paragraph(assembly.description, styles['Normal']))
        story.append(Spacer(1, 15))
    
    # Agenda
    if assembly.agenda:
        story.append(Paragraph("<b>Orden del Día:</b>", styles['Heading3']))
        story.append(Paragraph(assembly.agenda, styles['Normal']))
        story.append(Spacer(1, 20))
    
    # Legal notice
    legal_notice = """
    <b>AVISO LEGAL:</b><br/>
    De conformidad con la Ley 284 de Propiedad Horizontal de la República de Panamá, 
    se convoca a todos los propietarios a participar en la presente asamblea. 
    La asistencia es obligatoria y el quórum se calculará según lo establecido en la ley.
    """
    story.append(Paragraph(legal_notice, styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Signature
    signature = f"""
    <br/><br/>
    _________________________________<br/>
    {assembly.property.admin.full_name}<br/>
    Administrador de la Propiedad Horizontal<br/>
    Fecha: {datetime.now().strftime('%d de %B de %Y')}
    """
    story.append(Paragraph(signature, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="Convocatoria_Asamblea_{assembly.id}.pdf"'
    
    return response

@legal_bp.route('/assemblies/<int:assembly_id>/minutes')
@login_required
def generate_minutes(assembly_id):
    """Generate assembly minutes document"""
    assembly = Assembly.query.get_or_404(assembly_id)
    
    # Check permissions
    if current_user.role == 'admin_ph' and assembly.property.admin_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not assembly.minutes:
        flash('La asamblea no tiene acta registrada.', 'warning')
        return redirect(url_for('legal.view_assembly', assembly_id=assembly_id))
    
    # Generate PDF minutes
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1
    )
    
    title = Paragraph("ACTA DE ASAMBLEA", title_style)
    story.append(title)
    
    # Assembly info
    assembly_info = f"""
    <b>Propiedad Horizontal:</b> {assembly.property.name}<br/>
    <b>Tipo de Asamblea:</b> {assembly.assembly_type.title()}<br/>
    <b>Fecha:</b> {assembly.scheduled_date.strftime('%d de %B de %Y')}<br/>
    <b>Hora:</b> {assembly.scheduled_date.strftime('%H:%M')}<br/>
    <b>Lugar:</b> {assembly.location}<br/>
    <b>Quórum Logrado:</b> {assembly.quorum_achieved or 'No registrado'}%
    """
    story.append(Paragraph(assembly_info, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Minutes content
    story.append(Paragraph("<b>DESARROLLO DE LA ASAMBLEA:</b>", styles['Heading3']))
    story.append(Paragraph(assembly.minutes, styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Signature
    signature = f"""
    <br/><br/>
    _________________________________<br/>
    {assembly.property.admin.full_name}<br/>
    Administrador de la Propiedad Horizontal<br/>
    <br/>
    _________________________________<br/>
    Secretario de la Asamblea<br/>
    <br/>
    Fecha de elaboración: {datetime.now().strftime('%d de %B de %Y')}
    """
    story.append(Paragraph(signature, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="Acta_Asamblea_{assembly.id}.pdf"'
    
    return response

@legal_bp.route('/compliance')
@login_required
def compliance():
    """Legal compliance checklist"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('legal.index'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    compliance_items = []
    
    for property_obj in properties:
        # Check annual assembly requirement
        current_year = datetime.now().year
        year_start = datetime(current_year, 1, 1)
        year_end = datetime(current_year, 12, 31, 23, 59, 59)
        
        annual_assemblies = Assembly.query.filter(
            Assembly.property_id == property_obj.id,
            Assembly.scheduled_date >= year_start,
            Assembly.scheduled_date <= year_end,
            Assembly.assembly_type == 'ordinary'
        ).count()
        
        # Check if regulations are up to date
        regulations = Document.query.filter(
            Document.property_id == property_obj.id,
            Document.document_type == 'regulation'
        ).count()
        
        # Check recent financial reports
        financial_docs = Document.query.filter(
            Document.property_id == property_obj.id,
            Document.document_type == 'report',
            Document.created_at >= year_start
        ).count()
        
        compliance_items.append({
            'property': property_obj,
            'annual_assembly': annual_assemblies >= 1,
            'regulations': regulations > 0,
            'financial_reports': financial_docs > 0,
            'compliance_score': sum([
                annual_assemblies >= 1,
                regulations > 0,
                financial_docs > 0
            ]) / 3 * 100
        })
    
    return render_template('legal/compliance.html', compliance_items=compliance_items)

@legal_bp.route('/templates')
@login_required
def templates():
    """Legal document templates"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('legal.index'))
    
    templates_list = [
        {
            'name': 'Convocatoria a Asamblea Ordinaria',
            'description': 'Plantilla para convocar asambleas ordinarias anuales',
            'type': 'convocation'
        },
        {
            'name': 'Convocatoria a Asamblea Extraordinaria',
            'description': 'Plantilla para asambleas extraordinarias',
            'type': 'convocation'
        },
        {
            'name': 'Acta de Asamblea',
            'description': 'Formato para registrar las actas de asambleas',
            'type': 'minutes'
        },
        {
            'name': 'Reglamento Interno',
            'description': 'Plantilla base para reglamentos internos',
            'type': 'regulation'
        },
        {
            'name': 'Contrato de Administración',
            'description': 'Modelo de contrato para administradores',
            'type': 'contract'
        }
    ]
    
    return render_template('legal/templates.html', templates=templates_list)

def notify_assembly_created(assembly):
    """Notify residents about new assembly"""
    try:
        # Get all unit owners in the property
        from models import Unit
        units = Unit.query.filter_by(property_id=assembly.property_id).all()
        
        for unit in units:
            if unit.owner:
                notification = Notification(
                    user_id=unit.owner.id,
                    title=f"Nueva Asamblea: {assembly.title}",
                    message=f"Se ha programado una asamblea para el {assembly.scheduled_date.strftime('%d/%m/%Y a las %H:%M')}. Ubicación: {assembly.location or 'Por definir'}",
                    notification_type='info'
                )
                db.session.add(notification)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error creating assembly notifications: {e}")