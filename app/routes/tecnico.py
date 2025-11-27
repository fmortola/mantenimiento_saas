from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.ubicacion import Ubicacion
from app.models.equipo import Equipo, TIPOS_EQUIPO, CONDICIONES_EQUIPO
from app.models.orden_trabajo import OrdenTrabajo, FotoTrabajo
from app.models.ticket import Ticket
from app.models.mantenimiento import Mantenimiento, MantenimientoEquipo
from app.models.notificacion import Notificacion
from app.services.notificaciones import enviar_notificacion_push, notificar_admins
from datetime import datetime
import os
import uuid

tecnico_bp = Blueprint('tecnico', __name__)

def tecnico_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_tecnico():
            flash('Acceso denegado. Se requieren permisos de técnico.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== DASHBOARD ====================
@tecnico_bp.route('/dashboard')
@login_required
@tecnico_required
def dashboard():
    # Estadísticas del técnico
    stats = {
        'ordenes_pendientes': current_user.ordenes_asignadas.filter(
            OrdenTrabajo.estado.in_(['asignado', 'en_progreso'])).count(),
        'tickets_asignados': current_user.tickets_asignados.filter(
            Ticket.estado.in_(['asignado', 'en_progreso'])).count(),
        'mantenimientos_activos': current_user.mantenimientos_asignados.filter(
            Mantenimiento.estado.in_(['programado', 'en_progreso'])).count(),
        'trabajos_hoy': current_user.ordenes_asignadas.filter(
            OrdenTrabajo.fecha_programada >= datetime.utcnow().replace(hour=0, minute=0, second=0)).count()
    }

    # Órdenes asignadas
    ordenes = current_user.ordenes_asignadas.filter(
        OrdenTrabajo.estado.in_(['asignado', 'en_progreso'])
    ).order_by(OrdenTrabajo.fecha_programada).all()

    # Tickets asignados
    tickets = current_user.tickets_asignados.filter(
        Ticket.estado.in_(['asignado', 'en_progreso'])
    ).order_by(Ticket.fecha_creacion.desc()).all()

    # Mantenimientos asignados
    mantenimientos = current_user.mantenimientos_asignados.filter(
        Mantenimiento.estado.in_(['programado', 'en_progreso'])
    ).all()

    return render_template('tecnico/dashboard.html',
                           stats=stats,
                           ordenes=ordenes,
                           tickets=tickets,
                           mantenimientos=mantenimientos)

# ==================== ÓRDENES DE TRABAJO ====================
@tecnico_bp.route('/ordenes')
@login_required
@tecnico_required
def ordenes():
    estado = request.args.get('estado', 'activas')
    if estado == 'activas':
        ordenes = current_user.ordenes_asignadas.filter(
            OrdenTrabajo.estado.in_(['asignado', 'en_progreso'])
        ).order_by(OrdenTrabajo.fecha_programada).all()
    elif estado == 'completadas':
        ordenes = current_user.ordenes_asignadas.filter(
            OrdenTrabajo.estado == 'completado'
        ).order_by(OrdenTrabajo.fecha_fin.desc()).all()
    else:
        ordenes = current_user.ordenes_asignadas.order_by(
            OrdenTrabajo.fecha_creacion.desc()).all()

    return render_template('tecnico/ordenes/lista.html', ordenes=ordenes, estado_filtro=estado)

@tecnico_bp.route('/ordenes/<int:id>')
@login_required
@tecnico_required
def orden_ver(id):
    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        flash('No tienes acceso a esta orden.', 'danger')
        return redirect(url_for('tecnico.ordenes'))

    return render_template('tecnico/ordenes/ver.html', orden=orden)

@tecnico_bp.route('/ordenes/<int:id>/iniciar', methods=['POST'])
@login_required
@tecnico_required
def orden_iniciar(id):
    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        flash('No tienes acceso a esta orden.', 'danger')
        return redirect(url_for('tecnico.ordenes'))

    orden.estado = 'en_progreso'
    orden.fecha_inicio = datetime.utcnow()
    db.session.commit()
    flash('Has iniciado el trabajo en esta orden.', 'success')
    return redirect(url_for('tecnico.orden_ver', id=id))

@tecnico_bp.route('/ordenes/<int:id>/actualizar', methods=['POST'])
@login_required
@tecnico_required
def orden_actualizar(id):
    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        flash('No tienes acceso a esta orden.', 'danger')
        return redirect(url_for('tecnico.ordenes'))

    orden.descripcion_trabajo = request.form.get('descripcion_trabajo')
    orden.tiempo_real = request.form.get('tiempo_real', type=int)
    db.session.commit()
    flash('Orden actualizada.', 'success')
    return redirect(url_for('tecnico.orden_ver', id=id))

@tecnico_bp.route('/ordenes/<int:id>/completar', methods=['POST'])
@login_required
@tecnico_required
def orden_completar(id):
    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        flash('No tienes acceso a esta orden.', 'danger')
        return redirect(url_for('tecnico.ordenes'))

    orden.descripcion_trabajo = request.form.get('descripcion_trabajo')
    orden.tiempo_real = request.form.get('tiempo_real', type=int)
    orden.estado = 'completado'
    orden.fecha_fin = datetime.utcnow()
    db.session.commit()

    # Notificar a administradores
    notificar_admins(
        'Orden Completada',
        f'El técnico {current_user.nombre} ha completado la orden {orden.numero}',
        url_for('admin.orden_ver', id=orden.id)
    )

    flash('Orden completada exitosamente.', 'success')
    return redirect(url_for('tecnico.ordenes'))

# ==================== TICKETS ====================
@tecnico_bp.route('/tickets')
@login_required
@tecnico_required
def tickets():
    estado = request.args.get('estado', 'activos')
    if estado == 'activos':
        tickets = current_user.tickets_asignados.filter(
            Ticket.estado.in_(['asignado', 'en_progreso'])
        ).order_by(Ticket.fecha_creacion.desc()).all()
    else:
        tickets = current_user.tickets_asignados.order_by(
            Ticket.fecha_creacion.desc()).all()

    return render_template('tecnico/tickets/lista.html', tickets=tickets, estado_filtro=estado)

@tecnico_bp.route('/tickets/<int:id>')
@login_required
@tecnico_required
def ticket_ver(id):
    ticket = Ticket.query.get_or_404(id)
    if current_user not in ticket.tecnicos.all():
        flash('No tienes acceso a este ticket.', 'danger')
        return redirect(url_for('tecnico.tickets'))

    return render_template('tecnico/tickets/ver.html', ticket=ticket)

@tecnico_bp.route('/tickets/<int:id>/resolver', methods=['POST'])
@login_required
@tecnico_required
def ticket_resolver(id):
    ticket = Ticket.query.get_or_404(id)
    if current_user not in ticket.tecnicos.all():
        flash('No tienes acceso a este ticket.', 'danger')
        return redirect(url_for('tecnico.tickets'))

    ticket.estado = 'resuelto'
    ticket.fecha_resolucion = datetime.utcnow()
    ticket.respuesta_admin = request.form.get('respuesta')
    db.session.commit()

    # Notificar a administradores
    notificar_admins(
        'Ticket Resuelto',
        f'El técnico {current_user.nombre} ha resuelto el ticket {ticket.numero}',
        url_for('admin.ticket_ver', id=ticket.id)
    )

    flash('Ticket resuelto.', 'success')
    return redirect(url_for('tecnico.tickets'))

# ==================== MANTENIMIENTOS ====================
@tecnico_bp.route('/mantenimientos')
@login_required
@tecnico_required
def mantenimientos():
    estado = request.args.get('estado', 'activos')
    if estado == 'activos':
        mantenimientos = current_user.mantenimientos_asignados.filter(
            Mantenimiento.estado.in_(['programado', 'en_progreso'])
        ).all()
    else:
        mantenimientos = current_user.mantenimientos_asignados.all()

    return render_template('tecnico/mantenimientos/lista.html', mantenimientos=mantenimientos, estado_filtro=estado)

@tecnico_bp.route('/mantenimientos/<int:id>')
@login_required
@tecnico_required
def mantenimiento_ver(id):
    mantenimiento = Mantenimiento.query.get_or_404(id)
    if current_user not in mantenimiento.tecnicos:
        flash('No tienes acceso a este mantenimiento.', 'danger')
        return redirect(url_for('tecnico.mantenimientos'))

    # Equipos de la ubicación
    equipos_ubicacion = Equipo.query.filter_by(ubicacion_id=mantenimiento.ubicacion_id, activo=True).all()

    # Equipos ya en el mantenimiento
    equipos_mantenimiento = {me.equipo_id: me for me in mantenimiento.equipos_mantenimiento}

    return render_template('tecnico/mantenimientos/ver.html',
                           mantenimiento=mantenimiento,
                           equipos_ubicacion=equipos_ubicacion,
                           equipos_mantenimiento=equipos_mantenimiento,
                           tipos_equipo=TIPOS_EQUIPO,
                           condiciones=CONDICIONES_EQUIPO)

@tecnico_bp.route('/mantenimientos/<int:id>/agregar-equipo', methods=['POST'])
@login_required
@tecnico_required
def mantenimiento_agregar_equipo(id):
    """El técnico agrega un equipo nuevo durante el levantamiento de inventario"""
    mantenimiento = Mantenimiento.query.get_or_404(id)
    if current_user not in mantenimiento.tecnicos:
        return jsonify({'error': 'Sin acceso'}), 403

    # Crear el equipo
    equipo = Equipo(
        tipo=request.form.get('tipo'),
        nombre=request.form.get('nombre'),
        marca=request.form.get('marca'),
        modelo=request.form.get('modelo'),
        serial=request.form.get('serial'),
        departamento=request.form.get('departamento'),
        condicion=request.form.get('condicion'),
        descripcion=request.form.get('descripcion'),
        ubicacion_id=mantenimiento.ubicacion_id,
        creado_por_id=current_user.id
    )

    # Guardar foto si se proporciona (base64 o archivo)
    foto_data = request.form.get('foto_data')
    if foto_data:
        # Foto viene como base64
        import base64
        if ',' in foto_data:
            foto_data = foto_data.split(',')[1]
        imagen_bytes = base64.b64decode(foto_data)
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as f:
            f.write(imagen_bytes)
        equipo.foto = filename
    elif 'foto' in request.files:
        foto = request.files['foto']
        if foto.filename:
            filename = f"{uuid.uuid4().hex}.jpg"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            foto.save(filepath)
            equipo.foto = filename

    db.session.add(equipo)
    db.session.flush()

    # Agregar al mantenimiento
    mant_equipo = MantenimientoEquipo(
        mantenimiento_id=mantenimiento.id,
        equipo_id=equipo.id,
        estado='pendiente',
        condicion_inicial=equipo.condicion
    )
    db.session.add(mant_equipo)
    db.session.commit()

    # Notificar a administradores
    notificar_admins(
        'Nuevo Equipo Registrado',
        f'El técnico {current_user.nombre} ha registrado un nuevo equipo: {equipo.tipo} - {equipo.nombre}',
        url_for('admin.mantenimiento_ver', id=mantenimiento.id)
    )

    flash('Equipo registrado y agregado al mantenimiento.', 'success')
    return redirect(url_for('tecnico.mantenimiento_ver', id=id))

@tecnico_bp.route('/mantenimientos/<int:mant_id>/equipo/<int:equipo_id>/iniciar', methods=['POST'])
@login_required
@tecnico_required
def mantenimiento_equipo_iniciar(mant_id, equipo_id):
    """Iniciar mantenimiento de un equipo específico"""
    mantenimiento = Mantenimiento.query.get_or_404(mant_id)
    if current_user not in mantenimiento.tecnicos:
        return jsonify({'error': 'Sin acceso'}), 403

    mant_equipo = MantenimientoEquipo.query.filter_by(
        mantenimiento_id=mant_id,
        equipo_id=equipo_id
    ).first()

    if not mant_equipo:
        # Si el equipo no está en el mantenimiento, agregarlo
        mant_equipo = MantenimientoEquipo(
            mantenimiento_id=mant_id,
            equipo_id=equipo_id,
            estado='en_progreso',
            tecnico_id=current_user.id,
            fecha_inicio=datetime.utcnow()
        )
        db.session.add(mant_equipo)
    else:
        mant_equipo.estado = 'en_progreso'
        mant_equipo.tecnico_id = current_user.id
        mant_equipo.fecha_inicio = datetime.utcnow()

    # Actualizar estado del mantenimiento general si está programado
    if mantenimiento.estado == 'programado':
        mantenimiento.estado = 'en_progreso'
        mantenimiento.fecha_inicio = datetime.utcnow()

    db.session.commit()
    flash('Has iniciado el mantenimiento de este equipo.', 'success')
    return redirect(url_for('tecnico.mantenimiento_ver', id=mant_id))

@tecnico_bp.route('/mantenimientos/<int:mant_id>/equipo/<int:equipo_id>/completar', methods=['POST'])
@login_required
@tecnico_required
def mantenimiento_equipo_completar(mant_id, equipo_id):
    """Completar mantenimiento de un equipo específico"""
    mantenimiento = Mantenimiento.query.get_or_404(mant_id)
    if current_user not in mantenimiento.tecnicos:
        return jsonify({'error': 'Sin acceso'}), 403

    mant_equipo = MantenimientoEquipo.query.filter_by(
        mantenimiento_id=mant_id,
        equipo_id=equipo_id
    ).first_or_404()

    mant_equipo.estado = 'completado'
    mant_equipo.descripcion_trabajo = request.form.get('descripcion_trabajo')
    mant_equipo.condicion_final = request.form.get('condicion_final')
    mant_equipo.observaciones = request.form.get('observaciones')
    mant_equipo.tiempo_minutos = request.form.get('tiempo_minutos', type=int)
    mant_equipo.fecha_fin = datetime.utcnow()

    # Actualizar condición del equipo
    equipo = Equipo.query.get(equipo_id)
    equipo.condicion = mant_equipo.condicion_final

    # Guardar foto si se proporciona (base64 o archivo)
    foto_data = request.form.get('foto_data')
    if foto_data:
        # Foto viene como base64
        import base64
        if ',' in foto_data:
            foto_data = foto_data.split(',')[1]
        imagen_bytes = base64.b64decode(foto_data)
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as f:
            f.write(imagen_bytes)

        foto_trabajo = FotoTrabajo(
            ruta=filename,
            descripcion=f'Mantenimiento {mantenimiento.numero}',
            tipo='despues',
            mantenimiento_equipo_id=mant_equipo.id
        )
        db.session.add(foto_trabajo)
    elif 'foto' in request.files:
        foto = request.files['foto']
        if foto.filename:
            filename = f"{uuid.uuid4().hex}.jpg"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            foto.save(filepath)

            foto_trabajo = FotoTrabajo(
                ruta=filename,
                descripcion=f'Mantenimiento {mantenimiento.numero}',
                tipo='despues',
                mantenimiento_equipo_id=mant_equipo.id
            )
            db.session.add(foto_trabajo)

    db.session.commit()
    flash('Mantenimiento del equipo completado.', 'success')
    return redirect(url_for('tecnico.mantenimiento_ver', id=mant_id))

# ==================== FOTOS ====================
@tecnico_bp.route('/ordenes/<int:id>/foto', methods=['POST'])
@login_required
@tecnico_required
def orden_subir_foto(id):
    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        return jsonify({'error': 'Sin acceso'}), 403

    if 'foto' not in request.files:
        return jsonify({'error': 'No se recibió ninguna foto'}), 400

    foto = request.files['foto']
    if foto.filename == '':
        return jsonify({'error': 'No se seleccionó ninguna foto'}), 400

    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    foto.save(filepath)

    foto_trabajo = FotoTrabajo(
        ruta=filename,
        descripcion=request.form.get('descripcion', ''),
        tipo=request.form.get('tipo', 'durante'),
        orden_trabajo_id=orden.id
    )
    db.session.add(foto_trabajo)
    db.session.commit()

    return jsonify({'success': True, 'filename': filename})

# ==================== NOTIFICACIONES ====================
@tecnico_bp.route('/notificaciones')
@login_required
@tecnico_required
def notificaciones():
    notificaciones = Notificacion.query.filter_by(usuario_id=current_user.id).order_by(
        Notificacion.fecha_creacion.desc()).limit(50).all()
    return render_template('tecnico/notificaciones.html', notificaciones=notificaciones)

@tecnico_bp.route('/notificaciones/<int:id>/leer', methods=['POST'])
@login_required
@tecnico_required
def notificacion_leer(id):
    notificacion = Notificacion.query.get_or_404(id)
    if notificacion.usuario_id != current_user.id:
        return jsonify({'error': 'Sin acceso'}), 403

    notificacion.leida = True
    notificacion.fecha_lectura = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})
