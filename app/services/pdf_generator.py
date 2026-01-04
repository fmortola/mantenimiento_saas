from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from flask import current_app
import os
import tempfile
import base64
import io
from datetime import datetime

def generar_pdf_orden(orden):
    """Genera PDF de una orden de trabajo"""
    # Crear archivo temporal
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(temp_file.name, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Bold', fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='TenantName', fontSize=14, fontName='Helvetica-Bold', alignment=TA_CENTER))

    elements = []

    # Nombre del Tenant (empresa)
    tenant_nombre = "Servicio Tecnico"
    if orden.tenant:
        tenant_nombre = orden.tenant.nombre
    elements.append(Paragraph(tenant_nombre.upper(), styles['TenantName']))
    elements.append(Spacer(1, 10))

    # Encabezado
    elements.append(Paragraph("ORDEN DE TRABAJO", styles['Heading1']))
    elements.append(Paragraph(f"N° {orden.numero}", styles['Center']))
    elements.append(Spacer(1, 20))

    # Información general
    info_data = [
        ['Fecha de Creación:', orden.fecha_creacion.strftime('%d/%m/%Y %H:%M')],
        ['Estado:', orden.estado.upper()],
        ['Prioridad:', orden.prioridad.upper()],
        ['Tipo:', orden.tipo.replace('_', ' ').title()],
    ]

    if orden.fecha_programada:
        info_data.append(['Fecha Programada:', orden.fecha_programada.strftime('%d/%m/%Y %H:%M')])

    # Técnicos asignados (relación many-to-many)
    if orden.tecnicos.count() > 0:
        tecnicos_nombres = ', '.join([t.nombre for t in orden.tecnicos])
        info_data.append(['Técnico(s) Asignado(s):', tecnicos_nombres])

    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # Información del cliente
    elements.append(Paragraph("DATOS DEL CLIENTE", styles['Heading2']))
    elements.append(Spacer(1, 10))

    if orden.cliente:
        cliente_data = [
            ['Cliente:', orden.cliente.nombre],
            ['Teléfono:', orden.cliente.telefono_principal or 'N/A'],
        ]
        if orden.ubicacion:
            cliente_data.append(['Ubicación:', orden.ubicacion.nombre])
            cliente_data.append(['Dirección:', orden.ubicacion.direccion or 'N/A'])
    else:
        cliente_data = [
            ['Cliente:', orden.cliente_rapido_nombre or 'N/A'],
            ['Teléfono:', orden.cliente_rapido_telefono or 'N/A'],
            ['Dirección:', orden.cliente_rapido_direccion or 'N/A'],
        ]

    cliente_table = Table(cliente_data, colWidths=[2*inch, 4*inch])
    cliente_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(cliente_table)
    elements.append(Spacer(1, 20))

    # Descripción de la solicitud
    elements.append(Paragraph("DESCRIPCIÓN DE LA SOLICITUD", styles['Heading2']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(orden.descripcion_solicitud or 'Sin descripción', styles['Normal']))
    elements.append(Spacer(1, 20))

    # Actividades realizadas (nuevo sistema)
    if orden.actividades.count() > 0:
        elements.append(Paragraph("ACTIVIDADES REALIZADAS", styles['Heading2']))
        elements.append(Spacer(1, 10))

        actividad_data = [['Fecha/Hora', 'Descripcion', 'Tiempo', 'Tecnico']]
        for act in orden.actividades.all():
            actividad_data.append([
                act.fecha_hora.strftime('%d/%m %H:%M'),
                act.descripcion[:60] + '...' if len(act.descripcion) > 60 else act.descripcion,
                f'{act.tiempo_minutos} min',
                act.tecnico.nombre if act.tecnico else 'N/A'
            ])

        # Agregar fila de total
        actividad_data.append(['', 'TIEMPO TOTAL:', f'{orden.tiempo_total_actividades} min', ''])

        act_table = Table(actividad_data, colWidths=[1.2*inch, 2.8*inch, 0.8*inch, 1.2*inch])
        act_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (1, -1), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(act_table)
        elements.append(Spacer(1, 15))

        if orden.fecha_fin:
            elements.append(Paragraph(f"Fecha de finalizacion: {orden.fecha_fin.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))

    # Trabajo realizado (sistema antiguo, por compatibilidad)
    elif orden.descripcion_trabajo:
        elements.append(Paragraph("TRABAJO REALIZADO", styles['Heading2']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(orden.descripcion_trabajo, styles['Normal']))
        elements.append(Spacer(1, 10))

        if orden.tiempo_real:
            elements.append(Paragraph(f"Tiempo empleado: {orden.tiempo_real} minutos", styles['Normal']))

        if orden.fecha_fin:
            elements.append(Paragraph(f"Fecha de finalizacion: {orden.fecha_fin.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))

    elements.append(Spacer(1, 20))

    # Fotos del trabajo
    fotos = orden.fotos.all()
    if fotos:
        elements.append(Paragraph("FOTOS DEL TRABAJO", styles['Heading2']))
        elements.append(Spacer(1, 10))

        fotos_por_tipo = {'antes': [], 'durante': [], 'despues': [], 'otro': []}
        for foto in fotos:
            tipo = foto.tipo or 'otro'
            if tipo in fotos_por_tipo:
                fotos_por_tipo[tipo].append(foto)
            else:
                fotos_por_tipo['otro'].append(foto)

        for tipo, fotos_lista in fotos_por_tipo.items():
            if fotos_lista:
                tipo_label = {'antes': 'Antes', 'durante': 'Durante', 'despues': 'Después', 'otro': 'Otras'}.get(tipo, tipo)
                elements.append(Paragraph(f"<b>{tipo_label}:</b>", styles['Normal']))
                elements.append(Spacer(1, 5))

                # Crear grid de fotos (3 por fila)
                foto_row = []
                for foto in fotos_lista:
                    try:
                        foto_path = os.path.join(current_app.config['UPLOAD_FOLDER'], foto.ruta)
                        if os.path.exists(foto_path):
                            # Obtener dimensiones respetando EXIF orientation
                            from PIL import Image as PILImage
                            from PIL import ImageOps

                            with PILImage.open(foto_path) as pil_img:
                                # Aplicar rotación EXIF si existe
                                pil_img = ImageOps.exif_transpose(pil_img)
                                orig_w, orig_h = pil_img.size

                                # Guardar en memoria
                                img_buffer = io.BytesIO()
                                pil_img.save(img_buffer, 'JPEG', quality=85)
                                img_buffer.seek(0)

                            # Tamaño máximo en el PDF
                            max_w = 1.8 * inch
                            max_h = 2.2 * inch

                            # Calcular escala manteniendo proporción
                            scale = min(max_w / orig_w, max_h / orig_h)
                            new_w = orig_w * scale
                            new_h = orig_h * scale

                            img = Image(img_buffer, width=new_w, height=new_h)
                            foto_row.append(img)

                            # Si tenemos 3 fotos, crear fila y resetear
                            if len(foto_row) == 3:
                                foto_table = Table([foto_row], colWidths=[2*inch, 2*inch, 2*inch])
                                foto_table.setStyle(TableStyle([
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                                ]))
                                elements.append(foto_table)
                                foto_row = []
                    except Exception as e:
                        pass

                # Fotos restantes
                if foto_row:
                    # Rellenar con celdas vacías
                    while len(foto_row) < 3:
                        foto_row.append('')
                    foto_table = Table([foto_row], colWidths=[2*inch, 2*inch, 2*inch])
                    foto_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ]))
                    elements.append(foto_table)

                elements.append(Spacer(1, 10))

    elements.append(Spacer(1, 20))

    # Firma del cliente (digital si existe)
    if orden.firma_cliente:
        elements.append(Paragraph("FIRMA DEL CLIENTE", styles['Heading2']))
        elements.append(Spacer(1, 10))

        # Convertir base64 a imagen
        try:
            firma_base64 = orden.firma_cliente
            if ',' in firma_base64:
                firma_base64 = firma_base64.split(',')[1]
            firma_bytes = base64.b64decode(firma_base64)
            firma_buffer = io.BytesIO(firma_bytes)

            firma_img = Image(firma_buffer, width=2.5*inch, height=1*inch)
            firma_img.hAlign = 'CENTER'
            elements.append(firma_img)
        except Exception as e:
            elements.append(Paragraph("[Firma digital no disponible]", styles['Center']))

        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"Firmado por: {orden.firma_nombre or 'N/A'}", styles['Center']))
        if orden.firma_fecha:
            elements.append(Paragraph(f"Fecha: {orden.firma_fecha.strftime('%d/%m/%Y %H:%M')}", styles['Center']))
    else:
        # Firma tradicional (lineas)
        firma_data = [
            ['_________________________', '_________________________'],
            ['Firma del Cliente', 'Firma del Tecnico'],
        ]
        firma_table = Table(firma_data, colWidths=[3*inch, 3*inch])
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 30),
        ]))
        elements.append(firma_table)

    # Pie de página
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle(name='Footer', fontSize=8, alignment=TA_CENTER)
    ))

    doc.build(elements)
    return temp_file.name


