#!/usr/bin/env python3
"""
Genera iconos para PWA usando Pillow
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    # Crear imagen con fondo azul
    img = Image.new('RGB', (size, size), '#2563eb')
    draw = ImageDraw.Draw(img)

    # Dibujar símbolo de herramienta simple
    center = size // 2
    margin = size // 4

    # Dibujar círculo blanco
    draw.ellipse([margin, margin, size - margin, size - margin], fill='white')

    # Dibujar llave/herramienta en el centro (símbolo simple)
    tool_margin = size // 3
    draw.rectangle([tool_margin, center - size//20, size - tool_margin, center + size//20], fill='#2563eb')
    draw.rectangle([center - size//20, tool_margin, center + size//20, size - tool_margin], fill='#2563eb')

    # Guardar
    img.save(output_path, 'PNG')
    print(f"Creado: {output_path}")

def main():
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    output_dir = 'app/static/images'

    os.makedirs(output_dir, exist_ok=True)

    for size in sizes:
        output_path = os.path.join(output_dir, f'icon-{size}.png')
        create_icon(size, output_path)

    # Badge para notificaciones
    create_icon(72, os.path.join(output_dir, 'badge-72.png'))

    print("\n¡Iconos generados correctamente!")

if __name__ == '__main__':
    main()
