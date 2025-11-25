from django.urls import path
from . import views

urlpatterns = [
    # --- RUTAS PÚBLICAS Y DE AUTENTICACIÓN ---
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'), 
    path('register/', views.register_view, name='register'), 
    path('logout/', views.logout_view, name='logout'),
    path('servicios/', views.services_view, name='services'),

    # --- RUTAS DE PACIENTES (CLIENTES) ---
    path('reservar/', views.reserve_appointment, name='reserve_appointment'), 
    path('mis-citas/', views.my_appointments, name='my_appointments'), 
    path('reservar/horas-disponibles/', views.get_available_times_view, name='get_available_times'),
    path('reserva/exitosa/', views.appointment_success, name='appointment_success'),
    path('mis-citas/modificar/<int:pk>/', views.modify_appointment_view, name='modify_appointment'),
    path('mis-citas/cancelar/<int:pk>/', views.cancel_appointment_view, name='cancel_appointment'),


    # --- RUTAS DE RECEPCIONISTA (REQUIEREN @recepcionista_required) ---
    # ¡ESTA LÍNEA ES LA QUE DEBISTE ELIMINAR O COMENTAR!
    path('recepcion/login/', views.recepcionista_login_view, name='recepcionista_login'),
    path('panel/recepcion/', views.panel_recepcion_view, name='panel_recepcion'),
    path('panel/recepcion/confirmar/<int:pk>/', views.confirm_appointment_view, name='confirm_appointment'),
    path('panel/recepcion/modificar/<int:pk>/', views.modify_appointment_view, name='modify_appointment'), 
    path('panel/recepcion/cobrar/<int:pk>/', views.cobrar_cita_view, name='cobrar_cita'),

    # --- RUTAS DE ESTILISTA (REQUIEREN @estilista_required) ---
    path('panel/estilista/', views.panel_estilista_view, name='panel_estilista'),
    path('panel/estilista/atendido/<int:pk>/', views.mark_attended_view, name='mark_attended'),
    path('equipo/', views.conoce_equipo_view, name='conoce_equipo'),
]