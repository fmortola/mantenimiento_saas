from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, Response
from flask_login import login_required, current_user
from app import db
from app.models.tenant import Tenant
from app.models.plan import Plan, PLANES_PREDEFINIDOS
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.equipo import Equipo
from app.models.ubicacion import Ubicacion
from app.models.tipo_equipo import TipoEquipo
from app.models.plantilla_tipo_equipo import PlantillaTipoEquipo, PlantillaTipoEquipoItem
from app.models.orden_trabajo import OrdenTrabajo, FotoTrabajo
from app.models.orden_actividad import OrdenActividad
from app.models.ticket import Ticket
from app.models.mantenimiento import Mantenimiento, MantenimientoEquipo
from app.models.notificacion import Notificacion
from app.utils.tenant_utils import superadmin_required
from datetime import datetime, timedelta
import re
import json

superadmin_bp = Blueprint('superadmin', __name__)


# ==================== DASHBOARD ====================
@superadmin_bp.route('/dashboard')
@login_required
@superadmin_required
def dashboard():
    stats = {
        'total_tenants': Tenant.query.count(),
        'tenants_activos': Tenant.query.filter_by(activo=True).count(),
        'total_usuarios': Usuario.query.filter(Usuario.rol != 'superadmin').count(),
        'total_tecnicos': Usuario.query.filter_by(rol='tecnico').count(),
        'total_clientes': Cliente.query.count(),
        'total_equipos': Equipo.query.count(),
    }

    # Tenants recientes
    tenants_recientes = Tenant.query.order_by(Tenant.fecha_creacion.desc()).limit(5).all()

    # Tenants por vencer (proximos 30 dias)
    fecha_limite = datetime.utcnow() + timedelta(days=30)
    tenants_por_vencer = Tenant.query.filter(
        Tenant.fecha_vencimiento <= fecha_limite,
        Tenant.fecha_vencimiento >= datetime.utcnow(),
        Tenant.activo == True
    ).order_by(Tenant.fecha_vencimiento).all()

    # Planes disponibles
    planes = Plan.query.filter_by(activo=True).order_by(Plan.precio_mensual).all()

    return render_template('superadmin/dashboard.html',
                           stats=stats,
                           tenants_recientes=tenants_recientes,
                           tenants_por_vencer=tenants_por_vencer,
                           planes=planes)


# ==================== USUARIOS (GLOBAL) ====================
@superadmin_bp.route('/usuarios')
@login_required
@superadmin_required
def usuarios():
    """Lista global de usuarios agrupados por tenant"""
    # Obtener todos los tenants con sus usuarios
    tenants = Tenant.query.order_by(Tenant.nombre).all()

    # Organizar usuarios por tenant
    usuarios_por_tenant = []
    for tenant in tenants:
        usuarios = Usuario.query.filter_by(tenant_id=tenant.id).order_by(Usuario.rol, Usuario.nombre).all()
        if usuarios:
            usuarios_por_tenant.append({
                'tenant': tenant,
                'usuarios': usuarios
            })

    # SuperAdmin (sin tenant)
    superadmins = Usuario.query.filter_by(rol='superadmin').all()

    # Totales
    total_usuarios = Usuario.query.count()

    return render_template('superadmin/usuarios/lista.html',
                           usuarios_por_tenant=usuarios_por_tenant,
                           superadmins=superadmins,
                           total_usuarios=total_usuarios)


# ==================== TENANTS ====================
@superadmin_bp.route('/tenants')
@login_required
@superadmin_required
def tenants():
    estado = request.args.get('estado', 'activos')
    plan_id = request.args.get('plan_id', type=int)

    query = Tenant.query

    if estado == 'activos':
        query = query.filter_by(activo=True)
    elif estado == 'inactivos':
        query = query.filter_by(activo=False)

    if plan_id:
        query = query.filter_by(plan_id=plan_id)

    tenants = query.order_by(Tenant.nombre).all()
    planes = Plan.query.filter_by(activo=True).all()

    return render_template('superadmin/tenants/lista.html',
                           tenants=tenants,
                           estado_filtro=estado,
                           plan_filtro=plan_id,
                           planes=planes)


