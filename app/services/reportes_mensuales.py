"""
Servicio para generar y enviar reportes mensuales a clientes
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
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


def obtener_rango_mes_anterior():
    """Obtiene el primer y último día del mes anterior"""
    hoy = datetime.now()
    primer_dia_mes_actual = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
    primer_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)
    return primer_dia_mes_anterior, ultimo_dia_mes_anterior


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
        Ticket.fecha_cierre >= fecha_inicio,
        Ticket.fecha_cierre <= fecha_fin
    ).all()

    return {
        'ordenes': ordenes,
        'mantenimientos': mantenimientos,
        'tickets': tickets
    }


def generar_pdf_reporte_mensual(cliente, fecha_inicio, fecha_fin, actividad):
    """Genera el PDF del reporte mensual para un cliente"""

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(temp_file.name, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='TenantName', fontSize=16, fontName='Helvetica-Bold', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='ReportTitle', fontSize=14, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle(name='SectionTitle', fontSize=12, fontName='Helvetica-Bold', spaceBefore=15, spaceAfter=10))
    styles.add(ParagraphStyle(name='SmallText', fontSize=9))

    elements = []

    # Encabezado con nombre del tenant
    tenant_nombre = cliente.tenant.nombre if cliente.tenant else "Servicio Técnico"
    elements.append(Paragraph(tenant_nombre.upper(), styles['TenantName']))
    elements.append(Spacer(1, 10))

    # Título del reporte
    mes_nombre = fecha_inicio.strftime('%B %Y').capitalize()
    elements.append(Paragraph(f"REPORTE MENSUAL DE SERVICIOS", styles['ReportTitle']))
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
    elements.append(Spacer(1, 30))

    # Detalle de órdenes de trabajo
    if actividad['ordenes']:
        elements.append(Paragraph("ÓRDENES DE TRABAJO COMPLETADAS", styles['SectionTitle']))

        orden_data = [['N°', 'Tipo', 'Descripción', 'Técnico', 'Fecha']]
        for orden in actividad['ordenes']:
            tecnicos = ', '.join([t.nombre for t in orden.tecnicos][:2])
            if orden.tecnicos.count() > 2:
                tecnicos += '...'
            descripcion = (orden.descripcion_solicitud or '')[:40]
            if len(orden.descripcion_solicitud or '') > 40:
                descripcion += '...'
            orden_data.append([
                orden.numero,
                orden.tipo.replace('_', ' ').title()[:15],
                descripcion,
                tecnicos[:20],
                orden.fecha_fin.strftime('%d/%m') if orden.fecha_fin else 'N/A'
            ])

        orden_table = Table(orden_data, colWidths=[0.8*inch, 1.2*inch, 2.2*inch, 1.3*inch, 0.7*inch])
        orden_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (4, 0), (4, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(orden_table)
        elements.append(Spacer(1, 20))

    # Detalle de mantenimientos
    if actividad['mantenimientos']:
        elements.append(Paragraph("MANTENIMIENTOS REALIZADOS", styles['SectionTitle']))

        mant_data = [['N°', 'Ubicación', 'Tipo', 'Equipos', 'Fecha']]
        for mant in actividad['mantenimientos']:
            equipos_count = mant.equipos_mantenimiento.count()
            mant_data.append([
                mant.numero,
                mant.ubicacion.nombre[:20] if mant.ubicacion else 'N/A',
                mant.tipo.replace('_', ' ').title()[:15],
                str(equipos_count),
                mant.fecha_fin.strftime('%d/%m') if mant.fecha_fin else 'N/A'
            ])

        mant_table = Table(mant_data, colWidths=[0.8*inch, 2*inch, 1.5*inch, 0.8*inch, 0.7*inch])
        mant_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (4, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(mant_table)
        elements.append(Spacer(1, 20))

    # Detalle de tickets
    if actividad['tickets']:
        elements.append(Paragraph("TICKETS DE SOPORTE RESUELTOS", styles['SectionTitle']))

        ticket_data = [['N°', 'Asunto', 'Prioridad', 'Fecha Apertura', 'Fecha Cierre']]
        for ticket in actividad['tickets']:
            asunto = (ticket.asunto or '')[:35]
            if len(ticket.asunto or '') > 35:
                asunto += '...'
            ticket_data.append([
                ticket.numero,
                asunto,
                ticket.prioridad.title(),
                ticket.fecha_creacion.strftime('%d/%m') if ticket.fecha_creacion else 'N/A',
                ticket.fecha_cierre.strftime('%d/%m') if ticket.fecha_cierre else 'N/A'
            ])

        ticket_table = Table(ticket_data, colWidths=[0.7*inch, 2.5*inch, 1*inch, 1*inch, 1*inch])
        ticket_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(ticket_table)

    # Pie de página
    elements.append(Spacer(1, 40))
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
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER', '')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        smtp_from = os.environ.get('SMTP_FROM', smtp_user)

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

    fecha_inicio, fecha_fin = obtener_rango_mes_anterior()
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
