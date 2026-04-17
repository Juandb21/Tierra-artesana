from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import models
from django.db import transaction
from .models import Producto, Cliente, Carrito, ItemCarrito, Pedido, DetallePedido, Categoria, Departamento, Municipio, Reporte, UbicacionCliente
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import uuid
import re


def limpiar_tallas_numericas(tallas_raw):
    """Limpia tamaños en formato numero:cantidad y retorna (texto_limpio, invalidas)."""
    tallas_limpias = []
    tallas_invalidas = []

    for talla in (tallas_raw or '').split(','):
        valor = talla.strip()
        if not valor:
            continue

        if ':' not in valor:
            tallas_invalidas.append(valor)
            continue

        tamano_raw, stock_raw = valor.split(':', 1)
        tamano_raw = tamano_raw.strip()
        stock_raw = stock_raw.strip()

        try:
            tamano = Decimal(tamano_raw)
            stock = int(stock_raw)
        except Exception:
            tallas_invalidas.append(valor)
            continue

        if tamano <= 0 or stock < 0:
            tallas_invalidas.append(valor)
            continue

        tamano_limpio = f"{tamano:.2f}".rstrip('0').rstrip('.')
        tallas_limpias.append(f"{tamano_limpio}:{stock}")

    # Evita duplicados manteniendo el orden (por tamaño).
    tallas_unicas = []
    vistos = set()
    for item in tallas_limpias:
        tamano, _stock = item.split(':', 1)
        if tamano in vistos:
            continue
        vistos.add(tamano)
        tallas_unicas.append(item)

    return ','.join(tallas_unicas), tallas_invalidas


def total_stock_desde_tallas(tallas_texto):
    total = 0
    for item in (tallas_texto or '').split(','):
        valor = item.strip()
        if not valor or ':' not in valor:
            continue
        _tamano, stock_raw = valor.split(':', 1)
        try:
            total += int(stock_raw.strip())
        except Exception:
            continue
    return total

# Vista principal
def index(request):
    productos_destacados = Producto.objects.filter(activo=True)[:6]
    productos_todos = Producto.objects.filter(activo=True)
    categorias = Categoria.objects.all()
    
    # Verificar si viene del menú "Productos" para ocultar el carrusel
    mostrar_carrusel = request.GET.get('solo_productos') != 'true'
    
    context = {
        'productos_destacados': productos_destacados,
        'productos_todos': productos_todos,
        'categorias': categorias,
        'mostrar_carrusel': mostrar_carrusel,
    }
    return render(request, 'tienda/index.html', context)

