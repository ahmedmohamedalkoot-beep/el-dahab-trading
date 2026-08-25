from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField, DecimalField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional, NumberRange
from app.models import User, Warehouse, Category

class LoginForm(FlaskForm):
    """نموذج تسجيل الدخول"""
    username = StringField('اسم المستخدم', validators=[DataRequired(message='اسم المستخدم مطلوب')])
    password = PasswordField('كلمة المرور', validators=[DataRequired(message='كلمة المرور مطلوبة')])
    remember_me = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

class RegisterForm(FlaskForm):
    """نموذج التسجيل"""
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    full_name = StringField('الاسم الكامل', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور', 
                                     validators=[DataRequired(), EqualTo('password', message='كلمات المرور غير متطابقة')])
    submit = SubmitField('إنشاء حساب')
    
    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('اسم المستخدم موجود بالفعل')
    
    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('البريد الإلكتروني موجود بالفعل')

class UserForm(FlaskForm):
    """نموذج المستخدم"""
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    full_name = StringField('الاسم الكامل', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور')
    is_admin = BooleanField('إدارة النظام')
    is_active = BooleanField('مفعّل', default=True)
    roles = SelectMultipleField('الأدوار', coerce=int)
    warehouses = SelectMultipleField('المخازن المسموحة', coerce=int)
    submit = SubmitField('حفظ')

class WarehouseForm(FlaskForm):
    """نموذج المخزن"""
    name = StringField('اسم المخزن', validators=[DataRequired()])
    location = StringField('الموقع', validators=[DataRequired()])
    description = TextAreaField('الوصف')
    submit = SubmitField('حفظ')

class CategoryForm(FlaskForm):
    """نموذج الفئة"""
    name = StringField('اسم الفئة', validators=[DataRequired()])
    description = TextAreaField('الوصف')
    submit = SubmitField('حفظ')

class ItemForm(FlaskForm):
    """نموذج الصنف"""
    code = StringField('الكود', validators=[DataRequired()])
    name = StringField('الاسم', validators=[DataRequired()])
    category_id = SelectField('الفئة', coerce=int, validators=[DataRequired()])
    carton_code = StringField('كود الكرتونة')
    items_per_carton = IntegerField('عدد القطع بالكرتونة', validators=[Optional(), NumberRange(min=0)])
    items_per_box = IntegerField('عدد القطع بالعلبة', validators=[Optional(), NumberRange(min=0)])
    unit_price = DecimalField('سعر الوحدة', places=2, validators=[Optional()])
    box_price = DecimalField('سعر العلبة', places=2, validators=[Optional()])
    carton_price = DecimalField('سعر الكرتونة', places=2, validators=[Optional()])
    description = TextAreaField('الوصف')
    show_price_in_print = BooleanField('إظهار السعر عند الطباعة')
    submit = SubmitField('حفظ')

class InvoiceForm(FlaskForm):
    """نموذج الفاتورة"""
    warehouse_id = SelectField('المخزن', coerce=int, validators=[DataRequired()])
    invoice_type = SelectField('نوع الفاتورة', choices=[('add', 'إضافة'), ('remove', 'تنزيل')])
    show_total_balance = BooleanField('إظهار الرصيد الإجمالي')
    show_items_amount = BooleanField('إظهار مجموع الأصناف')
    notes = TextAreaField('ملاحظات')
    submit = SubmitField('حفظ')

class InvoiceItemForm(FlaskForm):
    """نموذج عنصر الفاتورة"""
    item_id = SelectField('الصنف', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('الكمية', validators=[DataRequired(), NumberRange(min=1)])
    unit_type = SelectField('نوع الوحدة', 
                           choices=[('unit', 'وحدة'), ('box', 'علبة'), ('carton', 'كرتونة')],
                           validators=[DataRequired()])
    submit = SubmitField('إضافة')

class TransferForm(FlaskForm):
    """نموذج التحويل"""
    from_warehouse_id = SelectField('من المخزن', coerce=int, validators=[DataRequired()])
    to_warehouse_id = SelectField('إلى المخزن', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('ملاحظات')
    submit = SubmitField('حفظ')

class TransferItemForm(FlaskForm):
    """نموذج عنصر التحويل"""
    item_id = SelectField('الصنف', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('الكمية', validators=[DataRequired(), NumberRange(min=1)])
    unit_type = SelectField('نوع الوحدة',
                           choices=[('unit', 'وحدة'), ('box', 'علبة'), ('carton', 'كرتونة')],
                           validators=[DataRequired()])
    submit = SubmitField('إضافة')

class RoleForm(FlaskForm):
    """نموذج الدور"""
    name = StringField('اسم الدور', validators=[DataRequired()])
    description = TextAreaField('الوصف')
    permissions = SelectMultipleField('الصلاحيات', coerce=int)
    submit = SubmitField('حفظ')