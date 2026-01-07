from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.ubicacion import Ubicacion
from app.models.equipo import Equipo, TIPOS_EQUIPO, CONDICIONES_EQUIPO
from app.models.tipo_equipo import TipoEquipo
from app.models.orden_trabajo import OrdenTrabajo, FotoTrabajo
from app.models.orden_actividad import OrdenActividad
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

    # Tipos de equipo para crear nuevo
    tipos_equipo = TipoEquipo.query.filter_by(
        tenant_id=current_user.tenant_id,
        activo=True
    ).order_by(TipoEquipo.orden).all()

    # Equipos de la ubicacion (si tiene)
    equipos_ubicacion = []
    if orden.ubicacion_id:
        equipos_ubicacion = Equipo.query.filter_by(
            ubicacion_id=orden.ubicacion_id,
            tenant_id=current_user.tenant_id
        ).order_by(Equipo.nombre).all()

    return render_template('tecnico/ordenes/ver.html',
                           orden=orden,
                           tipos_equipo=tipos_equipo,
                           equipos_ubicacion=equipos_ubicacion)

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

@tecnico_bp.route('/ordenes/<int:id>/actividad', methods=['POST'])
@login_required
@tecnico_required
def orden_agregar_actividad(id):
    """Agrega una actividad/trabajo realizado a la orden"""
    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        flash('No tienes acceso a esta orden.', 'danger')
        return redirect(url_for('tecnico.ordenes'))

    descripcion = request.form.get('descripcion')
    tiempo = request.form.get('tiempo_minutos', type=int)

    if not descripcion or not tiempo:
        flash('Debes indicar la descripcion y el tiempo.', 'warning')
        return redirect(url_for('tecnico.orden_ver', id=id))

    actividad = OrdenActividad(
        orden_id=orden.id,
        tecnico_id=current_user.id,
        descripcion=descripcion,
        tiempo_minutos=tiempo,
        fecha_hora=datetime.utcnow()
    )
    db.session.add(actividad)

    # Actualizar tiempo_real de la orden con el total
    orden.tiempo_real = orden.tiempo_total_actividades + tiempo

    db.session.commit()
    flash(f'Actividad registrada: {tiempo} minutos.', 'success')
    return redirect(url_for('tecnico.orden_ver', id=id))

@tecnico_bp.route('/ordenes/<int:id>/actividad/<int:act_id>/eliminar', methods=['POST'])
@login_required
@tecnico_required
def orden_eliminar_actividad(id, act_id):
    """Elimina una actividad de la orden"""
    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        flash('No tienes acceso a esta orden.', 'danger')
        return redirect(url_for('tecnico.ordenes'))

    actividad = OrdenActividad.query.get_or_404(act_id)
    if actividad.orden_id != orden.id:
        flash('Actividad no pertenece a esta orden.', 'danger')
        return redirect(url_for('tecnico.orden_ver', id=id))

    db.session.delete(actividad)

    # Actualizar tiempo_real de la orden
    orden.tiempo_real = orden.tiempo_total_actividades

    db.session.commit()
    flash('Actividad eliminada.', 'success')
    return redirect(url_for('tecnico.orden_ver', id=id))

@tecnico_bp.route('/ordenes/<int:id>/equipo', methods=['POST'])
@login_required
@tecnico_required
def orden_asociar_equipo(id):
    """Asocia un equipo existente a la orden"""
    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        flash('No tienes acceso a esta orden.', 'danger')
        return redirect(url_for('tecnico.ordenes'))

    equipo_id = request.form.get('equipo_id', type=int)

    if equipo_id:
        # Verificar que el equipo existe y pertenece al tenant
        equipo = Equipo.query.filter_by(id=equipo_id, tenant_id=current_user.tenant_id).first()
        if equipo:
            orden.equipo_id = equipo_id
            db.session.commit()
            flash(f'Equipo "{equipo.nombre or equipo.tipo}" asociado a la orden.', 'success')
        else:
            flash('Equipo no encontrado.', 'danger')
    else:
        # Quitar equipo asociado
        orden.equipo_id = None
        db.session.commit()
        flash('Equipo desasociado de la orden.', 'info')

    return redirect(url_for('tecnico.orden_ver', id=id))

@tecnico_bp.route('/ordenes/<int:id>/equipo/nuevo', methods=['POST'])
@login_required
@tecnico_required
def orden_crear_equipo(id):
    """Crea un nuevo equipo y lo asocia a la orden"""
    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        flash('No tienes acceso a esta orden.', 'danger')
        return redirect(url_for('tecnico.ordenes'))

    if not orden.ubicacion_id:
        flash('La orden no tiene una ubicacion asignada. No se puede crear equipo.', 'warning')
        return redirect(url_for('tecnico.orden_ver', id=id))

    tipo_equipo_id = request.form.get('tipo_equipo_id', type=int)
    nombre = request.form.get('nombre', '').strip()
    marca = request.form.get('marca', '').strip()
    modelo = request.form.get('modelo', '').strip()

    if not tipo_equipo_id:
        flash('Debes seleccionar un tipo de equipo.', 'warning')
        return redirect(url_for('tecnico.orden_ver', id=id))

    # Crear el nuevo equipo
    equipo = Equipo(
        tipo_equipo_id=tipo_equipo_id,
        nombre=nombre or None,
        marca=marca or None,
        modelo=modelo or None,
        ubicacion_id=orden.ubicacion_id,
        creado_por_id=current_user.id,
        tenant_id=current_user.tenant_id,
        condicion='regular'
    )
    db.session.add(equipo)
    db.session.flush()  # Para obtener el ID

    # Asociar a la orden
    orden.equipo_id = equipo.id
    db.session.commit()

    flash(f'Equipo "{nombre or equipo.tipo}" creado y asociado a la orden.', 'success')
    return redirect(url_for('tecnico.orden_ver', id=id))

@tecnico_bp.route('/api/ubicacion/<int:ubicacion_id>/equipos')
@login_required
@tecnico_required
def api_equipos_ubicacion(ubicacion_id):
    """API para obtener equipos de una ubicacion"""
    ubicacion = Ubicacion.query.filter_by(
        id=ubicacion_id,
        tenant_id=current_user.tenant_id
    ).first()

    if not ubicacion:
        return jsonify([])

    equipos = Equipo.query.filter_by(
        ubicacion_id=ubicacion_id,
        tenant_id=current_user.tenant_id
    ).order_by(Equipo.nombre).all()

    return jsonify([{
        'id': e.id,
        'nombre': e.nombre or '',
        'tipo': e.tipo,
        'marca': e.marca or '',
        'modelo': e.modelo or ''
    } for e in equipos])