# Registro de cliente
def registrarse(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        nombre_completo = request.POST.get('nombre_completo')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono', '').strip()
        contraseña = request.POST.get('contraseña')
        confirmar_contraseña = request.POST.get('confirmar_contraseña')
        acepta_terminos = request.POST.get('acepta_terminos')
        
        # Validaciones
        if not all([nombre_completo, email, telefono, contraseña, confirmar_contraseña]):
            messages.error(request, 'Todos los campos son requeridos')
            return redirect('registrarse')

        telefono_limpio = re.sub(r'\D', '', telefono)
        if telefono_limpio.startswith('57') and len(telefono_limpio) == 12:
            telefono_limpio = telefono_limpio[2:]

        if len(telefono_limpio) != 10 or not telefono_limpio.startswith('3'):
            messages.error(request, 'Ingresa un número de celular colombiano válido (10 dígitos, inicia por 3)')
            return redirect('registrarse')

        if acepta_terminos != 'on':
            messages.error(request, 'Debes leer y aceptar los términos y condiciones para registrarte')
            return redirect('registrarse')
        
        if contraseña != confirmar_contraseña:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('registrarse')
        
        if len(contraseña) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return redirect('registrarse')
        
        if User.objects.filter(username=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado')
            return redirect('registrarse')
        
        # Crear usuario
        user = User.objects.create_user(
            username=email,
            email=email,
            password=contraseña,
            first_name=nombre_completo.split()[0],
            last_name=' '.join(nombre_completo.split()[1:])
        )
        
        # Crear cliente
        Cliente.objects.create(user=user, telefono=telefono_limpio)
        
        messages.success(request, 'Cuenta creada exitosamente. Inicia sesión')
        return redirect('iniciar_sesion')
    
    return render(request, 'tienda/registrarse.html')

# Iniciar sesión
def iniciar_sesion(request):
    if request.user.is_authenticated:
        # Si ya está autenticado, redirigir al dashboard si es admin, si no al index
        if request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard')
        return redirect('index')
    
    if request.method == 'POST':
        email = request.POST.get('email', '')
        contraseña = request.POST.get('contraseña', '')
        
        user = authenticate(request, username=email, password=contraseña)
        
        if user is not None:
            login(request, user)
            # Crear carrito si no existe
            try:
                cliente = Cliente.objects.get(user=user)
            except Cliente.DoesNotExist:
                cliente = Cliente.objects.create(user=user)
            
            Carrito.objects.get_or_create(cliente=cliente)
            
            messages.success(request, f'Bienvenido {user.first_name}')
            # Redireccionar al dashboard si es admin, si no al index
            if user.is_staff or user.is_superuser:
                return redirect('dashboard')
            return redirect('index')
        else:
            messages.error(request, 'Correo o contraseña incorrectos')
    
    return render(request, 'tienda/iniciar_sesion.html')

# Cerrar sesión
def cerrar_sesion(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión')
    return redirect('index')

# Ver detalles del producto
def detalle_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    productos_relacionados = Producto.objects.filter(
        categoria=producto.categoria,
        activo=True
    ).exclude(id=id)[:4]
    
    context = {
        'producto': producto,
        'productos_relacionados': productos_relacionados,
    }
    return render(request, 'tienda/detalle_producto.html', context)

# Carrito
@login_required(login_url='iniciar_sesion')
def carrito(request):
    cliente = get_object_or_404(Cliente, user=request.user)
    carrito_obj = get_object_or_404(Carrito, cliente=cliente)
    
    context = {
        'carrito': carrito_obj,
        'items': carrito_obj.items.all(),
    }
    return render(request, 'tienda/carrito.html', context)

# Agregar al carrito
@login_required(login_url='iniciar_sesion')
@require_http_methods(["POST"])
def agregar_al_carrito(request, producto_id):
    try:
        cliente = Cliente.objects.get(user=request.user)
        carrito_obj, _ = Carrito.objects.get_or_create(cliente=cliente)
        producto = get_object_or_404(Producto, id=producto_id)
        cantidad = int(request.POST.get('cantidad', 1))
        talla = request.POST.get('talla', '').strip()

        tallas_disponibles = producto.tallas_lista
        if tallas_disponibles and not talla:
            return JsonResponse({
                'success': False,
                'message': 'Selecciona una talla'
            })

        if tallas_disponibles and talla not in tallas_disponibles:
            return JsonResponse({
                'success': False,
                'message': 'Talla inválida'
            })
        
        if cantidad > producto.cantidad_disponible:
            return JsonResponse({
                'success': False,
                'message': f'Solo hay {producto.cantidad_disponible} productos disponibles'
            })

        stock_talla = producto.stock_por_talla(talla)
        item_existente = ItemCarrito.objects.filter(
            carrito=carrito_obj,
            producto=producto,
            talla=talla,
        ).first()
        cantidad_total_talla = cantidad + (item_existente.cantidad if item_existente else 0)

        if stock_talla is not None and cantidad_total_talla > stock_talla:
            return JsonResponse({
                'success': False,
                'message': f'Solo hay {stock_talla} disponibles del tamaño {talla}'
            })
        
        item, created = ItemCarrito.objects.get_or_create(
            carrito=carrito_obj,
            producto=producto,
            talla=talla,
            defaults={'cantidad': cantidad}
        )
        
        if not created:
            item.cantidad += cantidad
            item.save()
        
        messages.success(request, f'{producto.nombre} agregado al carrito')
        return redirect('carrito')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('index')

# Eliminar del carrito
@login_required(login_url='iniciar_sesion')
@require_http_methods(["POST"])
def eliminar_del_carrito(request, item_id):
    cliente = get_object_or_404(Cliente, user=request.user)
    carrito_obj = get_object_or_404(Carrito, cliente=cliente)
    item = get_object_or_404(ItemCarrito, id=item_id, carrito=carrito_obj)
    item.delete()
    messages.success(request, 'Producto eliminado del carrito')
    return redirect('carrito')

# Actualizar cantidad en carrito
@login_required(login_url='iniciar_sesion')
@require_http_methods(["POST"])
def actualizar_cantidad_carrito(request, item_id):
    try:
        cliente = get_object_or_404(Cliente, user=request.user)
        carrito_obj = get_object_or_404(Carrito, cliente=cliente)
        item = get_object_or_404(ItemCarrito, id=item_id, carrito=carrito_obj)
        
        cantidad = int(request.POST.get('cantidad', 1))
        
        if cantidad < 1:
            item.delete()
            messages.success(request, 'Producto eliminado del carrito')
        elif cantidad > item.producto.cantidad_disponible:
            messages.error(request, f'Solo hay {item.producto.cantidad_disponible} productos disponibles')
        elif item.talla and item.producto.stock_por_talla(item.talla) is not None and cantidad > item.producto.stock_por_talla(item.talla):
            messages.error(request, f'Solo hay {item.producto.stock_por_talla(item.talla)} disponibles del tamaño {item.talla}')
        else:
            item.cantidad = cantidad
            item.save()
            messages.success(request, 'Cantidad actualizada')
        
        return redirect('carrito')
    except ValueError:
        messages.error(request, 'Cantidad inválida')
        return redirect('carrito')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('carrito')

# Procesar compra
@login_required(login_url='iniciar_sesion')
def procesar_compra(request):
    if request.method == 'POST':
        cliente = get_object_or_404(Cliente, user=request.user)
        carrito_obj = get_object_or_404(Carrito, cliente=cliente)
        
        if not carrito_obj.items.exists():
            messages.error(request, 'El carrito está vacío')
            return redirect('carrito')
        
        ubicacion_guardada_id = request.POST.get('ubicacion_guardada', '').strip()
        municipio_id = request.POST.get('municipio', '').strip()
        direccion = request.POST.get('direccion', '').strip()

        if ubicacion_guardada_id:
            try:
                ubicacion_guardada = UbicacionCliente.objects.select_related('municipio', 'departamento').get(
                    id=ubicacion_guardada_id,
                    cliente=cliente,
                )
                municipio = ubicacion_guardada.municipio
                direccion = ubicacion_guardada.direccion
            except UbicacionCliente.DoesNotExist:
                messages.error(request, 'La ubicación seleccionada no es válida')
                return redirect('procesar_compra')
        else:
            if not municipio_id or not direccion:
                messages.error(request, 'Municipio y referencia son requeridos')
                return redirect('carrito')

            try:
                municipio = Municipio.objects.get(id=municipio_id)
            except Municipio.DoesNotExist:
                messages.error(request, 'Municipio inválido')
                return redirect('carrito')

        # Validar inventario antes de crear el pedido
        for item in carrito_obj.items.select_related('producto'):
            producto = item.producto
            if item.cantidad > producto.cantidad_disponible:
                messages.error(request, f'No hay suficiente stock de {producto.nombre}')
                return redirect('carrito')

            if item.talla:
                stock_talla = producto.stock_por_talla(item.talla)
                if stock_talla is not None and item.cantidad > stock_talla:
                    messages.error(request, f'{producto.nombre}: solo hay {stock_talla} del tamaño {item.talla}')
                    return redirect('carrito')

        try:
            with transaction.atomic():
                items = list(carrito_obj.items.select_related('producto'))
                productos_ids = [item.producto_id for item in items]
                productos_bloqueados = {
                    producto.id: producto
                    for producto in Producto.objects.select_for_update().filter(id__in=productos_ids)
                }

                # Revalidar inventario con bloqueo para evitar sobreventa por concurrencia.
                for item in items:
                    producto = productos_bloqueados.get(item.producto_id)
                    if not producto:
                        messages.error(request, 'Uno de los productos ya no existe')
                        return redirect('carrito')

                    if item.cantidad > producto.cantidad_disponible:
                        messages.error(request, f'No hay suficiente stock de {producto.nombre}')
                        return redirect('carrito')

                    if item.talla:
                        stock_talla = producto.stock_por_talla(item.talla)
                        if stock_talla is not None and item.cantidad > stock_talla:
                            messages.error(request, f'{producto.nombre}: solo hay {stock_talla} del tamaño {item.talla}')
                            return redirect('carrito')

                # Calcular totales sobre el snapshot bloqueado.
                subtotal = sum(item.cantidad * item.producto.precio for item in items)
                costo_envio = Decimal('0')
                descuento = Decimal('0')

                if subtotal > 100000:
                    descuento = subtotal * Decimal('0.10')

                total = subtotal + costo_envio - descuento

                # Crear pedido
                numero_pedido = f"PED{uuid.uuid4().hex[:8].upper()}"
                pedido = Pedido.objects.create(
                    cliente=cliente,
                    numero_pedido=numero_pedido,
                    total=total,
                    descuento=descuento,
                    costo_envio=costo_envio,
                    departamento=municipio.departamento,
                    municipio=municipio,
                    ciudad_entrega=f"{municipio.nombre}, {municipio.departamento.nombre}",
                    direccion_entrega=direccion,
                )

                # Guardar ubicacion para reutilizar en futuras compras.
                UbicacionCliente.objects.update_or_create(
                    cliente=cliente,
                    municipio=municipio,
                    direccion=direccion,
                    defaults={
                        'departamento': municipio.departamento,
                    },
                )

                cliente.departamento = municipio.departamento
                cliente.municipio = municipio
                cliente.ciudad = f"{municipio.nombre}, {municipio.departamento.nombre}"
                cliente.direccion = direccion
                cliente.save(update_fields=['departamento', 'municipio', 'ciudad', 'direccion'])

                # Crear detalles y descontar inventario bloqueado.
                for item in items:
                    producto = productos_bloqueados[item.producto_id]
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=producto,
                        cantidad=item.cantidad,
                        precio_unitario=producto.precio,
                        subtotal=item.cantidad * producto.precio,
                        talla=item.talla
                    )

                    producto.cantidad_disponible -= item.cantidad
                    if item.talla:
                        stock_talla = producto.stock_por_talla(item.talla)
                        if stock_talla is not None:
                            producto.actualizar_stock_talla(item.talla, stock_talla - item.cantidad)
                    producto.save(update_fields=['cantidad_disponible', 'tallas'])

                # Limpiar carrito
                carrito_obj.items.all().delete()
        except Exception:
            messages.error(request, 'No se pudo procesar la compra en este momento. Intenta de nuevo.')
            return redirect('carrito')
        
        messages.success(request, f'Pedido {numero_pedido} creado exitosamente')
        return redirect('pago', pedido_id=pedido.id)
    
    cliente = get_object_or_404(Cliente, user=request.user)
    carrito_obj = get_object_or_404(Carrito, cliente=cliente)
    departamentos = Departamento.objects.all()
    ubicaciones_guardadas = cliente.ubicaciones_guardadas.select_related('departamento', 'municipio')

    context = {
        'carrito': carrito_obj,
        'items': carrito_obj.items.all(),
        'departamentos': departamentos,
        'ubicaciones_guardadas': ubicaciones_guardadas,
    }
    return render(request, 'tienda/procesar_compra.html', context)


# API para obtener municipios por departamento (AJAX)
def obtener_municipios(request, departamento_id):
    """Retorna los municipios de un departamento en formato JSON"""
    try:
        departamento = Departamento.objects.get(id=departamento_id)
        municipios = departamento.municipios.all().values('id', 'nombre')
        return JsonResponse(list(municipios), safe=False)
    except Departamento.DoesNotExist:
        return JsonResponse({'error': 'Departamento no encontrado'}, status=404)

# Página de pago
@login_required(login_url='iniciar_sesion')
def pago(request, pedido_id):
    cliente = get_object_or_404(Cliente, user=request.user)
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=cliente)
    
    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago', '')
        
        if not metodo_pago:
            messages.error(request, 'Selecciona un método de pago')
            return redirect('pago', pedido_id=pedido.id)
        
        try:
            # Actualizar método de pago en el modelo
            # Primero necesitamos verificar si el campo existe
            pedido.metodo_pago = metodo_pago
            pedido.save()
        except:
            # Si el campo no existe aún, simplemente continuamos
            pass
        
        # Limpiar carrito después de confirmar pago
        cliente_carrito = get_object_or_404(Carrito, cliente=cliente)
        cliente_carrito.items.all().delete()
        
        return redirect('confirmacion_compra', pedido_id=pedido.id)
    
    context = {
        'pedido': pedido,
    }
    return render(request, 'tienda/pago.html', context)
@login_required(login_url='iniciar_sesion')
def confirmacion_compra(request, pedido_id):
    cliente = get_object_or_404(Cliente, user=request.user)
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=cliente)
    
    context = {
        'pedido': pedido,
    }
    return render(request, 'tienda/confirmacion_compra.html', context)

