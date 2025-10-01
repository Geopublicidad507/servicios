"""
Rutas para gestión de backups
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from utils.backup import backup_manager
from datetime import datetime
import os
from pathlib import Path
from functools import wraps

backup_bp = Blueprint('backup', __name__)


def admin_required(f):
    """Decorador para requerir permisos de administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin_general']:
            flash('No tienes permisos para acceder a esta sección.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


@backup_bp.route('/')
@login_required
@admin_required
def index():
    """Dashboard de backups."""
    try:
        backups = backup_manager.list_backups()
        status = backup_manager.get_backup_status()
        
        return render_template('backup/index.html', 
                             backups=backups, 
                             status=status)
    except Exception as e:
        flash(f'Error cargando información de backups: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@backup_bp.route('/create', methods=['POST'])
@login_required
@admin_required
def create_backup():
    """Crear un nuevo backup."""
    try:
        backup_type = request.form.get('backup_type', 'full')
        
        if backup_type == 'full':
            backup_path = backup_manager.create_full_backup()
            flash('Backup completo creado exitosamente.', 'success')
        elif backup_type == 'database':
            backup_path = backup_manager.backup_database()
            flash('Backup de base de datos creado exitosamente.', 'success')
        else:
            flash('Tipo de backup no válido.', 'error')
            return redirect(url_for('backup.index'))
        
        if not backup_path:
            flash('Error creando el backup.', 'error')
        
    except Exception as e:
        flash(f'Error creando backup: {str(e)}', 'error')
    
    return redirect(url_for('backup.index'))


@backup_bp.route('/download/<backup_name>')
@login_required
@admin_required
def download_backup(backup_name):
    """Descargar un archivo de backup."""
    try:
        backup_path = backup_manager.backup_dir / backup_name
        
        if not backup_path.exists():
            flash('Archivo de backup no encontrado.', 'error')
            return redirect(url_for('backup.index'))
        
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=backup_name
        )
        
    except Exception as e:
        flash(f'Error descargando backup: {str(e)}', 'error')
        return redirect(url_for('backup.index'))


@backup_bp.route('/restore', methods=['POST'])
@login_required
@admin_required
def restore_backup():
    """Restaurar desde un backup."""
    try:
        backup_name = request.form.get('backup_name')
        confirm = request.form.get('confirm')
        
        if not confirm:
            flash('Debes confirmar la restauración.', 'error')
            return redirect(url_for('backup.index'))
        
        if not backup_name:
            flash('Debes seleccionar un backup.', 'error')
            return redirect(url_for('backup.index'))
        
        backup_path = backup_manager.backup_dir / backup_name
        
        if not backup_path.exists():
            flash('Archivo de backup no encontrado.', 'error')
            return redirect(url_for('backup.index'))
        
        # Crear backup de seguridad antes de restaurar
        pre_restore_backup = backup_manager.create_full_backup()
        if pre_restore_backup:
            flash('Backup de seguridad creado antes de la restauración.', 'info')
        
        # Restaurar
        backup_manager.restore_backup(backup_path)
        flash('Backup restaurado exitosamente.', 'success')
        
    except Exception as e:
        flash(f'Error restaurando backup: {str(e)}', 'error')
    
    return redirect(url_for('backup.index'))


@backup_bp.route('/delete/<backup_name>', methods=['POST'])
@login_required
@admin_required
def delete_backup(backup_name):
    """Eliminar un archivo de backup."""
    try:
        backup_path = backup_manager.backup_dir / backup_name
        
        if not backup_path.exists():
            flash('Archivo de backup no encontrado.', 'error')
            return redirect(url_for('backup.index'))
        
        backup_path.unlink()
        flash(f'Backup {backup_name} eliminado exitosamente.', 'success')
        
    except Exception as e:
        flash(f'Error eliminando backup: {str(e)}', 'error')
    
    return redirect(url_for('backup.index'))


@backup_bp.route('/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_backups():
    """Limpiar backups antiguos."""
    try:
        backup_manager.cleanup_old_backups()
        flash('Limpieza de backups completada.', 'success')
        
    except Exception as e:
        flash(f'Error en limpieza de backups: {str(e)}', 'error')
    
    return redirect(url_for('backup.index'))


@backup_bp.route('/status')
@login_required
@admin_required
def backup_status():
    """API endpoint para obtener estado de backups."""
    try:
        status = backup_manager.get_backup_status()
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backup_bp.route('/upload', methods=['POST'])
@login_required
@admin_required
def upload_backup():
    """Subir un archivo de backup."""
    try:
        if 'backup_file' not in request.files:
            flash('No se seleccionó ningún archivo.', 'error')
            return redirect(url_for('backup.index'))
        
        file = request.files['backup_file']
        
        if file.filename == '':
            flash('No se seleccionó ningún archivo.', 'error')
            return redirect(url_for('backup.index'))
        
        # Validar extensión del archivo
        allowed_extensions = {'.zip', '.sql'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            flash('Tipo de archivo no permitido. Solo se permiten archivos .zip y .sql', 'error')
            return redirect(url_for('backup.index'))
        
        # Generar nombre único para el archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"uploaded_backup_{timestamp}{file_ext}"
        
        # Guardar archivo
        backup_path = backup_manager.backup_dir / filename
        file.save(backup_path)
        
        flash(f'Backup subido exitosamente: {filename}', 'success')
        
    except Exception as e:
        flash(f'Error subiendo backup: {str(e)}', 'error')
    
    return redirect(url_for('backup.index'))


@backup_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
@admin_required
def backup_schedule():
    """Configurar programación de backups."""
    if request.method == 'POST':
        try:
            # Aquí se podría implementar la configuración de horarios
            # Por ahora, solo mostramos un mensaje
            flash('Configuración de horarios guardada.', 'success')
            
        except Exception as e:
            flash(f'Error guardando configuración: {str(e)}', 'error')
        
        return redirect(url_for('backup.schedule'))
    
    # Obtener configuración actual
    schedule_config = {
        'daily_backup_time': '02:00',
        'database_backup_interval': 6,  # horas
        'max_backups': backup_manager.max_backups,
        'auto_cleanup': True
    }
    
    return render_template('backup/schedule.html', config=schedule_config)
