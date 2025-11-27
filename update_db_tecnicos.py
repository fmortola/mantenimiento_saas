#!/usr/bin/env python3
"""
Script para actualizar la base de datos agregando las nuevas tablas de asociación
para múltiples técnicos en tickets y órdenes de trabajo.

Ejecutar en el servidor con: python3 update_db_tecnicos.py
"""
from app import create_app, db
from app.models.usuario import Usuario
from app.models.ticket import Ticket, tecnicos_ticket
from app.models.orden_trabajo import OrdenTrabajo, tecnicos_orden

app = create_app()

with app.app_context():
    # Crear las nuevas tablas si no existen
    print("Creando tablas de asociación...")

    # Crear tabla tecnicos_ticket
    try:
        db.engine.execute('''
            CREATE TABLE IF NOT EXISTS tecnicos_ticket (
                tecnico_id INT NOT NULL,
                ticket_id INT NOT NULL,
                PRIMARY KEY (tecnico_id, ticket_id),
                FOREIGN KEY (tecnico_id) REFERENCES usuario(id),
                FOREIGN KEY (ticket_id) REFERENCES ticket(id)
            )
        ''')
        print("Tabla tecnicos_ticket creada o ya existía")
    except Exception as e:
        print(f"Error creando tecnicos_ticket: {e}")

    # Crear tabla tecnicos_orden
    try:
        db.engine.execute('''
            CREATE TABLE IF NOT EXISTS tecnicos_orden (
                tecnico_id INT NOT NULL,
                orden_id INT NOT NULL,
                PRIMARY KEY (tecnico_id, orden_id),
                FOREIGN KEY (tecnico_id) REFERENCES usuario(id),
                FOREIGN KEY (orden_id) REFERENCES orden_trabajo(id)
            )
        ''')
        print("Tabla tecnicos_orden creada o ya existía")
    except Exception as e:
        print(f"Error creando tecnicos_orden: {e}")

    # Migrar datos existentes
    print("\nMigrando asignaciones existentes...")

    # Migrar tickets con asignado_a_id
    tickets_con_tecnico = Ticket.query.filter(Ticket.asignado_a_id.isnot(None)).all()
    for ticket in tickets_con_tecnico:
        tecnico = Usuario.query.get(ticket.asignado_a_id)
        if tecnico and tecnico not in ticket.tecnicos.all():
            ticket.tecnicos.append(tecnico)
            print(f"  Ticket {ticket.numero}: agregado técnico {tecnico.nombre}")

    # Migrar órdenes con tecnico_id
    ordenes_con_tecnico = OrdenTrabajo.query.filter(OrdenTrabajo.tecnico_id.isnot(None)).all()
    for orden in ordenes_con_tecnico:
        tecnico = Usuario.query.get(orden.tecnico_id)
        if tecnico and tecnico not in orden.tecnicos.all():
            orden.tecnicos.append(tecnico)
            print(f"  Orden {orden.numero}: agregado técnico {tecnico.nombre}")

    db.session.commit()
    print("\nMigración completada exitosamente!")
