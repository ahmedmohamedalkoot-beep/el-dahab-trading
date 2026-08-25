from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import db, User, Role, Permission, Warehouse, Category, Item, Invoice, InvoiceItem, Transfer, TransferItem, ItemHistory, ActivityLog, WarehouseItem
from app.forms import WarehouseForm, CategoryForm, ItemForm, RoleForm
from datetime import datetime
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """التحقق من أن المستخدم إداري"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('ليس لديك صلاحيات كافية', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    """التحقق من وجود صلاحية معينة"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_permission(permission):
                flash('ليس لديك صلاحيات كافية', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== لوحة التحكم ====================
@admin_bp.route('/')
@admin_required
def dashboard():
    """لوحة التحكم الرئيسية"""
    total_items = Item.query.count()
    total_warehouses = Warehouse.query.count()
    total_users = User.query.count()
    total_invoices = Invoice.query.count()
    total_transfers = Transfer.query.count()
    
    recent_invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(5).all()
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_items=total_items,
                         total_warehouses=total_warehouses,
                         total_users=total_users,
                         total_invoices=total_invoices,
                         total_transfers=total_transfers,
                         recent_invoices=recent_invoices,
                         recent_activities=recent_activities)

# ==================== إدارة المخازن ====================
@admin_bp.route('/warehouses')
@admin_required
def warehouses():
    """عرض قائمة المخازن"""
    page = request.args.get('page', 1, type=int)
    warehouses = Warehouse.query.paginate(page=page, per_page=20)
    return render_template('admin/warehouses/list.html', warehouses=warehouses)

@admin_bp.route('/warehouses/add', methods=['GET', 'POST'])
@admin_required
@permission_required('manage_warehouse')
def add_warehouse():
    """إضافة مخزن جديد"""
    form = WarehouseForm()
    if form.validate_on_submit():
        warehouse = Warehouse(
            name=form.name.data,
            location=form.location.data,
            description=form.description.data
        )
        db.session.add(warehouse)
        db.session.commit()
        
        activity = ActivityLog(
            user_id=current_user.id,
            action='إضافة مخزن جديد: ' + warehouse.name,
            entity_type='warehouse',
            entity_id=warehouse.id,
            new_values={'name': warehouse.name, 'location': warehouse.location}
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'تم إضافة المخزن {warehouse.name} بنجاح', 'success')
        return redirect(url_for('admin.warehouses'))
    
    return render_template('admin/warehouses/form.html', form=form, title='إضافة مخزن')

