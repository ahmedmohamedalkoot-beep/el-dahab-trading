from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

# ==================== جداول الربط many-to-many ====================
user_role = db.Table('user_role',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

user_warehouse = db.Table('user_warehouse',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('warehouse_id', db.Integer, db.ForeignKey('warehouse.id'), primary_key=True)
)

role_permission = db.Table('role_permission',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

# ==================== نماذج الأمان ====================
class Permission(db.Model):
    """نموذج الصلاحيات"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Permission {self.name}>'

class Role(db.Model):
    """نموذج الأدوار"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    permissions = db.relationship('Permission', secondary=role_permission, 
                                  backref=db.backref('roles', lazy='dynamic'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    """نموذج المستخدم"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # العلاقات
    roles = db.relationship('Role', secondary=user_role, backref=db.backref('users', lazy='dynamic'))
    warehouses = db.relationship('Warehouse', secondary=user_warehouse, backref=db.backref('users', lazy='dynamic'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """تعيين كلمة المرور بشكل آمن"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """التحقق من كلمة المرور"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission_name):
        """التحقق من وجود صلاحية معينة"""
        if self.is_admin:
            return True
        
        for role in self.roles:
            for permission in role.permissions:
                if permission.name == permission_name:
                    return True
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

# ==================== نماذج المخازن والأصناف ====================
class Warehouse(db.Model):
    """نموذج المخزن"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    location = db.Column(db.String(500))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # العلاقات
    items = db.relationship('WarehouseItem', backref='warehouse', lazy='dynamic', cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='warehouse', lazy='dynamic')
    from_transfers = db.relationship('Transfer', foreign_keys='Transfer.from_warehouse_id', backref='from_warehouse', lazy='dynamic')
    to_transfers = db.relationship('Transfer', foreign_keys='Transfer.to_warehouse_id', backref='to_warehouse', lazy='dynamic')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Warehouse {self.name}>'

class Category(db.Model):
    """نموذج الفئة"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # العلاقات
    items = db.relationship('Item', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Item(db.Model):
    """نموذج الصنف"""
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    # معلومات التعبئة
    carton_code = db.Column(db.String(100))
    items_per_carton = db.Column(db.Integer, default=0)
    items_per_box = db.Column(db.Integer, default=0)
    
    # الأسعار
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    box_price = db.Column(db.Numeric(10, 2), default=0)
    carton_price = db.Column(db.Numeric(10, 2), default=0)
    
    description = db.Column(db.Text)
    show_price_in_print = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # العلاقات
    warehouse_items = db.relationship('WarehouseItem', backref='item', lazy='dynamic', cascade='all, delete-orphan')
    invoice_items = db.relationship('InvoiceItem', backref='item', lazy='dynamic', cascade='all, delete-orphan')
    transfer_items = db.relationship('TransferItem', backref='item', lazy='dynamic')
    history = db.relationship('ItemHistory', backref='item', lazy='dynamic', cascade='all, delete-orphan')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Item {self.name}>'

class WarehouseItem(db.Model):
    """نموذج الصنف في المخزن"""
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    
    quantity = db.Column(db.Integer, default=0)
    reserved_quantity = db.Column(db.Integer, default=0)
    available_quantity = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('warehouse_id', 'item_id', name='unique_warehouse_item'),)
    
    def __repr__(self):
        return f'<WarehouseItem {self.item.name} - {self.quantity}>'

# ==================== نماذج الفواتير ====================
class Invoice(db.Model):
    """نموذج الفاتورة"""
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    invoice_type = db.Column(db.String(20), nullable=False)  # add, remove
    
    show_total_balance = db.Column(db.Boolean, default=False)
    show_items_amount = db.Column(db.Boolean, default=False)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    notes = db.Column(db.Text)
    
    # العلاقات
    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by_user = db.relationship('User', backref='invoices')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_totals(self):
        """حساب إجمالي الفاتورة"""
        self.total_amount = sum(item.total_price or 0 for item in self.items)
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

class InvoiceItem(db.Model):
    """نموذج بند الفاتورة"""
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    
    quantity_before = db.Column(db.Integer)
    quantity = db.Column(db.Integer, nullable=False)
    quantity_after = db.Column(db.Integer)
    
    unit_price = db.Column(db.Numeric(10, 2))
    total_price = db.Column(db.Numeric(12, 2))
    unit_type = db.Column(db.String(20))  # unit, box, carton
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_price(self):
        """حساب السعر الإجمالي"""
        if self.unit_price:
            self.total_price = self.quantity * self.unit_price
    
    def __repr__(self):
        return f'<InvoiceItem {self.item.name} x{self.quantity}>'

# ==================== نماذج التحويلات ====================
class Transfer(db.Model):
    """نموذج التحويل بين المخازن"""
    id = db.Column(db.Integer, primary_key=True)
    transfer_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    from_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    to_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    
    total_quantity = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    
    # العلاقات
    items = db.relationship('TransferItem', backref='transfer', lazy='dynamic', cascade='all, delete-orphan')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by_user = db.relationship('User', backref='transfers')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transfer {self.transfer_number}>'

class TransferItem(db.Model):
    """نموذج بند التحويل"""
    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('transfer.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False)
    unit_type = db.Column(db.String(20))  # unit, box, carton
    
    quantity_before_from = db.Column(db.Integer)
    quantity_after_from = db.Column(db.Integer)
    quantity_before_to = db.Column(db.Integer)
    quantity_after_to = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TransferItem {self.item.name} x{self.quantity}>'

# ==================== نماذج السجلات ====================
class ItemHistory(db.Model):
    """نموذج سجل تاريخ الصنف"""
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    
    operation_type = db.Column(db.String(50), nullable=False)  # add, remove, transfer
    quantity_before = db.Column(db.Integer)
    quantity_change = db.Column(db.Integer)
    quantity_after = db.Column(db.Integer)
    
    reference_id = db.Column(db.Integer)
    reference_type = db.Column(db.String(50))  # invoice, transfer
    
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by_user = db.relationship('User', backref='item_histories')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ItemHistory {self.operation_type} - {self.item.name}>'

class ActivityLog(db.Model):
    """نموذج سجل الأنشطة"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(500), nullable=False)
    entity_type = db.Column(db.String(100))  # invoice, item, warehouse, etc
    entity_id = db.Column(db.Integer)
    
    old_values = db.Column(JSON)
    new_values = db.Column(JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ActivityLog {self.action} - {self.created_at}>'