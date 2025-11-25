# clinicapp/templatetags/clinicapp_tags.py

from django import template
from django.contrib.auth.models import Group

# 1. Crear la instancia de la biblioteca (este nombre 'register' es obligatorio)
register = template.Library()

@register.simple_tag
def is_in_group(user, group_name):
    """
    Verifica si el usuario (user) pertenece al grupo (group_name).
    Uso en plantillas: {% if is_in_group user 'Recepcionista' %}
    """
    # Si el usuario no está autenticado, no puede estar en ningún grupo.
    if not user.is_authenticated:
        return False
        
    # La lógica robusta para chequear el grupo
    return user.groups.filter(name=group_name).exists()