@tecnico_bp.route('/equipos/<int:id>/historial')
@login_required
@tecnico_required
def equipo_historial(id):
    """Ver historial de un equipo"""
    equipo = Equipo.query.filter_by(
        id=id,
        tenant_id=current_user.tenant_id
    ).first_or_404()

    # Ordenes de trabajo del equipo
    ordenes = OrdenTrabajo.query.filter_by(
        equipo_id=equipo.id,
        tenant_id=current_user.tenant_id
    ).order_by(OrdenTrabajo.fecha_creacion.desc()).all()

    # Tickets del equipo
    tickets = Ticket.query.filter_by(
        equipo_id=equipo.id,
        tenant_id=current_user.tenant_id
    ).order_by(Ticket.fecha_creacion.desc()).all()

    # Mantenimientos del equipo
    mantenimientos = MantenimientoEquipo.query.filter_by(
        equipo_id=equipo.id
    ).order_by(MantenimientoEquipo.fecha_inicio.desc()).all()

    return render_template('tecnico/equipos/historial.html',
                           equipo=equipo,
                           ordenes=ordenes,
                           tickets=tickets,
                           mantenimientos=mantenimientos)

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

    # Notificar a administradores del mismo tenant
    notificar_admins(
        'Orden Completada',
        f'El técnico {current_user.nombre} ha completado la orden {orden.numero}',
        url_for('admin.orden_ver', id=orden.id),
        tenant_id=current_user.tenant_id
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

    # Notificar a administradores del mismo tenant
    notificar_admins(
        'Ticket Resuelto',
        f'El técnico {current_user.nombre} ha resuelto el ticket {ticket.numero}',
        url_for('admin.ticket_ver', id=ticket.id),
        tenant_id=current_user.tenant_id
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

    # Verificar limite del plan
    tenant = current_user.tenant
    if tenant and not tenant.puede_agregar_equipo():
        flash(f'Se ha alcanzado el limite de equipos del plan ({tenant.plan.max_equipos}).', 'warning')
        return redirect(url_for('tecnico.mantenimiento_ver', id=id))

    # Crear el equipo con tenant_id del técnico
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
        creado_por_id=current_user.id,
        tenant_id=current_user.tenant_id
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

    # Notificar a administradores del mismo tenant
    notificar_admins(
        'Nuevo Equipo Registrado',
        f'El técnico {current_user.nombre} ha registrado un nuevo equipo: {equipo.tipo} - {equipo.nombre}',
        url_for('admin.mantenimiento_ver', id=mantenimiento.id),
        tenant_id=current_user.tenant_id
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


@tecnico_bp.route('/mantenimientos/<int:id>/firma')
@login_required
@tecnico_required
def mantenimiento_firma(id):
    """Página para completar mantenimiento con opciones de firma"""
    mantenimiento = Mantenimiento.query.get_or_404(id)
    if current_user not in mantenimiento.tecnicos:
        flash('No tienes acceso a este mantenimiento.', 'danger')
        return redirect(url_for('tecnico.mantenimientos'))

    # Contar equipos
    total_equipos = mantenimiento.equipos_mantenimiento.count()
    equipos_completados = sum(1 for me in mantenimiento.equipos_mantenimiento if me.estado == 'completado')

    return render_template('tecnico/mantenimientos/firma.html',
                           mantenimiento=mantenimiento,
                           total_equipos=total_equipos,
                           equipos_completados=equipos_completados)


@tecnico_bp.route('/mantenimientos/<int:id>/completar-flexible', methods=['POST'])
@login_required
@tecnico_required
def mantenimiento_completar_flexible(id):
    """Completa el mantenimiento con opciones: firma presencial, remota o sin firma"""
    import secrets
    from app.services.notificaciones import notificar_cliente

    mantenimiento = Mantenimiento.query.get_or_404(id)
    if current_user not in mantenimiento.tecnicos:
        return jsonify({'error': 'No tienes acceso a este mantenimiento'}), 403

    data = request.get_json()
    opcion = data.get('opcion')
    observaciones = data.get('observaciones')

    if not opcion:
        return jsonify({'error': 'Seleccione una opcion'}), 400

    # Guardar observaciones
    if observaciones:
        mantenimiento.observaciones = observaciones

    mantenimiento.fecha_fin = datetime.utcnow()

    if opcion == 'presencial':
        # Firma presencial
        firma_data = data.get('firma_data')
        firma_nombre = data.get('firma_nombre')

        if not firma_data or not firma_nombre:
            return jsonify({'error': 'Falta la firma del responsable'}), 400

        mantenimiento.firma_cliente = firma_data
        mantenimiento.firma_nombre = firma_nombre
        mantenimiento.firma_fecha = datetime.utcnow()
        mantenimiento.firma_estado = 'firmado'
        mantenimiento.estado = 'completado'

        mensaje_flash = 'Mantenimiento completado con firma.'
        titulo_notif = 'Mantenimiento Completado con Firma'

    elif opcion == 'remota':
        # Firma remota - generar token y enviar notificacion
        # Generar token unico
        mantenimiento.firma_token = secrets.token_urlsafe(32)
        mantenimiento.firma_estado = 'pendiente'
        mantenimiento.estado = 'pendiente_firma'

        db.session.commit()

        # URL para firmar
        firma_url = url_for('firma_publica.firmar_mantenimiento', token=mantenimiento.firma_token, _external=True)

        # Notificar al cliente
        notificar_cliente(
            mantenimiento.cliente,
            'Firma Requerida',
            f'El mantenimiento {mantenimiento.numero} ha sido completado. Por favor firme para confirmar.',
            firma_url
        )

        # Notificar admin
        notificar_admins(
            'Mantenimiento Pendiente de Firma',
            f'El tecnico {current_user.nombre} ha solicitado firma remota para el mantenimiento {mantenimiento.numero}',
            url_for('admin.mantenimiento_ver', id=mantenimiento.id),
            tenant_id=current_user.tenant_id
        )

        flash('Se ha enviado solicitud de firma al cliente.', 'info')
        return jsonify({'success': True, 'message': 'Solicitud de firma enviada'})

    else:
        # Sin firma
        mantenimiento.firma_estado = 'sin_firma'
        mantenimiento.estado = 'completado'

        mensaje_flash = 'Mantenimiento completado sin firma.'
        titulo_notif = 'Mantenimiento Completado'

    db.session.commit()

    # Notificar a administradores
    notificar_admins(
        titulo_notif,
        f'El tecnico {current_user.nombre} ha completado el mantenimiento {mantenimiento.numero}',
        url_for('admin.mantenimiento_ver', id=mantenimiento.id),
        tenant_id=current_user.tenant_id
    )

    flash(mensaje_flash, 'success')
    return jsonify({'success': True, 'message': mensaje_flash})


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

    # Aplicar rotación EXIF y guardar correctamente orientada
    from PIL import Image as PILImage
    from PIL import ImageOps
    import io as pil_io

    # Leer imagen desde el archivo subido
    foto_data = foto.read()
    pil_img = PILImage.open(pil_io.BytesIO(foto_data))

    # Aplicar rotación según EXIF
    pil_img = ImageOps.exif_transpose(pil_img)

    # Convertir a RGB si es necesario (para JPEG)
    if pil_img.mode in ('RGBA', 'P'):
        pil_img = pil_img.convert('RGB')

    # Guardar con orientación correcta
    pil_img.save(filepath, 'JPEG', quality=85)

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

# ==================== FIRMA DIGITAL DEL CLIENTE ====================
@tecnico_bp.route('/ordenes/<int:id>/firma')
@login_required
@tecnico_required
def orden_firma(id):
    """Muestra el formulario de firma para que el cliente firme"""
    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        flash('No tienes acceso a esta orden.', 'danger')
        return redirect(url_for('tecnico.ordenes'))

    if orden.firma_cliente:
        flash('Esta orden ya tiene firma del cliente.', 'info')
        return redirect(url_for('tecnico.orden_ver', id=id))

    return render_template('tecnico/ordenes/firma.html', orden=orden)

@tecnico_bp.route('/ordenes/<int:id>/guardar-firma', methods=['POST'])
@login_required
@tecnico_required
def orden_guardar_firma(id):
    """Guarda la firma del cliente"""
    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        return jsonify({'error': 'Sin acceso'}), 403

    firma_data = request.form.get('firma_data')
    firma_nombre = request.form.get('firma_nombre')

    if not firma_data or not firma_nombre:
        return jsonify({'error': 'Faltan datos de la firma'}), 400

    orden.firma_cliente = firma_data
    orden.firma_nombre = firma_nombre
    orden.firma_fecha = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'message': 'Firma guardada correctamente'})

@tecnico_bp.route('/ordenes/<int:id>/completar-con-firma', methods=['POST'])
@login_required
@tecnico_required
def orden_completar_con_firma(id):
    """Completa la orden con firma del cliente"""
    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        flash('No tienes acceso a esta orden.', 'danger')
        return redirect(url_for('tecnico.ordenes'))

    firma_data = request.form.get('firma_data')
    firma_nombre = request.form.get('firma_nombre')

    if not firma_data or not firma_nombre:
        flash('Falta la firma del cliente.', 'danger')
        return redirect(url_for('tecnico.orden_firma', id=id))

    # Guardar descripcion del trabajo
    orden.descripcion_trabajo = request.form.get('descripcion_trabajo')
    orden.tiempo_real = request.form.get('tiempo_real', type=int)

    # Guardar firma
    orden.firma_cliente = firma_data
    orden.firma_nombre = firma_nombre
    orden.firma_fecha = datetime.utcnow()

    # Completar orden
    orden.estado = 'completado'
    orden.fecha_fin = datetime.utcnow()

    db.session.commit()

    # Notificar a administradores del mismo tenant
    notificar_admins(
        'Orden Completada con Firma',
        f'El tecnico {current_user.nombre} ha completado la orden {orden.numero} con firma del cliente',
        url_for('admin.orden_ver', id=orden.id),
        tenant_id=current_user.tenant_id
    )

    flash('Orden completada exitosamente con firma del cliente.', 'success')
    return redirect(url_for('tecnico.ordenes'))


@tecnico_bp.route('/ordenes/<int:id>/completar-flexible', methods=['POST'])
@login_required
@tecnico_required
def orden_completar_flexible(id):
    """Completa la orden con opciones: firma presencial, remota o sin firma"""
    import secrets
    from app.services.notificaciones import notificar_cliente

    orden = OrdenTrabajo.query.get_or_404(id)
    if current_user not in orden.tecnicos.all():
        return jsonify({'error': 'No tienes acceso a esta orden'}), 403

    data = request.get_json()
    opcion = data.get('opcion')
    descripcion_trabajo = data.get('descripcion_trabajo')

    if not opcion:
        return jsonify({'error': 'Seleccione una opcion'}), 400

    # Guardar descripcion del trabajo
    if descripcion_trabajo:
        orden.descripcion_trabajo = descripcion_trabajo

    orden.fecha_fin = datetime.utcnow()

    if opcion == 'presencial':
        # Firma presencial
        firma_data = data.get('firma_data')
        firma_nombre = data.get('firma_nombre')

        if not firma_data or not firma_nombre:
            return jsonify({'error': 'Falta la firma del cliente'}), 400

        orden.firma_cliente = firma_data
        orden.firma_nombre = firma_nombre
        orden.firma_fecha = datetime.utcnow()
        orden.firma_estado = 'firmado'
        orden.estado = 'completado'

        mensaje_flash = 'Orden completada con firma del cliente.'
        titulo_notif = 'Orden Completada con Firma'

    elif opcion == 'remota':
        # Firma remota - generar token y enviar notificacion
        if not orden.cliente:
            return jsonify({'error': 'No se puede solicitar firma remota sin cliente registrado'}), 400

        # Generar token unico
        orden.firma_token = secrets.token_urlsafe(32)
        orden.firma_estado = 'pendiente'
        orden.estado = 'pendiente_firma'

        db.session.commit()

        # URL para firmar
        firma_url = url_for('firma_publica.firmar_orden', token=orden.firma_token, _external=True)

        # Notificar al cliente
        notificar_cliente(
            orden.cliente,
            'Firma Requerida',
            f'El trabajo {orden.numero} ha sido completado. Por favor firme para confirmar.',
            firma_url
        )

        # Notificar admin
        notificar_admins(
            'Orden Pendiente de Firma',
            f'El tecnico {current_user.nombre} ha solicitado firma remota para la orden {orden.numero}',
            url_for('admin.orden_ver', id=orden.id),
            tenant_id=current_user.tenant_id
        )

        flash('Se ha enviado solicitud de firma al cliente.', 'info')
        return jsonify({'success': True, 'message': 'Solicitud de firma enviada'})

    else:
        # Sin firma
        orden.firma_estado = 'sin_firma'
        orden.estado = 'completado'

        mensaje_flash = 'Orden completada sin firma.'
        titulo_notif = 'Orden Completada'

    db.session.commit()

    # Notificar a administradores
    notificar_admins(
        titulo_notif,
        f'El tecnico {current_user.nombre} ha completado la orden {orden.numero}',
        url_for('admin.orden_ver', id=orden.id),
        tenant_id=current_user.tenant_id
    )

    flash(mensaje_flash, 'success')
    return jsonify({'success': True, 'message': mensaje_flash})
