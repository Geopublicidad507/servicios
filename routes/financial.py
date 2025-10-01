from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from models import Property, Unit, Payment, Expense, Budget, User, db
from sqlalchemy import func, extract, and_, or_
from datetime import datetime, date, timedelta
from decimal import Decimal
import calendar
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

financial_bp = Blueprint('financial', __name__)

@financial_bp.route('/')
@login_required
def index():
    """Financial dashboard"""
    # Get properties based on user role
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    elif current_user.role == 'admin_ph':
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    else:
        return redirect(url_for('dashboard.resident'))
    
    # Current month/year
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Financial summary
    total_income = 0
    total_expenses = 0
    
    for prop in properties:
        # Monthly income
        income = db.session.query(func.sum(Payment.amount)).join(Unit).filter(
            Unit.property_id == prop.id,
            extract('month', Payment.payment_date) == current_month,
            extract('year', Payment.payment_date) == current_year
        ).scalar() or 0
        total_income += income
        
        # Monthly expenses
        expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.property_id == prop.id,
            extract('month', Expense.expense_date) == current_month,
            extract('year', Expense.expense_date) == current_year
        ).scalar() or 0
        total_expenses += expenses
    
    net_income = total_income - total_expenses
    
    # Recent transactions
    recent_payments = Payment.query.join(Unit).join(Property).filter(
        Property.id.in_([p.id for p in properties])
    ).order_by(Payment.created_at.desc()).limit(10).all()
    
    recent_expenses = Expense.query.filter(
        Expense.property_id.in_([p.id for p in properties])
    ).order_by(Expense.created_at.desc()).limit(10).all()
    
    # Overdue payments
    overdue_payments = Payment.query.join(Unit).join(Property).filter(
        Property.id.in_([p.id for p in properties]),
        Payment.status == 'overdue'
    ).all()
    
    return render_template('financial/index.html',
                         properties=properties,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         net_income=net_income,
                         recent_payments=recent_payments,
                         recent_expenses=recent_expenses,
                         overdue_payments=overdue_payments)

