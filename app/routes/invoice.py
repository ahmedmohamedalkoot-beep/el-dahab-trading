from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app.models import db, Invoice, InvoiceItem, Item, Warehouse, WarehouseItem, ItemHistory, ActivityLog, Transfer, TransferItem
from app.forms import InvoiceForm, InvoiceItemForm, TransferForm, TransferItemForm
from datetime import datetime
from functools import wraps
import string
import random

invoice_bp = Blueprint('invoice', __name__, url_prefix='/invoices')

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

def generate_invoice_number():
    """توليد رقم فاتورة فريد"""
    while True:
        prefix = 'INV'
        number = ''.join(random.choices(string.digits, k=6))
        invoice_number = f"{prefix}-{number}"
        if not Invoice.query.filter_by(invoice_number=invoice_number).first():
            return invoice_number

def generate_transfer_number():
    """توليد رقم تحويل فريد"""
    while True:
        prefix = 'TRN'
        number = ''.join(random.choices(string.digits, k=6))
        transfer_number = f"{prefix}-{number}"
        if not Transfer.query.filter_by(transfer_number=transfer_number).first():
            return transfer_number

# ==================== الفواتير ====================
@invoice_bp.route('/')
@login_required
def list_invoices():
    """عرض قائمة الفواتير"""
    page = request.args.get('page', 1, type=int)
    invoice_type = request.args.get('type', '')
    warehouse_id = request.args.get('warehouse', '', type=int)
    
    query = Invoice.query
    
    if invoice_type:
        query = query.filter_by(invoice_type=invoice_type)
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    
    invoices = query.order_by(Invoice.created_at.desc()).paginate(page=page, per_page=20)
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    
    return render_template('invoices/list.html', invoices=invoices, warehouses=warehouses, 
                         invoice_type=invoice_type, warehouse_id=warehouse_id)

