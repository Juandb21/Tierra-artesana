#!/usr/bin/env python
"""
Script para sincronizar los 32 departamentos de Colombia y todos sus municipios.

Fuente: API Colombia (https://api-colombia.com/)
"""
import json
import os
import unicodedata
import urllib.error
import urllib.request

import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nombre_proyecto.settings')
django.setup()

from tienda.models import Departamento, Municipio

API_BASE = "https://api-colombia.com/api/v1"

DEPARTAMENTOS_OFICIALES_32 = [
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bolívar", "Boyacá", "Caldas",
    "Caquetá", "Casanare", "Cauca", "Cesar", "Chocó", "Córdoba", "Cundinamarca",
    "Guainía", "Guaviare", "Huila", "La Guajira", "Magdalena", "Meta", "Nariño",
    "Norte de Santander", "Putumayo", "Quindío", "Risaralda", "San Andrés y Providencia",
    "Santander", "Sucre", "Tolima", "Valle del Cauca", "Vaupés", "Vichada",
]


def normalizar(texto):
    texto = texto.strip().lower()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    texto = ' '.join(texto.split())
    return texto


DEPT_OFICIAL_MAP = {normalizar(nombre): nombre for nombre in DEPARTAMENTOS_OFICIALES_32}
ALIAS_DEPARTAMENTOS = {
    'archipielago de san andres, providencia y santa catalina': 'San Andrés y Providencia',
    'san andres, providencia y santa catalina': 'San Andrés y Providencia',
    'san andres y providencia': 'San Andrés y Providencia',
}


def obtener_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'TierraArtesana/1.0'})
    with urllib.request.urlopen(req, timeout=30) as respuesta:
        return json.loads(respuesta.read().decode('utf-8'))


def extraer_nombre(item):
    if isinstance(item, str):
        return item.strip()
    for key in ('name', 'nombre', 'city', 'municipio'):
        value = item.get(key)
        if value:
            return str(value).strip()
    return ''


def nombre_oficial_departamento(nombre_api):
    nombre_norm = normalizar(nombre_api)
    if nombre_norm in ALIAS_DEPARTAMENTOS:
        return ALIAS_DEPARTAMENTOS[nombre_norm]
    return DEPT_OFICIAL_MAP.get(nombre_norm)


def construir_catalogo():
    departamentos_api = obtener_json(f"{API_BASE}/Department")
    catalogo = {nombre: [] for nombre in DEPARTAMENTOS_OFICIALES_32}

    for dept in departamentos_api:
        nombre_api = extraer_nombre(dept)
        nombre_oficial = nombre_oficial_departamento(nombre_api)
        if not nombre_oficial:
            continue

        dept_id = dept.get('id')
        if not dept_id:
            continue

        try:
            ciudades = obtener_json(f"{API_BASE}/Department/{dept_id}/cities")
        except urllib.error.HTTPError:
            ciudades = obtener_json(f"{API_BASE}/department/{dept_id}/cities")

        municipios = []
        for ciudad in ciudades:
            nombre_ciudad = extraer_nombre(ciudad)
            if nombre_ciudad:
                municipios.append(nombre_ciudad)

        # Quitar duplicados preservando orden
        vistos = set()
        unicos = []
        for municipio in municipios:
            key = normalizar(municipio)
            if key in vistos:
                continue
            vistos.add(key)
            unicos.append(municipio)

        catalogo[nombre_oficial] = sorted(unicos)

    faltantes = [d for d in DEPARTAMENTOS_OFICIALES_32 if not catalogo[d]]
    if faltantes:
        raise RuntimeError(
            f"No se pudieron obtener municipios para: {', '.join(faltantes)}"
        )

    total_municipios = sum(len(m) for m in catalogo.values())
    if len(catalogo) != 32:
        raise RuntimeError("El catálogo no contiene exactamente 32 departamentos")
    if total_municipios < 1100:
        raise RuntimeError(
            f"Cantidad inesperada de municipios ({total_municipios})."
        )

    return catalogo


@transaction.atomic
def guardar_catalogo(catalogo):
    Municipio.objects.all().delete()
    Departamento.objects.all().delete()

    departamentos_creados = {}
    for idx, nombre in enumerate(DEPARTAMENTOS_OFICIALES_32, start=1):
        dept = Departamento.objects.create(
            nombre=nombre,
            codigo=f"D{idx:02d}",
        )
        departamentos_creados[nombre] = dept

    municipios_bulk = []
    for nombre_dept, municipios in catalogo.items():
        dept = departamentos_creados[nombre_dept]
        for municipio in municipios:
            municipios_bulk.append(
                Municipio(
                    nombre=municipio,
                    departamento=dept,
                    costo_envio=15000,
                )
            )

    Municipio.objects.bulk_create(municipios_bulk, batch_size=500)


def crear_departamentos_y_municipios():
    print('=' * 60)
    print('Sincronizando departamentos y municipios de Colombia')
    print('=' * 60)

    catalogo = construir_catalogo()
    guardar_catalogo(catalogo)

    total_dept = Departamento.objects.count()
    total_mun = Municipio.objects.count()

    print(f'✓ Departamentos cargados: {total_dept}')
    print(f'✓ Municipios cargados: {total_mun}')
    print('=' * 60)

if __name__ == '__main__':
    crear_departamentos_y_municipios()