@financial_bp.route('/payments')
@login_required
def payments():
    """Payments management"""
    page = request.args.get('page', 1, type=int)
    property_id = request.args.get('property_id', type=int)
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Get properties based on user role
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    elif current_user.role == 'admin_ph':
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    else:
        return redirect(url_for('dashboard.resident'))
    
    # Build query
    query = Payment.query.join(Unit).join(Property).filter(
        Property.id.in_([p.id for p in properties])
    )
    
    # Apply filters
    if property_id:
        query = query.filter(Property.id == property_id)
    if status:
        query = query.filter(Payment.status == status)
    if date_from:
        query = query.filter(Payment.payment_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(Payment.payment_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    payments = query.order_by(Payment.payment_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('financial/payments.html',
                         payments=payments,
                         properties=properties,
                         filters={
                             'property_id': property_id,
                             'status': status,
                             'date_from': date_from,
                             'date_to': date_to
                         })

@financial_bp.route('/payments/add', methods=['GET', 'POST'])
@login_required
def add_payment():
    """Add new payment"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        flash('No tienes permisos para realizar esta acción.', 'error')
        return redirect(url_for('financial.payments'))
    
    # Get properties and units
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        unit_id = request.form.get('unit_id', type=int)
        amount = request.form.get('amount', type=float)
        payment_type = request.form.get('payment_type')
        payment_method = request.form.get('payment_method')
        payment_date = request.form.get('payment_date')
        description = request.form.get('description')
        
        # Validation
        if not all([unit_id, amount, payment_type, payment_date]):
            flash('Por favor completa todos los campos obligatorios.', 'error')
            return render_template('financial/add_payment.html', properties=properties)
        
        unit = Unit.query.get(unit_id)
        if not unit or unit.property_id not in [p.id for p in properties]:
            flash('Unidad no válida.', 'error')
            return render_template('financial/add_payment.html', properties=properties)
        
        # Generate receipt number
        last_payment = Payment.query.order_by(Payment.id.desc()).first()
        receipt_number = f"REC-{datetime.now().year}-{(last_payment.id + 1) if last_payment else 1:06d}"
        
        payment = Payment(
            unit_id=unit_id,
            user_id=unit.owner_id or current_user.id,
            amount=Decimal(str(amount)),
            payment_type=payment_type,
            payment_method=payment_method,
            payment_date=datetime.strptime(payment_date, '%Y-%m-%d').date(),
            description=description,
            receipt_number=receipt_number,
            status='paid'
        )
        
        try:
            db.session.add(payment)
            db.session.commit()
            flash(f'Pago registrado exitosamente. Recibo: {receipt_number}', 'success')
            return redirect(url_for('financial.payments'))
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar el pago.', 'error')
    
    return render_template('financial/add_payment.html', properties=properties)

@financial_bp.route('/expenses')
@login_required
def expenses():
    """Expenses management"""
    page = request.args.get('page', 1, type=int)
    property_id = request.args.get('property_id', type=int)
    category = request.args.get('category')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Get properties based on user role
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    elif current_user.role == 'admin_ph':
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    else:
        return redirect(url_for('dashboard.resident'))
    
    # Build query
    query = Expense.query.filter(
        Expense.property_id.in_([p.id for p in properties])
    )
    
    # Apply filters
    if property_id:
        query = query.filter(Expense.property_id == property_id)
    if category:
        query = query.filter(Expense.category == category)
    if date_from:
        query = query.filter(Expense.expense_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(Expense.expense_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    expenses = query.order_by(Expense.expense_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get expense categories
    categories = db.session.query(Expense.category).filter(
        Expense.property_id.in_([p.id for p in properties])
    ).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('financial/expenses.html',
                         expenses=expenses,
                         properties=properties,
                         categories=categories,
                         filters={
                             'property_id': property_id,
                             'category': category,
                             'date_from': date_from,
                             'date_to': date_to
                         })

@financial_bp.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Add new expense"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        flash('No tienes permisos para realizar esta acción.', 'error')
        return redirect(url_for('financial.expenses'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        property_id = request.form.get('property_id', type=int)
        category = request.form.get('category')
        description = request.form.get('description')
        amount = request.form.get('amount', type=float)
        expense_date = request.form.get('expense_date')
        vendor = request.form.get('vendor')
        invoice_number = request.form.get('invoice_number')
        payment_method = request.form.get('payment_method')
        
        # Validation
        if not all([property_id, category, description, amount, expense_date]):
            flash('Por favor completa todos los campos obligatorios.', 'error')
            return render_template('financial/add_expense.html', properties=properties)
        
        if property_id not in [p.id for p in properties]:
            flash('Propiedad no válida.', 'error')
            return render_template('financial/add_expense.html', properties=properties)
        
        expense = Expense(
            property_id=property_id,
            category=category,
            description=description,
            amount=Decimal(str(amount)),
            expense_date=datetime.strptime(expense_date, '%Y-%m-%d').date(),
            vendor=vendor,
            invoice_number=invoice_number,
            payment_method=payment_method,
            created_by=current_user.id,
            status='paid'
        )
        
        try:
            db.session.add(expense)
            db.session.commit()
            flash('Gasto registrado exitosamente.', 'success')
            return redirect(url_for('financial.expenses'))
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar el gasto.', 'error')
    
    return render_template('financial/add_expense.html', properties=properties)

@financial_bp.route('/reports')
@login_required
def reports():
    """Financial reports"""
    if current_user.role not in ['admin_general', 'admin_ph']:
        return redirect(url_for('dashboard.resident'))
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    else:
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    
    return render_template('financial/reports.html', properties=properties)

@financial_bp.route('/reports/income-statement')
@login_required
def income_statement():
    """Generate income statement report"""
    property_id = request.args.get('property_id', type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', type=int)
    format_type = request.args.get('format', 'html')
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    elif current_user.role == 'admin_ph':
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    else:
        return redirect(url_for('dashboard.resident'))
    
    # Filter by property if specified
    if property_id:
        properties = [p for p in properties if p.id == property_id]
    
    # Build date filters
    date_filters = [extract('year', Payment.payment_date) == year]
    expense_date_filters = [extract('year', Expense.expense_date) == year]
    
    if month:
        date_filters.append(extract('month', Payment.payment_date) == month)
        expense_date_filters.append(extract('month', Expense.expense_date) == month)
    
    # Calculate income by category
    income_data = {}
    for prop in properties:
        # Get payments by type
        payment_types = db.session.query(
            Payment.payment_type,
            func.sum(Payment.amount)
        ).join(Unit).filter(
            Unit.property_id == prop.id,
            and_(*date_filters)
        ).group_by(Payment.payment_type).all()
        
        for payment_type, amount in payment_types:
            if payment_type not in income_data:
                income_data[payment_type] = 0
            income_data[payment_type] += float(amount or 0)
    
    # Calculate expenses by category
    expense_data = {}
    for prop in properties:
        expense_categories = db.session.query(
            Expense.category,
            func.sum(Expense.amount)
        ).filter(
            Expense.property_id == prop.id,
            and_(*expense_date_filters)
        ).group_by(Expense.category).all()
        
        for category, amount in expense_categories:
            if category not in expense_data:
                expense_data[category] = 0
            expense_data[category] += float(amount or 0)
    
    total_income = sum(income_data.values())
    total_expenses = sum(expense_data.values())
    net_income = total_income - total_expenses
    
    report_data = {
        'period': f"{calendar.month_name[month]} {year}" if month else str(year),
        'properties': [p.name for p in properties],
        'income_data': income_data,
        'expense_data': expense_data,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': net_income
    }
    
    if format_type == 'pdf':
        return generate_pdf_report('Estado de Resultados', report_data)
    
    return render_template('financial/income_statement.html', **report_data)

@financial_bp.route('/reports/overdue')
@login_required
def overdue_report():
    """Generate overdue payments report"""
    property_id = request.args.get('property_id', type=int)
    days_overdue = request.args.get('days_overdue', 0, type=int)
    format_type = request.args.get('format', 'html')
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    elif current_user.role == 'admin_ph':
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    else:
        return redirect(url_for('dashboard.resident'))
    
    # Filter by property if specified
    if property_id:
        properties = [p for p in properties if p.id == property_id]
    
    # Get overdue payments
    today = datetime.now().date()
    overdue_date = today - timedelta(days=days_overdue)
    
    overdue_payments = []
    for prop in properties:
        payments = Payment.query.join(Unit).filter(
            Unit.property_id == prop.id,
            Payment.status == 'overdue',
            Payment.due_date <= overdue_date
        ).all()
        
        overdue_payments.extend(payments)
    
    # Group by property
    property_data = {}
    for payment in overdue_payments:
        property_name = payment.unit.property.name
        if property_name not in property_data:
            property_data[property_name] = {
                'total': 0,
                'count': 0,
                'payments': []
            }
        
        days_late = (today - payment.due_date).days if payment.due_date else 0
        
        property_data[property_name]['total'] += float(payment.amount)
        property_data[property_name]['count'] += 1
        property_data[property_name]['payments'].append({
            'unit': payment.unit.number,
            'owner': payment.user.full_name,
            'amount': float(payment.amount),
            'due_date': payment.due_date,
            'days_late': days_late
        })
    
    total_overdue = sum(data['total'] for data in property_data.values())
    total_count = sum(data['count'] for data in property_data.values())
    
    report_data = {
        'property_data': property_data,
        'total_overdue': total_overdue,
        'total_count': total_count,
        'days_overdue': days_overdue,
        'report_date': today
    }
    
    if format_type == 'pdf':
        return generate_pdf_report('Reporte de Morosidad', report_data)
    
    return render_template('financial/overdue_report.html', **report_data)

@financial_bp.route('/reports/balance-sheet')
@login_required
def balance_sheet():
    """Generate balance sheet report"""
    property_id = request.args.get('property_id', type=int)
    date_str = request.args.get('date')
    format_type = request.args.get('format', 'html')
    
    # Parse date or use today
    if date_str:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        report_date = datetime.now().date()
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    elif current_user.role == 'admin_ph':
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    else:
        return redirect(url_for('dashboard.resident'))
    
    # Filter by property if specified
    if property_id:
        properties = [p for p in properties if p.id == property_id]
    
    # Calculate assets
    assets = {
        'cash': 0,
        'accounts_receivable': 0,
        'fixed_assets': 0,
        'other_assets': 0
    }
    
    # Calculate liabilities
    liabilities = {
        'accounts_payable': 0,
        'loans': 0,
        'other_liabilities': 0
    }
    
    # Calculate cash (total payments received)
    for prop in properties:
        # Cash: payments received up to report date
        cash = db.session.query(func.sum(Payment.amount)).join(Unit).filter(
            Unit.property_id == prop.id,
            Payment.payment_date <= report_date,
            Payment.status == 'paid'
        ).scalar() or 0
        assets['cash'] += float(cash)
        
        # Accounts receivable: pending and overdue payments
        receivables = db.session.query(func.sum(Payment.amount)).join(Unit).filter(
            Unit.property_id == prop.id,
            Payment.status.in_(['pending', 'overdue'])
        ).scalar() or 0
        assets['accounts_receivable'] += float(receivables)
        
        # Fixed assets: property value (placeholder)
        assets['fixed_assets'] += float(prop.total_units * 50000)  # Placeholder value
        
        # Accounts payable: unpaid expenses
        payables = db.session.query(func.sum(Expense.amount)).filter(
            Expense.property_id == prop.id,
            Expense.status != 'paid'
        ).scalar() or 0
        liabilities['accounts_payable'] += float(payables)
    
    total_assets = sum(assets.values())
    total_liabilities = sum(liabilities.values())
    equity = total_assets - total_liabilities
    
    report_data = {
        'properties': [p.name for p in properties],
        'report_date': report_date,
        'assets': assets,
        'liabilities': liabilities,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'equity': equity
    }
    
    if format_type == 'pdf':
        return generate_pdf_report('Balance General', report_data)
    
    return render_template('financial/balance_sheet.html', **report_data)

@financial_bp.route('/reports/cash-flow')
@login_required
def cash_flow():
    """Generate cash flow report"""
    property_id = request.args.get('property_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    format_type = request.args.get('format', 'html')
    
    # Parse dates or use current month
    today = datetime.now().date()
    if date_from:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
    else:
        start_date = date(today.year, today.month, 1)
    
    if date_to:
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    else:
        end_date = today
    
    # Get properties
    if current_user.role == 'admin_general':
        properties = Property.query.filter_by(is_active=True).all()
    elif current_user.role == 'admin_ph':
        properties = Property.query.filter_by(admin_id=current_user.id, is_active=True).all()
    else:
        return redirect(url_for('dashboard.resident'))
    
    # Filter by property if specified
    if property_id:
        properties = [p for p in properties if p.id == property_id]
    
    # Calculate cash flow by day
    cash_flow_data = {}
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        cash_flow_data[date_str] = {
            'inflows': 0,
            'outflows': 0,
            'net': 0
        }
        current_date += timedelta(days=1)
    
    # Get inflows (payments)
    for prop in properties:
        payments = Payment.query.join(Unit).filter(
            Unit.property_id == prop.id,
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date,
            Payment.status == 'paid'
        ).all()
        
        for payment in payments:
            date_str = payment.payment_date.strftime('%Y-%m-%d')
            cash_flow_data[date_str]['inflows'] += float(payment.amount)
    
    # Get outflows (expenses)
    for prop in properties:
        expenses = Expense.query.filter(
            Expense.property_id == prop.id,
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
            Expense.status == 'paid'
        ).all()
        
        for expense in expenses:
            date_str = expense.expense_date.strftime('%Y-%m-%d')
            cash_flow_data[date_str]['outflows'] += float(expense.amount)
    
    # Calculate net and running balance
    running_balance = 0
    for date_str in sorted(cash_flow_data.keys()):
        data = cash_flow_data[date_str]
        data['net'] = data['inflows'] - data['outflows']
        running_balance += data['net']
        data['balance'] = running_balance
    
    # Calculate totals
    total_inflows = sum(data['inflows'] for data in cash_flow_data.values())
    total_outflows = sum(data['outflows'] for data in cash_flow_data.values())
    total_net = total_inflows - total_outflows
    
    report_data = {
        'properties': [p.name for p in properties],
        'start_date': start_date,
        'end_date': end_date,
        'cash_flow_data': cash_flow_data,
        'total_inflows': total_inflows,
        'total_outflows': total_outflows,
        'total_net': total_net,
        'final_balance': running_balance
    }
    
    if format_type == 'pdf':
        return generate_pdf_report('Flujo de Caja', report_data)
    
    return render_template('financial/cash_flow.html', **report_data)

@financial_bp.route('/api/units/<int:property_id>')
@login_required
def get_units(property_id):
    """Get units for a property (AJAX)"""
    property_obj = Property.query.get_or_404(property_id)
    
    # Check permissions
    if current_user.role == 'admin_ph' and property_obj.admin_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    units = Unit.query.filter_by(property_id=property_id).all()
    
    return jsonify([{
        'id': unit.id,
        'number': unit.number,
        'owner_name': unit.owner.full_name if unit.owner else 'Sin propietario',
        'monthly_fee': float(unit.monthly_fee)
    } for unit in units])

def generate_pdf_report(title, data):
    """Generate PDF report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_para = Paragraph(f"<b>{title}</b>", styles['Title'])
    story.append(title_para)
    story.append(Spacer(1, 12))
    
    # Period
    period_para = Paragraph(f"Período: {data['period']}", styles['Normal'])
    story.append(period_para)
    story.append(Spacer(1, 12))
    
    # Properties
    if data['properties']:
        props_para = Paragraph(f"Propiedades: {', '.join(data['properties'])}", styles['Normal'])
        story.append(props_para)
        story.append(Spacer(1, 12))
    
    # Income table
    if data['income_data']:
        income_table_data = [['Tipo de Ingreso', 'Monto']]
        for income_type, amount in data['income_data'].items():
            income_table_data.append([income_type.replace('_', ' ').title(), f"${amount:,.2f}"])
        income_table_data.append(['TOTAL INGRESOS', f"${data['total_income']:,.2f}"])
        
        income_table = Table(income_table_data)
        income_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(income_table)
        story.append(Spacer(1, 12))
    
    # Expenses table
    if data['expense_data']:
        expense_table_data = [['Categoría de Gasto', 'Monto']]
        for category, amount in data['expense_data'].items():
            expense_table_data.append([category.replace('_', ' ').title(), f"${amount:,.2f}"])
        expense_table_data.append(['TOTAL GASTOS', f"${data['total_expenses']:,.2f}"])
        
        expense_table = Table(expense_table_data)
        expense_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(expense_table)
        story.append(Spacer(1, 12))
    
    # Net income
    net_color = colors.green if data['net_income'] >= 0 else colors.red
    net_para = Paragraph(f"<b>UTILIDAD NETA: ${data['net_income']:,.2f}</b>", styles['Heading2'])
    story.append(net_para)
    
    doc.build(story)
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{title.replace(" ", "_")}.pdf"'
    
    return response
