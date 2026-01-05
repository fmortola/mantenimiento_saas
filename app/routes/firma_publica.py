"""
Rutas públicas para firma remota de clientes.
No requieren autenticación, usan tokens únicos.
"""
from flask import Blueprint, render_template, request, jsonify, abort
from app import db, csrf
from app.models.orden_trabajo import OrdenTrabajo
from app.models.mantenimiento import Mantenimiento
from app.services.notificaciones import notificar_admins
from datetime import datetime

firma_publica_bp = Blueprint('firma_publica', __name__)


@firma_publica_bp.route('/firmar/orden/<token>')
def firmar_orden(token):
    """Página pública para firmar una orden de trabajo"""
    orden = OrdenTrabajo.query.filter_by(firma_token=token).first()

    if not orden:
        abort(404)

    # Verificar que está pendiente de firma
    if orden.firma_estado != 'pendiente':
        return render_template('firma_publica/ya_firmado.html',
                             tipo='orden',
                             numero=orden.numero,
                             firma_fecha=orden.firma_fecha)

    return render_template('firma_publica/firmar.html',
                         tipo='orden',
                         item=orden,
                         token=token)


@firma_publica_bp.route('/firmar/orden/<token>/guardar', methods=['POST'])
@csrf.exempt
def guardar_firma_orden(token):
    """Guardar la firma de una orden"""
    orden = OrdenTrabajo.query.filter_by(firma_token=token).first()

    if not orden:
        return jsonify({'error': 'Token inválido'}), 404

    if orden.firma_estado != 'pendiente':
        return jsonify({'error': 'Esta orden ya fue firmada'}), 400

    data = request.get_json()
    firma_data = data.get('firma_data')
    firma_nombre = data.get('firma_nombre')

    if not firma_data or not firma_nombre:
        return jsonify({'error': 'Faltan datos de firma'}), 400

    # Guardar firma
    orden.firma_cliente = firma_data
    orden.firma_nombre = firma_nombre
    orden.firma_fecha = datetime.utcnow()
    orden.firma_estado = 'firmado'
    orden.estado = 'completado'

    db.session.commit()

    # Notificar a administradores
    notificar_admins(
        'Firma Recibida',
        f'El cliente ha firmado remotamente la orden {orden.numero}',
        f'/admin/ordenes/{orden.id}',
        tenant_id=orden.tenant_id
    )

    return jsonify({'success': True, 'message': 'Firma guardada correctamente'})


@firma_publica_bp.route('/firmar/mantenimiento/<token>')
def firmar_mantenimiento(token):
    """Página pública para firmar un mantenimiento"""
    mant = Mantenimiento.query.filter_by(firma_token=token).first()

    if not mant:
        abort(404)

    # Verificar que está pendiente de firma
    if mant.firma_estado != 'pendiente':
        return render_template('firma_publica/ya_firmado.html',
                             tipo='mantenimiento',
                             numero=mant.numero,
                             firma_fecha=mant.firma_fecha)

    return render_template('firma_publica/firmar.html',
                         tipo='mantenimiento',
                         item=mant,
                         token=token)


@firma_publica_bp.route('/firmar/mantenimiento/<token>/guardar', methods=['POST'])
@csrf.exempt
def guardar_firma_mantenimiento(token):
    """Guardar la firma de un mantenimiento"""
    mant = Mantenimiento.query.filter_by(firma_token=token).first()

    if not mant:
        return jsonify({'error': 'Token inválido'}), 404

    if mant.firma_estado != 'pendiente':
        return jsonify({'error': 'Este mantenimiento ya fue firmado'}), 400

    data = request.get_json()
    firma_data = data.get('firma_data')
    firma_nombre = data.get('firma_nombre')

    if not firma_data or not firma_nombre:
        return jsonify({'error': 'Faltan datos de firma'}), 400

    # Guardar firma
    mant.firma_cliente = firma_data
    mant.firma_nombre = firma_nombre
    mant.firma_fecha = datetime.utcnow()
    mant.firma_estado = 'firmado'
    mant.estado = 'completado'

    db.session.commit()

    # Notificar a administradores
    notificar_admins(
        'Firma Recibida',
        f'El cliente ha firmado remotamente el mantenimiento {mant.numero}',
        f'/admin/mantenimientos/{mant.id}',
        tenant_id=mant.tenant_id
    )

    return jsonify({'success': True, 'message': 'Firma guardada correctamente'})