def generar_pdf_mantenimiento(mantenimiento):
    """Genera PDF de un mantenimiento programado"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(temp_file.name, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='TenantName', fontSize=14, fontName='Helvetica-Bold', alignment=TA_CENTER))

    elements = []

    # Nombre del Tenant (empresa)
    tenant_nombre = "Servicio Tecnico"
    if mantenimiento.tenant:
        tenant_nombre = mantenimiento.tenant.nombre
    elements.append(Paragraph(tenant_nombre.upper(), styles['TenantName']))
    elements.append(Spacer(1, 10))

    # Encabezado
    elements.append(Paragraph("REPORTE DE MANTENIMIENTO", styles['Heading1']))
    elements.append(Paragraph(f"N° {mantenimiento.numero}", styles['Center']))
    elements.append(Spacer(1, 20))

    # Información general
    info_data = [
        ['Título:', mantenimiento.titulo],
        ['Tipo:', mantenimiento.tipo.replace('_', ' ').title()],
        ['Estado:', mantenimiento.estado.upper()],
        ['Cliente:', mantenimiento.cliente.nombre],
        ['Ubicación:', mantenimiento.ubicacion.nombre],
        ['Dirección:', mantenimiento.ubicacion.direccion or 'N/A'],
    ]

    if mantenimiento.fecha_programada:
        info_data.append(['Fecha Programada:', mantenimiento.fecha_programada.strftime('%d/%m/%Y')])
    if mantenimiento.fecha_inicio:
        info_data.append(['Fecha Inicio:', mantenimiento.fecha_inicio.strftime('%d/%m/%Y %H:%M')])
    if mantenimiento.fecha_fin:
        info_data.append(['Fecha Fin:', mantenimiento.fecha_fin.strftime('%d/%m/%Y %H:%M')])

    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # Técnicos asignados
    tecnicos = [t.nombre for t in mantenimiento.tecnicos]
    elements.append(Paragraph(f"Técnicos: {', '.join(tecnicos)}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Progreso
    total = mantenimiento.equipos_mantenimiento.count()
    completados = mantenimiento.equipos_con_mantenimiento()
    elements.append(Paragraph(f"Progreso: {completados}/{total} equipos ({mantenimiento.progreso_porcentaje()}%)", styles['Heading3']))
    elements.append(Spacer(1, 20))

    # Tabla de equipos
    elements.append(Paragraph("DETALLE DE EQUIPOS", styles['Heading2']))
    elements.append(Spacer(1, 10))

    equipo_data = [['Equipo', 'Tipo', 'Estado', 'Trabajo Realizado']]

    for me in mantenimiento.equipos_mantenimiento:
        equipo = me.equipo
        equipo_data.append([
            equipo.nombre or f'{equipo.marca} {equipo.modelo}',
            equipo.tipo,
            me.estado.upper(),
            (me.descripcion_trabajo or '')[:50] + '...' if me.descripcion_trabajo and len(me.descripcion_trabajo) > 50 else (me.descripcion_trabajo or 'N/A')
        ])

    equipo_table = Table(equipo_data, colWidths=[1.5*inch, 1*inch, 1*inch, 2.5*inch])
    equipo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(equipo_table)
    elements.append(Spacer(1, 20))

    # Notas de cierre
    if mantenimiento.notas_cierre:
        elements.append(Paragraph("NOTAS DE CIERRE", styles['Heading2']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(mantenimiento.notas_cierre, styles['Normal']))
        elements.append(Spacer(1, 20))

    # Firmas
    firma_data = [
        ['_________________________', '_________________________'],
        ['Firma del Cliente', 'Firma del Responsable'],
    ]
    firma_table = Table(firma_data, colWidths=[3*inch, 3*inch])
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 30),
    ]))
    elements.append(firma_table)

    # Pie de página
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle(name='Footer', fontSize=8, alignment=TA_CENTER)
    ))

    doc.build(elements)
    return temp_file.name