@superadmin_bp.route('/tenants/nuevo', methods=['GET', 'POST'])
@login_required
@superadmin_required
def tenant_nuevo():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()

        # Generar slug unico
        slug = re.sub(r'[^a-z0-9]+', '-', nombre.lower()).strip('-')

        # Verificar slug unico
        base_slug = slug
        contador = 1
        while Tenant.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{contador}"
            contador += 1

        # Calcular fecha de vencimiento
        fecha_vencimiento = None
        if request.form.get('fecha_vencimiento'):
            fecha_vencimiento = datetime.strptime(request.form.get('fecha_vencimiento'), '%Y-%m-%d')

        tenant = Tenant(
            nombre=nombre,
            slug=slug,
            email_contacto=request.form.get('email_contacto', '').strip(),
            telefono=request.form.get('telefono', '').strip(),
            plan_id=request.form.get('plan_id', type=int),
            fecha_vencimiento=fecha_vencimiento,
            dia_envio_reportes=request.form.get('dia_envio_reportes', 28, type=int),
            activo=True
        )

        db.session.add(tenant)
        db.session.flush()  # Para obtener el ID

        # Crear usuario admin del tenant
        admin_email = request.form.get('admin_email', '').strip()
        admin_password = request.form.get('admin_password', '').strip()
        admin_nombre = request.form.get('admin_nombre', 'Administrador').strip()

        if admin_email and admin_password:
            # Verificar que el email no exista
            if Usuario.query.filter_by(email=admin_email).first():
                flash('El email del administrador ya esta en uso.', 'danger')
                db.session.rollback()
                planes = Plan.query.filter_by(activo=True).all()
                return render_template('superadmin/tenants/form.html', tenant=None, planes=planes)

            admin = Usuario(
                nombre=admin_nombre,
                email=admin_email,
                rol='admin',
                tenant_id=tenant.id,
                activo=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)

        # Crear tipos de equipo por defecto (sin commit, se hará después)
        TipoEquipo.crear_tipos_default(tenant.id, commit=False)

        db.session.commit()
        flash(f'Tenant "{nombre}" creado exitosamente.', 'success')
        return redirect(url_for('superadmin.tenant_ver', id=tenant.id))

    planes = Plan.query.filter_by(activo=True).all()
    return render_template('superadmin/tenants/form.html', tenant=None, planes=planes)


@superadmin_bp.route('/tenants/<int:id>')
@login_required
@superadmin_required
def tenant_ver(id):
    tenant = Tenant.query.get_or_404(id)

    # Estadisticas del tenant
    stats = tenant.get_estadisticas()

    # Usuarios del tenant
    usuarios = Usuario.query.filter_by(tenant_id=tenant.id).order_by(Usuario.rol, Usuario.nombre).all()

    return render_template('superadmin/tenants/ver.html',
                           tenant=tenant,
                           stats=stats,
                           usuarios=usuarios)