@invoice_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('add_invoice')
def add_invoice():
    """إضافة فاتورة جديدة"""
    form = InvoiceForm()
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        invoice = Invoice(
            invoice_number=generate_invoice_number(),
            warehouse_id=form.warehouse_id.data,
            invoice_type=form.invoice_type.data,
            show_total_balance=form.show_total_balance.data,
            show_items_amount=form.show_items_amount.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(invoice)
        db.session.commit()
        
        activity = ActivityLog(
            user_id=current_user.id,
            action='إنشاء فاتورة جديدة: ' + invoice.invoice_number,
            entity_type='invoice',
            entity_id=invoice.id,
            new_values={'invoice_number': invoice.invoice_number, 'type': invoice.invoice_type}
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'تم إنشاء الفاتورة {invoice.invoice_number} بنجاح', 'success')
        return redirect(url_for('invoice.edit_invoice', id=invoice.id))
    
    return render_template('invoices/form.html', form=form, title='إضافة فاتورة')

@invoice_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('edit_invoice')
def edit_invoice(id):
    """تعديل الفاتورة"""
    invoice = Invoice.query.get_or_404(id)
    form = InvoiceForm()
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    item_form = InvoiceItemForm()
    item_form.item_id.choices = [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter_by(is_active=True).all()]
    item_form.unit_type.choices = [('unit', 'وحدة'), ('box', 'علبة'), ('carton', 'كرتونة')]
    
    if form.validate_on_submit():
        old_values = {
            'invoice_type': invoice.invoice_type,
            'show_total_balance': invoice.show_total_balance
        }
        
        invoice.invoice_type = form.invoice_type.data
        invoice.show_total_balance = form.show_total_balance.data
        invoice.show_items_amount = form.show_items_amount.data
        invoice.notes = form.notes.data
        db.session.commit()
        
        activity = ActivityLog(
            user_id=current_user.id,
            action='تعديل فاتورة: ' + invoice.invoice_number,
            entity_type='invoice',
            entity_id=invoice.id,
            old_values=old_values,
            new_values={'invoice_type': invoice.invoice_type}
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'تم تحديث الفاتورة {invoice.invoice_number} بنجاح', 'success')
        return redirect(url_for('invoice.edit_invoice', id=invoice.id))
    
    elif request.method == 'GET':
        form.warehouse_id.data = invoice.warehouse_id
        form.invoice_type.data = invoice.invoice_type
        form.show_total_balance.data = invoice.show_total_balance
        form.show_items_amount.data = invoice.show_items_amount
        form.notes.data = invoice.notes
    
    return render_template('invoices/edit.html', invoice=invoice, form=form, item_form=item_form)

@invoice_bp.route('/<int:id>/add-item', methods=['POST'])
@login_required
@permission_required('add_invoice')
def add_invoice_item(id):
    """إضافة عنصر للفاتورة"""
    invoice = Invoice.query.get_or_404(id)
    form = InvoiceItemForm()
    form.item_id.choices = [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        item = Item.query.get_or_404(form.item_id.data)
        warehouse_item = WarehouseItem.query.filter_by(
            warehouse_id=invoice.warehouse_id,
            item_id=item.id
        ).first()
        
        quantity_before = warehouse_item.quantity if warehouse_item else 0
        
        # حساب الكمية بناءً على نوع الوحدة
        total_units = form.quantity.data
        if form.unit_type.data == 'carton' and item.items_per_carton > 0:
            total_units = form.quantity.data * item.items_per_carton
        elif form.unit_type.data == 'box' and item.items_per_box > 0:
            total_units = form.quantity.data * item.items_per_box
        
        # حساب السعر
        if form.unit_type.data == 'carton':
            unit_price = item.carton_price
        elif form.unit_type.data == 'box':
            unit_price = item.box_price
        else:
            unit_price = item.unit_price
        
        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            item_id=item.id,
            quantity_before=quantity_before,
            quantity=total_units,
            unit_price=unit_price,
            unit_type=form.unit_type.data
        )
        invoice_item.calculate_price()
        
        db.session.add(invoice_item)
        
        # تحديث الكمية في المخزن
        if not warehouse_item:
            warehouse_item = WarehouseItem(
                warehouse_id=invoice.warehouse_id,
                item_id=item.id,
                quantity=0,
                reserved_quantity=0,
                available_quantity=0
            )
            db.session.add(warehouse_item)
            db.session.commit()
        
        if invoice.invoice_type == 'add':
            warehouse_item.quantity += total_units
        else:
            warehouse_item.quantity = max(0, warehouse_item.quantity - total_units)
        
        warehouse_item.available_quantity = warehouse_item.quantity - warehouse_item.reserved_quantity
        invoice_item.quantity_after = warehouse_item.quantity
        
        db.session.commit()
        
        # تسجيل التاريخ
        history = ItemHistory(
            item_id=item.id,
            warehouse_id=invoice.warehouse_id,
            operation_type='add' if invoice.invoice_type == 'add' else 'remove',
            quantity_before=quantity_before,
            quantity_change=total_units if invoice.invoice_type == 'add' else -total_units,
            quantity_after=warehouse_item.quantity,
            reference_id=invoice.id,
            reference_type='invoice',
            created_by=current_user.id
        )
        db.session.add(history)
        
        invoice.calculate_totals()
        db.session.commit()
        
        flash(f'تم إضافة {item.name} للفاتورة بنجاح', 'success')
        return redirect(url_for('invoice.edit_invoice', id=invoice.id))
    
    return redirect(url_for('invoice.edit_invoice', id=invoice.id))

@invoice_bp.route('/<int:invoice_id>/item/<int:item_id>/delete', methods=['POST'])
@login_required
@permission_required('edit_invoice')
def delete_invoice_item(invoice_id, item_id):
    """حذف عنصر من الفاتورة"""
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice_item = InvoiceItem.query.filter_by(invoice_id=invoice_id, id=item_id).first_or_404()
    
    # استرجاع الكمية من المخزن
    warehouse_item = WarehouseItem.query.filter_by(
        warehouse_id=invoice.warehouse_id,
        item_id=invoice_item.item_id
    ).first()
    
    if warehouse_item:
        if invoice.invoice_type == 'add':
            warehouse_item.quantity -= invoice_item.quantity
        else:
            warehouse_item.quantity += invoice_item.quantity
        
        warehouse_item.quantity = max(0, warehouse_item.quantity)
        warehouse_item.available_quantity = warehouse_item.quantity - warehouse_item.reserved_quantity
        db.session.commit()
    
    db.session.delete(invoice_item)
    invoice.calculate_totals()
    db.session.commit()
    
    flash('تم حذف العنصر من الفاتورة بنجاح', 'success')
    return redirect(url_for('invoice.edit_invoice', id=invoice.id))

@invoice_bp.route('/<int:id>/view')
@login_required
def view_invoice(id):
    """عرض الفاتورة"""
    invoice = Invoice.query.get_or_404(id)
    return render_template('invoices/view.html', invoice=invoice)

@invoice_bp.route('/<int:id>/print')
@login_required
@permission_required('print_invoice')
def print_invoice(id):
    """طباعة الفاتورة"""
    invoice = Invoice.query.get_or_404(id)
    return render_template('invoices/print.html', invoice=invoice)

@invoice_bp.route('/<int:id>/pdf')
@login_required
@permission_required('export_pdf')
def export_pdf(id):
    """تصدير الفاتورة بصيغة PDF"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.units import inch
    from io import BytesIO
    
    invoice = Invoice.query.get_or_404(id)
    
    # إنشاء ملف PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # العنوان
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0E3A5A'),
        spaceAfter=6,
        alignment=1  # وسط
    )
    elements.append(Paragraph('El Dahab Trading', title_style))
    elements.append(Paragraph('مستودعات الفناديق', title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # معلومات الفاتورة
    info_data = [
        ['رقم الفاتورة:', invoice.invoice_number, 'النوع:', 'إضافة' if invoice.invoice_type == 'add' else 'تنزيل'],
        ['المخزن:', invoice.warehouse.name, 'التاريخ:', invoice.created_at.strftime('%Y-%m-%d %H:%M')],
        ['المستخدم:', invoice.created_by_user.full_name, 'الحالة:', 'مكتملة']
    ]
    
    info_table = Table(info_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # جدول الأصناف
    items_data = [['الصنف', 'الكود', 'السعر', 'الكمية', 'المجموع', 'قبل', 'بعد']]
    for item in invoice.items:
        if current_user.has_permission('view_prices') or current_user.is_admin:
            items_data.append([
                item.item.name,
                item.item.code,
                f'{item.unit_price:.2f}' if item.item.show_price_in_print else '---',
                str(item.quantity),
                f'{item.total_price:.2f}' if item.item.show_price_in_print else '---',
                str(item.quantity_before or 0),
                str(item.quantity_after or 0)
            ])
        else:
            items_data.append([
                item.item.name,
                item.item.code,
                '---',
                str(item.quantity),
                '---',
                str(item.quantity_before or 0),
                str(item.quantity_after or 0)
            ])
    
    items_table = Table(items_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.6*inch, 0.6*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E3A5A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # الإجمالي
    totals_data = []
    if invoice.show_items_amount:
        totals_data.append(['إجمالي المبلغ:', f'{invoice.total_amount:.2f}'])
    if invoice.show_total_balance:
        total_qty = sum(wi.quantity for wi in WarehouseItem.query.filter_by(warehouse_id=invoice.warehouse_id).all())
        totals_data.append(['الرصيد الإجمالي:', str(total_qty)])
    
    if totals_data:
        totals_table = Table(totals_data, colWidths=[2*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold', 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#D4A574')),
        ]))
        elements.append(totals_table)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # توقيع المستخدم
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=2  # يمين
    )
    elements.append(Paragraph(f'{current_user.full_name}', signature_style))
    
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, 
                    download_name=f'Invoice_{invoice.invoice_number}.pdf')

# ==================== التحويلات ====================
@invoice_bp.route('/transfers')
@login_required
def list_transfers():
    """عرض قائمة التحويلات"""
    page = request.args.get('page', 1, type=int)
    transfers = Transfer.query.order_by(Transfer.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('transfers/list.html', transfers=transfers)

@invoice_bp.route('/transfers/add', methods=['GET', 'POST'])
@login_required
@permission_required('transfer_items')
def add_transfer():
    """إضافة تحويل جديد"""
    form = TransferForm()
    form.from_warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    form.to_warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        if form.from_warehouse_id.data == form.to_warehouse_id.data:
            flash('لا يمكن التحويل من نفس المخزن', 'danger')
            return redirect(url_for('invoice.add_transfer'))
        
        transfer = Transfer(
            transfer_number=generate_transfer_number(),
            from_warehouse_id=form.from_warehouse_id.data,
            to_warehouse_id=form.to_warehouse_id.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(transfer)
        db.session.commit()
        
        activity = ActivityLog(
            user_id=current_user.id,
            action='إنشاء تحويل جديد: ' + transfer.transfer_number,
            entity_type='transfer',
            entity_id=transfer.id,
            new_values={'transfer_number': transfer.transfer_number}
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'تم إنشاء التحويل {transfer.transfer_number} بنجاح', 'success')
        return redirect(url_for('invoice.edit_transfer', id=transfer.id))
    
    return render_template('transfers/form.html', form=form, title='إضافة تحويل')

@invoice_bp.route('/transfers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('transfer_items')
def edit_transfer(id):
    """تعديل التحويل"""
    transfer = Transfer.query.get_or_404(id)
    form = TransferForm()
    form.from_warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    form.to_warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    item_form = TransferItemForm()
    item_form.item_id.choices = [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter_by(is_active=True).all()]
    item_form.unit_type.choices = [('unit', 'وحدة'), ('box', 'علبة'), ('carton', 'كرتونة')]
    
    if form.validate_on_submit():
        transfer.notes = form.notes.data
        db.session.commit()
        
        flash(f'تم تحديث التحويل {transfer.transfer_number} بنجاح', 'success')
        return redirect(url_for('invoice.edit_transfer', id=transfer.id))
    
    elif request.method == 'GET':
        form.from_warehouse_id.data = transfer.from_warehouse_id
        form.to_warehouse_id.data = transfer.to_warehouse_id
        form.notes.data = transfer.notes
    
    return render_template('transfers/edit.html', transfer=transfer, form=form, item_form=item_form)

@invoice_bp.route('/transfers/<int:id>/add-item', methods=['POST'])
@login_required
@permission_required('transfer_items')
def add_transfer_item(id):
    """إضافة عنصر للتحويل"""
    transfer = Transfer.query.get_or_404(id)
    form = TransferItemForm()
    form.item_id.choices = [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        item = Item.query.get_or_404(form.item_id.data)
        
        # الحصول على الكميات من المخزن المصدر
        from_warehouse_item = WarehouseItem.query.filter_by(
            warehouse_id=transfer.from_warehouse_id,
            item_id=item.id
        ).first()
        
        to_warehouse_item = WarehouseItem.query.filter_by(
            warehouse_id=transfer.to_warehouse_id,
            item_id=item.id
        ).first()
        
        quantity_before_from = from_warehouse_item.quantity if from_warehouse_item else 0
        quantity_before_to = to_warehouse_item.quantity if to_warehouse_item else 0
        
        if quantity_before_from == 0:
            flash(f'لا توجد كمية كافية من {item.name} في المخزن المصدر', 'danger')
            return redirect(url_for('invoice.edit_transfer', id=transfer.id))
        
        # حساب الكمية
        total_units = form.quantity.data
        if form.unit_type.data == 'carton' and item.items_per_carton > 0:
            total_units = form.quantity.data * item.items_per_carton
        elif form.unit_type.data == 'box' and item.items_per_box > 0:
            total_units = form.quantity.data * item.items_per_box
        
        if total_units > quantity_before_from:
            flash(f'الكمية المطلوبة أكثر من المتاح في المخزن', 'danger')
            return redirect(url_for('invoice.edit_transfer', id=transfer.id))
        
        transfer_item = TransferItem(
            transfer_id=transfer.id,
            item_id=item.id,
            quantity=total_units,
            unit_type=form.unit_type.data,
            quantity_before_from=quantity_before_from,
            quantity_before_to=quantity_before_to
        )
        
        # تحديث الكمية في المخزن المصدر
        if not from_warehouse_item:
            from_warehouse_item = WarehouseItem(
                warehouse_id=transfer.from_warehouse_id,
                item_id=item.id,
                quantity=0,
                reserved_quantity=0,
                available_quantity=0
            )
            db.session.add(from_warehouse_item)
        
        from_warehouse_item.quantity -= total_units
        from_warehouse_item.available_quantity = from_warehouse_item.quantity - from_warehouse_item.reserved_quantity
        transfer_item.quantity_after_from = from_warehouse_item.quantity
        
        # تحديث الكمية في المخزن الهدف
        if not to_warehouse_item:
            to_warehouse_item = WarehouseItem(
                warehouse_id=transfer.to_warehouse_id,
                item_id=item.id,
                quantity=0,
                reserved_quantity=0,
                available_quantity=0
            )
            db.session.add(to_warehouse_item)
        
        to_warehouse_item.quantity += total_units
        to_warehouse_item.available_quantity = to_warehouse_item.quantity - to_warehouse_item.reserved_quantity
        transfer_item.quantity_after_to = to_warehouse_item.quantity
        
        db.session.add(transfer_item)
        db.session.commit()
        
        # تسجيل التاريخ في كلا المخزنين
        history_from = ItemHistory(
            item_id=item.id,
            warehouse_id=transfer.from_warehouse_id,
            operation_type='transfer',
            quantity_before=quantity_before_from,
            quantity_change=-total_units,
            quantity_after=from_warehouse_item.quantity,
            reference_id=transfer.id,
            reference_type='transfer',
            created_by=current_user.id
        )
        
        history_to = ItemHistory(
            item_id=item.id,
            warehouse_id=transfer.to_warehouse_id,
            operation_type='transfer',
            quantity_before=quantity_before_to,
            quantity_change=total_units,
            quantity_after=to_warehouse_item.quantity,
            reference_id=transfer.id,
            reference_type='transfer',
            created_by=current_user.id
        )
        
        db.session.add(history_from)
        db.session.add(history_to)
        
        transfer.total_quantity += total_units
        db.session.commit()
        
        flash(f'تم إضافة {item.name} للتحويل بنجاح', 'success')
        return redirect(url_for('invoice.edit_transfer', id=transfer.id))
    
    return redirect(url_for('invoice.edit_transfer', id=transfer.id))

@invoice_bp.route('/transfers/<int:transfer_id>/item/<int:item_id>/delete', methods=['POST'])
@login_required
@permission_required('transfer_items')
def delete_transfer_item(transfer_id, item_id):
    """حذف عنصر من التحويل"""
    transfer = Transfer.query.get_or_404(transfer_id)
    transfer_item = TransferItem.query.filter_by(transfer_id=transfer_id, id=item_id).first_or_404()
    
    # استرجاع الكميات من المخزن
    from_warehouse_item = WarehouseItem.query.filter_by(
        warehouse_id=transfer.from_warehouse_id,
        item_id=transfer_item.item_id
    ).first()
    
    to_warehouse_item = WarehouseItem.query.filter_by(
        warehouse_id=transfer.to_warehouse_id,
        item_id=transfer_item.item_id
    ).first()
    
    if from_warehouse_item:
        from_warehouse_item.quantity += transfer_item.quantity
        from_warehouse_item.available_quantity = from_warehouse_item.quantity - from_warehouse_item.reserved_quantity
    
    if to_warehouse_item:
        to_warehouse_item.quantity -= transfer_item.quantity
        to_warehouse_item.quantity = max(0, to_warehouse_item.quantity)
        to_warehouse_item.available_quantity = to_warehouse_item.quantity - to_warehouse_item.reserved_quantity
    
    db.session.delete(transfer_item)
    transfer.total_quantity -= transfer_item.quantity
    db.session.commit()
    
    flash('تم حذف العنصر من التحويل بنجاح', 'success')
    return redirect(url_for('invoice.edit_transfer', id=transfer.id))