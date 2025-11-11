from django.urls import path
from . import views

urlpatterns = [
    # VISTAS GENERALES
    path('', views.inicio_TiendadeMagia, name='inicio'),
    path('reportes/', views.ver_reportes, name='ver_reportes'), # Se mantiene la URL oculta

    # CRUD DE PRODUCTO (Fase 1)
    path('productos/', views.ver_producto, name='ver_producto'),
    path('producto/agregar/', views.agregar_producto, name='agregar_producto'),
    path('producto/actualizar/<int:producto_id>/', views.actualizar_producto, name='actualizar_producto'),
    path('producto/borrar/<int:producto_id>/', views.borrar_producto, name='borrar_producto'),

    # CRUD DE ORDEN DE VENTA (Fase 2)
    path('ordenes/', views.ver_ordenes, name='ver_ordenes'),
    path('orden/agregar/', views.agregar_orden, name='agregar_orden'),
    path('orden/editar/<int:pk>/', views.editar_orden, name='editar_orden'),
    path('orden/eliminar/<int:pk>/', views.eliminar_orden, name='eliminar_orden'),
    
    # CRUD DE DETALLE DE ORDEN (Fase 3)
    path('detalles/', views.ver_detalles, name='ver_detalles'),
    path('detalles/agregar/', views.agregar_detalle, name='agregar_detalle'),
    path('detalles/editar/<int:pk>/', views.editar_detalle, name='editar_detalle'),
    path('detalles/eliminar/<int:pk>/', views.eliminar_detalle, name='eliminar_detalle'),
]