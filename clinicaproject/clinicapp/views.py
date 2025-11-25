from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .decorators import recepcionista_required, estilista_required, admin_or_recepcionista_required

# --- ASUMIENDO QUE ESTAS CLASES/FUNCIONES EXISTEN EN ARCHIVOS HERMANOS ---
from .forms import (
    RegisterForm,
    AppointmentForm,
    RecepcionistaLoginForm,
    ModifyAppointmentForm,
)
from .models import Service, Specialist, Appointment
from .decorators import recepcionista_required, estilista_required
from .utils import get_available_times # Para la vista AJAX

# --- Función Auxiliar Requerida (Placeholder) ---
def calcular_descuento_cumpleaños(user):
    """
    [PLACEHOLDER] Lógica para calcular un descuento, por ejemplo, por cumpleaños.
    Se requiere en cobrar_cita_view pero no estaba definida.
    """
    # Lógica de ejemplo: 0.0 significa 0% de descuento.
    return 0.0

# --- VISTAS PÚBLICAS Y DE AUTENTICACIÓN ---

def home(request):
    """Muestra la página de inicio."""
    return render(request, 'clinicapp/home.html', {
        'services': Service.objects.all()[:3],
        'specialists': Specialist.objects.all()[:3]
    })

def services_view(request):
    """Muestra todos los tratamientos/servicios."""
    services = Service.objects.all()
    return render(request, 'clinicapp/services.html', {'services': services})