# Detalle de pedido
@login_required(login_url='iniciar_sesion')
def detalle_pedido(request, pedido_id):
    cliente = get_object_or_404(Cliente, user=request.user)
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=cliente)
    
    # Redirigir a la vista de confirmación/factura
    return redirect('confirmacion_compra', pedido_id=pedido.id)

# Editar pedido
@login_required(login_url='iniciar_sesion')
def editar_pedido(request, pedido_id):
    cliente = get_object_or_404(Cliente, user=request.user)
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=cliente)
    
    # La edición de pedidos está deshabilitada
    messages.error(request, 'La edición de pedidos no está disponible')
    return redirect('historial_pedidos')

# Eliminar pedido
@login_required(login_url='iniciar_sesion')
def eliminar_pedido(request, pedido_id):
    cliente = get_object_or_404(Cliente, user=request.user)
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=cliente)
    
    if not pedido.puede_editarse:
        messages.error(request, 'Ya no se puede eliminar este pedido (plazo de 15 minutos expirado)')
        return redirect('historial_pedidos')
    
    if request.method == 'POST':
        pedido_numero = pedido.numero_pedido
        pedido.delete()
        messages.success(request, f'Pedido {pedido_numero} ha sido eliminado')
    
    return redirect('historial_pedidos')

# Reportar problema con un pedido
@login_required(login_url='iniciar_sesion')
def reportar_problema(request, pedido_id):
    cliente = get_object_or_404(Cliente, user=request.user)
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=cliente)

    if pedido.estado != 'entregado':
        messages.error(request, 'Solo puedes reportar problemas cuando el pedido esté entregado.')
        return redirect('historial_pedidos')
    
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', '')
        imagen = request.FILES.get('imagen', None)
        
        if not descripcion:
            messages.error(request, 'Describe el problema por favor')
            return redirect('reportar_problema', pedido_id=pedido.id)
        
        reporte = Reporte.objects.create(
            pedido=pedido,
            cliente=cliente,
            descripcion=descripcion,
            imagen=imagen,
        )
        
        messages.success(request, 'Reporte enviado exitosamente. Nos pondremos en contacto pronto.')
        return redirect('historial_pedidos')
    
    context = {
        'pedido': pedido,
    }
    return render(request, 'tienda/reportar_problema.html', context)

