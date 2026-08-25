from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import db, User, Role, Permission, Warehouse
from app.forms import UserForm, RoleForm
from datetime import datetime
from functools import wraps

user_bp = Blueprint('user', __name__, url_prefix='/users')

def admin_required(f):
    """التحقق من أن المستخدم إداري"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('ليس لديك صلاحيات كافية', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== إدارة المستخدمين ====================
@user_bp.route('/')
@admin_required
def list_users():
    """عرض قائمة المستخدمين"""
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    return render_template('users/list.html', users=users)

@user_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    """إضافة مستخدم جديد"""
    form = UserForm()
    form.roles.choices = [(r.id, r.name) for r in Role.query.all()]
    form.warehouses.choices = [(w.id, w.name) for w in Warehouse.query.all()]
    
    if form.validate_on_submit():
        if not form.password.data:
            flash('كلمة المرور مطلوبة', 'danger')
            return redirect(url_for('user.add_user'))
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            is_admin=form.is_admin.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
        
        for role_id in form.roles.data:
            role = Role.query.get(role_id)
            if role:
                user.roles.append(role)
        
        for warehouse_id in form.warehouses.data:
            warehouse = Warehouse.query.get(warehouse_id)
            if warehouse:
                user.warehouses.append(warehouse)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'تم إضافة المستخدم {user.full_name} بنجاح', 'success')
        return redirect(url_for('user.list_users'))
    
    return render_template('users/form.html', form=form, title='إضافة مستخدم')

@user_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    """تعديل بيانات المستخدم"""
    user = User.query.get_or_404(id)
    form = UserForm()
    form.roles.choices = [(r.id, r.name) for r in Role.query.all()]
    form.warehouses.choices = [(w.id, w.name) for w in Warehouse.query.all()]
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.is_admin = form.is_admin.data
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        user.roles.clear()
        for role_id in form.roles.data:
            role = Role.query.get(role_id)
            if role:
                user.roles.append(role)
        
        user.warehouses.clear()
        for warehouse_id in form.warehouses.data:
            warehouse = Warehouse.query.get(warehouse_id)
            if warehouse:
                user.warehouses.append(warehouse)
        
        db.session.commit()
        
        flash(f'تم تحديث بيانات المستخدم {user.full_name} بنجاح', 'success')
        return redirect(url_for('user.list_users'))
    
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.full_name.data = user.full_name
        form.is_admin.data = user.is_admin
        form.is_active.data = user.is_active
        form.roles.data = [role.id for role in user.roles]
        form.warehouses.data = [warehouse.id for warehouse in user.warehouses]
    
    return render_template('users/form.html', form=form, user=user, title='تعديل مستخدم')

@user_bp.route('/deactivate/<int:id>', methods=['POST'])
@admin_required
def deactivate_user(id):
    """تعطيل المستخدم"""
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('لا يمكنك تعطيل حسابك بنفسك', 'danger')
        return redirect(url_for('user.list_users'))
    
    user.is_active = False
    db.session.commit()
    
    flash(f'تم تعطيل حساب {user.full_name} بنجاح', 'success')
    return redirect(url_for('user.list_users'))

@user_bp.route('/activate/<int:id>', methods=['POST'])
@admin_required
def activate_user(id):
    """تفعيل المستخدم"""
    user = User.query.get_or_404(id)
    user.is_active = True
    db.session.commit()
    
    flash(f'تم تفعيل حساب {user.full_name} بنجاح', 'success')
    return redirect(url_for('user.list_users'))

# ==================== إدارة الأدوار ====================
@user_bp.route('/roles')
@admin_required
def list_roles():
    """عرض قائمة الأدوار"""
    page = request.args.get('page', 1, type=int)
    roles = Role.query.paginate(page=page, per_page=20)
    return render_template('roles/list.html', roles=roles)

@user_bp.route('/roles/add', methods=['GET', 'POST'])
@admin_required
def add_role():
    """إضافة دور جديدة"""
    form = RoleForm()
    form.permissions.choices = [(p.id, p.description or p.name) for p in Permission.query.all()]
    
    if form.validate_on_submit():
        role = Role(
            name=form.name.data,
            description=form.description.data
        )
        
        for permission_id in form.permissions.data:
            permission = Permission.query.get(permission_id)
            if permission:
                role.permissions.append(permission)
        
        db.session.add(role)
        db.session.commit()
        
        flash(f'تم إضافة الدور {role.name} بنجاح', 'success')
        return redirect(url_for('user.list_roles'))
    
    return render_template('roles/form.html', form=form, title='إضافة دور')

@user_bp.route('/roles/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_role(id):
    """تعديل الدور"""
    role = Role.query.get_or_404(id)
    form = RoleForm()
    form.permissions.choices = [(p.id, p.description or p.name) for p in Permission.query.all()]
    
    if form.validate_on_submit():
        role.name = form.name.data
        role.description = form.description.data
        
        role.permissions.clear()
        for permission_id in form.permissions.data:
            permission = Permission.query.get(permission_id)
            if permission:
                role.permissions.append(permission)
        
        db.session.commit()
        
        flash(f'تم تحديث الدور {role.name} بنجاح', 'success')
        return redirect(url_for('user.list_roles'))
    
    elif request.method == 'GET':
        form.name.data = role.name
        form.description.data = role.description
        form.permissions.data = [permission.id for permission in role.permissions]
    
    return render_template('roles/form.html', form=form, role=role, title='تعديل دور')

# ==================== الملف الشخصي ====================
@user_bp.route('/profile')
@login_required
def profile():
    """عرض الملف الشخصي"""
    return render_template('users/profile.html', user=current_user)

@user_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """تغيير كلمة المرور"""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(old_password):
            flash('كلمة المرور القديمة غير صحيحة', 'danger')
        elif new_password != confirm_password:
            flash('كلمات المرور الجديدة غير متطابقة', 'danger')
        elif len(new_password) < 6:
            flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'danger')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('تم تغيير كلمة المرور بنجاح', 'success')
            return redirect(url_for('user.profile'))
    
    return render_template('users/change_password.html')