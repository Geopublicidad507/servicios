from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required, current_user
from models import Property, Document, User, db
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

documents_bp = Blueprint('documents', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@documents_bp.route('/')
@login_required
def index():
    """Documents dashboard"""
    page = request.args.get('page', 1, type=int)
    property_id = request.args.get('property_id', type=int)
    document_type = request.args.get('document_type')
    search = request.args.get('search')
    
    # Get properties based on user role
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    elif current_user.role == 'admin_ph':
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    else:
        # Residents can only see public documents
        properties = Property.query.join(Property.units).filter(
            Property.units.any(owner_id=current_user.id)
        ).all()
    
    # Build query
    query = Document.query.filter(
        Document.property_id.in_([p.id for p in properties])
    )
    
    # For residents, only show public documents
    if current_user.role == 'resident':
        query = query.filter(Document.is_public == True)
    
    # Apply filters
    if property_id:
        query = query.filter(Document.property_id == property_id)
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if search:
        query = query.filter(
            db.or_(
                Document.title.ilike(f'%{search}%'),
                Document.description.ilike(f'%{search}%')
            )
        )
    
    documents = query.order_by(Document.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get document types for filter
    doc_types = db.session.query(Document.document_type).filter(
        Document.property_id.in_([p.id for p in properties])
    ).distinct().all()
    doc_types = [dt[0] for dt in doc_types]
    
    return render_template('documents/index.html',
                         documents=documents,
                         properties=properties,
                         doc_types=doc_types,
                         filters={
                             'property_id': property_id,
                             'document_type': document_type,
                             'search': search
                         })

@documents_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload new document"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        flash('No tienes permisos para subir documentos.', 'error')
        return redirect(url_for('documents.index'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        property_id = request.form.get('property_id', type=int)
        title = request.form.get('title')
        description = request.form.get('description')
        document_type = request.form.get('document_type')
        version = request.form.get('version', '1.0')
        is_public = request.form.get('is_public') == 'on'
        
        # Validation
        if not all([property_id, title, document_type]):
            flash('Por favor completa todos los campos obligatorios.', 'error')
            return render_template('documents/upload.html', properties=properties)
        
        if property_id not in [p.id for p in properties]:
            flash('Propiedad no válida.', 'error')
            return render_template('documents/upload.html', properties=properties)
        
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo.', 'error')
            return render_template('documents/upload.html', properties=properties)
        
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo.', 'error')
            return render_template('documents/upload.html', properties=properties)
        
        if not allowed_file(file.filename):
            flash('Tipo de archivo no permitido.', 'error')
            return render_template('documents/upload.html', properties=properties)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, unique_filename)
        
        try:
            # Save file
            file.save(file_path)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            mime_type = file.content_type
            
            # Create document record
            document = Document(
                property_id=property_id,
                title=title,
                description=description,
                document_type=document_type,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                version=version,
                is_public=is_public,
                uploaded_by=current_user.id
            )
            
            db.session.add(document)
            db.session.commit()
            
            flash('Documento subido exitosamente.', 'success')
            return redirect(url_for('documents.index'))
            
        except Exception as e:
            # Remove file if database operation failed
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.rollback()
            flash('Error al subir el documento.', 'error')
    
    return render_template('documents/upload.html', properties=properties)

@documents_bp.route('/<int:document_id>')
@login_required
def view(document_id):
    """View document details"""
    document = Document.query.get_or_404(document_id)
    
    # Check permissions
    if current_user.role == 'resident':
        if not document.is_public:
            flash('No tienes permisos para ver este documento.', 'error')
            return redirect(url_for('documents.index'))
        
        # Check if user belongs to the property
        user_properties = Property.query.join(Property.units).filter(
            Property.units.any(owner_id=current_user.id)
        ).all()
        
        if document.property not in user_properties:
            flash('No tienes permisos para ver este documento.', 'error')
            return redirect(url_for('documents.index'))
    
    elif current_user.role == 'admin_ph':
        if document.property.admin_id != current_user.id:
            flash('No tienes permisos para ver este documento.', 'error')
            return redirect(url_for('documents.index'))
    
    return render_template('documents/view.html', document=document)

@documents_bp.route('/<int:document_id>/download')
@login_required
def download(document_id):
    """Download document"""
    document = Document.query.get_or_404(document_id)
    
    # Check permissions (same as view)
    if current_user.role == 'resident':
        if not document.is_public:
            flash('No tienes permisos para descargar este documento.', 'error')
            return redirect(url_for('documents.index'))
        
        user_properties = Property.query.join(Property.units).filter(
            Property.units.any(owner_id=current_user.id)
        ).all()
        
        if document.property not in user_properties:
            flash('No tienes permisos para descargar este documento.', 'error')
            return redirect(url_for('documents.index'))
    
    elif current_user.role == 'admin_ph':
        if document.property.admin_id != current_user.id:
            flash('No tienes permisos para descargar este documento.', 'error')
            return redirect(url_for('documents.index'))
    
    # Check if file exists
    if not os.path.exists(document.file_path):
        flash('El archivo no se encuentra disponible.', 'error')
        return redirect(url_for('documents.view', document_id=document_id))
    
    # Get original filename
    original_filename = os.path.basename(document.file_path).split('_', 1)[1] if '_' in os.path.basename(document.file_path) else os.path.basename(document.file_path)
    
    return send_file(
        document.file_path,
        as_attachment=True,
        download_name=original_filename
    )

@documents_bp.route('/<int:document_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(document_id):
    """Edit document metadata"""
    document = Document.query.get_or_404(document_id)
    
    # Check permissions
    if current_user.role not in ['admin_general', 'admin_ph']:
        flash('No tienes permisos para editar documentos.', 'error')
        return redirect(url_for('documents.view', document_id=document_id))
    
    if current_user.role == 'admin_ph' and document.property.admin_id != current_user.id:
        flash('No tienes permisos para editar este documento.', 'error')
        return redirect(url_for('documents.view', document_id=document_id))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        document.title = request.form.get('title')
        document.description = request.form.get('description')
        document.document_type = request.form.get('document_type')
        document.version = request.form.get('version')
        document.is_public = request.form.get('is_public') == 'on'
        
        try:
            db.session.commit()
            flash('Documento actualizado exitosamente.', 'success')
            return redirect(url_for('documents.view', document_id=document_id))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el documento.', 'error')
    
    return render_template('documents/edit.html', document=document, properties=properties)

@documents_bp.route('/<int:document_id>/delete', methods=['POST'])
@login_required
def delete(document_id):
    """Delete document"""
    document = Document.query.get_or_404(document_id)
    
    # Check permissions
    if current_user.role not in ['admin_general', 'admin_ph']:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    if current_user.role == 'admin_ph' and document.property.admin_id != current_user.id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        # Delete file from filesystem
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete database record
        db.session.delete(document)
        db.session.commit()
        
        flash('Documento eliminado exitosamente.', 'success')
        return redirect(url_for('documents.index'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error al eliminar el documento'}), 500

@documents_bp.route('/categories')
@login_required
def categories():
    """Document categories management"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('documents.index'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    # Get document statistics by category
    category_stats = []
    categories = ['contract', 'act', 'regulation', 'plan', 'report', 'other']
    
    for category in categories:
        count = Document.query.filter(
            Document.property_id.in_([p.id for p in properties]),
            Document.document_type == category
        ).count()
        
        category_stats.append({
            'name': category,
            'display_name': category.replace('_', ' ').title(),
            'count': count
        })
    
    return render_template('documents/categories.html',
                         properties=properties,
                         category_stats=category_stats)

@documents_bp.route('/search')
@login_required
def search():
    """Advanced document search"""
    query = request.args.get('q', '')
    property_id = request.args.get('property_id', type=int)
    document_type = request.args.get('document_type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if not query and not any([property_id, document_type, date_from, date_to]):
        return render_template('documents/search.html', documents=[], query='')
    
    # Get properties based on user role
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    elif current_user.role == 'admin_ph':
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    else:
        properties = Property.query.join(Property.units).filter(
            Property.units.any(owner_id=current_user.id)
        ).all()
    
    # Build search query
    search_query = Document.query.filter(
        Document.property_id.in_([p.id for p in properties])
    )
    
    # For residents, only show public documents
    if current_user.role == 'resident':
        search_query = search_query.filter(Document.is_public == True)
    
    # Apply search filters
    if query:
        search_query = search_query.filter(
            db.or_(
                Document.title.ilike(f'%{query}%'),
                Document.description.ilike(f'%{query}%')
            )
        )
    
    if property_id:
        search_query = search_query.filter(Document.property_id == property_id)
    
    if document_type:
        search_query = search_query.filter(Document.document_type == document_type)
    
    if date_from:
        search_query = search_query.filter(Document.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        search_query = search_query.filter(Document.created_at <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    
    documents = search_query.order_by(Document.created_at.desc()).limit(50).all()
    
    return render_template('documents/search.html',
                         documents=documents,
                         query=query,
                         properties=properties,
                         filters={
                             'property_id': property_id,
                             'document_type': document_type,
                             'date_from': date_from,
                             'date_to': date_to
                         })

@documents_bp.route('/api/upload-progress/<upload_id>')
@login_required
def upload_progress(upload_id):
    """Get upload progress (for future implementation)"""
    # This would be used for showing upload progress
    # For now, return a simple response
    return jsonify({'progress': 100, 'status': 'completed'})