# Historial de pedidos
@login_required(login_url='iniciar_sesion')
def historial_pedidos(request):
    cliente = get_object_or_404(Cliente, user=request.user)
    pedidos = Pedido.objects.filter(cliente=cliente).order_by('-fecha_pedido')
    
    context = {
        'pedidos': pedidos,
    }
    return render(request, 'tienda/historial_pedidos.html', context)

# Búsqueda de productos
def buscar_productos(request):
    query = request.GET.get('q', '')
    categorias = Categoria.objects.all()
    
    if query:
        productos = Producto.objects.filter(
            nombre__icontains=query,
            activo=True
        ) | Producto.objects.filter(
            descripcion__icontains=query,
            activo=True
        )
    else:
        productos = Producto.objects.filter(activo=True)
    
    context = {
        'productos': productos,
        'query': query,
        'categorias': categorias,
    }
    return render(request, 'tienda/resultados_busqueda.html', context)

# Filtrar por categoría
def filtrar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    productos = Producto.objects.filter(categoria=categoria, activo=True)
    categorias = Categoria.objects.all()
    
    context = {
        'productos': productos,
        'categoria': categoria,
        'categorias': categorias,
    }
    return render(request, 'tienda/productos_por_categoria.html', context)

# ========== FUNCIONES DE PROTECCIÓN PARA ADMIN ==========

def verificar_admin(request):
    """Verifica que el usuario sea administrador (staff o superuser)"""
    return request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)


# ========== DASHBOARD DE ADMINISTRACIÓN ==========

@login_required(login_url='iniciar_sesion')
def dashboard(request):
    """Dashboard principal del administrador"""
    if not verificar_admin(request):
        messages.error(request, 'No tienes permisos para acceder al dashboard')
        return redirect('index')
    
    # Obtener período seleccionado (por defecto: día)
    periodo = request.GET.get('periodo', 'dia')
    
    # Calcular fecha de inicio según el período
    hoy = timezone.now()
    # Convertir a zona horaria local para obtener la fecha correcta
    hoy_local = hoy.astimezone()
    hoy_fecha = hoy_local.date()
    
    if periodo == 'dia':
        # Inicio del día actual (00:00:00 en zona local)
        fecha_inicio = timezone.make_aware(
            datetime.combine(hoy_fecha, datetime.min.time())
        )
        # Fin del día actual (23:59:59 en zona local)
        fecha_fin = timezone.make_aware(
            datetime.combine(hoy_fecha, datetime.max.time())
        )
    elif periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
        fecha_fin = hoy
    elif periodo == 'mes':
        # Primer día del mes actual a las 00:00:00
        primer_dia = hoy_fecha.replace(day=1)
        fecha_inicio = timezone.make_aware(
            datetime.combine(primer_dia, datetime.min.time())
        )
        fecha_fin = hoy
    elif periodo == 'ano':
        # Primer día del año a las 00:00:00
        primer_dia_ano = hoy_fecha.replace(month=1, day=1)
        fecha_inicio = timezone.make_aware(
            datetime.combine(primer_dia_ano, datetime.min.time())
        )
        fecha_fin = hoy
    else:
        fecha_inicio = timezone.make_aware(
            datetime.combine(hoy_fecha, datetime.min.time())
        )
        fecha_fin = timezone.make_aware(
            datetime.combine(hoy_fecha, datetime.max.time())
        )
    
    # Filtrar pedidos por período
    pedidos_periodo = Pedido.objects.filter(fecha_pedido__gte=fecha_inicio, fecha_pedido__lte=fecha_fin)
    
    # Obtener datos resumen
    total_pedidos = pedidos_periodo.count()
    total_ingresos = pedidos_periodo.aggregate(total=models.Sum('total'))['total'] or Decimal('0')
    productos_activos = Producto.objects.filter(activo=True).count()
    pedidos_en_transporte = pedidos_periodo.filter(estado='enviado').count()
    pedidos_pendientes = pedidos_periodo.filter(estado='pendiente').count()
    
    # Productos más vendidos
    productos_top = DetallePedido.objects.filter(
        pedido__fecha_pedido__gte=fecha_inicio,
        pedido__fecha_pedido__lte=fecha_fin
    ).values('producto__nombre', 'producto__id').annotate(
        cantidad_vendida=models.Sum('cantidad'),
        ingresos=models.Sum('subtotal')
    ).order_by('-cantidad_vendida')[:5]
    
    # Ingresos por producto
    ingresos_por_producto = DetallePedido.objects.filter(
        pedido__fecha_pedido__gte=fecha_inicio,
        pedido__fecha_pedido__lte=fecha_fin
    ).values('producto__nombre').annotate(
        total_ingresos=models.Sum('subtotal')
    ).order_by('-total_ingresos')[:5]
    
    # Departamentos con más pedidos e ingresos
    departamentos_top = Pedido.objects.filter(
        fecha_pedido__gte=fecha_inicio,
        fecha_pedido__lte=fecha_fin
    ).values('departamento__nombre').annotate(
        total_pedidos=models.Count('id'),
        total_ingresos=models.Sum('total')
    ).order_by('-total_ingresos')[:5]
    
    # Tendencia de ventas (últimos 7 días o 30 días según período)
    if periodo in ['dia', 'semana']:
        dias = 7
    else:
        dias = 30
    
    tendencia_ventas = []
    tendencia_fechas = []
    for i in range(dias - 1, -1, -1):
        fecha = (hoy - timedelta(days=i)).date()
        # Crear datetimes timezone-aware para inicio y fin del día
        fecha_inicio_dia = timezone.make_aware(
            datetime.combine(fecha, datetime.min.time())
        )
        fecha_fin_dia = timezone.make_aware(
            datetime.combine(fecha, datetime.max.time())
        )
        
        ventas_dia = Pedido.objects.filter(
            fecha_pedido__gte=fecha_inicio_dia,
            fecha_pedido__lte=fecha_fin_dia
        ).aggregate(total=models.Sum('total'))['total'] or 0
        
        tendencia_ventas.append(float(ventas_dia))
        tendencia_fechas.append(fecha.strftime('%d/%m'))
    

    
    context = {
        'total_pedidos': total_pedidos,
        'total_ingresos': total_ingresos,
        'productos_activos': productos_activos,
        'pedidos_en_transporte': pedidos_en_transporte,
        'pedidos_pendientes': pedidos_pendientes,
        'productos_top': list(productos_top),
        'ingresos_por_producto': list(ingresos_por_producto),
        'departamentos_top': list(departamentos_top),
        'tendencia_ventas': tendencia_ventas,
        'tendencia_fechas': tendencia_fechas,
        'periodo': periodo,
    }
    return render(request, 'tienda/dashboard.html', context)


