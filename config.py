import os
from datetime import timedelta

class Config:
    """إعدادات التطبيق الأساسية"""
    # قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///el_dahab_trading.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # المفتاح السري
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2024'
    
    # جلسة المستخدم
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # تسجيل الأخطاء
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    
    # رفع الملفات
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 ميجابايت
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    
    # إعدادات البريد الإلكتروني (اختياري)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', False)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['admin@eldahab-trading.com']

class DevelopmentConfig(Config):
    """إعدادات التطوير"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """إعدادات الإنتاج"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """إعدادات الاختبار"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
