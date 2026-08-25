from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class=Config):
    """إنشاء تطبيق Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # تهيئة الإضافات
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # إعداد رسالة تسجيل الدخول
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'يرجى تسجيل الدخول أولاً'
    login_manager.login_message_category = 'warning'
    
    # تسجيل مسارات Blueprint
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.user import user_bp
    from app.routes.invoice import invoice_bp
    from app.routes.warehouse import warehouse_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(warehouse_bp)
    
    @login_manager.user_loader
    def load_user(id):
        from app.models import User
        return User.query.get(int(id))
    
    @app.shell_context_processor
    def make_shell_context():
        from app.models import (
            User, Role, Permission, Warehouse, Item, Category,
            Invoice, InvoiceItem, Transfer, TransferItem,
            ItemHistory, ActivityLog, WarehouseItem
        )
        return {
            'db': db,
            'User': User,
            'Role': Role,
            'Permission': Permission,
            'Warehouse': Warehouse,
            'Item': Item,
            'Category': Category,
            'Invoice': Invoice,
            'InvoiceItem': InvoiceItem,
            'Transfer': Transfer,
            'TransferItem': TransferItem,
            'ItemHistory': ItemHistory,
            'ActivityLog': ActivityLog,
            'WarehouseItem': WarehouseItem
        }
    
    # معالجات الأخطاء
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403
    
    return app