# ========== GESTIÓN DE PRODUCTOS ==========

@login_required(login_url='iniciar_sesion')
def productos_lista(request):
    """Listar todos los productos"""
    if not verificar_admin(request):
        return redirect('index')
    
    productos = Producto.objects.all().order_by('-fecha_creacion')
    
    context = {
        'productos': productos,
    }
    return render(request, 'tienda/productos_lista.html', context)


@login_required(login_url='iniciar_sesion')
def productos_crear(request):
    """Crear nuevo producto"""
    if not verificar_admin(request):
        return redirect('index')
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '')
        descripcion = request.POST.get('descripcion', '')
        precio = request.POST.get('precio', '')
        cantidad_disponible = request.POST.get('cantidad_disponible', '')
        categoria_id = request.POST.get('categoria', '')
        tallas_raw = request.POST.get('tallas', '').strip()
        tallas, tallas_invalidas = limpiar_tallas_numericas(tallas_raw)
        imagen = request.FILES.get('imagen', None)
        
        # Validaciones
        errores = []
        if not nombre:
            errores.append('Nombre es requerido')
        if not precio:
            errores.append('Precio es requerido')
        if not cantidad_disponible and not tallas:
            errores.append('Cantidad disponible es requerida')
        if tallas_invalidas:
            errores.append('Cada tamaño debe tener formato número:cantidad (ej: 26:3)')
        
        if errores:
            context = {
                'errores': errores,
                'nombre': nombre,
                'descripcion': descripcion,
                'precio': precio,
                'cantidad_disponible': cantidad_disponible,
                'tallas': tallas_raw,
                'categorias': Categoria.objects.all(),
            }
            return render(request, 'tienda/productos_crear.html', context)
        
        try:
            categoria = None
            if categoria_id:
                categoria = Categoria.objects.get(id=categoria_id)

            cantidad_final = int(cantidad_disponible) if cantidad_disponible else 0
            if tallas:
                cantidad_final = total_stock_desde_tallas(tallas)
            
            producto = Producto.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                precio=Decimal(precio),
                cantidad_disponible=cantidad_final,
                categoria=categoria,
                tallas=tallas,
                imagen=imagen,
                activo=True
            )
            messages.success(request, f'Producto "{nombre}" creado exitosamente')
            return redirect('productos_lista')
        except Exception as e:
            messages.error(request, f'Error al crear el producto: {str(e)}')
    
    context = {
        'categorias': Categoria.objects.all(),
    }
    return render(request, 'tienda/productos_crear.html', context)


