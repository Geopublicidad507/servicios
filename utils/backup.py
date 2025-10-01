"""
Sistema de backup automático para PH Control
"""
import os
import shutil
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import zipfile
import schedule
import time
from threading import Thread
from flask import current_app


class BackupManager:
    """Gestor de backups automáticos."""
    
    def __init__(self, app=None):
        self.app = app
        self.backup_dir = None
        self.max_backups = 30  # Mantener 30 backups por defecto
        self.logger = logging.getLogger(__name__)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar el gestor de backups con la aplicación Flask."""
        self.app = app
        self.backup_dir = Path(app.config.get('BACKUP_DIR', 'backups'))
        self.max_backups = app.config.get('MAX_BACKUPS', 30)
        
        # Crear directorio de backups si no existe
        self.backup_dir.mkdir(exist_ok=True)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Programar backups automáticos
        self._schedule_backups()
    
    def _schedule_backups(self):
        """Programar backups automáticos."""
        # Backup diario a las 2:00 AM
        schedule.every().day.at("02:00").do(self.create_full_backup)
        
        # Backup de base de datos cada 6 horas
        schedule.every(6).hours.do(self.backup_database)
        
        # Limpiar backups antiguos diariamente
        schedule.every().day.at("03:00").do(self.cleanup_old_backups)
        
        # Iniciar el scheduler en un hilo separado
        scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
        
        self.logger.info("Backup scheduler iniciado")
    
    def _run_scheduler(self):
        """Ejecutar el scheduler de backups."""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto
    
    def create_full_backup(self):
        """Crear un backup completo del sistema."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"full_backup_{timestamp}"
            backup_path = self.backup_dir / f"{backup_name}.zip"
            
            self.logger.info(f"Iniciando backup completo: {backup_name}")
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup de la base de datos
                db_backup = self._backup_database_to_temp()
                if db_backup:
                    zipf.write(db_backup, 'database.sql')
                    os.remove(db_backup)  # Limpiar archivo temporal
                
                # Backup de archivos subidos
                uploads_dir = Path(self.app.config.get('UPLOAD_FOLDER', 'uploads'))
                if uploads_dir.exists():
                    for file_path in uploads_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = f"uploads/{file_path.relative_to(uploads_dir)}"
                            zipf.write(file_path, arcname)
                
                # Backup de configuración
                config_files = ['.env', 'docker-compose.yml', 'requirements.txt']
                for config_file in config_files:
                    config_path = Path(config_file)
                    if config_path.exists():
                        zipf.write(config_path, config_file)
            
            self.logger.info(f"Backup completo creado: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creando backup completo: {str(e)}")
            return None
    
    def backup_database(self):
        """Crear backup solo de la base de datos."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"db_backup_{timestamp}.sql"
            backup_path = self.backup_dir / backup_name
            
            self.logger.info(f"Iniciando backup de base de datos: {backup_name}")
            
            database_url = self.app.config.get('DATABASE_URL', '')
            
            if database_url.startswith('postgresql://'):
                # Backup de PostgreSQL
                self._backup_postgresql(database_url, backup_path)
            elif database_url.startswith('sqlite://'):
                # Backup de SQLite
                self._backup_sqlite(database_url, backup_path)
            else:
                self.logger.warning("Tipo de base de datos no soportado para backup")
                return None
            
            self.logger.info(f"Backup de base de datos creado: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creando backup de base de datos: {str(e)}")
            return None
    
    def _backup_database_to_temp(self):
        """Crear backup temporal de la base de datos."""
        try:
            temp_path = self.backup_dir / f"temp_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            database_url = self.app.config.get('DATABASE_URL', '')
            
            if database_url.startswith('postgresql://'):
                self._backup_postgresql(database_url, temp_path)
            elif database_url.startswith('sqlite://'):
                self._backup_sqlite(database_url, temp_path)
            else:
                return None
            
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Error creando backup temporal: {str(e)}")
            return None
    
    def _backup_postgresql(self, database_url, backup_path):
        """Crear backup de PostgreSQL usando pg_dump."""
        try:
            # Extraer información de conexión de la URL
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password
            
            cmd = [
                'pg_dump',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path[1:],  # Remover el '/' inicial
                '-f', str(backup_path),
                '--no-password'
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump falló: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Error en backup de PostgreSQL: {str(e)}")
            raise
    
    def _backup_sqlite(self, database_url, backup_path):
        """Crear backup de SQLite."""
        try:
            # Extraer ruta del archivo SQLite
            db_path = database_url.replace('sqlite:///', '')
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
            else:
                raise Exception(f"Archivo SQLite no encontrado: {db_path}")
                
        except Exception as e:
            self.logger.error(f"Error en backup de SQLite: {str(e)}")
            raise
    
    def restore_backup(self, backup_path):
        """Restaurar desde un archivo de backup."""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                raise Exception(f"Archivo de backup no encontrado: {backup_path}")
            
            self.logger.info(f"Iniciando restauración desde: {backup_path}")
            
            if backup_path.suffix == '.zip':
                # Restaurar backup completo
                self._restore_full_backup(backup_path)
            elif backup_path.suffix == '.sql':
                # Restaurar solo base de datos
                self._restore_database_backup(backup_path)
            else:
                raise Exception("Formato de backup no soportado")
            
            self.logger.info("Restauración completada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error en restauración: {str(e)}")
            raise
    
    def _restore_full_backup(self, backup_path):
        """Restaurar backup completo desde ZIP."""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Restaurar base de datos
                if 'database.sql' in zipf.namelist():
                    zipf.extract('database.sql', self.backup_dir)
                    db_backup_path = self.backup_dir / 'database.sql'
                    self._restore_database_backup(db_backup_path)
                    os.remove(db_backup_path)  # Limpiar archivo temporal
                
                # Restaurar archivos subidos
                uploads_dir = Path(self.app.config.get('UPLOAD_FOLDER', 'uploads'))
                for file_info in zipf.infolist():
                    if file_info.filename.startswith('uploads/'):
                        zipf.extract(file_info, '.')
                        
        except Exception as e:
            self.logger.error(f"Error restaurando backup completo: {str(e)}")
            raise
    
    def _restore_database_backup(self, backup_path):
        """Restaurar backup de base de datos."""
        try:
            database_url = self.app.config.get('DATABASE_URL', '')
            
            if database_url.startswith('postgresql://'):
                self._restore_postgresql(database_url, backup_path)
            elif database_url.startswith('sqlite://'):
                self._restore_sqlite(database_url, backup_path)
            else:
                raise Exception("Tipo de base de datos no soportado para restauración")
                
        except Exception as e:
            self.logger.error(f"Error restaurando base de datos: {str(e)}")
            raise
    
    def _restore_postgresql(self, database_url, backup_path):
        """Restaurar backup de PostgreSQL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password
            
            cmd = [
                'psql',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path[1:],
                '-f', str(backup_path)
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"psql falló: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Error restaurando PostgreSQL: {str(e)}")
            raise
    
    def _restore_sqlite(self, database_url, backup_path):
        """Restaurar backup de SQLite."""
        try:
            db_path = database_url.replace('sqlite:///', '')
            shutil.copy2(backup_path, db_path)
            
        except Exception as e:
            self.logger.error(f"Error restaurando SQLite: {str(e)}")
            raise
    
    def cleanup_old_backups(self):
        """Limpiar backups antiguos."""
        try:
            self.logger.info("Iniciando limpieza de backups antiguos")
            
            # Obtener todos los archivos de backup
            backup_files = []
            for pattern in ['full_backup_*.zip', 'db_backup_*.sql']:
                backup_files.extend(self.backup_dir.glob(pattern))
            
            # Ordenar por fecha de modificación (más reciente primero)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Eliminar backups que excedan el límite
            if len(backup_files) > self.max_backups:
                files_to_delete = backup_files[self.max_backups:]
                for file_path in files_to_delete:
                    file_path.unlink()
                    self.logger.info(f"Backup eliminado: {file_path.name}")
            
            # Eliminar backups más antiguos que 90 días
            cutoff_date = datetime.now() - timedelta(days=90)
            for file_path in backup_files:
                if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_date:
                    file_path.unlink()
                    self.logger.info(f"Backup antiguo eliminado: {file_path.name}")
            
            self.logger.info("Limpieza de backups completada")
            
        except Exception as e:
            self.logger.error(f"Error en limpieza de backups: {str(e)}")
    
    def list_backups(self):
        """Listar todos los backups disponibles."""
        try:
            backups = []
            
            # Buscar backups completos
            for backup_file in self.backup_dir.glob('full_backup_*.zip'):
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'type': 'full',
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime),
                })
            
            # Buscar backups de base de datos
            for backup_file in self.backup_dir.glob('db_backup_*.sql'):
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'type': 'database',
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime),
                })
            
            # Ordenar por fecha de creación (más reciente primero)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            return backups
            
        except Exception as e:
            self.logger.error(f"Error listando backups: {str(e)}")
            return []
    
    def get_backup_status(self):
        """Obtener estado del sistema de backups."""
        try:
            backups = self.list_backups()
            
            status = {
                'total_backups': len(backups),
                'last_backup': backups[0]['created'] if backups else None,
                'backup_dir': str(self.backup_dir),
                'backup_dir_size': sum(f.stat().st_size for f in self.backup_dir.iterdir() if f.is_file()),
                'max_backups': self.max_backups,
                'scheduler_running': True,  # Simplificado para este ejemplo
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de backups: {str(e)}")
            return None


# Instancia global del gestor de backups
backup_manager = BackupManager()