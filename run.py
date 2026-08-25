import os
from app import create_app, db
from app.models import User, Role, Permission, Warehouse, Category, Item

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Role': Role, 'Permission': Permission,
            'Warehouse': Warehouse, 'Category': Category, 'Item': Item}

@app.cli.command()
def init_db():
    """إنشاء جداول قاعدة البيانات"""
    db.create_all()
    print('تم إنشاء قاعدة البيانات بنجاح')

@app.cli.command()
def seed_db():
    """ملء قاعدة البيانات ببيانات افتراضية"""
    # الصلاحيات
    permissions = [
        Permission(name='add_invoice', description='إضافة الفواتير'),
        Permission(name='edit_invoice', description='تعديل الفواتير'),
        Permission(name='delete_invoice', description='حذف الفواتير'),
        Permission(name='print_invoice', description='طباعة الفواتير'),
        Permission(name='export_pdf', description='تصدير PDF'),
        Permission(name='transfer_items', description='تحويل الأصناف'),
        Permission(name='view_prices', description='عرض الأسعار'),
        Permission(name='manage_items', description='إدارة الأصناف'),
        Permission(name='manage_warehouse', description='إدارة المخازن'),
        Permission(name='manage_users', description='إدارة المستخدمين'),
    ]
    
    for permission in permissions:
        if not Permission.query.filter_by(name=permission.name).first():
            db.session.add(permission)
    
    db.session.commit()
    
    # الأدوار
    admin_role = Role.query.filter_by(name='مسؤول').first()
    if not admin_role:
        admin_role = Role(name='مسؤول', description='لديه جميع الصلاحيات')
        admin_role.permissions = Permission.query.all()
        db.session.add(admin_role)
    
    manager_role = Role.query.filter_by(name='مدير').first()
    if not manager_role:
        manager_role = Role(name='مدير', description='مدير المخزن')
        manager_role.permissions = Permission.query.filter(
            Permission.name.in_([
                'add_invoice', 'edit_invoice', 'delete_invoice',
                'print_invoice', 'export_pdf', 'transfer_items',
                'view_prices', 'manage_items'
            ])
        ).all()
        db.session.add(manager_role)
    
    employee_role = Role.query.filter_by(name='موظف').first()
    if not employee_role:
        employee_role = Role(name='موظف', description='موظف مخزن')
        employee_role.permissions = Permission.query.filter(
            Permission.name.in_([
                'add_invoice', 'print_invoice', 'view_prices'
            ])
        ).all()
        db.session.add(employee_role)
    
    db.session.commit()
    
    # المستخدم الإداري الأساسي
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@eldahab-trading.com',
            full_name='مسؤول النظام',
            is_admin=True,
            is_active=True
        )
        admin.set_password('admin123')
        admin.roles.append(admin_role)
        db.session.add(admin)
    
    # المخزن الأساسي
    if not Warehouse.query.filter_by(name='المخزن الرئيسي').first():
        warehouse = Warehouse(
            name='المخزن الرئيسي',
            location='القاهرة',
            description='المخزن الرئيسي للشركة',
            is_active=True
        )
        db.session.add(warehouse)
    
    db.session.commit()
    print('تم ملء قاعدة البيانات ببيانات افتراضية')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)