@login_required(login_url='iniciar_sesion')
def productos_editar(request, producto_id):
    """Editar un producto"""
    if not verificar_admin(request):
        return redirect('index')
    
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '')
        descripcion = request.POST.get('descripcion', '')
        precio = request.POST.get('precio', '')
        cantidad_disponible = request.POST.get('cantidad_disponible', '')
        categoria_id = request.POST.get('categoria', '')
        tallas_raw = request.POST.get('tallas', '').strip()
        tallas, tallas_invalidas = limpiar_tallas_numericas(tallas_raw)
        imagen = request.FILES.get('imagen', None)
        
        # Validaciones
        errores = []
        if not nombre:
            errores.append('Nombre es requerido')
        if not precio:
            errores.append('Precio es requerido')
        if not cantidad_disponible and not tallas:
            errores.append('Cantidad disponible es requerida')
        if tallas_invalidas:
            errores.append('Cada tamaño debe tener formato número:cantidad (ej: 26:3)')
        
        if errores:
            context = {
                'errores': errores,
                'producto': producto,
                'nombre': nombre,
                'descripcion': descripcion,
                'precio': precio,
                'cantidad_disponible': cantidad_disponible,
                'categoria_id': categoria_id,
                'tallas': tallas_raw,
                'categorias': Categoria.objects.all(),
            }
            return render(request, 'tienda/productos_editar.html', context)
        
        try:
            producto.nombre = nombre
            producto.descripcion = descripcion
            producto.precio = Decimal(precio)
            cantidad_final = int(cantidad_disponible) if cantidad_disponible else 0
            if tallas:
                cantidad_final = total_stock_desde_tallas(tallas)
            producto.cantidad_disponible = cantidad_final
            producto.tallas = tallas
            if categoria_id:
                producto.categoria = Categoria.objects.get(id=categoria_id)
            if imagen:
                producto.imagen = imagen
            producto.save()
            
            messages.success(request, f'Producto "{nombre}" actualizado exitosamente')
            return redirect('productos_lista')
        except Exception as e:
            messages.error(request, f'Error al actualizar el producto: {str(e)}')
            context = {
                'producto': producto,
                'nombre': nombre,
                'descripcion': descripcion,
                'precio': precio,
                'cantidad_disponible': cantidad_disponible,
                'categoria_id': categoria_id,
                'tallas': tallas,
                'categorias': Categoria.objects.all(),
            }
            return render(request, 'tienda/productos_editar.html', context)
    
    context = {
        'producto': producto,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio': str(producto.precio),
        'cantidad_disponible': str(producto.cantidad_disponible),
        'categoria_id': str(producto.categoria.id) if producto.categoria else '',
        'tallas': producto.tallas,
        'categorias': Categoria.objects.all(),
    }
    return render(request, 'tienda/productos_editar.html', context)


@login_required(login_url='iniciar_sesion')
def productos_eliminar(request, producto_id):
    """Eliminar un producto"""
    if not verificar_admin(request):
        return redirect('index')
    
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado exitosamente')
        return redirect('productos_lista')
    
    context = {
        'producto': producto,
    }
    return render(request, 'tienda/productos_eliminar.html', context)


# ========== GESTIÓN DE PEDIDOS ==========

