from flask import current_app
from app import db
from app.models.notificacion import PushSubscription, Notificacion
from app.models.usuario import Usuario
import json

def enviar_notificacion_push(usuario, titulo, mensaje, url=None):
    """Enviar notificación push a un usuario específico"""
    try:
        from pywebpush import webpush, WebPushException

        # Guardar notificación en BD
        notificacion = Notificacion(
            usuario_id=usuario.id,
            titulo=titulo,
            mensaje=mensaje,
            url=url
        )
        db.session.add(notificacion)
        db.session.commit()

        # Obtener suscripciones del usuario
        subscriptions = PushSubscription.query.filter_by(usuario_id=usuario.id).all()

        for sub in subscriptions:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub.endpoint,
                        "keys": {
                            "p256dh": sub.p256dh,
                            "auth": sub.auth
                        }
                    },
                    data=json.dumps({
                        "title": titulo,
                        "body": mensaje,
                        "url": url,
                        "icon": "/static/images/icon-192.png"
                    }),
                    vapid_private_key=current_app.config['VAPID_PRIVATE_KEY'],
                    vapid_claims=current_app.config['VAPID_CLAIMS']
                )
            except WebPushException as e:
                # Si la suscripción ya no es válida, eliminarla
                if e.response and e.response.status_code in [404, 410]:
                    db.session.delete(sub)
                    db.session.commit()
            except Exception as e:
                print(f"Error enviando push: {e}")

        return True
    except Exception as e:
        print(f"Error en notificación push: {e}")
        return False

def notificar_admins(titulo, mensaje, url=None):
    """Enviar notificación a todos los administradores"""
    admins = Usuario.query.filter_by(rol='admin', activo=True).all()
    for admin in admins:
        enviar_notificacion_push(admin, titulo, mensaje, url)

def crear_notificacion(usuario_id, titulo, mensaje, tipo=None, url=None):
    """Crear solo notificación en BD (sin push)"""
    notificacion = Notificacion(
        usuario_id=usuario_id,
        titulo=titulo,
        mensaje=mensaje,
        tipo=tipo,
        url=url
    )
    db.session.add(notificacion)
    db.session.commit()
    return notificacion

def notificar_cliente(cliente, titulo, mensaje, url=None):
    """Enviar notificación push a todos los usuarios de un cliente"""
    for usuario in cliente.usuarios:
        if usuario.activo:
            enviar_notificacion_push(usuario, titulo, mensaje, url)

def notificar_tecnicos(tecnicos, titulo, mensaje, url=None):
    """Enviar notificación push a una lista de técnicos"""
    for tecnico in tecnicos:
        if tecnico.activo:
            enviar_notificacion_push(tecnico, titulo, mensaje, url)
