from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# --- MODELOS PRINCIPALES ---

class Service(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Servicio")
    description = models.TextField(verbose_name="Descripción")
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Precio Estimado")

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return self.name


class Specialist(models.Model):
    first_name = models.CharField(max_length=50, verbose_name="Nombre")
    last_name = models.CharField(max_length=50, verbose_name="Apellido")
    specialty = models.CharField(max_length=100, verbose_name="Especialidad Principal")
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")

    class Meta:
        verbose_name = "Especialista"
        verbose_name_plural = "Especialistas"

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name()


class Appointment(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Paciente")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Servicio")
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, verbose_name="Especialista")
    
    date = models.DateField(verbose_name="Fecha de la Cita")
    time = models.TimeField(default=timezone.now, verbose_name="Hora de la Cita")

    STATUS_CHOICES = [
        ('P', 'Pendiente'),
        ('C', 'Confirmada'),
        ('X', 'Cancelada'),
    ]
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P', verbose_name="Estado")
    
    is_paid = models.BooleanField(default=False, verbose_name="¿Pagada?")
    final_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Precio Final")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
        unique_together = ('specialist', 'date', 'time')
        ordering = ['date', 'time']

    def __str__(self):
        return f"Cita {self.id} - {self.patient.username} con {self.specialist} para {self.service.name}"

    @property
    def precio_estimado(self):
        return self.service.price or 0.00


# --- PERFIL DEL PACIENTE ---
class PacienteProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


# --- ROLES ---
def is_recepcionista(user):
    return user.groups.filter(name='Recepcionista').exists()

User.add_to_class('is_recepcionista', is_recepcionista)
class Appointment(models.Model):
    # ... (contenido existente) ...
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments', verbose_name="Paciente")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Servicio")
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, verbose_name="Especialista")
    date = models.DateField(default=timezone.localdate, verbose_name="Fecha de la Cita")
    time = models.TimeField(default=timezone.now, verbose_name="Hora de la Cita")

    STATUS_CHOICES = [
        ('P', 'Pendiente'),
        ('C', 'Confirmada'),
        ('X', 'Cancelada'),
        ('F', 'Finalizada (Atendida)'), # Nuevo estado para el estilista
    ]
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P', verbose_name="Estado")
    
    is_paid = models.BooleanField(default=False, verbose_name="¿Pagada?")
    final_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Precio Final")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
        unique_together = ('specialist', 'date', 'time')
        ordering = ['date', 'time']

    def __str__(self):
        return f"Cita {self.id} - {self.patient.username} con {self.specialist} para {self.service.name}"

    @property
    def precio_estimado(self):
        return self.service.price or 0.00
        
    @property
    def get_status_badge_class(self):
        """Devuelve la clase CSS de Bootstrap según el estado."""
        if self.status == 'P':
            return 'bg-warning text-dark'
        elif self.status == 'C':
            return 'bg-primary'
        elif self.status == 'X':
            return 'bg-danger'
        elif self.status == 'F':
            return 'bg-success'
        return 'bg-secondary'


# --- PERFIL DEL PACIENTE ---\r\n
class PacienteProfile(models.Model):
    # ... (contenido existente) ...
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='paciente_profile')
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento")
