"""
TimetablePro - Application Configuration
Supports dual database mode: SQLite out-of-the-box (zero configuration)
and MySQL for production deployment.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'timetablepro-secret-key-2026-production')
    
    # Database Configuration:
    # Set DB_TYPE='mysql' and configure connection parameters, or leave as 'sqlite'
    DB_TYPE = os.environ.get('DB_TYPE', 'sqlite').lower()
    
    # SQLite configuration (Default zero-setup)
    SQLITE_PATH = os.path.join(BASE_DIR, 'timetable.db')
    
    # MySQL configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'timetablepro')
    
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
