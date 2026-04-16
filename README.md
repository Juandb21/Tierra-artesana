# 🎨 Tierra Artesana - Plataforma de E-Commerce

## 🚀 ¡La plataforma está lista!

El servidor Django está ejecutándose en: **http://127.0.0.1:8000/**

---

## 📝 Credenciales de Acceso

### 👥 Usuario Cliente (Demo)
- **Email:** `cliente@test.com`
- **Contraseña:** `123456`

### 👨‍💼 Usuario Administrador
- **Email:** `admin@tierra.com`
- **Contraseña:** `admin123`

---

## 🌐 Acceso a Secciones

### Cliente
1. **Página Principal:** http://127.0.0.1:8000/
   - Catálogo de productos
   - Búsqueda de productos
   - Carrusel de productos destacados

2. **Registro:** http://127.0.0.1:8000/registrarse/
   - Crear nueva cuenta de cliente

3. **Inicio de Sesión:** http://127.0.0.1:8000/iniciar-sesion/
   - Acceder con credenciales

4. **Carrito:** http://127.0.0.1:8000/carrito/
   - Ver productos agregados
   - Eliminar productos
   - Ver total

5. **Procesar Compra:** http://127.0.0.1:8000/procesar-compra/
   - Seleccionar ciudad de entrega
   - Ingresar dirección
   - Confirmar pedido
   - Ver detalles del descuento y envío

6. **Historial de Pedidos:** http://127.0.0.1:8000/historial-pedidos/
   - Ver todos tus pedidos
   - Estado de cada pedido
   - Detalles de cada compra

7. **Detalles del Producto:** http://127.0.0.1:8000/producto/1/
   - Información completa del producto
   - Precio disponibilidad
   - Productos relacionados

### Administrador
1. **Panel de Admin:** http://127.0.0.1:8000/admin/
   - Gestionar productos (crear, editar, eliminar)
   - Ver pedidos y clientes
   - Responder reportes
   - Ver estadísticas

---

## ✨ Características Implementadas

### Para Clientes
✅ Registro y autenticación segura
✅ Catálogo de productos con descarga de imágenes
✅ Búsqueda de productos
✅ Carrito de compras
✅ Procesar pedidos
✅ Descuentos automáticos (10% si el monto > $100.000)
✅ Envío gratis en Bogotá o $15.000 en otros departamentos
✅ Editar pedidos dentro de los primeros 15 minutos
✅ Historial de pedidos con estados
✅ Detalles completos de cada compra

### Para Administrador
✅ Panel de administración completo
✅ Gestiona productos (CRUD)
✅ Gestiona categorías
✅ Visualiza pedidos y sus detalles
✅ Ve información de clientes
✅ Gestiona reportes de daños
✅ Seguimiento del inventario

### Seguridad
✅ Contraseñas encriptadas
✅ Autenticación de usuarios
✅ Protección CSRF
✅ Validación de datos en formularios

---

## 📦 Productos Disponibles

Los siguientes productos ya están en el catálogo:

1. **Cerámica Artesanal** - $45.000 (5 disponibles)
2. **Jarrón Decorativo** - $65.000 (3 disponibles)
3. **Plato Artesanal** - $35.000 (8 disponibles)
4. **Maceta de Barro** - $28.000 (12 disponibles)
5. **Taza Personalizada** - $22.000 (15 disponibles)
6. **Escultura Cerámica** - $95.000 (2 disponibles)

---

## 🧪 Pruebas Sugeridas

### 1. Como Cliente
```
1. Inicia sesión con: cliente@test.com / 123456
2. Navega por los productos
3. Agrega varios productos al carrito
4. Ve al carrito y revisa el total
5. Procesa la compra:
   - Prueba con "Bogotá" para envío gratis
   - Prueba con otra ciudad para ver costo de envío ($15.000)
   - Si el total es > $100.000, verás un descuento del 10%
6. Edita el pedido dentro de 15 minutos si lo deseas
7. Ve tu historial de pedidos
```

