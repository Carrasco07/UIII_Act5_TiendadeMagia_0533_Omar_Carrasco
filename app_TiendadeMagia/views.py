from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F
from django.db import transaction # Usado para asegurar la integridad de las operaciones
from datetime import date 
import decimal # Para manejar DecimalFields con seguridad

# IMPORTACIONES CLAVE: Incluir todas las clases y constantes
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
            print(f"Error al guardar producto: {e}")
            return render(request, 'producto/agregar_producto.html', {
                'error_message': 'Hubo un error al guardar el producto.',
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
            print(f"Error al actualizar producto: {e}")
            return render(request, 'producto/actualizar_producto.html', {
                'producto': producto,
                'error_message': 'Hubo un error al actualizar el producto.',
                'titulo': 'Actualizar Producto'
            })
    return render(request, 'producto/actualizar_producto.html', {
        'producto': producto,
        'titulo': 'Actualizar Producto'
    })


def realizar_actualizacion_producto(request, producto_id):
    # Esta vista es innecesaria si actualizar_producto maneja POST.
    # Si la mantienes, asegúrate de que solo redirija o use la lógica de POST de actualizar_producto
    return redirect('actualizar_producto', producto_id=producto_id) # Redirigir a la vista que maneja el POST


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
# VISTAS CRUD DE ORDEN DE VENTA
# =========================================================================

def ver_ordenes(request):
    """Muestra la lista de todas las órdenes de venta."""
    ordenes = OrdenDeVenta.objects.all().order_by('-fecha_orden')
    return render(request, 'orden/ver_ordenes.html', {
        'ordenes': ordenes,
        'titulo': 'Ver Órdenes de Venta'
    })

def agregar_orden(request):
    if request.method == 'POST':
        cliente = request.POST.get('cliente')
        direccion_envio = request.POST.get('direccion_envio')
        estado = request.POST.get('estado')
        metodo_pago = request.POST.get('metodo_pago')
        comentarios = request.POST.get('comentarios')
        
        if not cliente or not direccion_envio:
            return render(request, 'orden/agregar_orden.html', {
                'titulo': 'Agregar Orden de Venta',
                'error': 'Faltan campos obligatorios: Cliente y Dirección.',
                'estado_choices': ESTADO_CHOICES,
                'metodo_choices': METODO_CHOICES
            })

        OrdenDeVenta.objects.create(
            cliente=cliente,
            direccion_envio=direccion_envio,
            estado=estado,
            metodo_pago=metodo_pago,
            comentarios=comentarios,
            total=0.00
        )
        return redirect('ver_ordenes')
            
    return render(request, 'orden/agregar_orden.html', {
        'titulo': 'Agregar Orden de Venta',
        'estado_choices': ESTADO_CHOICES,
        'metodo_choices': METODO_CHOICES
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
        orden.delete()
        return redirect('ver_ordenes')
    return render(request, 'orden/eliminar_orden.html', {
        'orden': orden,
        'titulo': f'Eliminar Orden #{orden.pk}'
    })
    
# =========================================================================
# VISTAS CRUD DE DETALLE DE ORDEN (Fase 3 - CORREGIDAS)
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
    productos = Producto.objects.all().filter(stock__gt=0) # Solo productos en stock

    if request.method == 'POST':
        orden_id = request.POST.get('orden')
        producto_id = request.POST.get('producto')
        cantidad_str = request.POST.get('cantidad')
        
        # CAPTURA DE NUEVOS CAMPOS
        descuento_str = request.POST.get('descuento', '0.00') 
        observaciones = request.POST.get('observaciones', '')
        
        try:
            orden = get_object_or_404(OrdenDeVenta, pk=orden_id)
            producto = get_object_or_404(Producto, pk=producto_id)
            
            # Conversión y validación
            cantidad = int(cantidad_str)
            descuento = decimal.Decimal(descuento_str or '0.00') 
            
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a cero.")
            if descuento < 0:
                 raise ValueError("El descuento no puede ser negativo.")

            precio_unitario = producto.precio 
            
            # CALCULAR SUBTOTAL
            subtotal_calc = (precio_unitario * cantidad) - descuento
            if subtotal_calc < 0:
                 raise ValueError("El subtotal no puede ser negativo. Revise el descuento.")

            detalle_existente = DetalleOrden.objects.filter(
                orden=orden,
                producto=producto
            ).first()

            with transaction.atomic():
                if detalle_existente:
                    # Lógica simple: sumar cantidad y recalcular subtotal
                    detalle_existente.cantidad += cantidad
                    detalle_existente.descuento += descuento # Sumar descuento al existente
                    detalle_existente.subtotal = detalle_existente.subtotal_calculado # Recalcular
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
        
        # Captura y validación de campos
        cantidad = int(request.POST.get('cantidad'))
        descuento = decimal.Decimal(request.POST.get('descuento', '0.00') or '0.00')
        observaciones = request.POST.get('observaciones')
        
        if cantidad <= 0 or descuento < 0:
             return redirect('editar_detalle', pk=pk) # Mejorar la validación con mensaje de error

        # Asignación de objetos
        orden_nueva = get_object_or_404(OrdenDeVenta, pk=request.POST.get('orden'))
        nuevo_producto = get_object_or_404(Producto, pk=request.POST.get('producto'))
        
        with transaction.atomic():
            # Actualizar campos
            detalle.orden = orden_nueva
            detalle.cantidad = cantidad
            detalle.descuento = descuento
            detalle.observaciones = observaciones

            if detalle.producto.pk != nuevo_producto.pk:
                detalle.precio_unitario = nuevo_producto.precio 
            detalle.producto = nuevo_producto
            
            # Recalcular Subtotal antes de guardar
            detalle.subtotal = detalle.subtotal_calculado
            detalle.save()
        
            # Recalcular totales de órdenes
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
            actualizar_total_orden(orden_pk) # Actualiza el total de la orden afectada
            
        return redirect('ver_detalles')

    return render(request, 'orden/eliminar_detalle.html', {
        'detalle': detalle,
        'titulo': f'Eliminar Detalle #{detalle.pk}'
    })


# =========================================================================
# VISTA DE REPORTES
# =========================================================================

def ver_reportes(request):
    """Vista mínima para el módulo de reportes."""
    return render(request, 'reportes/ver_reportes.html', {'titulo': 'Reportes'})