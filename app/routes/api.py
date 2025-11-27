from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from app import db, csrf
from app.models.notificacion import PushSubscription, Notificacion
from app.models.orden_trabajo import OrdenTrabajo, FotoTrabajo
from app.models.mantenimiento import Mantenimiento, MantenimientoEquipo
from app.models.equipo import Equipo
from app.services.pdf_generator import generar_pdf_orden, generar_pdf_mantenimiento
from datetime import datetime
import os
import uuid
import base64

api_bp = Blueprint('api', __name__)

# ==================== PUSH NOTIFICATIONS ====================
@api_bp.route('/push/subscribe', methods=['POST'])
@csrf.exempt
@login_required
def push_subscribe():
    """Registrar suscripción para notificaciones push"""
    data = request.get_json()

    print(f"[PUSH] Datos recibidos: {data}")

    if not data or 'endpoint' not in data:
        print(f"[PUSH] Error: datos inválidos o sin endpoint")
        return jsonify({'error': 'Datos inválidos'}), 400

    if 'keys' not in data or 'p256dh' not in data.get('keys', {}) or 'auth' not in data.get('keys', {}):
        print(f"[PUSH] Error: faltan keys")
        return jsonify({'error': 'Faltan keys de suscripción'}), 400

    # Verificar si ya existe esta suscripción
    existing = PushSubscription.query.filter_by(
        usuario_id=current_user.id,
        endpoint=data['endpoint']
    ).first()

    if existing:
        return jsonify({'success': True, 'message': 'Ya suscrito'})

    subscription = PushSubscription(
        usuario_id=current_user.id,
        endpoint=data['endpoint'],
        p256dh=data['keys']['p256dh'],
        auth=data['keys']['auth']
    )
    db.session.add(subscription)
    db.session.commit()

    # Enviar notificación de confirmación
    try:
        from pywebpush import webpush
        import json

        webpush(
            subscription_info={
                "endpoint": data['endpoint'],
                "keys": {
                    "p256dh": data['keys']['p256dh'],
                    "auth": data['keys']['auth']
                }
            },
            data=json.dumps({
                "title": "Notificaciones Activadas",
                "body": "Recibirás alertas de tickets, órdenes y mantenimientos",
                "icon": "/static/images/icon-192.png"
            }),
            vapid_private_key=current_app.config['VAPID_PRIVATE_KEY'],
            vapid_claims=current_app.config['VAPID_CLAIMS']
        )
    except Exception as e:
        print(f"Error enviando notificación de bienvenida: {e}")

    return jsonify({'success': True})

@api_bp.route('/push/unsubscribe', methods=['POST'])
@login_required
def push_unsubscribe():
    """Cancelar suscripción de notificaciones push"""
    data = request.get_json()

    if not data or 'endpoint' not in data:
        return jsonify({'error': 'Datos inválidos'}), 400

    subscription = PushSubscription.query.filter_by(
        usuario_id=current_user.id,
        endpoint=data['endpoint']
    ).first()

    if subscription:
        db.session.delete(subscription)
        db.session.commit()

    return jsonify({'success': True})

@api_bp.route('/push/vapid-public-key')
def vapid_public_key():
    """Obtener clave pública VAPID"""
    return jsonify({'publicKey': current_app.config['VAPID_PUBLIC_KEY']})

# ==================== NOTIFICACIONES ====================
@api_bp.route('/notificaciones')
@login_required
def obtener_notificaciones():
    """Obtener notificaciones del usuario"""
    notificaciones = Notificacion.query.filter_by(
        usuario_id=current_user.id
    ).order_by(Notificacion.fecha_creacion.desc()).limit(20).all()

    no_leidas = Notificacion.query.filter_by(
        usuario_id=current_user.id,
        leida=False
    ).count()

    return jsonify({
        'notificaciones': [{
            'id': n.id,
            'titulo': n.titulo,
            'mensaje': n.mensaje,
            'tipo': n.tipo,
            'leida': n.leida,
            'fecha': n.fecha_creacion.isoformat(),
            'url': n.url
        } for n in notificaciones],
        'no_leidas': no_leidas
    })

@api_bp.route('/notificaciones/marcar-leidas', methods=['POST'])
@csrf.exempt
@login_required
def marcar_notificaciones_leidas():
    """Marcar todas las notificaciones como leídas"""
    Notificacion.query.filter_by(
        usuario_id=current_user.id,
        leida=False
    ).update({'leida': True, 'fecha_lectura': datetime.utcnow()})
    db.session.commit()
    return jsonify({'success': True})

