import os
import shutil
import zipfile
from datetime import datetime
import paramiko
import subprocess
from typing import Optional, Tuple
from config import Config

class BackupManager:
    """Менеджер резервного копирования базы данных"""
    
    def __init__(self, db_path: str = 'library.db'):
        self.db_path = db_path
        self.backup_dir = Config.BACKUP_PATH
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self) -> Tuple[bool, str]:
        """Создание резервной копии базы данных"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"library_backup_{timestamp}"
            
            # Создаем zip-архив с базой данных
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.exists(self.db_path):
                    zipf.write(self.db_path, os.path.basename(self.db_path))
                else:
                    # Если используется SQLite в памяти или другой механизм
                    # Создаем дамп через SQLAlchemy или subprocess
                    dump_file = os.path.join(self.backup_dir, f"{backup_name}.sql")
                    self._create_sql_dump(dump_file)
                    zipf.write(dump_file, os.path.basename(dump_file))
                    os.remove(dump_file)
            
            # Добавляем информацию о резервной копии
            info_file = os.path.join(self.backup_dir, f"{backup_name}.info")
            with open(info_file, 'w') as f:
                f.write(f"Backup created: {datetime.now().isoformat()}\n")
                f.write(f"Original DB: {self.db_path}\n")
                f.write(f"Backup size: {os.path.getsize(backup_path)} bytes\n")
            
            return True, backup_path
        
        except Exception as e:
            return False, f"Ошибка при создании резервной копии: {str(e)}"
    
    def _create_sql_dump(self, dump_file: str):
        """Создание SQL дампа базы данных"""
        # Для SQLite используем sqlite3 для создания дампа
        if self.db_path.startswith('sqlite:///'):
            db_file = self.db_path.replace('sqlite:///', '')
            if os.path.exists(db_file):
                subprocess.run(['sqlite3', db_file, '.dump'], stdout=open(dump_file, 'w'))
    
    def restore_backup(self, backup_path: str) -> Tuple[bool, str]:
        """Восстановление базы данных из резервной копии"""
        try:
            # Извлекаем архив
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Находим файл базы данных в архиве
                db_files = [f for f in zipf.namelist() if f.endswith('.db') or f.endswith('.sql')]
                
                if not db_files:
                    return False, "В архиве не найден файл базы данных"
                
                # Извлекаем файл
                db_file = db_files[0]
                zipf.extract(db_file, self.backup_dir)
                
                # Восстанавливаем базу данных
                temp_db_path = os.path.join(self.backup_dir, db_file)
                
                if db_file.endswith('.sql'):
                    # Это SQL дамп, нужно выполнить его
                    self._restore_from_sql_dump(temp_db_path)
                else:
                    # Это файл базы данных, копируем его
                    shutil.copy(temp_db_path, self.db_path)
                
                # Удаляем временный файл
                os.remove(temp_db_path)
            
            return True, "База данных успешно восстановлена"
        
        except Exception as e:
            return False, f"Ошибка при восстановлении: {str(e)}"
    
    def _restore_from_sql_dump(self, dump_file: str):
        """Восстановление из SQL дампа"""
        # Для SQLite
        if self.db_path.startswith('sqlite:///'):
            db_file = self.db_path.replace('sqlite:///', '')
            # Создаем пустую базу данных
            open(db_file, 'w').close()
            # Выполняем дамп
            subprocess.run(['sqlite3', db_file], stdin=open(dump_file, 'r'))
    
    def list_backups(self) -> list:
        """Список доступных резервных копий"""
        backups = []
        for file in os.listdir(self.backup_dir):
            if file.endswith('.zip'):
                file_path = os.path.join(self.backup_dir, file)
                info = {
                    'name': file,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'created': datetime.fromtimestamp(os.path.getctime(file_path))
                }
                backups.append(info)
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def upload_to_remote(self, backup_path: str, 
                        host: str = None, 
                        username: str = None, 
                        password: str = None,
                        remote_path: str = None) -> Tuple[bool, str]:
        """Загрузка резервной копии на удаленный сервер по SSH"""
        try:
            host = host or Config.REMOTE_HOST
            username = username or Config.REMOTE_USER
            password = password or Config.REMOTE_PASSWORD
            remote_path = remote_path or Config.REMOTE_PATH
            
            if not all([host, username]):
                return False, "Не указаны параметры подключения к удаленному серверу"
            
            # Подключение по SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(host, username=username, password=password)
            
            # Создаем SFTP сессию
            sftp = ssh.open_sftp()
            
            # Создаем директорию на удаленном сервере, если её нет
            try:
                sftp.stat(remote_path)
            except IOError:
                # Директории нет, создаем её
                sftp.mkdir(remote_path)
            
            # Загружаем файл
            remote_file = os.path.join(remote_path, os.path.basename(backup_path))
            sftp.put(backup_path, remote_file)
            
            # Закрываем соединения
            sftp.close()
            ssh.close()
            
            return True, f"Резервная копия успешно загружена на {host}:{remote_file}"
        
        except Exception as e:
            return False, f"Ошибка при загрузке на удаленный сервер: {str(e)}"
    
    def upload_to_cloud_storage(self, backup_path: str, cloud_type: str = 'ftp') -> Tuple[bool, str]:
        """Загрузка резервной копии в облачное хранилище"""
        # Реализация для различных облачных хранилищ
        # В данной реализации - заглушка
        if cloud_type == 'ftp':
            return self.upload_to_remote(backup_path)
        elif cloud_type == 'dropbox':
            # Интеграция с Dropbox API
            return False, "Интеграция с Dropbox не реализована"
        elif cloud_type == 'google_drive':
            # Интеграция с Google Drive API
            return False, "Интеграция с Google Drive не реализована"
        else:
            return False, f"Неподдерживаемый тип облачного хранилища: {cloud_type}"
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> Tuple[bool, str]:
        """Очистка старых резервных копий"""
        try:
            backups = self.list_backups()
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            
            deleted_count = 0
            for backup in backups:
                if backup['created'].timestamp() < cutoff_date:
                    os.remove(backup['path'])
                    # Удаляем соответствующий info файл
                    info_file = backup['path'].replace('.zip', '.info')
                    if os.path.exists(info_file):
                        os.remove(info_file)
                    deleted_count += 1
            
            return True, f"Удалено {deleted_count} старых резервных копий"
        
        except Exception as e:
            return False, f"Ошибка при очистке старых копий: {str(e)}"