def register_view(request):
    """Maneja el registro de nuevos usuarios (pacientes)."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Registro exitoso. ¡Bienvenido, {user.username}!")
            return redirect('home')
    else:
        form = RegisterForm()
    
    return render(request, 'clinicapp/register.html', {'form': form})

def login_view(request):
    """
    Maneja el inicio de sesión y redirige al usuario al panel de su rol.
    """
    # 1. Redirección si ya está autenticado
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Recepcionista').exists():
            return redirect('panel_recepcion')
        if request.user.groups.filter(name='Estilista').exists():
            return redirect('panel_estilista')
        return redirect('my_appointments') # Pacientes

    # 2. Procesar POST (intento de login)
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bienvenido, {user.username}.")
            
            # LÓGICA DE REDIRECCIÓN POR ROL
            if user.groups.filter(name='Recepcionista').exists():
                return redirect('panel_recepcion')
            
            if user.groups.filter(name='Estilista').exists():
                return redirect('panel_estilista')
            
            return redirect('my_appointments') # Si es solo un paciente

        else:
            messages.error(request, "Usuario o contraseña inválidos.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'clinicapp/login.html', {'form': form})

def logout_view(request):
    """Cierra la sesión del usuario."""
    logout(request)
    messages.info(request, "Sesión cerrada con éxito.")
    return redirect('home')

# --- VISTAS DE PACIENTES (CLIENTES) ---

@login_required
def reserve_appointment(request):
    """Maneja la reserva de citas."""
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.patient = request.user 
            reservation.status = 'P' # Pendiente
            reservation.save()
            messages.success(request, "Cita reservada con éxito. Esperando confirmación.")
            return redirect('my_appointments')
    else:
        form = AppointmentForm()
    
    return render(request, 'clinicapp/reserve_appointment.html', {'form': form})

@login_required
def my_appointments(request):
    """Muestra todas las citas agendadas por el usuario actual (el cliente)."""
    appointments = Appointment.objects.filter(patient=request.user).order_by('date', 'time')
    
    return render(request, 'clinicapp/my_appointments.html', {'appointments': appointments})

# --- VISTAS AUXILIARES AJAX ---

def get_available_times_view(request):
    """
    Vista AJAX que retorna una lista JSON de las horas disponibles para un especialista y fecha.
    """
    specialist_id = request.GET.get('specialist_id')
    date_str = request.GET.get('date') 
    
    if not specialist_id or not date_str:
        return JsonResponse({'available_times': []}, status=400)

    try:
        available_times = get_available_times(specialist_id, date_str)
        return JsonResponse({'available_times': available_times})
    except Exception as e:
        return JsonResponse({'error': f"Error al obtener horarios: {str(e)}"}, status=500)

# --- VISTAS DE RECEPCIONISTA ---

def recepcionista_login_view(request):
    """Login específico para el personal de Recepción."""
    if request.user.is_authenticated and request.user.groups.filter(name='Recepcionista').exists():
         return redirect('panel_recepcion')
         
    if request.method == 'POST':
        form = RecepcionistaLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # VERIFICACIÓN DE GRUPO
            if hasattr(user, 'is_recepcionista') and user.is_recepcionista():
                login(request, user)
                messages.success(request, f"Bienvenido, {user.username}.")
                return redirect('panel_recepcion')
            else:
                messages.error(request, "Acceso denegado. Este login es solo para personal de Recepción.")
                return redirect('recepcionista_login') 
        else:
            messages.error(request, "Credenciales inválidas.")
    else:
        form = RecepcionistaLoginForm()
        
    return render(request, 'clinicapp/recepcionista_login.html', {'form': form})

@login_required 
@recepcionista_required 
def panel_recepcion_view(request):
    """Muestra el panel de control para la recepcionista, listando citas pendientes."""
    # Filtrar solo citas pendientes (status='P')
    citas_pendientes = Appointment.objects.filter(status='P').order_by('date', 'time')
    
    context = {
        'citas_pendientes': citas_pendientes
    }
    return render(request, 'clinicapp/panel_recepcion.html', context)

@login_required
@recepcionista_required
def confirm_appointment_view(request, pk):
    """Permite a la recepcionista confirmar (cambiar a 'C') una cita."""
    cita = get_object_or_404(Appointment, pk=pk)
    
    if cita.status == 'P':
        cita.status = 'C'
        cita.save()
        messages.success(request, f"Cita #{pk} CONFIRMADA con éxito para {cita.patient.get_full_name()}.")
    else:
        messages.warning(request, f"La Cita #{pk} ya estaba en estado '{cita.get_status_display()}'.")
        
    return redirect('panel_recepcion')

@login_required
@recepcionista_required
def cancel_appointment_view(request, pk):
    """Permite a la recepcionista cancelar (cambiar a 'X') una cita."""
    cita = get_object_or_404(Appointment, pk=pk)
    
    if cita.status != 'X':
        cita.status = 'X'
        cita.save()
        messages.success(request, f"Cita #{pk} CANCELADA con éxito para {cita.patient.get_full_name()}.")
    else:
        messages.warning(request, f"La Cita #{pk} ya estaba CANCELADA.")

    return redirect('panel_recepcion')

@login_required
@recepcionista_required
def modify_appointment_view(request, pk):
    """Permite a la recepcionista modificar la fecha y hora de una cita."""
    cita = get_object_or_404(Appointment, pk=pk)
    
    if request.method == 'POST':
        form = ModifyAppointmentForm(request.POST, instance=cita)
        if form.is_valid():
            form.save()
            date_str = cita.date.strftime('%d/%m/%Y') if cita.date else 'N/A'
            time_str = cita.time.strftime('%H:%M') if cita.time else 'N/A'
            messages.success(request, f"Cita #{pk} modificada con éxito. Nueva fecha: {date_str} a las {time_str}.")
            return redirect('panel_recepcion')
    else:
        form = ModifyAppointmentForm(instance=cita)
    
    context = {
        'form': form,
        'cita': cita,
        'patient_name': cita.patient.get_full_name(),
    }
    return render(request, 'clinicapp/modify_appointment.html', context)

@login_required
@recepcionista_required
def cobrar_cita_view(request, pk):
    """Maneja el proceso de cobro, calcula descuentos y finaliza la cita."""
    
    # 1. Obtener la cita
    cita = get_object_or_404(Appointment.objects.select_related('patient', 'service'), pk=pk)
    
    if cita.is_paid:
        messages.warning(request, f"La Cita #{cita.id} ya fue cobrada y completada.")
        return redirect('panel_recepcion')

    # 2. Lógica de cálculo de precios y descuentos
    precio_base = cita.service.price
    
    try:
        tasa_descuento = calcular_descuento_cumpleaños(cita.patient)
        descuento_aplicado = (tasa_descuento > 0.0)
    except Exception:
        tasa_descuento = 0.0
        descuento_aplicado = False
        messages.warning(request, "Advertencia: No se pudo verificar el descuento (función auxiliar no disponible).")
        
    monto_descuento = precio_base * tasa_descuento
    precio_final = precio_base - monto_descuento
    
    # 3. Procesar el formulario POST (Confirmación de pago)
    if request.method == 'POST':
        cita.is_paid = True
        cita.final_price = precio_final
        # Opcional: Cambiar estado a 'Finalizada' si tu modelo lo tiene.
        cita.save()
        
        messages.success(request, f"Cobro de Cita #{cita.id} realizado. Total: ${precio_final:.2f}. Cita completada.")
        return redirect('panel_recepcion')

    # 4. Mostrar la plantilla
    context = {
        'cita': cita,
        'paciente': cita.patient, 
        'precio_base': precio_base,
        'tasa_descuento': tasa_descuento * 100, # Para mostrar 20%
        'monto_descuento': monto_descuento,
        'precio_final': precio_final,
        'descuento_aplicado': descuento_aplicado,
    }
    
    return render(request, 'clinicapp/cobrar_cita.html', context)

# --- VISTAS DE ESTILISTA ---

@login_required
@estilista_required 
def panel_estilista_view(request):
    """Muestra las citas asignadas al especialista logueado."""
    
    # 1. Encontrar el perfil de Especialista 
    try:
        estilista = Specialist.objects.get(email=request.user.email)
    except Specialist.DoesNotExist:
        messages.error(request, "Tu cuenta no está vinculada a un perfil de Especialista. Contacta a un administrador.")
        return redirect('home')
        
    # 2. Filtrar las citas para ESE especialista
    citas_agendadas = Appointment.objects.filter(
        specialist=estilista,
        status__in=['P', 'C'], # Pendiente o Confirmada
        date__gte=timezone.localdate() # Hoy o futuras
    ).select_related('patient', 'service').order_by('date', 'time')
    
    context = {
        'estilista': estilista,
        'citas_agendadas': citas_agendadas
    }
    
    return render(request, 'clinicapp/panel_estilista.html', context)
def conoce_equipo(request):
    specialists = Specialist.objects.all()
    return render(request, 'clinicapp/conoce_al_equipo.html', {
        'specialists': specialists
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

# --- IMPORTACIONES DE ARCHIVOS LOCALES ---
from .forms import (
    RegisterForm,
    AppointmentForm,
    RecepcionistaLoginForm,
    ModifyAppointmentForm,
)
from .models import Service, Specialist, Appointment, PacienteProfile
from .decorators import recepcionista_required, estilista_required, is_in_group # Importamos is_in_group
from .utils import get_available_times, calcular_descuento_cumpleaños # Funciones auxiliares


# --- VISTAS PÚBLICAS Y DE AUTENTICACIÓN ---

# (Asumo que home, login_view, register_view, logout_view, services_view y conoce_equipo están implementadas)

# --- VISTAS DE PACIENTES (CLIENTES) ---

@login_required
def reserve_appointment(request):
    """Permite al cliente reservar una cita."""
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            
            # Validación de superposición (ya se hace en el formulario/utils, pero seguridad extra)
            if Appointment.objects.filter(
                specialist=appointment.specialist,
                date=appointment.date,
                time=appointment.time,
                status__in=['P', 'C']
            ).exists():
                messages.error(request, "La hora seleccionada ya no está disponible.")
                return redirect('reserve_appointment')

            appointment.save()
            messages.success(request, "Cita reservada con éxito. Pendiente de confirmación.")
            return redirect('appointment_success')
        else:
            # Añade mensajes de error para mostrar en la plantilla
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
    else:
        form = AppointmentForm()
        
    context = {
        'form': form,
        'services': Service.objects.all(),
        'specialists': Specialist.objects.all(),
    }
    return render(request, 'clinicapp/reserve_appointment.html', context)


def appointment_success(request):
    return render(request, 'clinicapp/appointment_success.html')


@login_required
def my_appointments(request):
    """Lista las citas del paciente logueado."""
    appointments = Appointment.objects.filter(
        patient=request.user
    ).select_related('service', 'specialist').order_by('-date', '-time')
    
    context = {'appointments': appointments}
    return render(request, 'clinicapp/my_appointments.html', context)


@login_required
def get_available_times_view(request):
    """Vista AJAX para obtener horarios disponibles."""
    specialist_id = request.GET.get('specialist_id')
    date_str = request.GET.get('date')

    # Valida la fecha para evitar errores en get_available_times
    if not specialist_id or not date_str:
        return JsonResponse([], safe=False)

    available_times = get_available_times(specialist_id, date_str)
    return JsonResponse(available_times, safe=False)


# --- VISTAS DE RECEPCIONISTA ---

# Nota: La función is_in_group ahora está en decorators.py y se importa.
def recepcionista_login_view(request):
    """Login específico para el personal de Recepción."""
    if request.user.is_authenticated and is_in_group(request.user, 'Recepcionista'):
         return redirect('panel_recepcion')
         
    if request.method == 'POST':
        form = RecepcionistaLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # VERIFICACIÓN DE GRUPO (Usando la función auxiliar is_in_group)
            if is_in_group(user, 'Recepcionista'):
                login(request, user)
                messages.success(request, f"Bienvenido, {user.username} (Recepcionista).")
                return redirect('panel_recepcion')
            else:
                messages.error(request, "Acceso denegado. Este login es solo para personal de Recepción.")
                return redirect('recepcionista_login') 
        else:
            messages.error(request, "Credenciales inválidas.")
    else:
        form = RecepcionistaLoginForm()
        
    # La plantilla recepcion_login.html es necesaria para esta vista
    return render(request, 'clinicapp/recepcion_login.html', {'form': form})


@login_required 
@recepcionista_required 
def panel_recepcion_view(request):
    """Muestra el panel de control para la recepcionista."""
    
    # 1. Filtrar por fecha si se proporciona un filtro
    date_filter = request.GET.get('date')
    
    citas = Appointment.objects.filter(
        date__gte=timezone.localdate(), # Desde hoy en adelante
        status__in=['P', 'C'] # Pendientes o Confirmadas
    ).select_related('patient', 'service', 'specialist')

    if date_filter:
        citas = citas.filter(date=date_filter)
        
    citas = citas.order_by('date', 'time')
    
    context = {
        'upcoming': citas,
        'has_filter': 'date' in request.GET
    }
    return render(request, 'clinicapp/panel_recepcion.html', context)


@login_required
@recepcionista_required
@transaction.atomic
def confirm_appointment_view(request, pk):
    """Confirma una cita y notifica al paciente."""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if appointment.status != 'P':
        messages.warning(request, f"La cita #{pk} ya fue {appointment.get_status_display()}.")
    else:
        appointment.status = 'C' # 'C' = Confirmada
        appointment.save()
        messages.success(request, f"Cita #{pk} con {appointment.patient.username} ha sido CONFIRMADA.")
        
    # Redirige al panel o a la página anterior
    return redirect('panel_recepcion')


@login_required
@recepcionista_required
@transaction.atomic
def cancel_appointment_view(request, pk):
    """Cancela una cita."""
    appointment = get_object_or_404(Appointment, pk=pk)

    if appointment.status == 'X':
        messages.warning(request, f"La cita #{pk} ya estaba cancelada.")
    else:
        appointment.status = 'X' # 'X' = Cancelada
        appointment.save()
        messages.success(request, f"Cita #{pk} con {appointment.patient.username} ha sido CANCELADA.")
        
    # Comprobación de origen (puede ser Recepcionista o Estilista)
    if is_in_group(request.user, 'Recepcionista'):
        return redirect('panel_recepcion')
    elif is_in_group(request.user, 'Estilista'):
        return redirect('panel_estilista')
    
    return redirect('my_appointments') # Fallback o si es un cliente


@login_required
@recepcionista_required
@transaction.atomic
def modify_appointment_view(request, pk):
    """Permite a la recepcionista modificar la fecha y hora de una cita."""
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == 'POST':
        form = ModifyAppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cita #{pk} modificada con éxito.")
            return redirect('panel_recepcion')
        else:
             # Añade mensajes de error del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        # Inicializa el formulario con la instancia existente
        form = ModifyAppointmentForm(instance=appointment)

    context = {
        'appointment': appointment,
        'form': form,
    }
    return render(request, 'clinicapp/modify_appointment.html', context)


@login_required
@recepcionista_required
@transaction.atomic
def cobrar_cita_view(request, pk):
    """
    Vista para registrar el pago de una cita.
    Recupera los datos, calcula descuentos y registra el pago.
    """
    appointment = get_object_or_404(Appointment, pk=pk, status__in=['C', 'F'])

    if request.method == 'POST':
        # En una app real, aquí se procesaría el pago (ej. tarjeta, efectivo)
        # Asumimos que el monto final ya está calculado en el front o aquí
        
        monto_pagado = request.POST.get('final_amount')
        
        if not monto_pagado:
             messages.error(request, "El monto de pago es obligatorio.")
             return redirect('cobrar_cita', pk=pk)
             
        try:
            final_price = Decimal(monto_pagado)
        except:
             messages.error(request, "Monto inválido.")
             return redirect('cobrar_cita', pk=pk)
             
        if final_price < 0:
            messages.error(request, "El monto no puede ser negativo.")
            return redirect('cobrar_cita', pk=pk)
            
        # 1. Registrar el pago en la cita
        appointment.final_price = final_price
        appointment.is_paid = True
        appointment.status = 'F' # Marcar como finalizada/pagada
        appointment.save()
        
        messages.success(request, f"Pago de ${final_price} registrado con éxito para la cita #{pk}.")
        return redirect('panel_recepcion')

    # --- Lógica GET para mostrar detalles del cobro ---
    
    # Precio base del servicio
    precio_base = appointment.service.price
    
    # Calcula el descuento (ej. cumpleaños)
    tasa_descuento = calcular_descuento_cumpleaños(appointment.patient)
    
    if tasa_descuento > 0:
        monto_descuento = precio_base * Decimal(tasa_descuento)
        precio_final = precio_base - monto_descuento
        descuento_aplicado = True
    else:
        monto_descuento = Decimal(0)
        precio_final = precio_base
        descuento_aplicado = False

    context = {
        'appointment': appointment,
        'precio_base': precio_base,
        'tasa_descuento': tasa_descuento * 100, # Para mostrar 20%
        'monto_descuento': monto_descuento,
        'precio_final': precio_final,
        'descuento_aplicado': descuento_aplicado,
    }
    
    return render(request, 'clinicapp/cobrar_cita.html', context)


# --- VISTAS DE ESTILISTA ---

@login_required
@estilista_required 
def panel_estilista_view(request):
    """Muestra las citas asignadas al especialista logueado."""
    
    # 1. Encontrar el perfil de Especialista (asumo que se vincula por email)
    try:
        estilista = Specialist.objects.get(email=request.user.email)
    except Specialist.DoesNotExist:
        messages.error(request, "Tu cuenta no está vinculada a un perfil de Especialista. Contacta a un administrador.")
        return redirect('home')
        
    # 2. Filtrar las citas para ESE especialista
    # Solo citas Pendientes o Confirmadas, desde hoy en adelante
    citas_agendadas = Appointment.objects.filter(
        specialist=estilista,
        status__in=['P', 'C'], 
        date__gte=timezone.localdate()
    ).select_related('patient', 'service').order_by('date', 'time')
    
    context = {
        'estilista': estilista,
        'bookings': citas_agendadas,
    }
    return render(request, 'clinicapp/panel_estilista.html', context)


@login_required
@estilista_required
@transaction.atomic
def mark_attended_view(request, pk):
    """Permite al estilista marcar una cita como atendida (Finalizada)."""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Seguridad extra: Solo permite marcar si la cita le pertenece
    try:
        estilista = Specialist.objects.get(email=request.user.email)
        if appointment.specialist != estilista:
             messages.error(request, "No tienes permiso para modificar esta cita.")
             return redirect('panel_estilista')
    except Specialist.DoesNotExist:
        messages.error(request, "Error de perfil de especialista.")
        return redirect('home')
        
    if appointment.status == 'F':
        messages.warning(request, f"La cita #{pk} ya fue marcada como Finalizada.")
    elif appointment.status == 'X':
        messages.warning(request, f"La cita #{pk} está Cancelada.")
    else:
        # La marca como finalizada. La recepcionista luego la marcará como pagada
        appointment.status = 'F' 
        appointment.save()
        messages.success(request, f"Cita #{pk} con {appointment.patient.username} marcada como ATENDIDA (Finalizada).")
        
    return redirect('panel_estilista')
# En clinicapp/views.py
from .models import Specialist # Asegúrate de importar Specialist

def conoce_equipo(request):
    """Muestra la lista completa de especialistas."""
    context = {'specialists': Specialist.objects.all()}
    return render(request, 'clinicapp/conoce_al_equipo.html', context)
# En clinicapp/views.py

@admin_or_recepcionista_required # Aplica el decorador solo a la vista de recepción/admin
def modify_appointment_view(request, pk):
    """
    Permite a un paciente modificar su propia cita o a un Admin/Recepcionista modificar cualquier cita.
    """
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Comprobación de Propiedad o Rol (redundante con el decorador si se usa la URL de recepción, 
    # pero necesario si se comparte con el paciente)
    is_admin_or_recepcionista = request.user.is_superuser or request.user.is_staff or (hasattr(request.user, 'role') and request.user.role == 'reception')
    
    # Lógica para permitir solo al propietario modificar sus propias citas si no es staff
    if not is_admin_or_recepcionista and appointment.patient != request.user:
        messages.error(request, "No tiene permisos para modificar esta cita.")
        return redirect('my_appointments')

    # Restricción: El paciente no puede modificar citas ya Confirmadas o Finalizadas
    if appointment.status in ['C', 'F'] and not is_admin_or_recepcionista:
        messages.error(request, "Solo puede modificar citas en estado Pendiente.")
        return redirect('my_appointments')

    if request.method == 'POST':
        # ModifyAppointmentForm debe contener los campos necesarios para modificar la cita
        form = ModifyAppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cita #{pk} modificada exitosamente.")
            
            # Redirigir al panel de recepción si fue un admin/recepcionista quien la modificó
            if is_admin_or_recepcionista:
                 return redirect('panel_recepcion') 
            
            return redirect('my_appointments')
    else:
        form = ModifyAppointmentForm(instance=appointment)

    context = {
        'form': form,
        'appointment': appointment,
    }
    return render(request, 'clinicapp/modify_appointment.html', context)
# En clinicapp/views.py

@admin_or_recepcionista_required # Aplica el decorador solo a la vista de recepción/admin
def cancel_appointment_view(request, pk):
    """
    Permite a un paciente cancelar su propia cita o a un Admin/Recepcionista cancelar cualquier cita.
    """
    if request.method == 'POST' or request.GET: # Permite GET para el botón simple de cancelar
        appointment = get_object_or_404(Appointment, pk=pk)

        is_admin_or_recepcionista = request.user.is_superuser or request.user.is_staff or (hasattr(request.user, 'role') and request.user.role == 'reception')
        
        # Comprobación de Propiedad o Rol
        if not is_admin_or_recepcionista and appointment.patient != request.user:
            messages.error(request, "No tiene permisos para cancelar esta cita.")
            return redirect('my_appointments')

        # Comprobar estado: no se puede cancelar si ya está finalizada o cancelada
        if appointment.status == 'F':
            messages.warning(request, f"La cita #{pk} ya ha sido finalizada. No puede cancelarse.")
            return redirect('panel_recepcion' if is_admin_or_recepcionista else 'my_appointments')
        
        if appointment.status == 'X':
            messages.warning(request, f"La cita #{pk} ya estaba cancelada.")
            return redirect('panel_recepcion' if is_admin_or_recepcionista else 'my_appointments')

        # Cancelar la cita
        appointment.status = 'X' # 'X' es el código para Cancelada en models.py
        appointment.save()
        messages.success(request, f"Cita #{pk} con {appointment.patient.username} ha sido CANCELADA.")

        # Redirigir
        return redirect('panel_recepcion' if is_admin_or_recepcionista else 'my_appointments')

    # Si se accede por otro método (ej. POST, pero no se requiere formulario), redirige
    return redirect('home')
def get_specialist_from_user(user):
    """Intenta mapear un usuario (asumiendo que es un Estilista) a un objeto Specialist por email."""
    if not user.is_authenticated:
        return None
    try:
        # Busca un Specialist cuyo email coincida con el email del User
        return Specialist.objects.get(email=user.email)
    except Specialist.DoesNotExist:
        return None

# --- VISTA DEL ESTILISTA MODIFICADA ---
@estilista_required
def panel_estilista_view(request):
    """Muestra el panel del estilista con sus citas del día."""
    
    specialist_obj = get_specialist_from_user(request.user)

    if not specialist_obj:
        messages.error(request, "No se encontró un Specialist asociado a su cuenta. Verifique su email en el Admin.")
        return redirect('home')

    today = timezone.now().date()
    
    # FILTRO: Citas de HOY, asignadas al Especialista logueado, y solo Pendientes o Confirmadas.
    stylist_bookings = Appointment.objects.select_related('patient', 'service').filter(
        specialist=specialist_obj,
        date=today,
        status__in=['P', 'C'] 
    ).order_by('time')

    context = {
        'bookings': stylist_bookings,
        'today': today,
        'specialist': specialist_obj.full_name()
    }
    return render(request, 'clinicapp/panel_estilista.html', context)

def panel_recepcion_view(request):
    """Muestra el panel de recepción con todas las citas próximas o filtradas."""
    
    today = timezone.now().date()
    filter_date_str = request.GET.get('date') # Permite filtrar por fecha
    
    # Base Query: Citas desde hoy en adelante, solo Pendientes o Confirmadas.
    upcoming_appointments = Appointment.objects.select_related('patient', 'service', 'specialist').filter(
        date__gte=today, 
        status__in=['P', 'C'] 
    )
    
    # Aplicar filtro por fecha si existe (sobrescribe la lógica por defecto si se usa el filtro)
    if filter_date_str:
        try:
            filter_date = date.fromisoformat(filter_date_str)
            upcoming_appointments = Appointment.objects.select_related('patient', 'service', 'specialist').filter(date=filter_date)

        except ValueError:
            messages.error(request, "Formato de fecha inválido.")
            return redirect('panel_recepcion')

    # Ordenar por fecha, hora y especialista
    upcoming_appointments = upcoming_appointments.order_by('date', 'time', 'specialist__last_name')
    
    context = {
        'upcoming': upcoming_appointments,
    }
    return render(request, 'clinicapp/panel_recepcion.html', context)
def conoce_equipo_view(request):
    """Muestra la lista de especialistas."""
    # Obtiene todos los especialistas para mostrarlos en la plantilla
    specialists = Specialist.objects.all() 
    
    return render(request, 'clinicapp/conoce_al_equipo.html', {
        'specialists': specialists
    })