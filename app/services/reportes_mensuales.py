"""
Servicio para generar y enviar reportes mensuales a clientes
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from flask import current_app
from app import db
from app.models.cliente import Cliente
from app.models.orden_trabajo import OrdenTrabajo
from app.models.mantenimiento import Mantenimiento
from app.models.ticket import Ticket
from app.models.tenant import Tenant
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import tempfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import base64
from io import BytesIO


def obtener_rango_mes_anterior():
    """Obtiene el primer y último día del mes anterior"""
    hoy = datetime.now()
    primer_dia_mes_actual = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
    primer_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)
    return primer_dia_mes_anterior, ultimo_dia_mes_anterior


def obtener_rango_mes_actual():
    """Obtiene el primer día del mes actual hasta hoy (para facturación)"""
    hoy = datetime.now()
    primer_dia = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ultimo_dia = hoy.replace(hour=23, minute=59, second=59)
    return primer_dia, ultimo_dia


def obtener_actividad_cliente(cliente, fecha_inicio, fecha_fin):
    """Obtiene toda la actividad del cliente en el rango de fechas"""

    # Órdenes completadas
    ordenes = OrdenTrabajo.query.filter(
        OrdenTrabajo.cliente_id == cliente.id,
        OrdenTrabajo.estado == 'completado',
        OrdenTrabajo.fecha_fin >= fecha_inicio,
        OrdenTrabajo.fecha_fin <= fecha_fin
    ).all()

    # Mantenimientos completados
    mantenimientos = Mantenimiento.query.filter(
        Mantenimiento.cliente_id == cliente.id,
        Mantenimiento.estado == 'completado',
        Mantenimiento.fecha_fin >= fecha_inicio,
        Mantenimiento.fecha_fin <= fecha_fin
    ).all()

    # Tickets resueltos
    tickets = Ticket.query.filter(
        Ticket.cliente_id == cliente.id,
        Ticket.estado == 'resuelto',
        Ticket.fecha_resolucion >= fecha_inicio,
        Ticket.fecha_resolucion <= fecha_fin
    ).all()

    return {
        'ordenes': ordenes,
        'mantenimientos': mantenimientos,
        'tickets': tickets
    }


def obtener_imagen_firma(firma_base64, max_width=2*inch, max_height=1*inch):
    """Convierte firma base64 a imagen de ReportLab"""
    try:
        if not firma_base64:
            return None
        # Remover prefijo data:image si existe
        if ',' in firma_base64:
            firma_base64 = firma_base64.split(',')[1]
        img_data = base64.b64decode(firma_base64)
        img_buffer = BytesIO(img_data)
        img = Image(img_buffer, width=max_width, height=max_height)
        return img
    except Exception as e:
        print(f"[REPORTE] Error procesando firma: {e}")
        return None


def obtener_imagen_foto(ruta_foto, upload_folder, max_width=2*inch, max_height=1.5*inch):
    """Obtiene imagen de foto desde ruta"""
    try:
        if not ruta_foto:
            return None
        # Construir path completo
        full_path = os.path.join(upload_folder, ruta_foto)
        if not os.path.exists(full_path):
            return None
        img = Image(full_path)
        # Escalar proporcionalmente
        img_width, img_height = img.drawWidth, img.drawHeight
        ratio = min(max_width/img_width, max_height/img_height)
        img.drawWidth = img_width * ratio
        img.drawHeight = img_height * ratio
        return img
    except Exception as e:
        print(f"[REPORTE] Error procesando foto {ruta_foto}: {e}")
        return None


def generar_pdf_reporte_mensual(cliente, fecha_inicio, fecha_fin, actividad):
    """Genera el PDF del reporte mensual para un cliente - CON DETALLE COMPLETO"""

    # Obtener upload folder
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    except:
        upload_folder = 'uploads'

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(temp_file.name, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='TenantName', fontSize=16, fontName='Helvetica-Bold', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='ReportTitle', fontSize=14, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle(name='SectionTitle', fontSize=12, fontName='Helvetica-Bold', spaceBefore=15, spaceAfter=10, textColor=colors.HexColor('#2563eb')))
    styles.add(ParagraphStyle(name='SubSectionTitle', fontSize=11, fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle(name='SmallText', fontSize=9))
    styles.add(ParagraphStyle(name='DetailLabel', fontSize=9, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='DetailValue', fontSize=9))

    elements = []

    # Encabezado con nombre del tenant
    tenant_nombre = cliente.tenant.nombre if cliente.tenant else "Servicio Técnico"
    elements.append(Paragraph(tenant_nombre.upper(), styles['TenantName']))
    elements.append(Spacer(1, 10))

    # Título del reporte
    mes_nombre = fecha_inicio.strftime('%B %Y').capitalize()
    elements.append(Paragraph(f"REPORTE DE SERVICIOS REALIZADOS", styles['ReportTitle']))
    elements.append(Paragraph(f"{mes_nombre}", styles['Center']))
    elements.append(Spacer(1, 20))

    # Información del cliente
    cliente_info = [
        ['Cliente:', cliente.nombre],
        ['Período:', f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"],
        ['Fecha de emisión:', datetime.now().strftime('%d/%m/%Y %H:%M')],
    ]

    info_table = Table(cliente_info, colWidths=[1.5*inch, 4.5*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # Resumen ejecutivo
    elements.append(Paragraph("RESUMEN EJECUTIVO", styles['SectionTitle']))

    resumen_data = [
        ['Tipo de Servicio', 'Cantidad', 'Estado'],
        ['Órdenes de Trabajo', str(len(actividad['ordenes'])), 'Completadas'],
        ['Mantenimientos', str(len(actividad['mantenimientos'])), 'Completados'],
        ['Tickets de Soporte', str(len(actividad['tickets'])), 'Resueltos'],
        ['TOTAL', str(len(actividad['ordenes']) + len(actividad['mantenimientos']) + len(actividad['tickets'])), ''],
    ]

    resumen_table = Table(resumen_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(resumen_table)

    # =============================================
    # DETALLE DE ÓRDENES DE TRABAJO
    # =============================================
    if actividad['ordenes']:
        elements.append(PageBreak())
        elements.append(Paragraph("DETALLE DE ÓRDENES DE TRABAJO", styles['SectionTitle']))
        elements.append(Spacer(1, 10))

        for i, orden in enumerate(actividad['ordenes']):
            if i > 0:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("─" * 60, styles['Center']))
                elements.append(Spacer(1, 10))

            # Encabezado de la orden
            elements.append(Paragraph(f"Orden {orden.numero}", styles['SubSectionTitle']))

            # Información de la orden
            orden_info = [
                ['Tipo:', orden.tipo.replace('_', ' ').title() if orden.tipo else 'N/A'],
                ['Ubicación:', orden.ubicacion.nombre if orden.ubicacion else 'N/A'],
                ['Equipo:', orden.equipo.modelo if orden.equipo else 'N/A'],
                ['Técnico(s):', ', '.join([t.nombre for t in orden.tecnicos]) or 'N/A'],
                ['Fecha:', orden.fecha_fin.strftime('%d/%m/%Y %H:%M') if orden.fecha_fin else 'N/A'],
            ]

            info_ord_table = Table(orden_info, colWidths=[1.2*inch, 5*inch])
            info_ord_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(info_ord_table)
            elements.append(Spacer(1, 10))

            # Descripción del trabajo
            if orden.descripcion_solicitud:
                elements.append(Paragraph("Solicitud:", styles['DetailLabel']))
                elements.append(Paragraph(orden.descripcion_solicitud, styles['DetailValue']))
                elements.append(Spacer(1, 5))

            if orden.descripcion_trabajo:
                elements.append(Paragraph("Trabajo Realizado:", styles['DetailLabel']))
                elements.append(Paragraph(orden.descripcion_trabajo, styles['DetailValue']))
                elements.append(Spacer(1, 10))

            # Actividades
            actividades = orden.actividades.all()
            if actividades:
                elements.append(Paragraph("Actividades:", styles['DetailLabel']))
                act_data = [['Actividad', 'Tiempo', 'Técnico']]
                for act in actividades:
                    act_data.append([
                        act.descripcion[:40] if act.descripcion else 'N/A',
                        f"{act.tiempo_minutos} min" if act.tiempo_minutos else 'N/A',
                        act.tecnico.nombre if act.tecnico else 'N/A'
                    ])
                act_table = Table(act_data, colWidths=[3.5*inch, 1*inch, 1.5*inch])
                act_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ]))
                elements.append(act_table)
                elements.append(Spacer(1, 10))

            # Fotos
            fotos = orden.fotos.all()
            if fotos:
                elements.append(Paragraph("Fotos:", styles['DetailLabel']))
                fotos_row = []
                for foto in fotos[:4]:  # Máximo 4 fotos por orden
                    img = obtener_imagen_foto(foto.ruta, upload_folder, max_width=1.4*inch, max_height=1.2*inch)
                    if img:
                        foto_cell = [img, Paragraph(foto.tipo.title() if foto.tipo else '',
                                    ParagraphStyle(name='FotoLabel', fontSize=7, alignment=TA_CENTER))]
                        fotos_row.append(foto_cell)

                if fotos_row:
                    # Crear tabla de fotos
                    fotos_table = Table([fotos_row], colWidths=[1.5*inch] * len(fotos_row))
                    fotos_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    elements.append(fotos_table)
                    elements.append(Spacer(1, 10))

            # Firma
            if orden.firma_cliente and orden.firma_estado == 'firmado':
                elements.append(Paragraph("Firma del Cliente:", styles['DetailLabel']))
                firma_img = obtener_imagen_firma(orden.firma_cliente)
                if firma_img:
                    firma_data = [[firma_img]]
                    if orden.firma_nombre:
                        firma_data.append([Paragraph(f"Firmado por: {orden.firma_nombre}",
                                          ParagraphStyle(name='FirmaNombre', fontSize=8))])
                    if orden.firma_fecha:
                        firma_data.append([Paragraph(f"Fecha: {orden.firma_fecha.strftime('%d/%m/%Y %H:%M')}",
                                          ParagraphStyle(name='FirmaFecha', fontSize=8))])
                    firma_table = Table(firma_data, colWidths=[3*inch])
                    firma_table.setStyle(TableStyle([
                        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    elements.append(firma_table)

    # =============================================
    # DETALLE DE MANTENIMIENTOS
    # =============================================
    if actividad['mantenimientos']:
        elements.append(PageBreak())
        elements.append(Paragraph("DETALLE DE MANTENIMIENTOS", styles['SectionTitle']))
        elements.append(Spacer(1, 10))

        for i, mant in enumerate(actividad['mantenimientos']):
            if i > 0:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("─" * 60, styles['Center']))
                elements.append(Spacer(1, 10))

            # Encabezado del mantenimiento
            elements.append(Paragraph(f"Mantenimiento {mant.numero}", styles['SubSectionTitle']))

            # Información del mantenimiento
            mant_info = [
                ['Título:', mant.titulo or 'N/A'],
                ['Tipo:', mant.tipo.replace('_', ' ').title() if mant.tipo else 'N/A'],
                ['Ubicación:', mant.ubicacion.nombre if mant.ubicacion else 'N/A'],
                ['Fecha:', mant.fecha_fin.strftime('%d/%m/%Y %H:%M') if mant.fecha_fin else 'N/A'],
            ]

            info_mant_table = Table(mant_info, colWidths=[1.2*inch, 5*inch])
            info_mant_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(info_mant_table)
            elements.append(Spacer(1, 10))

            if mant.descripcion:
                elements.append(Paragraph("Descripción:", styles['DetailLabel']))
                elements.append(Paragraph(mant.descripcion, styles['DetailValue']))
                elements.append(Spacer(1, 10))

            # Equipos trabajados
            equipos_mant = mant.equipos_mantenimiento.filter_by(estado='completado').all()
            if equipos_mant:
                elements.append(Paragraph("Equipos Atendidos:", styles['DetailLabel']))
                eq_data = [['Equipo', 'Condición Inicial', 'Condición Final', 'Tiempo']]
                for eq in equipos_mant:
                    equipo_nombre = eq.equipo.modelo if eq.equipo else 'N/A'
                    eq_data.append([
                        equipo_nombre[:25],
                        (eq.condicion_inicial or 'N/A').title()[:15],
                        (eq.condicion_final or 'N/A').title()[:15],
                        f"{eq.tiempo_minutos} min" if eq.tiempo_minutos else 'N/A'
                    ])
                eq_table = Table(eq_data, colWidths=[2.2*inch, 1.3*inch, 1.3*inch, 0.8*inch])
                eq_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ]))
                elements.append(eq_table)
                elements.append(Spacer(1, 10))

                # Fotos de equipos (máximo 4 del mantenimiento)
                fotos_mant = []
                for eq in equipos_mant:
                    for foto in eq.fotos.all()[:2]:
                        fotos_mant.append(foto)
                        if len(fotos_mant) >= 4:
                            break
                    if len(fotos_mant) >= 4:
                        break

                if fotos_mant:
                    elements.append(Paragraph("Fotos:", styles['DetailLabel']))
                    fotos_row = []
                    for foto in fotos_mant:
                        img = obtener_imagen_foto(foto.ruta, upload_folder, max_width=1.4*inch, max_height=1.2*inch)
                        if img:
                            fotos_row.append(img)

                    if fotos_row:
                        fotos_table = Table([fotos_row], colWidths=[1.5*inch] * len(fotos_row))
                        fotos_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ]))
                        elements.append(fotos_table)
                        elements.append(Spacer(1, 10))

            # Notas de cierre
            if mant.notas_cierre:
                elements.append(Paragraph("Notas de Cierre:", styles['DetailLabel']))
                elements.append(Paragraph(mant.notas_cierre, styles['DetailValue']))
                elements.append(Spacer(1, 10))

            # Firma
            if mant.firma_cliente and mant.firma_estado == 'firmado':
                elements.append(Paragraph("Firma del Cliente:", styles['DetailLabel']))
                firma_img = obtener_imagen_firma(mant.firma_cliente)
                if firma_img:
                    firma_data = [[firma_img]]
                    if mant.firma_nombre:
                        firma_data.append([Paragraph(f"Firmado por: {mant.firma_nombre}",
                                          ParagraphStyle(name='FirmaNombre', fontSize=8))])
                    if mant.firma_fecha:
                        firma_data.append([Paragraph(f"Fecha: {mant.firma_fecha.strftime('%d/%m/%Y %H:%M')}",
                                          ParagraphStyle(name='FirmaFecha', fontSize=8))])
                    firma_table = Table(firma_data, colWidths=[3*inch])
                    firma_table.setStyle(TableStyle([
                        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    elements.append(firma_table)

    # =============================================
    # DETALLE DE TICKETS
    # =============================================
    if actividad['tickets']:
        elements.append(PageBreak())
        elements.append(Paragraph("DETALLE DE TICKETS DE SOPORTE", styles['SectionTitle']))
        elements.append(Spacer(1, 10))

        ticket_data = [['N°', 'Asunto', 'Prioridad', 'Creación', 'Resolución']]
        for ticket in actividad['tickets']:
            ticket_data.append([
                ticket.numero,
                (ticket.asunto or '')[:40],
                ticket.prioridad.title() if ticket.prioridad else 'N/A',
                ticket.fecha_creacion.strftime('%d/%m/%Y') if ticket.fecha_creacion else 'N/A',
                ticket.fecha_resolucion.strftime('%d/%m/%Y') if ticket.fecha_resolucion else 'N/A'
            ])

        ticket_table = Table(ticket_data, colWidths=[0.8*inch, 2.7*inch, 0.9*inch, 0.9*inch, 0.9*inch])
        ticket_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(ticket_table)

        # Detalle de cada ticket con respuesta
        for ticket in actividad['tickets']:
            if ticket.respuesta_admin:
                elements.append(Spacer(1, 15))
                elements.append(Paragraph(f"Ticket {ticket.numero} - Respuesta:", styles['DetailLabel']))
                elements.append(Paragraph(ticket.respuesta_admin, styles['DetailValue']))

    # Pie de página
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("─" * 60, styles['Center']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        f"Este reporte fue generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle(name='Footer', fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    ))
    elements.append(Paragraph(
        f"© {datetime.now().year} {tenant_nombre} - Sistema de Gestión de Servicio Técnico",
        ParagraphStyle(name='Footer2', fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    ))

    doc.build(elements)
    return temp_file.name


def enviar_email_reporte(cliente, pdf_path, fecha_inicio, fecha_fin):
    """Envía el reporte por email al cliente"""

    if not cliente.email_reportes:
        print(f"[REPORTE] Cliente {cliente.nombre} no tiene email de reportes configurado")
        return False

    try:
        # Configuración SMTP desde variables de entorno
        smtp_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('MAIL_PORT', 587))
        smtp_user = os.environ.get('MAIL_USERNAME', '')
        smtp_password = os.environ.get('MAIL_PASSWORD', '')
        smtp_from = os.environ.get('MAIL_DEFAULT_SENDER', smtp_user)

        if not smtp_user or not smtp_password:
            print("[REPORTE] ERROR: Configuración SMTP no disponible")
            return False

        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = cliente.email_reportes
        msg['Subject'] = f"Reporte Mensual de Servicios - {fecha_inicio.strftime('%B %Y').capitalize()}"

        # Cuerpo del email
        tenant_nombre = cliente.tenant.nombre if cliente.tenant else "Servicio Técnico"
        body = f"""
