from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F
from django.db import transaction 
from datetime import date 
import decimal

# IMPORTACIONES CLAVE
from .models import (
    Producto, 
    OrdenDeVenta, 
    DetalleOrden, 
    ESTADO_CHOICES,
    METODO_CHOICES
) 

# =========================================================================
# FUNCIONES DE UTILIDAD
# =========================================================================

def actualizar_total_orden(orden_pk):
    """Calcula la suma de todos los subtotales de los detalles de una orden y actualiza el campo total."""
    
    try:
        orden = OrdenDeVenta.objects.get(pk=orden_pk)
    except OrdenDeVenta.DoesNotExist:
        return 

    # Calcula el total sumando el campo 'subtotal' de todos los detalles
    nuevo_total = DetalleOrden.objects.filter(orden=orden).aggregate(
        total_calculado=Sum('subtotal')
    )['total_calculado'] or decimal.Decimal('0.00')
        
    orden.total = nuevo_total
    orden.save()


# =========================================================================
# VISTAS GENERALES
# =========================================================================

def inicio_TiendadeMagia(request):
    """Muestra la página de inicio del sistema."""
    return render(request, 'inicio.html', {
        'titulo': 'Sistema de Administración de Tienda de Magia'
    })

# =========================================================================
# VISTAS CRUD DE PRODUCTO
# =========================================================================

def ver_producto(request):
    """Muestra la lista de todos los productos en una tabla."""
    productos = Producto.objects.all().order_by('nombre')
    return render(request, 'producto/ver_producto.html', {
        'productos': productos,
        'titulo': 'Ver Productos'
    })

def agregar_producto(request):
    if request.method == 'POST':
        try:
            Producto.objects.create(
                nombre=request.POST['nombre'],
                descripcion=request.POST['descripcion'],
                categoria=request.POST['categoria'],
                precio=request.POST['precio'],
                proveedor=request.POST['proveedor'],
                stock=request.POST.get('stock', 0),
                fecha_registro=request.POST.get('fecha_registro', date.today()) 
            )
            return redirect('ver_producto')
        except Exception as e:
            return render(request, 'producto/agregar_producto.html', {
                'error_message': f'Hubo un error al guardar el producto: {e}',
                'titulo': 'Agregar Producto'
            })
            
    return render(request, 'producto/agregar_producto.html', {
        'titulo': 'Agregar Producto'
    })

def actualizar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        try:
            producto.nombre = request.POST['nombre']
            producto.descripcion = request.POST['descripcion']
            producto.categoria = request.POST['categoria']
            producto.precio = request.POST['precio']
            producto.proveedor = request.POST['proveedor']
            producto.stock = request.POST.get('stock', producto.stock)
            producto.fecha_registro = request.POST['fecha_registro']
            
            producto.save()
            return redirect('ver_producto')
        except Exception as e:
            return render(request, 'producto/actualizar_producto.html', {
                'producto': producto,
                'error_message': f'Hubo un error al actualizar el producto: {e}',
                'titulo': 'Actualizar Producto'
            })
    return render(request, 'producto/actualizar_producto.html', {
        'producto': producto,
        'titulo': 'Actualizar Producto'
    })


def borrar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        try:
            producto.delete()
            return redirect('ver_producto')
        except Exception as e:
            return render(request, 'producto/borrar_producto.html', {
                'producto': producto,
                'error_message': 'No se pudo eliminar el producto. Podría estar asociado a una Orden de Venta.',
                'titulo': 'Borrar Producto'
            })
    return render(request, 'producto/borrar_producto.html', {
        'producto': producto,
        'titulo': 'Borrar Producto'
    })

# =========================================================================
# VISTAS CRUD DE ORDEN DE VENTA (MODIFICADA)
# =========================================================================

def ver_ordenes(request):
    """Muestra la lista de todas las órdenes de venta."""
    ordenes = OrdenDeVenta.objects.all().order_by('-fecha_orden')
    
    # MODIFICACIÓN: Añadir el primer detalle a cada orden para mostrarlo en la tabla
    for orden in ordenes:
        primer_detalle = orden.detalles.select_related('producto').first() 
        orden.producto_muestra = primer_detalle.producto.nombre if primer_detalle else 'Sin productos'
        orden.cantidad_muestra = primer_detalle.cantidad if primer_detalle else 0
        
    return render(request, 'orden/ver_ordenes.html', {
        'ordenes': ordenes,
        'titulo': 'Ver Órdenes de Venta'
    })

