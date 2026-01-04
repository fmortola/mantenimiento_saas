from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.ubicacion import Ubicacion
from app.models.equipo import Equipo, TIPOS_EQUIPO, CONDICIONES_EQUIPO
from app.models.tipo_equipo import TipoEquipo
from app.models.orden_trabajo import OrdenTrabajo, TIPOS_ORDEN, PRIORIDADES, ESTADOS_ORDEN
from app.models.ticket import Ticket, ESTADOS_TICKET
from app.models.mantenimiento import Mantenimiento, MantenimientoEquipo, TIPOS_MANTENIMIENTO
from app.models.notificacion import Notificacion
from app.services.notificaciones import enviar_notificacion_push, notificar_cliente, notificar_admins
from app.utils.tenant_utils import tenant_required, get_current_tenant_id
from app.utils.query_helpers import (
    get_clientes_query, get_tecnicos_query, get_ordenes_query,
    get_tickets_query, get_mantenimientos_query, get_equipos_query, get_ubicaciones_query
)
from datetime import datetime

admin_bp = Blueprint('admin', __name__)


def get_tenant_id():
    """Obtiene el tenant_id actual (del usuario o de impersonacion)"""
    if current_user.es_superadmin():
        return session.get('impersonate_tenant_id')
    return current_user.tenant_id


def get_current_tenant():
    """Obtiene el objeto Tenant actual"""
    from app.models.tenant import Tenant
    if current_user.es_superadmin():
        tenant_id = session.get('impersonate_tenant_id')
        return Tenant.query.get(tenant_id) if tenant_id else None
    return current_user.tenant


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Acceso denegado. Debes iniciar sesion.', 'danger')
            return redirect(url_for('auth.login'))

        # Permitir superadmin en modo impersonacion
        if current_user.es_superadmin():
            if 'impersonate_tenant_id' in session:
                return f(*args, **kwargs)
            flash('Debes seleccionar un tenant para ver esta seccion.', 'warning')
            return redirect(url_for('superadmin.tenants'))

        if not current_user.es_admin():
            flash('Acceso denegado. Se requieren permisos de administrador.', 'danger')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function

# ==================== DASHBOARD ====================
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Estadisticas generales - filtradas por tenant
    stats = {
        'total_clientes': get_clientes_query().filter_by(activo=True).count(),
        'total_tecnicos': get_tecnicos_query().filter_by(activo=True).count(),
        'total_equipos': get_equipos_query().filter_by(activo=True).count(),
        'tickets_abiertos': get_tickets_query().filter(Ticket.estado.in_(['abierto', 'asignado'])).count(),
        'ordenes_pendientes': get_ordenes_query().filter(OrdenTrabajo.estado.in_(['pendiente', 'asignado', 'en_progreso'])).count(),
        'mantenimientos_activos': get_mantenimientos_query().filter(Mantenimiento.estado.in_(['programado', 'en_progreso'])).count()
    }

    # Tickets recientes sin asignar
    tickets_nuevos = get_tickets_query().filter_by(estado='abierto').order_by(Ticket.fecha_creacion.desc()).limit(5).all()

    # Ordenes recientes
    ordenes_recientes = get_ordenes_query().order_by(OrdenTrabajo.fecha_creacion.desc()).limit(5).all()

    # Mantenimientos en progreso
    mantenimientos_activos = get_mantenimientos_query().filter_by(estado='en_progreso').all()

    return render_template('admin/dashboard.html',
                           stats=stats,
                           tickets_nuevos=tickets_nuevos,
                           ordenes_recientes=ordenes_recientes,
                           mantenimientos_activos=mantenimientos_activos)

# ==================== CLIENTES ====================
@admin_bp.route('/clientes')
@login_required
@admin_required
def clientes():
    clientes = get_clientes_query().filter_by(activo=True).order_by(Cliente.nombre).all()
    return render_template('admin/clientes/lista.html', clientes=clientes)

@admin_bp.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def cliente_nuevo():
    # Verificar limite del plan
    tenant = get_current_tenant()
    if tenant and not tenant.puede_agregar_cliente():
        flash(f'Has alcanzado el limite de clientes de tu plan ({tenant.plan.max_clientes}). Actualiza tu plan para agregar mas.', 'warning')
        return redirect(url_for('admin.clientes'))

    if request.method == 'POST':
        # Verificar limite nuevamente antes de guardar
        if tenant and not tenant.puede_agregar_cliente():
            flash(f'Has alcanzado el limite de clientes de tu plan.', 'warning')
            return redirect(url_for('admin.clientes'))

        cliente = Cliente(
            nombre=request.form.get('nombre'),
            rif=request.form.get('rif'),
            email=request.form.get('email'),
            telefono_principal=request.form.get('telefono_principal'),
            telefono_secundario=request.form.get('telefono_secundario'),
            persona_contacto=request.form.get('persona_contacto'),
            notas=request.form.get('notas'),
            tenant_id=get_tenant_id()
        )
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente creado exitosamente.', 'success')
        return redirect(url_for('admin.cliente_ver', id=cliente.id))

    return render_template('admin/clientes/form.html', cliente=None)

@admin_bp.route('/clientes/<int:id>')
@login_required
@admin_required
def cliente_ver(id):
    cliente = get_clientes_query().filter_by(id=id).first_or_404()
    return render_template('admin/clientes/ver.html', cliente=cliente)

@admin_bp.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def cliente_editar(id):
    cliente = get_clientes_query().filter_by(id=id).first_or_404()

    if request.method == 'POST':
        cliente.nombre = request.form.get('nombre')
        cliente.rif = request.form.get('rif')
        cliente.email = request.form.get('email')
        cliente.telefono_principal = request.form.get('telefono_principal')
        cliente.telefono_secundario = request.form.get('telefono_secundario')
        cliente.persona_contacto = request.form.get('persona_contacto')
        cliente.notas = request.form.get('notas')
        db.session.commit()
        flash('Cliente actualizado exitosamente.', 'success')
        return redirect(url_for('admin.cliente_ver', id=cliente.id))

    return render_template('admin/clientes/form.html', cliente=cliente)

