from flask_login import current_user
from flask import session

from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.models.ubicacion import Ubicacion
from app.models.equipo import Equipo
from app.models.orden_trabajo import OrdenTrabajo
from app.models.ticket import Ticket
from app.models.mantenimiento import Mantenimiento


def _get_tenant_id():
    """Obtiene el tenant_id aplicable para las queries"""
    if not current_user.is_authenticated:
        return None

    # Si es superadmin impersonando
    if current_user.es_superadmin():
        return session.get('impersonate_tenant_id')

    return current_user.tenant_id


def get_clientes_query():
    """Retorna query de clientes filtrada por tenant"""
    tenant_id = _get_tenant_id()

    if current_user.es_superadmin() and not tenant_id:
        # SuperAdmin sin impersonacion ve todos
        return Cliente.query

    return Cliente.query.filter_by(tenant_id=tenant_id)


def get_tecnicos_query():
    """Retorna query de tecnicos filtrada por tenant"""
    tenant_id = _get_tenant_id()

    if current_user.es_superadmin() and not tenant_id:
        return Usuario.query.filter_by(rol='tecnico')

    return Usuario.query.filter_by(rol='tecnico', tenant_id=tenant_id)


def get_admins_query():
    """Retorna query de admins filtrada por tenant"""
    tenant_id = _get_tenant_id()

    if current_user.es_superadmin() and not tenant_id:
        return Usuario.query.filter_by(rol='admin')

    return Usuario.query.filter_by(rol='admin', tenant_id=tenant_id)


def get_usuarios_query():
    """Retorna query de usuarios (no superadmin) filtrada por tenant"""
    tenant_id = _get_tenant_id()

    if current_user.es_superadmin() and not tenant_id:
        return Usuario.query.filter(Usuario.rol != 'superadmin')

    return Usuario.query.filter_by(tenant_id=tenant_id)


def get_ubicaciones_query():
    """Retorna query de ubicaciones filtrada por tenant"""
    tenant_id = _get_tenant_id()

    if current_user.es_superadmin() and not tenant_id:
        return Ubicacion.query

    return Ubicacion.query.filter_by(tenant_id=tenant_id)


def get_equipos_query():
    """Retorna query de equipos filtrada por tenant"""
    tenant_id = _get_tenant_id()

    if current_user.es_superadmin() and not tenant_id:
        return Equipo.query

    return Equipo.query.filter_by(tenant_id=tenant_id)


def get_ordenes_query():
    """Retorna query de ordenes de trabajo filtrada por tenant"""
    tenant_id = _get_tenant_id()

    if current_user.es_superadmin() and not tenant_id:
        return OrdenTrabajo.query

    return OrdenTrabajo.query.filter_by(tenant_id=tenant_id)


def get_tickets_query():
    """Retorna query de tickets filtrada por tenant"""
    tenant_id = _get_tenant_id()

    if current_user.es_superadmin() and not tenant_id:
        return Ticket.query

    return Ticket.query.filter_by(tenant_id=tenant_id)


def get_mantenimientos_query():
    """Retorna query de mantenimientos filtrada por tenant"""
    tenant_id = _get_tenant_id()

    if current_user.es_superadmin() and not tenant_id:
        return Mantenimiento.query

    return Mantenimiento.query.filter_by(tenant_id=tenant_id)
