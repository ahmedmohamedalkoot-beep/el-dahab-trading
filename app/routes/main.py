from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user, login_user
from app.models import db, User
from app.forms import LoginForm, RegisterForm
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """الصفحة الرئيسية"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    return render_template('index.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """تسجيل دخول المستخدم"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('اسم مستخدم أو كلمة مرور غير صحيحة', 'danger')
            return redirect(url_for('main.login'))
        
        if not user.is_active:
            flash('حسابك معطل', 'danger')
            return redirect(url_for('main.login'))
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
    
    return render_template('login.html', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    """تسجيل خروج المستخدم"""
    logout_user()
    flash('تم تسجيل خروجك بنجاح', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """التسجيل المباشر (إذا كانت مفعلة)"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return redirect(url_for('main.register'))
        
        if User.query.filter_by(email=form.email.data).first():
            flash('البريد الإلكتروني موجود بالفعل', 'danger')
            return redirect(url_for('main.register'))
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('تم إنشاء حسابك بنجاح! يرجى تسجيل الدخول', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)

@main_bp.errorhandler(404)
def not_found_error(error):
    """معالجة خطأ 404"""
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """معالجة خطأ 500"""
    db.session.rollback()
    return render_template('errors/500.html'), 500

@main_bp.errorhandler(403)
def forbidden_error(error):
    """معالجة خطأ 403"""
    return render_template('errors/403.html'), 403