### 2. Como Administrador
```
1. Ve a http://127.0.0.1:8000/admin/
2. Inicia sesión con: admin@tierra.com / admin123
3. Crea, edita o elimina productos
4. Ve los pedidos de cualquier cliente
5. Revisa la información de clientes
6. Visualiza reportes y estadísticas
```

---

## 🎨 Interfaz

- **Diseño Responsive:** Funciona en PC, tablet y celular
- **Colores:** Naranja/Marrón (#C85A17) tema artesanal
- **Tipografía:** Minimalista y clara
- **UX:** Intuitiva y fácil de navegar

---

## 📊 Funcionalidades Técnicas

### Base de Datos SQLite
- Modelos completos de Usuario, Producto, Pedido, etc.
- Relaciones entre tablas
- Validaciones en los modelos

### Django ORM
- Consultas optimizadas
- Relaciones OneToOne, ForeignKey
- Métodos personalizados para cálculos

### Vistas y URLs
- URLs limpias y descriptivas
- Vistas basadas en funciones
- Decoradores de autenticación

### Plantillas
- Herencia de templates
- Filtros personalizados
- Formularios seguros con CSRF

### Seguridad
- Hash de contraseñas con PBKDF2
- Validación de sesiones
- Protección contra CSRF

---

## 📋 Estructura del Proyecto

```
Tierra artesana/
├── nombre_proyecto/           # Configuración principal
│   ├── settings.py           # Configuraciones
│   ├── urls.py               # URLs raíz
│   ├── wsgi.py               # Configuración WSGI
│   └── asgi.py
├── tienda/                    # App principal
│   ├── models.py             # Modelos de datos
│   ├── views.py              # Lógicas de negocio
│   ├── urls.py               # URLs de tienda
│   ├── admin.py              # Panel de administración
│   └── migrations/           # Migraciones de BD
├── templates/                # Plantillas HTML
│   └── tienda/
│       ├── base.html         # Plantilla base
│       ├── index.html        # Página principal
│       ├── iniciar_sesion.html
│       ├── registrarse.html
│       ├── carrito.html
│       ├── procesar_compra.html
│       ├── detalle_pedido.html
│       ├── historial_pedidos.html
│       └── ...
├── manage.py                 # Comando Django
├── populate_db.py            # Script para dato iniciales
├── requirements.txt          # Dependencias
└── venv/                     # Ambiente virtual

---

## 🛠️ Comandos Útiles

```bash
# Activar ambiente virtual
venv\Scripts\activate

# Hacer migraciones (después de cambiar modelos)
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver

# Ejecutar shell Django
python manage.py shell

# Crear app
python manage.py startapp nombre_app

# Recopilar archivos estáticos
python manage.py collectstatic
```

---

## ⚠️ Notas Importantes

1. **Zona Horaria:** Configurada para Colombia (America/Bogota)
2. **Base de Datos:** SQLite (db.sqlite3) - ideal para desarrollo
3. **Archivos Media:** Guardados en carpeta `/media/`
4. **Archivos Estáticos:** Guardados en carpeta `/staticfiles/` (generados con collectstatic)
5. **DEBUG:** Activado (cambiar a False en producción)

---

## 🚀 Próximas Mejoras Sugeridas

1. Integrar pasarela de pagos (Stripe, PayU)
2. Sistema de notificaciones por email
3. Panel de reportes más avanzado
4. Sistema de puntos/recompensas
5. Chat con administrador
6. Seguimiento de envíos en tiempo real
7. Wishlist/Favoritos
8. Reseñas y calificaciones
9. Sistema de cupones descuento
10. Análisis de ventas más detallados

---

## 📞 Contacto del Vendedor

**Email:** admin@tierra.com
**Teléfono:** (Agregar teléfono)
**Ubicación:** Bogotá, Colombia

---

*Plataforma desarrollada con Django 6.0.4*
*Python 3.14*
*Última actualización: Abril 14, 2026*
