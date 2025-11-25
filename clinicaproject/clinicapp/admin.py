from django.contrib import admin
from .models import Service, Specialist, Appointment, PacienteProfile

# ---------------------------------------------------
# ADMIN DEL PERFIL DEL PACIENTE
# ---------------------------------------------------
@admin.register(PacienteProfile)
class PacienteProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'fecha_nacimiento')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


# ---------------------------------------------------
# ADMIN DE SERVICIOS
# ---------------------------------------------------
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name',)
    list_filter = ('price',)


# ---------------------------------------------------
# ADMIN DE ESPECIALISTAS
# ---------------------------------------------------
@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'specialty', 'email')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('specialty',)


# ---------------------------------------------------
# ADMIN DE CITAS
# ---------------------------------------------------
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'patient',
        'service',
        'specialist',
        'date',
        'time',
        'status',
        'is_paid'
    )
    list_filter = ('status', 'service', 'specialist', 'date')
    search_fields = ('patient__username',)
    ordering = ('date', 'time')
