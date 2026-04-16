#!/usr/bin/env python
"""
Script para poblar la base de datos con datos iniciales
"""
import os
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nombre_proyecto.settings')
django.setup()

from django.contrib.auth.models import User
from tienda.models import Cliente, Categoria, Producto

def crear_usuarios_y_clientes():
    """Crear usuarios demo y administrador"""
    
    print("Creando usuarios...")
    
    # Admin
    if not User.objects.filter(username='admin@tierra.com').exists():
        admin = User.objects.create_superuser(
            username='admin@tierra.com',
            email='admin@tierra.com',
            password='admin123',
            first_name='Admin',
            last_name='Tierra'
        )
        print("✓ Admin creado: admin@tierra.com / admin123")
    else:
        print("✓ Admin ya existe")
    
    # Cliente demo
    if not User.objects.filter(username='cliente@test.com').exists():
        cliente_user = User.objects.create_user(
            username='cliente@test.com',
            email='cliente@test.com',
            password='123456',
            first_name='Juan',
            last_name='Cliente'
        )
        Cliente.objects.create(
            user=cliente_user,
            ciudad='Bogotá',
            telefono='3001234567'
        )
        print("✓ Cliente creado: cliente@test.com / 123456")
    else:
        print("✓ Cliente ya existe")

def crear_categorias():
    """Crear categorías de productos"""
    
    print("\nCreando categorías...")
    
    categorias_data = [
        {
            'nombre': 'Cerámica',
            'descripcion': 'Piezas de cerámica artesanal hecha a mano'
        },
        {
            'nombre': 'Textiles',
            'descripcion': 'Textiles y tejidos tradicion ales'
        },
        {
            'nombre': 'Decoración',
            'descripcion': 'Artículos de decoración para el hogar'
        },
    ]
    
    for cat_data in categorias_data:
        cat, created = Categoria.objects.get_or_create(**cat_data)
        if created:
            print(f"✓ Categoría creada: {cat.nombre}")
        else:
            print(f"✓ Categoría ya existe: {cat.nombre}")

def crear_productos():
    """Crear productos de ejemplo"""
    
    print("\nCreando productos...")
    
    categoria_ceramica = Categoria.objects.get(nombre='Cerámica')
    
    productos_data = [
        {
            'nombre': 'Cerámica Artesanal',
            'descripcion': 'Pieza única de cerámica hecha a mano con técnicas tradicionales.',
            'precio': Decimal('45000'),
            'categoria': categoria_ceramica,
            'cantidad_disponible': 5,
        },
        {
            'nombre': 'Jarrón Decorativo',
            'descripcion': 'Hermoso jarrón de cerámica con diseño exclusivo.',
            'precio': Decimal('65000'),
            'categoria': categoria_ceramica,
            'cantidad_disponible': 3,
        },
        {
            'nombre': 'Plato Artesanal',
            'descripcion': 'Plato decorativo hecho a mano, único y exclusivo.',
            'precio': Decimal('35000'),
            'categoria': categoria_ceramica,
            'cantidad_disponible': 8,
        },
        {
            'nombre': 'Maceta de Barro',
            'descripcion': 'Maceta artesanal de barro cocido, perfecta para plantas.',
            'precio': Decimal('28000'),
            'categoria': categoria_ceramica,
            'cantidad_disponible': 12,
        },
        {
            'nombre': 'Taza Personalizada',
            'descripcion': 'Taza de cerámica decorada a mano con motivos tradicionales.',
            'precio': Decimal('22000'),
            'categoria': categoria_ceramica,
            'cantidad_disponible': 15,
        },
        {
            'nombre': 'Escultura Cerámica',
            'descripcion': 'Escultura artística hecha en cerámica, pieza de colección.',
            'precio': Decimal('95000'),
            'categoria': categoria_ceramica,
            'cantidad_disponible': 2,
        },
    ]
    
    for prod_data in productos_data:
        producto, created = Producto.objects.get_or_create(
            nombre=prod_data['nombre'],
            defaults={
                'descripcion': prod_data['descripcion'],
                'precio': prod_data['precio'],
                'categoria': prod_data['categoria'],
                'cantidad_disponible': prod_data['cantidad_disponible'],
                'activo': True,
            }
        )
        if created:
            print(f"✓ Producto creado: {producto.nombre} - ${producto.precio}")
        else:
            print(f"✓ Producto ya existe: {producto.nombre}")

def main():
    print("=" * 50)
    print("Poblando base de datos de Tierra Artesana")
    print("=" * 50)
    
    crear_usuarios_y_clientes()
    crear_categorias()
    crear_productos()
    
    print("\n" + "=" * 50)
    print("✓ Base de datos poblada exitosamente")
    print("=" * 50)
    print("\nCredenciales para acceder:")
    print("  Admin: admin@tierra.com / admin123")
    print("  Cliente: cliente@test.com / 123456")

if __name__ == '__main__':
    main()