@admin_bp.route('/warehouses/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
@permission_required('manage_warehouse')
def edit_warehouse(id):
    """تعديل المخزن"""
    warehouse = Warehouse.query.get_or_404(id)
    form = WarehouseForm()
    
    if form.validate_on_submit():
        old_values = {'name': warehouse.name, 'location': warehouse.location}
        
        warehouse.name = form.name.data
        warehouse.location = form.location.data
        warehouse.description = form.description.data
        db.session.commit()
        
        activity = ActivityLog(
            user_id=current_user.id,
            action='تعديل مخزن: ' + warehouse.name,
            entity_type='warehouse',
            entity_id=warehouse.id,
            old_values=old_values,
            new_values={'name': warehouse.name, 'location': warehouse.location}
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'تم تحديث المخزن {warehouse.name} بنجاح', 'success')
        return redirect(url_for('admin.warehouses'))
    elif request.method == 'GET':
        form.name.data = warehouse.name
        form.location.data = warehouse.location
        form.description.data = warehouse.description
    
    return render_template('admin/warehouses/form.html', form=form, warehouse=warehouse, title='تعديل مخزن')

# ==================== إدارة الفئات ====================
@admin_bp.route('/categories')
@admin_required
def categories():
    """عرض قائمة الفئات"""
    page = request.args.get('page', 1, type=int)
    categories = Category.query.paginate(page=page, per_page=20)
    return render_template('admin/categories/list.html', categories=categories)

@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
@permission_required('manage_items')
def add_category():
    """إضافة فئة جديدة"""
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        
        activity = ActivityLog(
            user_id=current_user.id,
            action='إضافة فئة جديدة: ' + category.name,
            entity_type='category',
            entity_id=category.id,
            new_values={'name': category.name}
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'تم إضافة الفئة {category.name} بنجاح', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/categories/form.html', form=form, title='إضافة فئة')

@admin_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
@permission_required('manage_items')
def edit_category(id):
    """تعديل الفئة"""
    category = Category.query.get_or_404(id)
    form = CategoryForm()
    
    if form.validate_on_submit():
        old_values = {'name': category.name}
        
        category.name = form.name.data
        category.description = form.description.data
        db.session.commit()
        
        activity = ActivityLog(
            user_id=current_user.id,
            action='تعديل فئة: ' + category.name,
            entity_type='category',
            entity_id=category.id,
            old_values=old_values,
            new_values={'name': category.name}
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'تم تحديث الفئة {category.name} بنجاح', 'success')
        return redirect(url_for('admin.categories'))
    elif request.method == 'GET':
        form.name.data = category.name
        form.description.data = category.description
    
    return render_template('admin/categories/form.html', form=form, category=category, title='تعديل فئة')

# ==================== إدارة الأصناف ====================
@admin_bp.route('/items')
@admin_required
def items():
    """عرض قائمة الأصناف"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Item.query
    if search:
        query = query.filter((Item.code.ilike(f'%{search}%')) | (Item.name.ilike(f'%{search}%')))
    
    items = query.paginate(page=page, per_page=20)
    return render_template('admin/items/list.html', items=items, search=search)

@admin_bp.route('/items/add', methods=['GET', 'POST'])
@admin_required
@permission_required('manage_items')
def add_item():
    """إضافة صنف جديد"""
    form = ItemForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        item = Item(
            code=form.code.data,
            name=form.name.data,
            category_id=form.category_id.data,
            carton_code=form.carton_code.data,
            items_per_carton=form.items_per_carton.data or 0,
            items_per_box=form.items_per_box.data or 0,
            unit_price=form.unit_price.data or 0,
            box_price=form.box_price.data or 0,
            carton_price=form.carton_price.data or 0,
            description=form.description.data,
            show_price_in_print=form.show_price_in_print.data
        )
        db.session.add(item)
        db.session.commit()
        
        activity = ActivityLog(
            user_id=current_user.id,
            action='إضافة صنف جديد: ' + item.name,
            entity_type='item',
            entity_id=item.id,
            new_values={'code': item.code, 'name': item.name}
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'تم إضافة الصنف {item.name} بنجاح', 'success')
        return redirect(url_for('admin.items'))
    
    return render_template('admin/items/form.html', form=form, title='إضافة صنف')

@admin_bp.route('/items/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
@permission_required('manage_items')
def edit_item(id):
    """تعديل الصنف"""
    item = Item.query.get_or_404(id)
    form = ItemForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        old_values = {
            'code': item.code,
            'name': item.name,
            'unit_price': str(item.unit_price)
        }
        
        item.code = form.code.data
        item.name = form.name.data
        item.category_id = form.category_id.data
        item.carton_code = form.carton_code.data
        item.items_per_carton = form.items_per_carton.data or 0
        item.items_per_box = form.items_per_box.data or 0
        item.unit_price = form.unit_price.data or 0
        item.box_price = form.box_price.data or 0
        item.carton_price = form.carton_price.data or 0
        item.description = form.description.data
        item.show_price_in_print = form.show_price_in_print.data
        db.session.commit()
        
        activity = ActivityLog(
            user_id=current_user.id,
            action='تعديل صنف: ' + item.name,
            entity_type='item',
            entity_id=item.id,
            old_values=old_values,
            new_values={
                'code': item.code,
                'name': item.name,
                'unit_price': str(item.unit_price)
            }
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'تم تحديث الصنف {item.name} بنجاح', 'success')
        return redirect(url_for('admin.items'))
    elif request.method == 'GET':
        form.code.data = item.code
        form.name.data = item.name
        form.category_id.data = item.category_id
        form.carton_code.data = item.carton_code
        form.items_per_carton.data = item.items_per_carton
        form.items_per_box.data = item.items_per_box
        form.unit_price.data = item.unit_price
        form.box_price.data = item.box_price
        form.carton_price.data = item.carton_price
        form.description.data = item.description
        form.show_price_in_print.data = item.show_price_in_print
    
    return render_template('admin/items/form.html', form=form, item=item, title='تعديل صنف')

@admin_bp.route('/items/history/<int:id>')
@admin_required
def item_history(id):
    """عرض تاريخ الصنف"""
    item = Item.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    
    history = ItemHistory.query.filter_by(item_id=id).order_by(ItemHistory.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('admin/items/history.html', item=item, history=history)

@admin_bp.route('/items/delete/<int:id>', methods=['POST'])
@admin_required
@permission_required('manage_items')
def delete_item(id):
    """حذف الصنف"""
    item = Item.query.get_or_404(id)
    item_name = item.name
    
    db.session.delete(item)
    db.session.commit()
    
    activity = ActivityLog(
        user_id=current_user.id,
        action='حذف صنف: ' + item_name,
        entity_type='item',
        entity_id=id,
        old_values={'code': item.code, 'name': item_name}
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f'تم حذف الصنف {item_name} بنجاح', 'success')
    return redirect(url_for('admin.items'))