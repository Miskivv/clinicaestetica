from datetime import date
from .models import Appointment

# --- 1. LÓGICA DE TIEMPOS DISPONIBLES (PLACEHOLDER) ---
def get_available_times(specialist_id, date_str):
    """
    Función que calcula los horarios disponibles para un especialista en una fecha.
    (Implementación real requeriría más lógica de horarios de apertura, etc.)
    """
    
    # Horarios de trabajo fijos (ejemplo)
    ALL_TIMES = [f"{h:02d}:00" for h in range(9, 18)] # 09:00 a 17:00
    
    try:
        # Busca las citas ya reservadas para ese especialista y fecha
        booked_appointments = Appointment.objects.filter(
            specialist__id=specialist_id, 
            date=date_str,
            status__in=['P', 'C'] # Pendientes o Confirmadas
        ).values_list('time', flat=True)
        
        # Convierte los objetos TimeField a cadenas 'HH:MM:SS' para la comparación
        booked_times_str = [t.strftime('%H:%M:%S') for t in booked_appointments]
        
        # Filtra los horarios fijos
        available_times = []
        for time_str in ALL_TIMES:
             # Compara solo la hora/minuto, que es suficiente para el slot
            if f"{time_str}:00" not in booked_times_str:
                available_times.append(time_str)

        return available_times
        
    except Exception:
        # En caso de error (ej. fecha mal formateada o especialista no encontrado)
        return []


# --- 2. LÓGICA DE DESCUENTO (PLACEHOLDER) ---
def calcular_descuento_cumpleaños(user):
    """
    Calcula un descuento del 20% si es el cumpleaños del paciente.
    """
    try:
        profile = user.paciente_profile
        today = date.today()
        
        # Verifica si el mes y día coinciden con el cumpleaños
        if profile.fecha_nacimiento.month == today.month and profile.fecha_nacimiento.day == today.day:
            return 0.20  # 20% de descuento
            
    except:
        # Si el usuario no tiene perfil de paciente (ej. es Estilista/Recepcionista)
        pass
        
    return 0.0 # 0% de descuento