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
        print(f"[NOTIF] Notificación guardada en BD para usuario {usuario.id}")

        # Verificar VAPID keys
        vapid_private = current_app.config.get('VAPID_PRIVATE_KEY', '')
        if not vapid_private:
            print("[NOTIF] ERROR: VAPID_PRIVATE_KEY no configurada")
            return False

        # Obtener suscripciones del usuario
        subscriptions = PushSubscription.query.filter_by(usuario_id=usuario.id).all()
        print(f"[NOTIF] Usuario {usuario.id} tiene {len(subscriptions)} suscripciones push")

        for sub in subscriptions:
            try:
                print(f"[NOTIF] Enviando push a endpoint: {sub.endpoint[:50]}...")
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
                print(f"[NOTIF] Push enviado exitosamente")
            except WebPushException as e:
                print(f"[NOTIF] WebPushException: {e}")
                # Si la suscripción ya no es válida, eliminarla
                if e.response and e.response.status_code in [404, 410]:
                    print(f"[NOTIF] Suscripción inválida, eliminando...")
                    db.session.delete(sub)
                    db.session.commit()
            except Exception as e:
                print(f"[NOTIF] Error enviando push: {e}")

        return True
    except Exception as e:
        print(f"[NOTIF] Error en notificación push: {e}")
        return False

def notificar_admins(titulo, mensaje, url=None, tenant_id=None):
    """Enviar notificación a administradores del tenant"""
    query = Usuario.query.filter_by(rol='admin', activo=True)
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    admins = query.all()
    print(f"[NOTIF] Notificando a {len(admins)} admins (tenant_id={tenant_id})")
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