Estimado/a cliente,

Adjunto encontrará el reporte mensual de los servicios realizados durante el período {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}.

Este reporte incluye:
- Órdenes de trabajo completadas
- Mantenimientos realizados
- Tickets de soporte resueltos

Si tiene alguna consulta sobre este reporte, no dude en contactarnos.

Saludos cordiales,
{tenant_nombre}
        """
        msg.attach(MIMEText(body, 'plain'))

        # Adjuntar PDF
        with open(pdf_path, 'rb') as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment',
                                     filename=f'Reporte_{cliente.nombre}_{fecha_inicio.strftime("%Y%m")}.pdf')
            msg.attach(pdf_attachment)

        # Enviar
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f"[REPORTE] Email enviado a {cliente.email_reportes}")
        return True

    except Exception as e:
        print(f"[REPORTE] Error enviando email: {e}")
        return False


def procesar_reportes_tenant(tenant):
    """Procesa y envía reportes para todos los clientes de un tenant"""
    from app.services.notificaciones import notificar_cliente

    # Usar mes actual (para facturación a fin de mes)
    fecha_inicio, fecha_fin = obtener_rango_mes_actual()
    clientes_procesados = 0
    clientes_con_actividad = 0

    print(f"[REPORTE] Procesando tenant: {tenant.nombre}")
    print(f"[REPORTE] Período: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")

    # Obtener clientes activos del tenant con email de reportes
    clientes = Cliente.query.filter_by(
        tenant_id=tenant.id,
        activo=True
    ).filter(Cliente.email_reportes.isnot(None)).filter(Cliente.email_reportes != '').all()

    print(f"[REPORTE] Clientes con email de reportes: {len(clientes)}")

    for cliente in clientes:
        try:
            # Obtener actividad
            actividad = obtener_actividad_cliente(cliente, fecha_inicio, fecha_fin)

            # Solo procesar si hubo actividad
            total_actividad = len(actividad['ordenes']) + len(actividad['mantenimientos']) + len(actividad['tickets'])

            if total_actividad > 0:
                print(f"[REPORTE] Cliente {cliente.nombre}: {total_actividad} servicios")

                # Generar PDF
                pdf_path = generar_pdf_reporte_mensual(cliente, fecha_inicio, fecha_fin, actividad)

                # Enviar email
                email_enviado = enviar_email_reporte(cliente, pdf_path, fecha_inicio, fecha_fin)

                # Enviar notificación push si tiene usuarios
                if cliente.usuarios:
                    for usuario in cliente.usuarios:
                        if usuario.activo:
                            from app.services.notificaciones import enviar_notificacion_push
                            enviar_notificacion_push(
                                usuario,
                                'Reporte Mensual Disponible',
                                f'Tu reporte de servicios de {fecha_inicio.strftime("%B %Y")} está disponible.',
                                None
                            )

                # Limpiar archivo temporal
                if os.path.exists(pdf_path):
                    os.unlink(pdf_path)

                clientes_con_actividad += 1

            clientes_procesados += 1

        except Exception as e:
            print(f"[REPORTE] Error procesando cliente {cliente.nombre}: {e}")

    return {
        'clientes_procesados': clientes_procesados,
        'clientes_con_actividad': clientes_con_actividad
    }


def ejecutar_envio_reportes():
    """Función principal para ejecutar desde cron"""
    from flask import current_app

    hoy = datetime.now()
    print(f"[REPORTE] Iniciando envío de reportes - {hoy.strftime('%d/%m/%Y %H:%M')}")

    # Obtener tenants activos donde hoy es el día de envío
    tenants = Tenant.query.filter_by(activo=True).filter(
        Tenant.dia_envio_reportes == hoy.day
    ).all()

    print(f"[REPORTE] Tenants a procesar hoy (día {hoy.day}): {len(tenants)}")

    resultados = []
    for tenant in tenants:
        resultado = procesar_reportes_tenant(tenant)
        resultado['tenant'] = tenant.nombre
        resultados.append(resultado)

    print(f"[REPORTE] Proceso completado")
    return resultados