def agregar_orden(request):
    productos = Producto.objects.all().filter(stock__gt=0) # Productos disponibles
    
    if request.method == 'POST':
        cliente = request.POST.get('cliente')
        direccion_envio = request.POST.get('direccion_envio')
        estado = request.POST.get('estado')
        metodo_pago = request.POST.get('metodo_pago')
        comentarios = request.POST.get('comentarios')
        
        # Nuevos campos del formulario para el producto inicial
        producto_id = request.POST.get('producto_inicial')
        cantidad_inicial_str = request.POST.get('cantidad_inicial')
        
        if not cliente or not direccion_envio or not producto_id or not cantidad_inicial_str:
            return render(request, 'orden/agregar_orden.html', {
                'titulo': 'Agregar Orden de Venta',
                'error': 'Faltan campos obligatorios: Cliente, Dirección y Producto Inicial.',
                'estado_choices': ESTADO_CHOICES,
                'metodo_choices': METODO_CHOICES,
                'productos': productos
            })

        try:
            cantidad_inicial = int(cantidad_inicial_str)
            producto = get_object_or_404(Producto, pk=producto_id)
            
            if cantidad_inicial <= 0:
                 raise ValueError("La cantidad debe ser mayor a cero.")
            
            with transaction.atomic():
                # 1. Crear la Orden de Venta
                nueva_orden = OrdenDeVenta.objects.create(
                    cliente=cliente,
                    direccion_envio=direccion_envio,
                    estado=estado,
                    metodo_pago=metodo_pago,
                    comentarios=comentarios,
                    total=0.00
                )
                
                # 2. Crear el DetalleOrden con el producto inicial
                precio_unitario = producto.precio
                subtotal_calc = precio_unitario * cantidad_inicial
                
                DetalleOrden.objects.create(
                    orden=nueva_orden,
                    producto=producto,
                    cantidad=cantidad_inicial,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal_calc,
                    descuento=decimal.Decimal('0.00'),
                    observaciones="Producto inicial al crear orden."
                )
                
                # 3. Actualizar el Total de la Orden
                actualizar_total_orden(nueva_orden.pk)
            
            return redirect('ver_ordenes')
            
        except (ValueError, Exception) as e:
             return render(request, 'orden/agregar_orden.html', {
                'titulo': 'Agregar Orden de Venta',
                'error': f'Error al procesar el producto: {e}',
                'estado_choices': ESTADO_CHOICES,
                'metodo_choices': METODO_CHOICES,
                'productos': productos
            })
            
    return render(request, 'orden/agregar_orden.html', {
        'titulo': 'Agregar Orden de Venta',
        'estado_choices': ESTADO_CHOICES,
        'metodo_choices': METODO_CHOICES,
        'productos': productos
    })

def editar_orden(request, pk):
    orden = get_object_or_404(OrdenDeVenta, pk=pk)
    
    if request.method == 'POST':
        orden.cliente = request.POST.get('cliente')
        orden.direccion_envio = request.POST.get('direccion_envio')
        orden.estado = request.POST.get('estado')
        orden.metodo_pago = request.POST.get('metodo_pago')
        orden.comentarios = request.POST.get('comentarios')
        orden.save()
        return redirect('ver_ordenes')

    return render(request, 'orden/editar_orden.html', {
        'orden': orden,
        'titulo': f'Editar Orden #{orden.pk}',
        'estado_choices': ESTADO_CHOICES,
        'metodo_choices': METODO_CHOICES
    })
    
