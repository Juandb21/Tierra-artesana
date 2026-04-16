from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=5, unique=True)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Municipio(models.Model):
    nombre = models.CharField(max_length=100)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='municipios')
    codigo = models.CharField(max_length=10, blank=True)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=15000)
    
    class Meta:
        unique_together = ('nombre', 'departamento')
        ordering = ['departamento', 'nombre']
    
    def __str__(self):
        return f"{self.nombre}, {self.departamento.nombre}"

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20, blank=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)
    municipio = models.ForeignKey(Municipio, on_delete=models.SET_NULL, null=True, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)  # Para compatibilidad
    direccion = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Cliente: {self.user.get_full_name()}"


class UbicacionCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ubicaciones_guardadas')
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE)
    direccion = models.TextField()
    alias = models.CharField(max_length=100, blank=True)
    fecha_ultima_vez = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_ultima_vez']
        unique_together = ('cliente', 'municipio', 'direccion')

    def __str__(self):
        nombre_alias = f" ({self.alias})" if self.alias else ''
        return f"{self.municipio.nombre}, {self.departamento.nombre if self.departamento else ''}{nombre_alias}"

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Categorías"
    
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad_disponible = models.IntegerField()
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    tallas = models.CharField(max_length=200, blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre
    
    @property
    def disponible(self):
        return self.cantidad_disponible > 0

    @property
    def tallas_lista(self):
        return [item['tamano'] for item in self.tallas_con_stock]

    @property
    def tallas_con_stock(self):
        """Retorna lista de dicts: [{'tamano': '26', 'stock': 3}, ...]."""
        resultado = []

        for fragmento in (self.tallas or '').split(','):
            dato = fragmento.strip()
            if not dato:
                continue

            if ':' in dato:
                tamano_raw, stock_raw = dato.split(':', 1)
            else:
                tamano_raw, stock_raw = dato, ''

            tamano = tamano_raw.strip()
            if not tamano:
                continue

            stock = None
            stock_limpio = stock_raw.strip()
            if stock_limpio != '':
                try:
                    stock = int(Decimal(stock_limpio))
                except Exception:
                    stock = None

            resultado.append({
                'tamano': tamano,
                'stock': stock,
            })

        return resultado

    def stock_por_talla(self, talla):
        talla_buscada = str(talla or '').strip()
        if not talla_buscada:
            return None

        for item in self.tallas_con_stock:
            if item['tamano'] == talla_buscada:
                return item['stock']
        return None

    def actualizar_stock_talla(self, talla, nuevo_stock):
        """Actualiza el stock de un tamaño y reescribe el campo tallas."""
        talla_objetivo = str(talla or '').strip()
        if not talla_objetivo:
            return

        actualizado = []
        stock_normalizado = max(0, int(nuevo_stock))

        for item in self.tallas_con_stock:
            tamano = item['tamano']
            stock = item['stock'] if item['stock'] is not None else 0
            if tamano == talla_objetivo:
                stock = stock_normalizado
            actualizado.append(f"{tamano}:{stock}")

        self.tallas = ','.join(actualizado)

class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    numero_pedido = models.CharField(max_length=50, unique=True)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='efectivo', blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)
    municipio = models.ForeignKey(Municipio, on_delete=models.SET_NULL, null=True, blank=True)
    ciudad_entrega = models.CharField(max_length=100, blank=True)  # Para compatibilidad
    direccion_entrega = models.TextField()
    notas = models.TextField(blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Pedido {self.numero_pedido}"
    
    @property
    def puede_editarse(self):
        tiempo_transcurrido = timezone.now() - self.fecha_pedido
        return tiempo_transcurrido.total_seconds() < 900  # 15 minutos
    
    @property
    def total_final(self):
        return self.total + self.costo_envio - self.descuento

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    talla = models.CharField(max_length=20, blank=True, default='')
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

class Reporte(models.Model):
    ESTADOS_REPORTE = [
        ('nuevo', 'Nuevo'),
        ('en_revision', 'En revisión'),
        ('resuelto', 'Resuelto'),
    ]
    
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='reportes/', blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_REPORTE, default='nuevo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    respuesta_admin = models.TextField(blank=True)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Reporte del pedido {self.pedido.numero_pedido}"

class Carrito(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Carrito de {self.cliente.user.username}"
    
    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    talla = models.CharField(max_length=20, blank=True, default='')
    cantidad = models.IntegerField()
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"
    
    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad
