#!/usr/bin/env python3
from app import create_app, db
from app.models.usuario import Usuario

app = create_app()
with app.app_context():
    usuarios = Usuario.query.all()
    print('ID | Nombre | Email | Rol | Activo')
    print('-' * 70)
    for u in usuarios:
        print(f'{u.id} | {u.nombre} | {u.email} | {u.rol} | {u.activo}')
