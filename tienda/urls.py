from django.urls import path
from . import views

urlpatterns = [
    # Página principal
    path('', views.index, name='index'),
    
    # Autenticación
    path('registrarse/', views.registrarse, name='registrarse'),
    path('iniciar-sesion/', views.iniciar_sesion, name='iniciar_sesion'),
    path('cerrar-sesion/', views.cerrar_sesion, name='cerrar_sesion'),
    
    # Productos
    path('producto/<int:id>/', views.detalle_producto, name='detalle_producto'),
    path('buscar/', views.buscar_productos, name='buscar_productos'),
    path('categoria/<int:categoria_id>/', views.filtrar_categoria, name='filtrar_categoria'),
    
    # Carrito
    path('carrito/', views.carrito, name='carrito'),
    path('agregar-carrito/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar-carrito/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('actualizar-carrito/<int:item_id>/', views.actualizar_cantidad_carrito, name='actualizar_cantidad_carrito'),
    
    # Pedidos
    path('procesar-compra/', views.procesar_compra, name='procesar_compra'),
    path('pago/<int:pedido_id>/', views.pago, name='pago'),
    path('confirmacion-compra/<int:pedido_id>/', views.confirmacion_compra, name='confirmacion_compra'),
    path('pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('editar-pedido/<int:pedido_id>/', views.editar_pedido, name='editar_pedido'),
    path('eliminar-pedido/<int:pedido_id>/', views.eliminar_pedido, name='eliminar_pedido'),
    path('reportar-problema/<int:pedido_id>/', views.reportar_problema, name='reportar_problema'),
    path('historial-pedidos/', views.historial_pedidos, name='historial_pedidos'),

    # API AJAX
    path('api/municipios/<int:departamento_id>/', views.obtener_municipios, name='obtener_municipios'),
    
    # Dashboard de administración
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Gestión de productos
    path('dashboard/productos/', views.productos_lista, name='productos_lista'),
    path('dashboard/productos/crear/', views.productos_crear, name='productos_crear'),
    path('dashboard/productos/editar/<int:producto_id>/', views.productos_editar, name='productos_editar'),
    path('dashboard/productos/eliminar/<int:producto_id>/', views.productos_eliminar, name='productos_eliminar'),
    
    # Gestión de pedidos
    path('dashboard/pedidos/', views.pedidos_lista, name='pedidos_lista'),
    path('dashboard/pedidos/cambiar-estado/<int:pedido_id>/', views.pedidos_cambiar_estado, name='pedidos_cambiar_estado'),
    
    # Gestión de facturas
    path('dashboard/facturas/', views.facturas_lista, name='facturas_lista'),
    path('dashboard/facturas/editar/<int:factura_id>/', views.facturas_editar, name='facturas_editar'),
]