# ==================== FOTOS ====================
@api_bp.route('/foto/subir', methods=['POST'])
@login_required
@csrf.exempt
def subir_foto():
    """Subir foto desde cámara del celular (base64)"""
    data = request.get_json()

    if not data or 'imagen' not in data:
        return jsonify({'error': 'No se recibió ninguna imagen'}), 400

    try:
        # Decodificar imagen base64
        imagen_data = data['imagen']
        if ',' in imagen_data:
            imagen_data = imagen_data.split(',')[1]

        imagen_bytes = base64.b64decode(imagen_data)

        # Generar nombre único
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Guardar archivo
        with open(filepath, 'wb') as f:
            f.write(imagen_bytes)

        # Si se especifica orden de trabajo
        if 'orden_id' in data:
            foto = FotoTrabajo(
                ruta=filename,
                descripcion=data.get('descripcion', ''),
                tipo=data.get('tipo', 'durante'),
                orden_trabajo_id=data['orden_id']
            )
            db.session.add(foto)
            db.session.commit()

        # Si se especifica mantenimiento de equipo
        elif 'mantenimiento_equipo_id' in data:
            foto = FotoTrabajo(
                ruta=filename,
                descripcion=data.get('descripcion', ''),
                tipo=data.get('tipo', 'despues'),
                mantenimiento_equipo_id=data['mantenimiento_equipo_id']
            )
            db.session.add(foto)
            db.session.commit()

        return jsonify({
            'success': True,
            'filename': filename,
            'url': f'/static/images/uploads/{filename}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/foto/subir-mantenimiento', methods=['POST'])
@login_required
@csrf.exempt
def subir_foto_mantenimiento():
    """Subir foto para mantenimiento (base64)"""
    data = request.get_json()

    if not data or 'imagen' not in data:
        return jsonify({'error': 'No se recibió ninguna imagen'}), 400

    try:
        # Decodificar imagen base64
        imagen_data = data['imagen']
        if ',' in imagen_data:
            imagen_data = imagen_data.split(',')[1]

        imagen_bytes = base64.b64decode(imagen_data)

        # Generar nombre único
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Guardar archivo
        with open(filepath, 'wb') as f:
            f.write(imagen_bytes)

        return jsonify({
            'success': True,
            'filename': filename,
            'url': f'/static/images/uploads/{filename}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/foto/subir-archivo', methods=['POST'])
@login_required
def subir_foto_archivo():
    """Subir foto como archivo"""
    if 'foto' not in request.files:
        return jsonify({'error': 'No se recibió ningún archivo'}), 400

    foto = request.files['foto']
    if foto.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400

    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    foto.save(filepath)

    # Si se especifica orden de trabajo
    orden_id = request.form.get('orden_id')
    if orden_id:
        foto_trabajo = FotoTrabajo(
            ruta=filename,
            descripcion=request.form.get('descripcion', ''),
            tipo=request.form.get('tipo', 'durante'),
            orden_trabajo_id=orden_id
        )
        db.session.add(foto_trabajo)
        db.session.commit()

    # Si se especifica mantenimiento de equipo
    mant_equipo_id = request.form.get('mantenimiento_equipo_id')
    if mant_equipo_id:
        foto_trabajo = FotoTrabajo(
            ruta=filename,
            descripcion=request.form.get('descripcion', ''),
            tipo=request.form.get('tipo', 'despues'),
            mantenimiento_equipo_id=mant_equipo_id
        )
        db.session.add(foto_trabajo)
        db.session.commit()

    return jsonify({
        'success': True,
        'filename': filename,
        'url': f'/static/images/uploads/{filename}'
    })

# ==================== PDF ====================
@api_bp.route('/pdf/orden/<int:id>')
@login_required
def pdf_orden(id):
    """Generar PDF de orden de trabajo"""
    orden = OrdenTrabajo.query.get_or_404(id)

    # Verificar acceso
    if current_user.es_tecnico() and current_user not in orden.tecnicos.all():
        return jsonify({'error': 'Sin acceso'}), 403
    if current_user.es_cliente() and orden.cliente_id != current_user.cliente_id:
        return jsonify({'error': 'Sin acceso'}), 403

    pdf_path = generar_pdf_orden(orden)
    return send_file(pdf_path, as_attachment=True, download_name=f'orden_{orden.numero}.pdf')

@api_bp.route('/pdf/mantenimiento/<int:id>')
@login_required
def pdf_mantenimiento(id):
    """Generar PDF de mantenimiento"""
    mantenimiento = Mantenimiento.query.get_or_404(id)

    # Verificar acceso
    if current_user.es_cliente() and mantenimiento.cliente_id != current_user.cliente_id:
        return jsonify({'error': 'Sin acceso'}), 403

    pdf_path = generar_pdf_mantenimiento(mantenimiento)
    return send_file(pdf_path, as_attachment=True, download_name=f'mantenimiento_{mantenimiento.numero}.pdf')

# ==================== ESTADÍSTICAS ====================
@api_bp.route('/stats/dashboard')
@login_required
def stats_dashboard():
    """Estadísticas para el dashboard (admin)"""
    if not current_user.es_admin():
        return jsonify({'error': 'Sin acceso'}), 403

    from app.models.cliente import Cliente
    from app.models.usuario import Usuario
    from app.models.ticket import Ticket

    stats = {
        'clientes': Cliente.query.filter_by(activo=True).count(),
        'tecnicos': Usuario.query.filter_by(rol='tecnico', activo=True).count(),
        'equipos': Equipo.query.filter_by(activo=True).count(),
        'tickets_abiertos': Ticket.query.filter(Ticket.estado.in_(['abierto', 'asignado'])).count(),
        'ordenes_pendientes': OrdenTrabajo.query.filter(
            OrdenTrabajo.estado.in_(['pendiente', 'asignado', 'en_progreso'])).count(),
        'mantenimientos_activos': Mantenimiento.query.filter(
            Mantenimiento.estado.in_(['programado', 'en_progreso'])).count()
    }

    return jsonify(stats)

@api_bp.route('/mantenimiento/<int:id>/progreso')
@login_required
def mantenimiento_progreso(id):
    """Obtener progreso de un mantenimiento"""
    mantenimiento = Mantenimiento.query.get_or_404(id)

    total = mantenimiento.equipos_mantenimiento.count()
    completados = mantenimiento.equipos_con_mantenimiento()
    en_progreso = mantenimiento.equipos_en_progreso()
    pendientes = mantenimiento.equipos_pendientes()

    return jsonify({
        'total': total,
        'completados': completados,
        'en_progreso': en_progreso,
        'pendientes': pendientes,
        'porcentaje': mantenimiento.progreso_porcentaje()
    })