@superadmin_bp.route('/tenants/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@superadmin_required
def tenant_editar(id):
    tenant = Tenant.query.get_or_404(id)

    if request.method == 'POST':
        tenant.nombre = request.form.get('nombre', '').strip()
        tenant.email_contacto = request.form.get('email_contacto', '').strip()
        tenant.telefono = request.form.get('telefono', '').strip()
        tenant.plan_id = request.form.get('plan_id', type=int)
        tenant.activo = 'activo' in request.form
        tenant.dia_envio_reportes = request.form.get('dia_envio_reportes', 28, type=int)

        if request.form.get('fecha_vencimiento'):
            tenant.fecha_vencimiento = datetime.strptime(
                request.form.get('fecha_vencimiento'), '%Y-%m-%d'
            )
        else:
            tenant.fecha_vencimiento = None

        db.session.commit()
        flash('Tenant actualizado correctamente.', 'success')
        return redirect(url_for('superadmin.tenant_ver', id=tenant.id))

    planes = Plan.query.filter_by(activo=True).all()
    return render_template('superadmin/tenants/form.html', tenant=tenant, planes=planes)


@superadmin_bp.route('/tenants/<int:id>/toggle-activo', methods=['POST'])
@login_required
@superadmin_required
def tenant_toggle_activo(id):
    tenant = Tenant.query.get_or_404(id)
    tenant.activo = not tenant.activo
    db.session.commit()

    estado = 'activado' if tenant.activo else 'desactivado'
    flash(f'Tenant {estado} correctamente.', 'success')
    return redirect(url_for('superadmin.tenant_ver', id=id))


@superadmin_bp.route('/tenants/<int:id>/extender', methods=['POST'])
@login_required
@superadmin_required
def tenant_extender(id):
    tenant = Tenant.query.get_or_404(id)
    dias = request.form.get('dias', 30, type=int)

    if tenant.fecha_vencimiento and tenant.fecha_vencimiento > datetime.utcnow():
        tenant.fecha_vencimiento = tenant.fecha_vencimiento + timedelta(days=dias)
    else:
        tenant.fecha_vencimiento = datetime.utcnow() + timedelta(days=dias)

    db.session.commit()
    flash(f'Suscripcion extendida por {dias} dias.', 'success')
    return redirect(url_for('superadmin.tenant_ver', id=id))


@superadmin_bp.route('/tenants/<int:id>/backup')
@login_required
@superadmin_required
def tenant_backup(id):
    """Genera un backup JSON de todos los datos del tenant"""
    tenant = Tenant.query.get_or_404(id)

    def serialize_date(obj):
        if obj:
            return obj.isoformat()
        return None

    # Recopilar todos los datos
    backup_data = {
        'tenant': {
            'nombre': tenant.nombre,
            'slug': tenant.slug,
            'email_contacto': tenant.email_contacto,
            'telefono': tenant.telefono,
            'plan': tenant.plan.nombre if tenant.plan else None,
            'fecha_creacion': serialize_date(tenant.fecha_creacion),
            'fecha_vencimiento': serialize_date(tenant.fecha_vencimiento),
        },
        'usuarios': [],
        'tipos_equipo': [],
        'clientes': [],
        'ubicaciones': [],
        'equipos': [],
        'tickets': [],
        'ordenes': [],
        'mantenimientos': [],
    }

    # Usuarios
    for u in Usuario.query.filter_by(tenant_id=id).all():
        backup_data['usuarios'].append({
            'nombre': u.nombre,
            'email': u.email,
            'telefono': u.telefono,
            'rol': u.rol,
            'activo': u.activo,
            'fecha_registro': serialize_date(u.fecha_registro),
        })

    # Tipos de equipo
    for te in TipoEquipo.query.filter_by(tenant_id=id).all():
        backup_data['tipos_equipo'].append({
            'nombre': te.nombre,
            'icono': te.icono,
            'descripcion': te.descripcion,
            'activo': te.activo,
        })

    # Clientes
    for c in Cliente.query.filter_by(tenant_id=id).all():
        backup_data['clientes'].append({
            'id': c.id,
            'nombre': c.nombre,
            'rif': c.rif,
            'email': c.email,
            'persona_contacto': c.persona_contacto,
            'telefono_principal': c.telefono_principal,
            'activo': c.activo,
        })

    # Ubicaciones
    for ub in Ubicacion.query.filter_by(tenant_id=id).all():
        backup_data['ubicaciones'].append({
            'id': ub.id,
            'cliente_id': ub.cliente_id,
            'nombre': ub.nombre,
            'direccion': ub.direccion,
            'ciudad': ub.ciudad,
            'persona_contacto': ub.persona_contacto,
            'telefono': ub.telefono,
        })

    # Equipos
    for eq in Equipo.query.filter_by(tenant_id=id).all():
        backup_data['equipos'].append({
            'id': eq.id,
            'ubicacion_id': eq.ubicacion_id,
            'tipo': eq.tipo,
            'nombre': eq.nombre,
            'marca': eq.marca,
            'modelo': eq.modelo,
            'serial': eq.serial,
            'departamento': eq.departamento,
            'condicion': eq.condicion,
        })

    # Tickets
    for t in Ticket.query.filter_by(tenant_id=id).all():
        backup_data['tickets'].append({
            'id': t.id,
            'cliente_id': t.cliente_id,
            'equipo_id': t.equipo_id,
            'asunto': t.asunto,
            'descripcion': t.descripcion,
            'estado': t.estado,
            'prioridad': t.prioridad,
            'fecha_creacion': serialize_date(t.fecha_creacion),
        })

    # Ordenes de trabajo
    for o in OrdenTrabajo.query.filter_by(tenant_id=id).all():
        backup_data['ordenes'].append({
            'id': o.id,
            'numero': o.numero,
            'tipo': o.tipo,
            'descripcion_solicitud': o.descripcion_solicitud,
            'descripcion_trabajo': o.descripcion_trabajo,
            'estado': o.estado,
            'cliente_id': o.cliente_id,
            'ubicacion_id': o.ubicacion_id,
            'equipo_id': o.equipo_id,
            'fecha_creacion': serialize_date(o.fecha_creacion),
            'fecha_programada': serialize_date(o.fecha_programada),
            'fecha_fin': serialize_date(o.fecha_fin),
        })

    # Mantenimientos
    for m in Mantenimiento.query.filter_by(tenant_id=id).all():
        backup_data['mantenimientos'].append({
            'id': m.id,
            'nombre': m.nombre,
            'tipo': m.tipo,
            'descripcion': m.descripcion,
            'estado': m.estado,
            'fecha_programada': serialize_date(m.fecha_programada),
        })

    # Generar JSON y descargar
    json_data = json.dumps(backup_data, indent=2, ensure_ascii=False)
    filename = f"backup_{tenant.slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    return Response(
        json_data,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )


