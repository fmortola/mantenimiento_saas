"""
Comandos CLI para tareas programadas (cron)
"""
import click
from flask.cli import with_appcontext


@click.command('enviar-reportes')
@with_appcontext
def enviar_reportes_command():
    """Envía reportes mensuales a los clientes"""
    from app.services.reportes_mensuales import ejecutar_envio_reportes

    click.echo('Iniciando envío de reportes mensuales...')
    resultados = ejecutar_envio_reportes()

    for r in resultados:
        click.echo(f"  Tenant: {r['tenant']}")
        click.echo(f"    - Clientes procesados: {r['clientes_procesados']}")
        click.echo(f"    - Clientes con actividad: {r['clientes_con_actividad']}")

    click.echo('Proceso completado.')


@click.command('test-reporte')
@click.argument('cliente_id', type=int)
@with_appcontext
def test_reporte_command(cliente_id):
    """Genera un reporte de prueba para un cliente específico"""
    from app.models.cliente import Cliente
    from app.services.reportes_mensuales import (
        obtener_rango_mes_anterior,
        obtener_actividad_cliente,
        generar_pdf_reporte_mensual,
        enviar_email_reporte
    )

    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        click.echo(f'Error: Cliente {cliente_id} no encontrado')
        return

    click.echo(f'Generando reporte para: {cliente.nombre}')

    fecha_inicio, fecha_fin = obtener_rango_mes_anterior()
    click.echo(f'Período: {fecha_inicio.strftime("%d/%m/%Y")} - {fecha_fin.strftime("%d/%m/%Y")}')

    actividad = obtener_actividad_cliente(cliente, fecha_inicio, fecha_fin)
    click.echo(f'Órdenes: {len(actividad["ordenes"])}')
    click.echo(f'Mantenimientos: {len(actividad["mantenimientos"])}')
    click.echo(f'Tickets: {len(actividad["tickets"])}')

    pdf_path = generar_pdf_reporte_mensual(cliente, fecha_inicio, fecha_fin, actividad)
    click.echo(f'PDF generado: {pdf_path}')

    if cliente.email_reportes:
        if click.confirm(f'¿Enviar email a {cliente.email_reportes}?'):
            enviar_email_reporte(cliente, pdf_path, fecha_inicio, fecha_fin)
            click.echo('Email enviado')
    else:
        click.echo('Cliente no tiene email de reportes configurado')


def init_app(app):
    """Registra los comandos en la aplicación Flask"""
    app.cli.add_command(enviar_reportes_command)
    app.cli.add_command(test_reporte_command)
