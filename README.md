Tierra Artesana - Plataforma de E-Commerce

Funcionalidades Técnicas

#Base de Datos SQLite
- Modelos completos de Usuario, Producto, Pedido, etc.
- Relaciones entre tablas
- Validaciones en los modelos

#Django ORM
- Consultas optimizadas
- Relaciones OneToOne, ForeignKey
- Métodos personalizados para cálculos

#Vistas y URLs
- URLs limpias y descriptivas
- Vistas basadas en funciones
- Decoradores de autenticación

#Plantillas
- Herencia de templates
- Filtros personalizados
- Formularios seguros con CSRF

#Seguridad
- Hash de contraseñas con PBKDF2
- Validación de sesiones
- Protección contra CSRF

---

Estructura del Proyecto

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