@superadmin_bp.route('/tenants/<int:id>/eliminar', methods=['POST'])
@login_required
@superadmin_required
def tenant_eliminar(id):
    """Elimina un tenant y todos sus datos"""
    tenant = Tenant.query.get_or_404(id)

    # Verificar confirmacion
    confirmacion = request.form.get('confirmacion', '')
    if confirmacion != tenant.slug:
        flash(f'Debes escribir "{tenant.slug}" para confirmar la eliminacion.', 'danger')
        return redirect(url_for('superadmin.tenant_ver', id=id))

    nombre_tenant = tenant.nombre

    try:
        # Eliminar en orden para respetar foreign keys
        # 1. Notificaciones
        Notificacion.query.filter_by(tenant_id=id).delete()

        # 2. Actividades de ordenes
        for orden in OrdenTrabajo.query.filter_by(tenant_id=id).all():
            OrdenActividad.query.filter_by(orden_id=orden.id).delete()
            FotoTrabajo.query.filter_by(orden_id=orden.id).delete()

        # 3. Mantenimientos de equipos
        for mant in Mantenimiento.query.filter_by(tenant_id=id).all():
            MantenimientoEquipo.query.filter_by(mantenimiento_id=mant.id).delete()

        # 4. Ordenes de trabajo
        OrdenTrabajo.query.filter_by(tenant_id=id).delete()

        # 5. Tickets
        Ticket.query.filter_by(tenant_id=id).delete()

        # 6. Mantenimientos
        Mantenimiento.query.filter_by(tenant_id=id).delete()

        # 7. Equipos
        Equipo.query.filter_by(tenant_id=id).delete()

        # 8. Ubicaciones
        Ubicacion.query.filter_by(tenant_id=id).delete()

        # 9. Clientes
        Cliente.query.filter_by(tenant_id=id).delete()

        # 10. Tipos de equipo
        TipoEquipo.query.filter_by(tenant_id=id).delete()

        # 11. Usuarios
        Usuario.query.filter_by(tenant_id=id).delete()

        # 12. Tenant
        db.session.delete(tenant)

        db.session.commit()
        flash(f'Tenant "{nombre_tenant}" y todos sus datos han sido eliminados.', 'success')
        return redirect(url_for('superadmin.tenants'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar tenant: {str(e)}', 'danger')
        return redirect(url_for('superadmin.tenant_ver', id=id))


# ==================== USUARIOS DE TENANT ====================
@superadmin_bp.route('/tenants/<int:tenant_id>/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@superadmin_required
def tenant_usuario_nuevo(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)

    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        # Verificar email unico
        if Usuario.query.filter_by(email=email).first():
            flash('El email ya esta en uso.', 'danger')
            return render_template('superadmin/tenants/usuario_form.html', tenant=tenant, usuario=None)

        usuario = Usuario(
            nombre=request.form.get('nombre', '').strip(),
            email=email,
            telefono=request.form.get('telefono', '').strip(),
            rol=request.form.get('rol'),
            tenant_id=tenant.id,
            activo=True
        )
        usuario.set_password(request.form.get('password', ''))

        db.session.add(usuario)
        db.session.commit()

        flash('Usuario creado correctamente.', 'success')
        return redirect(url_for('superadmin.tenant_ver', id=tenant.id))

    return render_template('superadmin/tenants/usuario_form.html', tenant=tenant, usuario=None)


# ==================== IMPERSONACION ====================
@superadmin_bp.route('/tenants/<int:id>/acceder')
@login_required
@superadmin_required
def acceder_como_tenant(id):
    """Permite al superadmin ver el sistema como si fuera un admin del tenant"""
    tenant = Tenant.query.get_or_404(id)
    session['impersonate_tenant_id'] = tenant.id
    session['impersonate_tenant_nombre'] = tenant.nombre
    flash(f'Ahora estas viendo el sistema como "{tenant.nombre}"', 'info')
    return redirect(url_for('admin.dashboard'))


@superadmin_bp.route('/salir-impersonacion')
@login_required
@superadmin_required
def salir_impersonacion():
    """Sale del modo impersonacion"""
    session.pop('impersonate_tenant_id', None)
    session.pop('impersonate_tenant_nombre', None)
    flash('Has salido del modo visualizacion de tenant.', 'info')
    return redirect(url_for('superadmin.dashboard'))


# ==================== PLANES ====================
@superadmin_bp.route('/planes')
@login_required
@superadmin_required
def planes():
    planes = Plan.query.order_by(Plan.precio_mensual).all()
    return render_template('superadmin/planes/lista.html', planes=planes)


@superadmin_bp.route('/planes/inicializar', methods=['POST'])
@login_required
@superadmin_required
def planes_inicializar():
    """Crea los planes predefinidos si no existen"""
    creados = 0
    for plan_data in PLANES_PREDEFINIDOS:
        if not Plan.query.filter_by(codigo=plan_data['codigo']).first():
            plan = Plan(**plan_data)
            db.session.add(plan)
            creados += 1

    db.session.commit()

    if creados > 0:
        flash(f'{creados} planes creados correctamente.', 'success')
    else:
        flash('Los planes ya estaban creados.', 'info')

    return redirect(url_for('superadmin.planes'))


@superadmin_bp.route('/planes/nuevo', methods=['GET', 'POST'])
@login_required
@superadmin_required
def plan_nuevo():
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip().lower()

        # Verificar codigo unico
        if Plan.query.filter_by(codigo=codigo).first():
            flash('El codigo del plan ya existe.', 'danger')
            return render_template('superadmin/planes/form.html', plan=None)

        plan = Plan(
            nombre=request.form.get('nombre', '').strip(),
            codigo=codigo,
            descripcion=request.form.get('descripcion', '').strip(),
            max_tecnicos=request.form.get('max_tecnicos', 3, type=int),
            max_clientes=request.form.get('max_clientes', 10, type=int),
            max_equipos=request.form.get('max_equipos', 100, type=int),
            max_usuarios_cliente=request.form.get('max_usuarios_cliente', 5, type=int),
            tiene_reportes='tiene_reportes' in request.form,
            tiene_api='tiene_api' in request.form,
            tiene_notificaciones_push='tiene_notificaciones_push' in request.form,
            tiene_exportacion_excel='tiene_exportacion_excel' in request.form,
            tiene_branding='tiene_branding' in request.form,
            precio_mensual=request.form.get('precio_mensual', 0, type=float),
            precio_anual=request.form.get('precio_anual', 0, type=float),
            activo=True
        )

        db.session.add(plan)
        db.session.commit()

        flash('Plan creado correctamente.', 'success')
        return redirect(url_for('superadmin.planes'))

    return render_template('superadmin/planes/form.html', plan=None)


@superadmin_bp.route('/planes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@superadmin_required
def plan_editar(id):
    plan = Plan.query.get_or_404(id)

    if request.method == 'POST':
        plan.nombre = request.form.get('nombre', '').strip()
        plan.descripcion = request.form.get('descripcion', '').strip()
        plan.max_tecnicos = request.form.get('max_tecnicos', 3, type=int)
        plan.max_clientes = request.form.get('max_clientes', 10, type=int)
        plan.max_equipos = request.form.get('max_equipos', 100, type=int)
        plan.max_usuarios_cliente = request.form.get('max_usuarios_cliente', 5, type=int)
        plan.tiene_reportes = 'tiene_reportes' in request.form
        plan.tiene_api = 'tiene_api' in request.form
        plan.tiene_notificaciones_push = 'tiene_notificaciones_push' in request.form
        plan.tiene_exportacion_excel = 'tiene_exportacion_excel' in request.form
        plan.tiene_branding = 'tiene_branding' in request.form
        plan.precio_mensual = request.form.get('precio_mensual', 0, type=float)
        plan.precio_anual = request.form.get('precio_anual', 0, type=float)
        plan.activo = 'activo' in request.form

        db.session.commit()
        flash('Plan actualizado correctamente.', 'success')
        return redirect(url_for('superadmin.planes'))

    return render_template('superadmin/planes/form.html', plan=plan)


@superadmin_bp.route('/planes/<int:id>/toggle-activo', methods=['POST'])
@login_required
@superadmin_required
def plan_toggle_activo(id):
    plan = Plan.query.get_or_404(id)

    # No desactivar si hay tenants usandolo
    if plan.activo:
        tenants_usando = Tenant.query.filter_by(plan_id=plan.id, activo=True).count()
        if tenants_usando > 0:
            flash(f'No se puede desactivar: {tenants_usando} tenant(s) estan usando este plan.', 'danger')
            return redirect(url_for('superadmin.planes'))

    plan.activo = not plan.activo
    db.session.commit()

    estado = 'activado' if plan.activo else 'desactivado'
    flash(f'Plan {estado}.', 'success')
    return redirect(url_for('superadmin.planes'))


# ==================== REPORTES GLOBALES ====================
@superadmin_bp.route('/reportes')
@login_required
@superadmin_required
def reportes():
    # Estadisticas por plan
    planes_stats = []
    for plan in Plan.query.filter_by(activo=True).all():
        tenants = Tenant.query.filter_by(plan_id=plan.id).all()
        planes_stats.append({
            'plan': plan,
            'total_tenants': len(tenants),
            'tenants_activos': len([t for t in tenants if t.activo]),
            'ingresos_potenciales': len([t for t in tenants if t.activo]) * float(plan.precio_mensual)
        })

    # Top tenants por uso
    top_tenants = []
    for tenant in Tenant.query.filter_by(activo=True).limit(10).all():
        stats = tenant.get_estadisticas()
        top_tenants.append({
            'tenant': tenant,
            'stats': stats
        })

    return render_template('superadmin/reportes.html',
                           planes_stats=planes_stats,
                           top_tenants=top_tenants)


# ==================== PLANTILLAS DE TIPOS DE EQUIPO ====================
@superadmin_bp.route('/plantillas')
@login_required
@superadmin_required
def plantillas():
    plantillas = PlantillaTipoEquipo.query.order_by(PlantillaTipoEquipo.orden).all()
    return render_template('superadmin/plantillas/lista.html', plantillas=plantillas)

@superadmin_bp.route('/plantillas/nueva', methods=['GET', 'POST'])
@login_required
@superadmin_required
def plantilla_nueva():
    if request.method == 'POST':
        # Generar codigo desde el nombre
        nombre = request.form.get('nombre', '').strip()
        codigo = re.sub(r'[^a-z0-9]+', '_', nombre.lower()).strip('_')

        # Verificar que el codigo no exista
        if PlantillaTipoEquipo.query.filter_by(codigo=codigo).first():
            flash('Ya existe una plantilla con ese nombre.', 'danger')
            return render_template('superadmin/plantillas/form.html', plantilla=None)

        max_orden = db.session.query(db.func.max(PlantillaTipoEquipo.orden)).scalar() or 0

        plantilla = PlantillaTipoEquipo(
            nombre=nombre,
            codigo=codigo,
            descripcion=request.form.get('descripcion', '').strip(),
            icono=request.form.get('icono', 'bi-grid'),
            orden=max_orden + 1
        )
        db.session.add(plantilla)
        db.session.commit()
        flash('Plantilla creada. Ahora agrega los tipos de equipo.', 'success')
        return redirect(url_for('superadmin.plantilla_editar', id=plantilla.id))

    return render_template('superadmin/plantillas/form.html', plantilla=None)

@superadmin_bp.route('/plantillas/<int:id>')
@login_required
@superadmin_required
def plantilla_ver(id):
    plantilla = PlantillaTipoEquipo.query.get_or_404(id)
    return render_template('superadmin/plantillas/ver.html', plantilla=plantilla)

@superadmin_bp.route('/plantillas/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@superadmin_required
def plantilla_editar(id):
    plantilla = PlantillaTipoEquipo.query.get_or_404(id)

    if request.method == 'POST':
        plantilla.nombre = request.form.get('nombre', '').strip()
        plantilla.descripcion = request.form.get('descripcion', '').strip()
        plantilla.icono = request.form.get('icono', 'bi-grid')
        plantilla.activo = 'activo' in request.form
        db.session.commit()
        flash('Plantilla actualizada.', 'success')
        return redirect(url_for('superadmin.plantillas'))

    return render_template('superadmin/plantillas/form.html', plantilla=plantilla)

@superadmin_bp.route('/plantillas/<int:id>/eliminar', methods=['POST'])
@login_required
@superadmin_required
def plantilla_eliminar(id):
    plantilla = PlantillaTipoEquipo.query.get_or_404(id)
    db.session.delete(plantilla)
    db.session.commit()
    flash('Plantilla eliminada.', 'success')
    return redirect(url_for('superadmin.plantillas'))

@superadmin_bp.route('/plantillas/<int:id>/item/nuevo', methods=['POST'])
@login_required
@superadmin_required
def plantilla_item_nuevo(id):
    plantilla = PlantillaTipoEquipo.query.get_or_404(id)

    max_orden = db.session.query(db.func.max(PlantillaTipoEquipoItem.orden)).filter_by(plantilla_id=id).scalar() or 0

    item = PlantillaTipoEquipoItem(
        plantilla_id=plantilla.id,
        nombre=request.form.get('nombre', '').strip(),
        icono=request.form.get('icono', 'bi-gear'),
        descripcion=request.form.get('descripcion', '').strip(),
        orden=max_orden + 1
    )
    db.session.add(item)
    db.session.commit()
    flash('Tipo agregado a la plantilla.', 'success')
    return redirect(url_for('superadmin.plantilla_ver', id=id))

@superadmin_bp.route('/plantillas/<int:id>/item/<int:item_id>/eliminar', methods=['POST'])
@login_required
@superadmin_required
def plantilla_item_eliminar(id, item_id):
    item = PlantillaTipoEquipoItem.query.get_or_404(item_id)
    if item.plantilla_id != id:
        flash('Item no pertenece a esta plantilla.', 'danger')
        return redirect(url_for('superadmin.plantilla_ver', id=id))

    db.session.delete(item)
    db.session.commit()
    flash('Tipo eliminado de la plantilla.', 'success')
    return redirect(url_for('superadmin.plantilla_ver', id=id))