@admin_bp.route('/clientes/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def cliente_eliminar(id):
    cliente = get_clientes_query().filter_by(id=id).first_or_404()
    cliente.activo = False
    db.session.commit()
    flash('Cliente eliminado.', 'success')
    return redirect(url_for('admin.clientes'))

# ==================== UBICACIONES ====================
@admin_bp.route('/clientes/<int:cliente_id>/ubicaciones/nueva', methods=['GET', 'POST'])
@login_required
@admin_required
def ubicacion_nueva(cliente_id):
    cliente = get_clientes_query().filter_by(id=cliente_id).first_or_404()

    if request.method == 'POST':
        ubicacion = Ubicacion(
            nombre=request.form.get('nombre'),
            direccion=request.form.get('direccion'),
            ciudad=request.form.get('ciudad'),
            estado=request.form.get('estado'),
            telefono=request.form.get('telefono'),
            persona_contacto=request.form.get('persona_contacto'),
            notas=request.form.get('notas'),
            cliente_id=cliente.id,
            tenant_id=get_tenant_id()
        )
        db.session.add(ubicacion)
        db.session.commit()
        flash('Ubicacion creada exitosamente.', 'success')
        return redirect(url_for('admin.cliente_ver', id=cliente.id))

    return render_template('admin/ubicaciones/form.html', cliente=cliente, ubicacion=None)

@admin_bp.route('/ubicaciones/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def ubicacion_editar(id):
    ubicacion = get_ubicaciones_query().filter_by(id=id).first_or_404()

    if request.method == 'POST':
        ubicacion.nombre = request.form.get('nombre')
        ubicacion.direccion = request.form.get('direccion')
        ubicacion.ciudad = request.form.get('ciudad')
        ubicacion.estado = request.form.get('estado')
        ubicacion.telefono = request.form.get('telefono')
        ubicacion.persona_contacto = request.form.get('persona_contacto')
        ubicacion.notas = request.form.get('notas')
        db.session.commit()
        flash('Ubicación actualizada.', 'success')
        return redirect(url_for('admin.cliente_ver', id=ubicacion.cliente_id))

    return render_template('admin/ubicaciones/form.html', cliente=ubicacion.cliente, ubicacion=ubicacion)

@admin_bp.route('/ubicaciones/<int:id>')
@login_required
@admin_required
def ubicacion_ver(id):
    ubicacion = get_ubicaciones_query().filter_by(id=id).first_or_404()
    equipos = ubicacion.equipos.filter_by(activo=True).all()
    return render_template('admin/ubicaciones/ver.html', ubicacion=ubicacion, equipos=equipos, tipos_equipo=TIPOS_EQUIPO, condiciones=CONDICIONES_EQUIPO)

# ==================== EQUIPOS ====================
@admin_bp.route('/equipos')
@login_required
@admin_required
def equipos():
    cliente_id = request.args.get('cliente_id', type=int)
    ubicacion_id = request.args.get('ubicacion_id', type=int)

    equipos = []
    ubicaciones = []

    # Solo mostrar equipos si hay ubicacion seleccionada
    if ubicacion_id:
        equipos = get_equipos_query().filter_by(ubicacion_id=ubicacion_id, activo=True).order_by(Equipo.tipo, Equipo.nombre).all()

    # Cargar ubicaciones si hay cliente seleccionado
    if cliente_id:
        ubicaciones = get_ubicaciones_query().filter_by(cliente_id=cliente_id, activo=True).order_by(Ubicacion.nombre).all()

    clientes = get_clientes_query().filter_by(activo=True).order_by(Cliente.nombre).all()

    return render_template('admin/equipos/lista.html',
                           equipos=equipos,
                           clientes=clientes,
                           ubicaciones=ubicaciones,
                           cliente_id=cliente_id,
                           ubicacion_id=ubicacion_id)

@admin_bp.route('/ubicaciones/<int:ubicacion_id>/equipos/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def equipo_nuevo(ubicacion_id):
    ubicacion = get_ubicaciones_query().filter_by(id=ubicacion_id).first_or_404()

    # Verificar limite del plan
    tenant = get_current_tenant()
    if tenant and not tenant.puede_agregar_equipo():
        flash(f'Has alcanzado el limite de equipos de tu plan ({tenant.plan.max_equipos}). Actualiza tu plan para agregar mas.', 'warning')
        return redirect(url_for('admin.ubicacion_ver', id=ubicacion_id))

    if request.method == 'POST':
        # Verificar limite nuevamente antes de guardar
        if tenant and not tenant.puede_agregar_equipo():
            flash(f'Has alcanzado el limite de equipos de tu plan.', 'warning')
            return redirect(url_for('admin.ubicacion_ver', id=ubicacion_id))

        equipo = Equipo(
            tipo_equipo_id=request.form.get('tipo_equipo_id', type=int),
            nombre=request.form.get('nombre'),
            marca=request.form.get('marca'),
            modelo=request.form.get('modelo'),
            serial=request.form.get('serial'),
            departamento=request.form.get('departamento'),
            condicion=request.form.get('condicion'),
            descripcion=request.form.get('descripcion'),
            ubicacion_id=ubicacion.id,
            creado_por_id=current_user.id,
            tenant_id=get_tenant_id()
        )
        db.session.add(equipo)
        db.session.commit()
        flash('Equipo registrado exitosamente.', 'success')
        return redirect(url_for('admin.ubicacion_ver', id=ubicacion.id))

    tipos = TipoEquipo.query.filter_by(tenant_id=get_tenant_id(), activo=True).order_by(TipoEquipo.orden).all()
    return render_template('admin/equipos/form.html', ubicacion=ubicacion, equipo=None,
                           tipos_equipo=tipos, condiciones=CONDICIONES_EQUIPO)

@admin_bp.route('/equipos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def equipo_editar(id):
    equipo = get_equipos_query().filter_by(id=id).first_or_404()

    if request.method == 'POST':
        equipo.tipo_equipo_id = request.form.get('tipo_equipo_id', type=int)
        equipo.nombre = request.form.get('nombre')
        equipo.marca = request.form.get('marca')
        equipo.modelo = request.form.get('modelo')
        equipo.serial = request.form.get('serial')
        equipo.departamento = request.form.get('departamento')
        equipo.condicion = request.form.get('condicion')
        equipo.descripcion = request.form.get('descripcion')
        db.session.commit()
        flash('Equipo actualizado.', 'success')
        return redirect(url_for('admin.ubicacion_ver', id=equipo.ubicacion_id))

    tipos = TipoEquipo.query.filter_by(tenant_id=get_tenant_id(), activo=True).order_by(TipoEquipo.orden).all()
    return render_template('admin/equipos/form.html', ubicacion=equipo.ubicacion, equipo=equipo,
                           tipos_equipo=tipos, condiciones=CONDICIONES_EQUIPO)

# ==================== TIPOS DE EQUIPO ====================
@admin_bp.route('/tipos-equipo')
@login_required
@admin_required
def tipos_equipo():
    from app.models.plantilla_tipo_equipo import PlantillaTipoEquipo
    tipos = TipoEquipo.query.filter_by(tenant_id=get_tenant_id()).order_by(TipoEquipo.orden, TipoEquipo.nombre).all()
    plantillas = PlantillaTipoEquipo.query.filter_by(activo=True).order_by(PlantillaTipoEquipo.orden).all()
    return render_template('admin/tipos_equipo/lista.html', tipos=tipos, plantillas=plantillas)

@admin_bp.route('/tipos-equipo/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def tipo_equipo_nuevo():
    if request.method == 'POST':
        # Obtener el siguiente orden
        max_orden = db.session.query(db.func.max(TipoEquipo.orden)).filter_by(tenant_id=get_tenant_id()).scalar() or 0

        tipo = TipoEquipo(
            nombre=request.form.get('nombre'),
            icono=request.form.get('icono', 'bi-gear'),
            descripcion=request.form.get('descripcion'),
            orden=max_orden + 1,
            tenant_id=get_tenant_id()
        )
        db.session.add(tipo)
        db.session.commit()
        flash('Tipo de equipo creado.', 'success')
        return redirect(url_for('admin.tipos_equipo'))

    return render_template('admin/tipos_equipo/form.html', tipo=None)

@admin_bp.route('/tipos-equipo/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def tipo_equipo_editar(id):
    tipo = TipoEquipo.query.filter_by(id=id, tenant_id=get_tenant_id()).first_or_404()

    if request.method == 'POST':
        tipo.nombre = request.form.get('nombre')
        tipo.icono = request.form.get('icono', 'bi-gear')
        tipo.descripcion = request.form.get('descripcion')
        tipo.activo = 'activo' in request.form
        db.session.commit()
        flash('Tipo de equipo actualizado.', 'success')
        return redirect(url_for('admin.tipos_equipo'))

    return render_template('admin/tipos_equipo/form.html', tipo=tipo)

@admin_bp.route('/tipos-equipo/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def tipo_equipo_eliminar(id):
    tipo = TipoEquipo.query.filter_by(id=id, tenant_id=get_tenant_id()).first_or_404()

    # Verificar si hay equipos usando este tipo
    if tipo.equipos.count() > 0:
        flash(f'No se puede eliminar. Hay {tipo.equipos.count()} equipo(s) usando este tipo.', 'warning')
        return redirect(url_for('admin.tipos_equipo'))

    db.session.delete(tipo)
    db.session.commit()
    flash('Tipo de equipo eliminado.', 'success')
    return redirect(url_for('admin.tipos_equipo'))

@admin_bp.route('/tipos-equipo/crear-defaults', methods=['POST'])
@login_required
@admin_required
def tipos_equipo_crear_defaults():
    """Crea tipos de equipo predefinidos"""
    plantilla = request.form.get('plantilla', 'default')

    # Verificar si ya hay tipos
    existentes = TipoEquipo.query.filter_by(tenant_id=get_tenant_id()).count()
    if existentes > 0:
        flash('Ya tienes tipos de equipo creados. Eliminalos primero si deseas usar una plantilla.', 'warning')
        return redirect(url_for('admin.tipos_equipo'))

    if plantilla == 'linea_blanca':
        TipoEquipo.crear_tipos_linea_blanca(get_tenant_id())
        flash('Tipos de equipo para Linea Blanca creados.', 'success')
    elif plantilla == 'hvac':
        TipoEquipo.crear_tipos_hvac(get_tenant_id())
        flash('Tipos de equipo para HVAC/Climatizacion creados.', 'success')
    else:
        TipoEquipo.crear_tipos_default(get_tenant_id())
        flash('Tipos de equipo predeterminados creados.', 'success')

    return redirect(url_for('admin.tipos_equipo'))

@admin_bp.route('/tipos-equipo/cambiar-plantilla', methods=['POST'])
@login_required
@admin_required
def tipos_equipo_cambiar_plantilla():
    """Elimina tipos existentes (sin equipos) y crea nuevos desde plantilla de BD"""
    from app.models.plantilla_tipo_equipo import PlantillaTipoEquipo

    plantilla_id = request.form.get('plantilla_id')
    tenant_id = get_tenant_id()

    if not plantilla_id:
        flash('Debe seleccionar una plantilla.', 'warning')
        return redirect(url_for('admin.tipos_equipo'))

    # Buscar la plantilla
    plantilla = PlantillaTipoEquipo.query.filter_by(id=plantilla_id, activo=True).first()
    if not plantilla:
        flash('Plantilla no encontrada o inactiva.', 'danger')
        return redirect(url_for('admin.tipos_equipo'))

    # Verificar si hay tipos con equipos asignados
    tipos_con_equipos = TipoEquipo.query.filter_by(tenant_id=tenant_id).filter(
        TipoEquipo.equipos.any()
    ).count()

    if tipos_con_equipos > 0:
        flash(f'No se puede cambiar la plantilla. Hay {tipos_con_equipos} tipo(s) con equipos asignados.', 'warning')
        return redirect(url_for('admin.tipos_equipo'))

    # Eliminar tipos existentes
    TipoEquipo.query.filter_by(tenant_id=tenant_id).delete()
    db.session.commit()

    # Aplicar la plantilla
    plantilla.aplicar_a_tenant(tenant_id)
    flash(f'Plantilla "{plantilla.nombre}" aplicada correctamente.', 'success')

    return redirect(url_for('admin.tipos_equipo'))

# ==================== TÉCNICOS ====================
@admin_bp.route('/tecnicos')
@login_required
@admin_required
def tecnicos():
    tecnicos = get_tecnicos_query().order_by(Usuario.nombre).all()
    return render_template('admin/tecnicos/lista.html', tecnicos=tecnicos)

@admin_bp.route('/tecnicos/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def tecnico_nuevo():
    # Verificar limite del plan
    tenant = get_current_tenant()
    if tenant and not tenant.puede_agregar_tecnico():
        flash(f'Has alcanzado el limite de tecnicos de tu plan ({tenant.plan.max_tecnicos}). Actualiza tu plan para agregar mas.', 'warning')
        return redirect(url_for('admin.tecnicos'))

    if request.method == 'POST':
        # Verificar limite nuevamente antes de guardar
        if tenant and not tenant.puede_agregar_tecnico():
            flash(f'Has alcanzado el limite de tecnicos de tu plan.', 'warning')
            return redirect(url_for('admin.tecnicos'))

        # Verificar que el email no exista
        if Usuario.query.filter_by(email=request.form.get('email')).first():
            flash('Ya existe un usuario con ese email.', 'danger')
            return redirect(url_for('admin.tecnico_nuevo'))

        tecnico = Usuario(
            nombre=request.form.get('nombre'),
            email=request.form.get('email'),
            telefono=request.form.get('telefono'),
            rol='tecnico',
            tenant_id=get_tenant_id()
        )
        tecnico.set_password(request.form.get('password'))
        db.session.add(tecnico)
        db.session.commit()
        flash('Tecnico creado exitosamente.', 'success')
        return redirect(url_for('admin.tecnicos'))

    return render_template('admin/tecnicos/form.html', tecnico=None)

@admin_bp.route('/tecnicos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def tecnico_editar(id):
    tecnico = get_tecnicos_query().filter_by(id=id).first_or_404()

    if request.method == 'POST':
        # Verificar si se intenta reactivar un tecnico inactivo
        quiere_activar = 'activo' in request.form
        esta_inactivo = not tecnico.activo

        if quiere_activar and esta_inactivo:
            # Verificar limite del plan antes de reactivar
            tenant = get_current_tenant()
            if tenant and not tenant.puede_agregar_tecnico():
                flash(f'No puedes reactivar este tecnico. Has alcanzado el limite de tu plan ({tenant.plan.max_tecnicos}).', 'warning')
                return redirect(url_for('admin.tecnicos'))

        tecnico.nombre = request.form.get('nombre')
        tecnico.telefono = request.form.get('telefono')
        tecnico.activo = quiere_activar

        if request.form.get('password'):
            tecnico.set_password(request.form.get('password'))

        db.session.commit()
        flash('Tecnico actualizado.', 'success')
        return redirect(url_for('admin.tecnicos'))

    return render_template('admin/tecnicos/form.html', tecnico=tecnico)

# ==================== USUARIOS CLIENTE ====================
@admin_bp.route('/clientes/<int:cliente_id>/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def usuario_cliente_nuevo(cliente_id):
    cliente = get_clientes_query().filter_by(id=cliente_id).first_or_404()

    if request.method == 'POST':
        if Usuario.query.filter_by(email=request.form.get('email')).first():
            flash('Ya existe un usuario con ese email.', 'danger')
            return redirect(url_for('admin.usuario_cliente_nuevo', cliente_id=cliente_id))

        usuario = Usuario(
            nombre=request.form.get('nombre'),
            email=request.form.get('email'),
            telefono=request.form.get('telefono'),
            rol='cliente',
            cliente_id=cliente.id,
            tenant_id=get_tenant_id()
        )
        usuario.set_password(request.form.get('password'))
        db.session.add(usuario)
        db.session.commit()
        flash('Usuario del cliente creado exitosamente.', 'success')
        return redirect(url_for('admin.cliente_ver', id=cliente.id))

    return render_template('admin/clientes/usuario_form.html', cliente=cliente, usuario=None)

# ==================== TICKETS ====================
@admin_bp.route('/tickets')
@login_required
@admin_required
def tickets():
    estado = request.args.get('estado', 'activos')
    if estado == 'todos':
        tickets = get_tickets_query().order_by(Ticket.fecha_creacion.desc()).all()
    elif estado == 'activos':
        # Por defecto: todos excepto cerrados
        tickets = get_tickets_query().filter(Ticket.estado != 'cerrado').order_by(Ticket.fecha_creacion.desc()).all()
    else:
        tickets = get_tickets_query().filter_by(estado=estado).order_by(Ticket.fecha_creacion.desc()).all()

    return render_template('admin/tickets/lista.html', tickets=tickets, estado_filtro=estado, estados=ESTADOS_TICKET)

@admin_bp.route('/tickets/<int:id>')
@login_required
@admin_required
def ticket_ver(id):
    ticket = get_tickets_query().filter_by(id=id).first_or_404()
    tecnicos = get_tecnicos_query().filter_by(activo=True).all()
    return render_template('admin/tickets/ver.html', ticket=ticket, tecnicos=tecnicos)

@admin_bp.route('/tickets/<int:id>/asignar', methods=['POST'])
@login_required
@admin_required
def ticket_asignar(id):
    ticket = get_tickets_query().filter_by(id=id).first_or_404()
    tecnicos_ids = request.form.getlist('tecnicos')

    if tecnicos_ids:
        # Limpiar tecnicos actuales
        ticket.tecnicos = []

        # Asignar nuevos tecnicos
        for tecnico_id in tecnicos_ids:
            tecnico = get_tecnicos_query().filter_by(id=tecnico_id).first()
            if tecnico:
                ticket.tecnicos.append(tecnico)

                # Notificacion push al tecnico
                enviar_notificacion_push(
                    tecnico,
                    'Ticket Asignado',
                    f'Se te ha asignado el ticket {ticket.numero}',
                    url_for('tecnico.ticket_ver', id=ticket.id)
                )

        ticket.estado = 'asignado'
        ticket.fecha_asignacion = datetime.utcnow()
        db.session.commit()

        # Notificar al cliente que su ticket fue asignado
        notificar_cliente(
            ticket.cliente,
            'Ticket Programado',
            f'Tu ticket {ticket.numero} ha sido asignado. Pronto un tecnico te contactara.',
            url_for('cliente.ticket_ver', id=ticket.id)
        )

        flash('Tecnicos asignados correctamente.', 'success')
    else:
        flash('Debes seleccionar al menos un tecnico.', 'danger')

    return redirect(url_for('admin.ticket_ver', id=id))

@admin_bp.route('/tickets/<int:id>/cerrar', methods=['POST'])
@login_required
@admin_required
def ticket_cerrar(id):
    ticket = get_tickets_query().filter_by(id=id).first_or_404()
    ticket.estado = 'cerrado'
    ticket.fecha_resolucion = datetime.utcnow()
    ticket.respuesta_admin = request.form.get('respuesta')
    db.session.commit()

    # Notificar al cliente que su ticket fue cerrado
    notificar_cliente(
        ticket.cliente,
        'Ticket Resuelto',
        f'Tu ticket {ticket.numero} ha sido resuelto. Gracias por contactarnos.',
        url_for('cliente.ticket_ver', id=ticket.id)
    )

    flash('Ticket cerrado.', 'success')
    return redirect(url_for('admin.tickets'))

# ==================== ORDENES DE TRABAJO ====================
@admin_bp.route('/ordenes')
@login_required
@admin_required
def ordenes():
    estado = request.args.get('estado', 'activos')
    if estado == 'todos':
        ordenes = get_ordenes_query().order_by(OrdenTrabajo.fecha_creacion.desc()).all()
    elif estado == 'activos':
        # Por defecto: todos excepto completados y cancelados
        ordenes = get_ordenes_query().filter(OrdenTrabajo.estado.notin_(['completado', 'cancelado'])).order_by(OrdenTrabajo.fecha_creacion.desc()).all()
    else:
        ordenes = get_ordenes_query().filter_by(estado=estado).order_by(OrdenTrabajo.fecha_creacion.desc()).all()

    return render_template('admin/ordenes/lista.html', ordenes=ordenes, estado_filtro=estado, estados=ESTADOS_ORDEN)

@admin_bp.route('/ordenes/nueva', methods=['GET', 'POST'])
@login_required
@admin_required
def orden_nueva():
    if request.method == 'POST':
        # Determinar si es cliente existente o nuevo
        cliente_id = request.form.get('cliente_id')
        ubicacion_id = request.form.get('ubicacion_id')

        orden = OrdenTrabajo(
            numero=OrdenTrabajo.generar_numero(),
            tipo=request.form.get('tipo'),
            descripcion_solicitud=request.form.get('descripcion_solicitud'),
            prioridad=request.form.get('prioridad'),
            fecha_programada=datetime.strptime(request.form.get('fecha_programada'), '%Y-%m-%dT%H:%M') if request.form.get('fecha_programada') else None,
            creado_por_id=current_user.id,
            tenant_id=get_tenant_id()
        )

        if cliente_id:
            orden.cliente_id = cliente_id
            orden.ubicacion_id = ubicacion_id if ubicacion_id else None
        else:
            # Cliente rapido (llamada telefonica)
            orden.cliente_rapido_nombre = request.form.get('cliente_rapido_nombre')
            orden.cliente_rapido_telefono = request.form.get('cliente_rapido_telefono')
            orden.cliente_rapido_direccion = request.form.get('cliente_rapido_direccion')

        db.session.add(orden)
        db.session.flush()

        # Asignar tecnicos si se seleccionaron
        tecnicos_ids = request.form.getlist('tecnicos')
        if tecnicos_ids:
            for tecnico_id in tecnicos_ids:
                tecnico = get_tecnicos_query().filter_by(id=tecnico_id).first()
                if tecnico:
                    orden.tecnicos.append(tecnico)

                    # Notificacion push al tecnico
                    enviar_notificacion_push(
                        tecnico,
                        'Nueva Orden de Trabajo',
                        f'Se te ha asignado la orden {orden.numero}',
                        url_for('tecnico.orden_ver', id=orden.id)
                    )

            orden.estado = 'asignado'

        db.session.commit()
        flash('Orden de trabajo creada exitosamente.', 'success')
        return redirect(url_for('admin.orden_ver', id=orden.id))

    clientes = get_clientes_query().filter_by(activo=True).order_by(Cliente.nombre).all()
    tecnicos = get_tecnicos_query().filter_by(activo=True).all()
    return render_template('admin/ordenes/form.html', orden=None, clientes=clientes, tecnicos=tecnicos,
                           tipos=TIPOS_ORDEN, prioridades=PRIORIDADES)

@admin_bp.route('/ordenes/<int:id>')
@login_required
@admin_required
def orden_ver(id):
    orden = get_ordenes_query().filter_by(id=id).first_or_404()
    tecnicos = get_tecnicos_query().filter_by(activo=True).all()
    return render_template('admin/ordenes/ver.html', orden=orden, tecnicos=tecnicos)

@admin_bp.route('/ordenes/<int:id>/asignar', methods=['POST'])
@login_required
@admin_required
def orden_asignar(id):
    orden = get_ordenes_query().filter_by(id=id).first_or_404()
    tecnicos_ids = request.form.getlist('tecnicos')

    if tecnicos_ids:
        # Limpiar técnicos actuales
        orden.tecnicos = []

        # Asignar nuevos técnicos
        for tecnico_id in tecnicos_ids:
            tecnico = get_tecnicos_query().filter_by(id=tecnico_id).first()
            if tecnico:
                orden.tecnicos.append(tecnico)

                enviar_notificacion_push(
                    tecnico,
                    'Orden de Trabajo Asignada',
                    f'Se te ha asignado la orden {orden.numero}',
                    url_for('tecnico.orden_ver', id=orden.id)
                )

        orden.estado = 'asignado'
        db.session.commit()
        flash('Técnicos asignados correctamente.', 'success')
    else:
        flash('Debes seleccionar al menos un técnico.', 'danger')

    return redirect(url_for('admin.orden_ver', id=id))

@admin_bp.route('/ordenes/<int:id>/finalizar', methods=['POST'])
@login_required
@admin_required
def orden_finalizar(id):
    orden = get_ordenes_query().filter_by(id=id).first_or_404()
    orden.estado = 'completado'
    orden.fecha_fin = datetime.utcnow()
    orden.notas_admin = request.form.get('notas_admin')
    db.session.commit()
    flash('Orden finalizada.', 'success')
    return redirect(url_for('admin.ordenes'))

# ==================== MANTENIMIENTOS ====================
@admin_bp.route('/mantenimientos')
@login_required
@admin_required
def mantenimientos():
    estado = request.args.get('estado', 'activos')
    if estado == 'todos':
        mantenimientos = get_mantenimientos_query().order_by(Mantenimiento.fecha_creacion.desc()).all()
    elif estado == 'activos':
        # Por defecto: todos excepto completados
        mantenimientos = get_mantenimientos_query().filter(Mantenimiento.estado != 'completado').order_by(Mantenimiento.fecha_creacion.desc()).all()
    else:
        mantenimientos = get_mantenimientos_query().filter_by(estado=estado).order_by(Mantenimiento.fecha_creacion.desc()).all()

    return render_template('admin/mantenimientos/lista.html', mantenimientos=mantenimientos, estado_filtro=estado)

@admin_bp.route('/mantenimientos/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def mantenimiento_nuevo():
    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        ubicacion_id = request.form.get('ubicacion_id')
        tecnicos_ids = request.form.getlist('tecnicos')

        mantenimiento = Mantenimiento(
            numero=Mantenimiento.generar_numero(),
            titulo=request.form.get('titulo'),
            descripcion=request.form.get('descripcion'),
            tipo=request.form.get('tipo'),
            fecha_programada=datetime.strptime(request.form.get('fecha_programada'), '%Y-%m-%dT%H:%M') if request.form.get('fecha_programada') else None,
            cliente_id=cliente_id,
            ubicacion_id=ubicacion_id,
            creado_por_id=current_user.id,
            tenant_id=get_tenant_id()
        )

        db.session.add(mantenimiento)
        db.session.flush()

        # Asignar tecnicos
        for tecnico_id in tecnicos_ids:
            tecnico = get_tecnicos_query().filter_by(id=tecnico_id).first()
            if tecnico:
                mantenimiento.tecnicos.append(tecnico)

                # Notificacion push
                enviar_notificacion_push(
                    tecnico,
                    'Mantenimiento Asignado',
                    f'Se te ha asignado el mantenimiento {mantenimiento.numero}',
                    url_for('tecnico.mantenimiento_ver', id=mantenimiento.id)
                )

        # Agregar equipos existentes de la ubicacion al mantenimiento
        ubicacion = get_ubicaciones_query().filter_by(id=ubicacion_id).first()
        for equipo in ubicacion.equipos.filter_by(activo=True):
            mant_equipo = MantenimientoEquipo(
                mantenimiento_id=mantenimiento.id,
                equipo_id=equipo.id,
                estado='pendiente'
            )
            db.session.add(mant_equipo)

        db.session.commit()
        flash('Mantenimiento programado exitosamente.', 'success')
        return redirect(url_for('admin.mantenimiento_ver', id=mantenimiento.id))

    clientes = get_clientes_query().filter_by(activo=True).order_by(Cliente.nombre).all()
    tecnicos = get_tecnicos_query().filter_by(activo=True).all()
    return render_template('admin/mantenimientos/form.html', mantenimiento=None, clientes=clientes,
                           tecnicos=tecnicos, tipos=TIPOS_MANTENIMIENTO)

@admin_bp.route('/mantenimientos/<int:id>')
@login_required
@admin_required
def mantenimiento_ver(id):
    mantenimiento = get_mantenimientos_query().filter_by(id=id).first_or_404()
    tecnicos = get_tecnicos_query().filter_by(activo=True).all()
    return render_template('admin/mantenimientos/ver.html', mantenimiento=mantenimiento, tecnicos=tecnicos)

@admin_bp.route('/mantenimientos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def mantenimiento_editar(id):
    mantenimiento = get_mantenimientos_query().filter_by(id=id).first_or_404()

    # Solo permitir editar si no está completado
    if mantenimiento.estado == 'completado':
        flash('No se puede editar un mantenimiento completado.', 'danger')
        return redirect(url_for('admin.mantenimiento_ver', id=id))

    if request.method == 'POST':
        # Guardar técnicos anteriores para comparar
        tecnicos_anteriores = set(t.id for t in mantenimiento.tecnicos)

        # Actualizar datos básicos
        mantenimiento.titulo = request.form.get('titulo')
        mantenimiento.descripcion = request.form.get('descripcion')
        mantenimiento.tipo = request.form.get('tipo')

        fecha_programada_str = request.form.get('fecha_programada')
        if fecha_programada_str:
            mantenimiento.fecha_programada = datetime.strptime(fecha_programada_str, '%Y-%m-%dT%H:%M')

        # Actualizar técnicos
        nuevos_tecnicos_ids = set(int(x) for x in request.form.getlist('tecnicos'))

        # Técnicos agregados
        tecnicos_agregados = nuevos_tecnicos_ids - tecnicos_anteriores
        # Técnicos removidos
        tecnicos_removidos = tecnicos_anteriores - nuevos_tecnicos_ids

        # Limpiar y reasignar técnicos
        mantenimiento.tecnicos = []
        for tecnico_id in nuevos_tecnicos_ids:
            tecnico = get_tecnicos_query().filter_by(id=tecnico_id).first()
            if tecnico:
                mantenimiento.tecnicos.append(tecnico)

        db.session.commit()

        # Notificar a técnicos nuevos
        for tecnico_id in tecnicos_agregados:
            tecnico = get_tecnicos_query().filter_by(id=tecnico_id).first()
            if tecnico:
                enviar_notificacion_push(
                    tecnico,
                    'Mantenimiento Asignado',
                    f'Se te ha asignado el mantenimiento {mantenimiento.numero}',
                    url_for('tecnico.mantenimiento_ver', id=mantenimiento.id)
                )

        # Notificar a técnicos removidos
        for tecnico_id in tecnicos_removidos:
            tecnico = get_tecnicos_query().filter_by(id=tecnico_id).first()
            if tecnico:
                enviar_notificacion_push(
                    tecnico,
                    'Mantenimiento Reasignado',
                    f'Ya no estás asignado al mantenimiento {mantenimiento.numero}',
                    None
                )

        flash('Mantenimiento actualizado exitosamente.', 'success')
        return redirect(url_for('admin.mantenimiento_ver', id=id))

    clientes = get_clientes_query().filter_by(activo=True).order_by(Cliente.nombre).all()
    tecnicos = get_tecnicos_query().filter_by(activo=True).all()
    ubicaciones = get_ubicaciones_query().filter_by(cliente_id=mantenimiento.cliente_id, activo=True).all()

    return render_template('admin/mantenimientos/form.html',
                           mantenimiento=mantenimiento,
                           clientes=clientes,
                           tecnicos=tecnicos,
                           ubicaciones=ubicaciones,
                           tipos=TIPOS_MANTENIMIENTO)

@admin_bp.route('/mantenimientos/<int:id>/iniciar', methods=['POST'])
@login_required
@admin_required
def mantenimiento_iniciar(id):
    mantenimiento = get_mantenimientos_query().filter_by(id=id).first_or_404()
    mantenimiento.estado = 'en_progreso'
    mantenimiento.fecha_inicio = datetime.utcnow()
    db.session.commit()
    flash('Mantenimiento iniciado.', 'success')
    return redirect(url_for('admin.mantenimiento_ver', id=id))

@admin_bp.route('/mantenimientos/<int:id>/finalizar', methods=['POST'])
@login_required
@admin_required
def mantenimiento_finalizar(id):
    mantenimiento = get_mantenimientos_query().filter_by(id=id).first_or_404()
    mantenimiento.estado = 'completado'
    mantenimiento.fecha_fin = datetime.utcnow()
    mantenimiento.notas_cierre = request.form.get('notas_cierre')
    db.session.commit()
    flash('Mantenimiento finalizado.', 'success')
    return redirect(url_for('admin.mantenimientos'))

# ==================== AGENDA / PLANIFICACIÓN ====================
@admin_bp.route('/agenda')
@login_required
@admin_required
def agenda():
    from datetime import timedelta
    from sqlalchemy import or_

    # Obtener rango de fechas (por defecto: hoy + 30 días)
    fecha_inicio = request.args.get('desde')
    fecha_fin = request.args.get('hasta')

    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    else:
        fecha_inicio = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    else:
        fecha_fin = fecha_inicio + timedelta(days=30)

    # Obtener órdenes programadas (no completadas/canceladas) - filtradas por tenant
    ordenes = get_ordenes_query().filter(
        OrdenTrabajo.fecha_programada.isnot(None),
        OrdenTrabajo.fecha_programada >= fecha_inicio,
        OrdenTrabajo.fecha_programada <= fecha_fin,
        OrdenTrabajo.estado.in_(['pendiente', 'asignado', 'en_progreso'])
    ).order_by(OrdenTrabajo.fecha_programada).all()

    # Obtener mantenimientos programados (no completados) - filtrados por tenant
    mantenimientos = get_mantenimientos_query().filter(
        Mantenimiento.fecha_programada.isnot(None),
        Mantenimiento.fecha_programada >= fecha_inicio,
        Mantenimiento.fecha_programada <= fecha_fin,
        Mantenimiento.estado.in_(['programado', 'en_progreso'])
    ).order_by(Mantenimiento.fecha_programada).all()

    # Obtener tickets asignados (con fecha de asignación como referencia) - filtrados por tenant
    tickets = get_tickets_query().filter(
        Ticket.estado.in_(['asignado', 'en_progreso']),
        or_(
            Ticket.fecha_asignacion >= fecha_inicio,
            Ticket.fecha_creacion >= fecha_inicio
        )
    ).order_by(Ticket.fecha_creacion).all()

    # Crear lista unificada de eventos
    eventos = []

    for orden in ordenes:
        eventos.append({
            'tipo': 'orden',
            'id': orden.id,
            'numero': orden.numero,
            'fecha': orden.fecha_programada,
            'descripcion': orden.descripcion_solicitud[:100] + '...' if len(orden.descripcion_solicitud) > 100 else orden.descripcion_solicitud,
            'cliente': orden.cliente.nombre if orden.cliente else orden.cliente_rapido_nombre,
            'ubicacion': orden.ubicacion.nombre if orden.ubicacion else (orden.cliente_rapido_direccion or 'N/A'),
            'tecnicos': orden.tecnicos.count(),
            'tecnicos_nombres': [t.nombre for t in orden.tecnicos],
            'estado': orden.estado,
            'prioridad': orden.prioridad
        })

    for mant in mantenimientos:
        eventos.append({
            'tipo': 'mantenimiento',
            'id': mant.id,
            'numero': mant.numero,
            'fecha': mant.fecha_programada,
            'descripcion': mant.titulo,
            'cliente': mant.cliente.nombre,
            'ubicacion': mant.ubicacion.nombre,
            'tecnicos': mant.tecnicos.count(),
            'tecnicos_nombres': [t.nombre for t in mant.tecnicos],
            'estado': mant.estado,
            'prioridad': 'normal'
        })

    for ticket in tickets:
        eventos.append({
            'tipo': 'ticket',
            'id': ticket.id,
            'numero': ticket.numero,
            'fecha': ticket.fecha_asignacion or ticket.fecha_creacion,
            'descripcion': ticket.asunto,
            'cliente': ticket.cliente.nombre,
            'ubicacion': ticket.ubicacion.nombre if ticket.ubicacion else 'N/A',
            'tecnicos': ticket.tecnicos.count(),
            'tecnicos_nombres': [t.nombre for t in ticket.tecnicos],
            'estado': ticket.estado,
            'prioridad': ticket.prioridad
        })

    # Ordenar por fecha
    eventos.sort(key=lambda x: x['fecha'])

    # Agrupar por día
    eventos_por_dia = {}
    for evento in eventos:
        dia = evento['fecha'].strftime('%Y-%m-%d')
        if dia not in eventos_por_dia:
            eventos_por_dia[dia] = {
                'fecha': evento['fecha'],
                'eventos': [],
                'total_tecnicos': 0
            }
        eventos_por_dia[dia]['eventos'].append(evento)
        eventos_por_dia[dia]['total_tecnicos'] += evento['tecnicos']

    # Contar técnicos disponibles - filtrados por tenant
    total_tecnicos = get_tecnicos_query().filter_by(activo=True).count()

    return render_template('admin/agenda/index.html',
                           eventos_por_dia=eventos_por_dia,
                           fecha_inicio=fecha_inicio,
                           fecha_fin=fecha_fin,
                           total_tecnicos=total_tecnicos)

# ==================== REPORTES ====================
@admin_bp.route('/reportes')
@login_required
@admin_required
def reportes():
    return render_template('admin/reportes/index.html')

@admin_bp.route('/reportes/ordenes')
@login_required
@admin_required
def reporte_ordenes():
    from datetime import timedelta
    from flask import Response
    from app.services.excel_export import exportar_ordenes

    # Filtros
    fecha_desde = request.args.get('desde')
    fecha_hasta = request.args.get('hasta')
    cliente_id = request.args.get('cliente_id', type=int)
    tecnico_id = request.args.get('tecnico_id', type=int)
    estado = request.args.get('estado')
    exportar = request.args.get('exportar')

    # Fechas por defecto: último mes
    if fecha_desde:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
    else:
        fecha_desde = datetime.utcnow() - timedelta(days=30)

    if fecha_hasta:
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    else:
        fecha_hasta = datetime.utcnow()

    # Query - filtrada por tenant
    query = get_ordenes_query().filter(
        OrdenTrabajo.fecha_creacion >= fecha_desde,
        OrdenTrabajo.fecha_creacion <= fecha_hasta
    )

    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    if estado:
        query = query.filter_by(estado=estado)
    if tecnico_id:
        query = query.filter(OrdenTrabajo.tecnicos.any(Usuario.id == tecnico_id))

    ordenes = query.order_by(OrdenTrabajo.fecha_creacion.desc()).all()

    # Exportar a Excel
    if exportar == 'excel':
        output = exportar_ordenes(ordenes, f"Órdenes de Trabajo {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}")
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment;filename=ordenes_{fecha_desde.strftime("%Y%m%d")}_{fecha_hasta.strftime("%Y%m%d")}.xlsx'}
        )

    clientes = get_clientes_query().filter_by(activo=True).order_by(Cliente.nombre).all()
    tecnicos = get_tecnicos_query().filter_by(activo=True).all()

    return render_template('admin/reportes/ordenes.html',
                           ordenes=ordenes,
                           clientes=clientes,
                           tecnicos=tecnicos,
                           estados=ESTADOS_ORDEN,
                           fecha_desde=fecha_desde,
                           fecha_hasta=fecha_hasta,
                           cliente_id=cliente_id,
                           tecnico_id=tecnico_id,
                           estado_filtro=estado)

@admin_bp.route('/reportes/mantenimientos')
@login_required
@admin_required
def reporte_mantenimientos():
    from datetime import timedelta
    from flask import Response
    from app.services.excel_export import exportar_mantenimientos

    # Filtros
    fecha_desde = request.args.get('desde')
    fecha_hasta = request.args.get('hasta')
    cliente_id = request.args.get('cliente_id', type=int)
    estado = request.args.get('estado')
    exportar = request.args.get('exportar')

    if fecha_desde:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
    else:
        fecha_desde = datetime.utcnow() - timedelta(days=30)

    if fecha_hasta:
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    else:
        fecha_hasta = datetime.utcnow()

    # Query - filtrada por tenant
    query = get_mantenimientos_query().filter(
        Mantenimiento.fecha_creacion >= fecha_desde,
        Mantenimiento.fecha_creacion <= fecha_hasta
    )

    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    if estado:
        query = query.filter_by(estado=estado)

    mantenimientos = query.order_by(Mantenimiento.fecha_creacion.desc()).all()

    if exportar == 'excel':
        output = exportar_mantenimientos(mantenimientos, f"Mantenimientos {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}")
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment;filename=mantenimientos_{fecha_desde.strftime("%Y%m%d")}_{fecha_hasta.strftime("%Y%m%d")}.xlsx'}
        )

    clientes = get_clientes_query().filter_by(activo=True).order_by(Cliente.nombre).all()

    return render_template('admin/reportes/mantenimientos.html',
                           mantenimientos=mantenimientos,
                           clientes=clientes,
                           fecha_desde=fecha_desde,
                           fecha_hasta=fecha_hasta,
                           cliente_id=cliente_id,
                           estado_filtro=estado)

@admin_bp.route('/reportes/tickets')
@login_required
@admin_required
def reporte_tickets():
    from datetime import timedelta
    from flask import Response
    from app.services.excel_export import exportar_tickets

    fecha_desde = request.args.get('desde')
    fecha_hasta = request.args.get('hasta')
    cliente_id = request.args.get('cliente_id', type=int)
    estado = request.args.get('estado')
    exportar = request.args.get('exportar')

    if fecha_desde:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
    else:
        fecha_desde = datetime.utcnow() - timedelta(days=30)

    if fecha_hasta:
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    else:
        fecha_hasta = datetime.utcnow()

    # Query - filtrada por tenant
    query = get_tickets_query().filter(
        Ticket.fecha_creacion >= fecha_desde,
        Ticket.fecha_creacion <= fecha_hasta
    )

    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    if estado:
        query = query.filter_by(estado=estado)

    tickets = query.order_by(Ticket.fecha_creacion.desc()).all()

    if exportar == 'excel':
        output = exportar_tickets(tickets, f"Tickets {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}")
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment;filename=tickets_{fecha_desde.strftime("%Y%m%d")}_{fecha_hasta.strftime("%Y%m%d")}.xlsx'}
        )

    clientes = get_clientes_query().filter_by(activo=True).order_by(Cliente.nombre).all()

    return render_template('admin/reportes/tickets.html',
                           tickets=tickets,
                           clientes=clientes,
                           estados=ESTADOS_TICKET,
                           fecha_desde=fecha_desde,
                           fecha_hasta=fecha_hasta,
                           cliente_id=cliente_id,
                           estado_filtro=estado)

@admin_bp.route('/reportes/productividad')
@login_required
@admin_required
def reporte_productividad():
    from datetime import timedelta
    from flask import Response
    from app.services.excel_export import exportar_productividad_tecnicos

    fecha_desde = request.args.get('desde')
    fecha_hasta = request.args.get('hasta')
    exportar = request.args.get('exportar')

    if fecha_desde:
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
    else:
        fecha_desde = datetime.utcnow() - timedelta(days=30)

    if fecha_hasta:
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    else:
        fecha_hasta = datetime.utcnow()

    # Técnicos - filtrados por tenant
    tecnicos = get_tecnicos_query().filter_by(activo=True).all()
    tecnicos_data = []

    for tecnico in tecnicos:
        # Órdenes completadas - filtradas por tenant
        ordenes_completadas = get_ordenes_query().filter(
            OrdenTrabajo.tecnicos.any(Usuario.id == tecnico.id),
            OrdenTrabajo.estado == 'completado',
            OrdenTrabajo.fecha_fin >= fecha_desde,
            OrdenTrabajo.fecha_fin <= fecha_hasta
        ).count()

        # Mantenimientos completados - filtrados por tenant
        mantenimientos_completados = get_mantenimientos_query().filter(
            Mantenimiento.tecnicos.any(Usuario.id == tecnico.id),
            Mantenimiento.estado == 'completado',
            Mantenimiento.fecha_fin >= fecha_desde,
            Mantenimiento.fecha_fin <= fecha_hasta
        ).count()

        # Tickets resueltos - filtrados por tenant
        tickets_resueltos = get_tickets_query().filter(
            Ticket.tecnicos.any(Usuario.id == tecnico.id),
            Ticket.estado.in_(['resuelto', 'cerrado']),
            Ticket.fecha_resolucion >= fecha_desde,
            Ticket.fecha_resolucion <= fecha_hasta
        ).count()

        # Equipos atendidos en mantenimientos
        equipos_atendidos = MantenimientoEquipo.query.filter(
            MantenimientoEquipo.tecnico_id == tecnico.id,
            MantenimientoEquipo.estado == 'completado',
            MantenimientoEquipo.fecha_fin >= fecha_desde,
            MantenimientoEquipo.fecha_fin <= fecha_hasta
        ).count()

        tecnicos_data.append({
            'id': tecnico.id,
            'nombre': tecnico.nombre,
            'ordenes_completadas': ordenes_completadas,
            'mantenimientos_completados': mantenimientos_completados,
            'tickets_resueltos': tickets_resueltos,
            'equipos_atendidos': equipos_atendidos,
            'total': ordenes_completadas + mantenimientos_completados + tickets_resueltos
        })

    # Ordenar por total descendente
    tecnicos_data.sort(key=lambda x: x['total'], reverse=True)

    if exportar == 'excel':
        output = exportar_productividad_tecnicos(tecnicos_data, fecha_desde, fecha_hasta)
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment;filename=productividad_{fecha_desde.strftime("%Y%m%d")}_{fecha_hasta.strftime("%Y%m%d")}.xlsx'}
        )

    return render_template('admin/reportes/productividad.html',
                           tecnicos_data=tecnicos_data,
                           fecha_desde=fecha_desde,
                           fecha_hasta=fecha_hasta)

@admin_bp.route('/reportes/cliente')
@login_required
@admin_required
def reporte_cliente():
    from flask import Response
    from app.services.excel_export import exportar_historial_cliente

    cliente_id = request.args.get('cliente_id', type=int)
    exportar = request.args.get('exportar')

    clientes = get_clientes_query().filter_by(activo=True).order_by(Cliente.nombre).all()

    if not cliente_id:
        return render_template('admin/reportes/cliente.html',
                               clientes=clientes,
                               cliente=None,
                               ordenes=[],
                               mantenimientos=[],
                               tickets=[])

    cliente = get_clientes_query().filter_by(id=cliente_id).first_or_404()
    ordenes = get_ordenes_query().filter_by(cliente_id=cliente_id).order_by(OrdenTrabajo.fecha_creacion.desc()).all()
    mantenimientos = get_mantenimientos_query().filter_by(cliente_id=cliente_id).order_by(Mantenimiento.fecha_creacion.desc()).all()
    tickets = get_tickets_query().filter_by(cliente_id=cliente_id).order_by(Ticket.fecha_creacion.desc()).all()

    if exportar == 'excel':
        output = exportar_historial_cliente(cliente, ordenes, mantenimientos, tickets)
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment;filename=historial_{cliente.nombre.replace(" ", "_")}.xlsx'}
        )

    return render_template('admin/reportes/cliente.html',
                           clientes=clientes,
                           cliente=cliente,
                           ordenes=ordenes,
                           mantenimientos=mantenimientos,
                           tickets=tickets)

@admin_bp.route('/reportes/equipos')
@login_required
@admin_required
def reporte_equipos():
    from flask import Response
    from app.services.excel_export import exportar_equipos

    cliente_id = request.args.get('cliente_id', type=int)
    ubicacion_id = request.args.get('ubicacion_id', type=int)
    tipo = request.args.get('tipo')
    exportar = request.args.get('exportar')

    # Query - filtrada por tenant
    query = get_equipos_query().filter_by(activo=True)

    if ubicacion_id:
        query = query.filter_by(ubicacion_id=ubicacion_id)
    elif cliente_id:
        ubicaciones_ids = [u.id for u in get_ubicaciones_query().filter_by(cliente_id=cliente_id, activo=True).all()]
        query = query.filter(Equipo.ubicacion_id.in_(ubicaciones_ids))

    if tipo:
        query = query.filter_by(tipo=tipo)

    equipos = query.order_by(Equipo.tipo, Equipo.nombre).all()

    if exportar == 'excel':
        titulo = "Inventario de Equipos"
        if cliente_id:
            cliente = get_clientes_query().filter_by(id=cliente_id).first()
            titulo = f"Inventario - {cliente.nombre}"
        output = exportar_equipos(equipos, titulo)
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment;filename=inventario_equipos.xlsx'}
        )

    clientes = get_clientes_query().filter_by(activo=True).order_by(Cliente.nombre).all()
    ubicaciones = []
    if cliente_id:
        ubicaciones = get_ubicaciones_query().filter_by(cliente_id=cliente_id, activo=True).order_by(Ubicacion.nombre).all()

    return render_template('admin/reportes/equipos.html',
                           equipos=equipos,
                           clientes=clientes,
                           ubicaciones=ubicaciones,
                           tipos_equipo=TIPOS_EQUIPO,
                           cliente_id=cliente_id,
                           ubicacion_id=ubicacion_id,
                           tipo_filtro=tipo)

# ==================== API AUXILIAR ====================
@admin_bp.route('/api/clientes/<int:cliente_id>/ubicaciones')
@login_required
@admin_required
def api_ubicaciones_cliente(cliente_id):
    # Filtrar por tenant
    ubicaciones = get_ubicaciones_query().filter_by(cliente_id=cliente_id, activo=True).all()
    return jsonify([{'id': u.id, 'nombre': u.nombre, 'direccion': u.direccion} for u in ubicaciones])
