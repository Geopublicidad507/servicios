from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import io
import os

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
    def generate_receipt(self, payment):
        """Generate payment receipt PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
        story = []
        
        # Header
        header_style = ParagraphStyle(
            'Header',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,
            textColor=colors.darkblue
        )
        
        story.append(Paragraph("RECIBO DE PAGO", header_style))
        story.append(Spacer(1, 20))
        
        # Property info
        property_info = f"""
        <b>Propiedad:</b> {payment.unit.property.name}<br/>
        <b>Dirección:</b> {payment.unit.property.address}<br/>
        <b>Código:</b> {payment.unit.property.code}
        """
        story.append(Paragraph(property_info, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Receipt details table
        data = [
            ['Recibo No.', payment.receipt_number or f'REC-{payment.id:06d}'],
            ['Fecha de Pago', payment.payment_date.strftime('%d/%m/%Y')],
            ['Unidad', payment.unit.unit_identifier],
            ['Propietario', payment.user.full_name],
            ['Tipo de Pago', payment.payment_type.replace('_', ' ').title()],
            ['Método de Pago', payment.payment_method.replace('_', ' ').title()],
            ['Monto', f'${payment.amount:,.2f}'],
            ['Estado', payment.status.title()]
        ]
        
        if payment.description:
            data.append(['Descripción', payment.description])
        
        table = Table(data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Footer
        footer = f"""
        <br/><br/>
        <b>Administrador:</b> {payment.unit.property.admin.full_name}<br/>
        <b>Fecha de Emisión:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>
        <br/>
        <i>Este recibo es válido como comprobante de pago.</i>
        """
        story.append(Paragraph(footer, self.styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_overdue_notice(self, unit, overdue_payments):
        """Generate overdue payment notice"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
        story = []
        
        # Header
        header_style = ParagraphStyle(
            'Header',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,
            textColor=colors.red
        )
        
        story.append(Paragraph("AVISO DE MOROSIDAD", header_style))
        story.append(Spacer(1, 20))
        
        # Property and unit info
        info = f"""
        <b>Propiedad:</b> {unit.property.name}<br/>
        <b>Unidad:</b> {unit.unit_identifier}<br/>
        <b>Propietario:</b> {unit.owner.full_name if unit.owner else 'No asignado'}<br/>
        <b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}
        """
        story.append(Paragraph(info, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Overdue payments table
        story.append(Paragraph("<b>PAGOS VENCIDOS:</b>", self.styles['Heading3']))
        
        data = [['Concepto', 'Fecha Vencimiento', 'Días Vencido', 'Monto']]
        total_overdue = 0
        
        for payment in overdue_payments:
            days_overdue = (datetime.now().date() - payment.due_date).days
            data.append([
                payment.payment_type.replace('_', ' ').title(),
                payment.due_date.strftime('%d/%m/%Y'),
                str(days_overdue),
                f'${payment.amount:,.2f}'
            ])
            total_overdue += payment.amount
        
        data.append(['', '', 'TOTAL:', f'${total_overdue:,.2f}'])
        
        table = Table(data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (-2, -1), (-1, -1), colors.lightcoral),
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Notice text
        notice = """
        <b>IMPORTANTE:</b><br/>
        Le informamos que tiene pagos pendientes que han vencido. 
        Le solicitamos regularizar su situación a la brevedad posible 
        para evitar recargos adicionales.<br/><br/>
        
        Para más información, contacte a la administración.
        """
        story.append(Paragraph(notice, self.styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer

pdf_generator = PDFGenerator()