def eliminar_orden(request, pk):
    orden = get_object_or_404(OrdenDeVenta, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            orden.delete()
        return redirect('ver_ordenes')
    return render(request, 'orden/eliminar_orden.html', {
        'orden': orden,
        'titulo': f'Eliminar Orden #{orden.pk}'
    })
    
# =========================================================================
# VISTAS CRUD DE DETALLE DE ORDEN
# =========================================================================

def ver_detalles(request):
    """Muestra la lista de todos los detalles de órdenes."""
    detalles = DetalleOrden.objects.all().order_by('-orden__fecha_orden')
    
    return render(request, 'orden/ver_detalles.html', {
        'detalles': detalles,
        'titulo': 'Ver Detalles de Órdenes'
    })

def agregar_detalle(request):
    ordenes = OrdenDeVenta.objects.all()
    productos = Producto.objects.all().filter(stock__gt=0)

    if request.method == 'POST':
        orden_id = request.POST.get('orden')
        producto_id = request.POST.get('producto')
        cantidad_str = request.POST.get('cantidad')
        
        descuento_str = request.POST.get('descuento', '0.00') 
        observaciones = request.POST.get('observaciones', '')
        
        try:
            orden = get_object_or_404(OrdenDeVenta, pk=orden_id)
            producto = get_object_or_404(Producto, pk=producto_id)
            
            cantidad = int(cantidad_str)
            descuento = decimal.Decimal(descuento_str or '0.00') 
            
            if cantidad <= 0 or descuento < 0:
                raise ValueError("Cantidad y Descuento deben ser válidos.")

            precio_unitario = producto.precio 
            subtotal_calc = (precio_unitario * cantidad) - descuento
            
            if subtotal_calc < 0:
                 raise ValueError("El subtotal no puede ser negativo.")

            detalle_existente = DetalleOrden.objects.filter(
                orden=orden,
                producto=producto
            ).first()

            with transaction.atomic():
                if detalle_existente:
                    detalle_existente.cantidad += cantidad
                    detalle_existente.descuento += descuento
                    detalle_existente.subtotal = detalle_existente.subtotal_calculado
                    detalle_existente.save()
                else:
                    DetalleOrden.objects.create(
                        orden=orden,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal_calc,      
                        descuento=descuento,         
                        observaciones=observaciones  
                    )
            
            actualizar_total_orden(orden.pk)
            return redirect('ver_detalles')
            
        except (ValueError, Exception) as e:
            error_msg = f'Error al guardar: Asegúrate de que todos los campos sean válidos. Detalle: {e}'
            return render(request, 'orden/agregar_detalle.html', {
                'error': error_msg,
                'titulo': 'Agregar Detalle de Orden',
                'ordenes': ordenes,
                'productos': productos
            })

    return render(request, 'orden/agregar_detalle.html', {
        'titulo': 'Agregar Detalle de Orden',
        'ordenes': ordenes,
        'productos': productos
    })

def editar_detalle(request, pk):
    detalle = get_object_or_404(DetalleOrden, pk=pk)
    ordenes = OrdenDeVenta.objects.all()
    productos = Producto.objects.all()

    if request.method == 'POST':
        orden_anterior_pk = detalle.orden.pk 
        
        cantidad = int(request.POST.get('cantidad'))
        descuento = decimal.Decimal(request.POST.get('descuento', '0.00') or '0.00')
        observaciones = request.POST.get('observaciones')
        
        if cantidad <= 0 or descuento < 0:
             return redirect('editar_detalle', pk=pk) 

        orden_nueva = get_object_or_404(OrdenDeVenta, pk=request.POST.get('orden'))
        nuevo_producto = get_object_or_404(Producto, pk=request.POST.get('producto'))
        
        with transaction.atomic():
            detalle.orden = orden_nueva
            detalle.cantidad = cantidad
            detalle.descuento = descuento
            detalle.observaciones = observaciones

            if detalle.producto.pk != nuevo_producto.pk:
                detalle.precio_unitario = nuevo_producto.precio 
            detalle.producto = nuevo_producto
            
            detalle.subtotal = detalle.subtotal_calculado
            detalle.save()
        
            if orden_anterior_pk != detalle.orden.pk:
                 actualizar_total_orden(orden_anterior_pk)
            
            actualizar_total_orden(detalle.orden.pk)
            return redirect('ver_detalles')

    return render(request, 'orden/editar_detalle.html', {
        'detalle': detalle,
        'titulo': f'Editar Detalle #{detalle.pk}',
        'ordenes': ordenes,
        'productos': productos
    })

def eliminar_detalle(request, pk):
    detalle = get_object_or_404(DetalleOrden, pk=pk)
    
    if request.method == 'POST':
        orden_pk = detalle.orden.pk 
        
        with transaction.atomic():
            detalle.delete()
            actualizar_total_orden(orden_pk)
            
        return redirect('ver_detalles')

    return render(request, 'orden/eliminar_detalle.html', {
        'detalle': detalle,
        'titulo': f'Eliminar Detalle #{detalle.pk}'
    })


# =========================================================================
# VISTA DE REPORTES (Mínima)
# =========================================================================

def ver_reportes(request):
    """Vista mínima para el módulo de reportes."""
    return render(request, 'reportes/ver_reportes.html', {'titulo': 'Reportes'})