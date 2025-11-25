from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.db import transaction
from .models import Service, Specialist, Appointment, PacienteProfile
from django.forms.widgets import DateInput, TimeInput

class RegisterForm(UserCreationForm):
    fecha_nacimiento = forms.DateField(
        label="Fecha de Nacimiento",
        required=True,
        widget=DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d', '%d-%m-%Y'],
    )

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email", "first_name", "last_name")

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')

        if commit:
            user.save()
            PacienteProfile.objects.create(
                user=user,
                fecha_nacimiento=self.cleaned_data['fecha_nacimiento']
            )
        return user

class AppointmentForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d', '%d-%m-%Y'],
        label="Fecha"
    )
    
    time = forms.TimeField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Hora",
        required=True
    )

    class Meta:
        model = Appointment
        fields = ['service', 'specialist', 'date', 'time']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['time'].choices = [('', '--- Seleccione la hora ---')]


# ---------------------------
# 3. FORMULARIO LOGIN RECEPCIÓN
# ---------------------------
class RecepcionistaLoginForm(AuthenticationForm):
    pass


# ---------------------------
# 4. FORMULARIO MODIFICAR CITA
# ---------------------------
class ModifyAppointmentForm(forms.ModelForm):
    date = forms.DateField(widget=DateInput(attrs={'type': 'date'}), label="Nueva Fecha")
    time = forms.TimeField(widget=TimeInput(attrs={'type': 'time'}), label="Nueva Hora")

    class Meta:
        model = Appointment
        fields = ['date', 'time']

class ModifyAppointmentForm(forms.ModelForm):
    # Definimos los campos que se van a modificar
    # Opcionalmente puedes definir los widgets aquí o dejar que Django los infiera
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d', '%d-%m-%Y'],
        label="Nueva Fecha"
    )
    
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        label="Nueva Hora",
        required=True
    )

    class Meta:
        model = Appointment
        # Solo permitimos modificar fecha y hora (y si quieres, especialista o servicio)
        # Para el ejemplo, solo date y time
        fields = ['date', 'time']

    def clean_date(self):
        # Validación para no permitir fechas pasadas
        selected_date = self.cleaned_data['date']
        if selected_date < date.today():
            raise forms.ValidationError("La fecha de la cita no puede ser en el pasado.")
        return selected_date

    def clean(self):
        """
        Validación general para asegurar que la nueva hora no esté ocupada
        por el mismo especialista.
        """
        cleaned_data = super().clean()
        new_date = cleaned_data.get("date")
        new_time = cleaned_data.get("time")

        if new_date and new_time and self.instance:
            specialist = self.instance.specialist
            # Excluye la cita que se está modificando (self.instance)
            if Appointment.objects.filter(
                specialist=specialist,
                date=new_date,
                time=new_time
            ).exclude(pk=self.instance.pk).exists():
                self.add_error(None, "El especialista ya tiene una cita reservada para esa hora. Por favor, seleccione otra.")
        
        return cleaned_data