@login_required(login_url='iniciar_sesion')
def pedidos_lista(request):
    """Listar todos los pedidos y marcar estado de transporte"""
    if not verificar_admin(request):
        return redirect('index')
    
    estados_permitidos = [
        estado for estado in Pedido.ESTADOS
        if estado[0] in ('pendiente', 'enviado', 'entregado', 'cancelado')
    ]
    valores_permitidos = {valor for valor, _ in estados_permitidos}

    # Filtros
    estado_filtro = request.GET.get('estado', '')
    busqueda = request.GET.get('busqueda', '')

    if estado_filtro not in valores_permitidos:
        estado_filtro = ''
    
    # FIFO para atender primero los mas antiguos, dejando los enviados al final.
    enviados_al_final = models.Case(
        models.When(estado='enviado', then=models.Value(1)),
        default=models.Value(0),
        output_field=models.IntegerField(),
    )
    pedidos = Pedido.objects.annotate(
        _enviados_al_final=enviados_al_final,
        total_reportes=models.Count('reporte', distinct=True),
    ).order_by('_enviados_al_final', 'fecha_pedido', 'id')
    
    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)
    
    if busqueda:
        pedidos = pedidos.filter(
            numero_pedido__icontains=busqueda
        ) | pedidos.filter(
            cliente__user__first_name__icontains=busqueda
        ) | pedidos.filter(
            cliente__user__last_name__icontains=busqueda
        )
    
    context = {
        'pedidos': pedidos,
        'estado_filtro': estado_filtro,
        'busqueda': busqueda,
        'estados': estados_permitidos,
    }
    return render(request, 'tienda/pedidos_lista.html', context)


@login_required(login_url='iniciar_sesion')
def pedidos_ver_reporte(request, pedido_id):
    """Ver reportes de un pedido desde el panel administrativo."""
    if not verificar_admin(request):
        return redirect('index')

    pedido = get_object_or_404(Pedido, id=pedido_id)
    reportes = Reporte.objects.filter(pedido=pedido).order_by('-fecha_creacion')

    if not reportes.exists():
        messages.info(request, f'El pedido {pedido.numero_pedido} no tiene reportes.')
        return redirect('pedidos_lista')

    context = {
        'pedido': pedido,
        'reportes': reportes,
    }
    return render(request, 'tienda/pedidos_reporte_detalle.html', context)


@login_required(login_url='iniciar_sesion')
def pedidos_cambiar_estado(request, pedido_id):
    """Cambiar estado del pedido a transporte"""
    if not verificar_admin(request):
        return redirect('index')
    
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if pedido.estado in ('entregado', 'cancelado'):
        messages.error(request, f'El pedido {pedido.numero_pedido} ya no se puede editar por estar finalizado')
        return redirect('pedidos_lista')

    estados_permitidos = [
        estado for estado in Pedido.ESTADOS
        if estado[0] in ('pendiente', 'enviado', 'entregado', 'cancelado')
    ]
    valores_permitidos = {valor for valor, _ in estados_permitidos}
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado', '')
        if nuevo_estado in valores_permitidos:
            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(request, f'Estado del pedido {pedido.numero_pedido} actualizado a {nuevo_estado}')
            return redirect('pedidos_lista')
    
    context = {
        'pedido': pedido,
        'estados': estados_permitidos,
    }
    return render(request, 'tienda/pedidos_cambiar_estado.html', context)


# ========== GESTIÓN DE FACTURAS ==========

@login_required(login_url='iniciar_sesion')
def facturas_lista(request):
    """Listar facturas con filtros por cliente y fechas"""
    if not verificar_admin(request):
        return redirect('index')
    
    # Filtros
    cliente_nombre = request.GET.get('cliente', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    # Obtener todos los pedidos (facturas)
    facturas = Pedido.objects.all().order_by('-fecha_pedido')
    
    # Aplicar filtros
    if cliente_nombre:
        facturas = facturas.filter(
            cliente__user__first_name__icontains=cliente_nombre
        ) | facturas.filter(
            cliente__user__last_name__icontains=cliente_nombre
        ) | facturas.filter(
            cliente__user__email__icontains=cliente_nombre
        )
        facturas = facturas.distinct()
    
    if fecha_desde:
        try:
            fecha_desde_dt = timezone.datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            facturas = facturas.filter(fecha_pedido__date__gte=fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = timezone.datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            facturas = facturas.filter(fecha_pedido__date__lte=fecha_hasta_dt)
        except ValueError:
            pass
    
    context = {
        'facturas': facturas,
        'cliente_nombre': cliente_nombre,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    return render(request, 'tienda/facturas_lista.html', context)


@login_required(login_url='iniciar_sesion')
def facturas_editar(request, factura_id):
    """Ver una factura (solo lectura)"""
    if not verificar_admin(request):
        return redirect('index')
    
    factura = get_object_or_404(Pedido, id=factura_id)

    # Reutiliza el mismo formato de factura que ve el cliente.
    context = {
        'pedido': factura,
        'admin_view': True,
    }
    return render(request, 'tienda/confirmacion_compra.html', context)

