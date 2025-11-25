from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.contrib.auth.models import Group # Importación necesaria

# --- FUNCIÓN AUXILIAR PARA VERIFICAR GRUPO ---
def is_in_group(user, group_name):
    """Verifica si el usuario pertenece al grupo dado."""
    if not user.is_authenticated:
        return False
    # Usamos Group.objects.filter para evitar errores si el grupo no existe.
    return user.groups.filter(name=group_name).exists()


def recepcionista_required(view_func):
    """
    Restringe el acceso solo a usuarios que pertenecen al grupo 'Recepcionista'.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para acceder a esta área.")
            return redirect('login')
            
        # *** VERIFICACIÓN CORRECTA DEL GRUPO ***
        if not is_in_group(request.user, 'Recepcionista'):
            messages.error(request, "No tiene permisos para acceder a esta página (Requiere Recepcionista).")
            return redirect('home')
            
        return view_func(request, *args, **kwargs)
    return wrapper


def estilista_required(view_func):
    """
    Restringe el acceso solo a usuarios que pertenecen al grupo 'Estilista'.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión para acceder a esta área.")
            return redirect('login')
            
        # *** VERIFICACIÓN CORRECTA DEL GRUPO ***
        if not is_in_group(request.user, 'Estilista'):
            messages.error(request, "No tiene permisos para acceder a esta página (Requiere Estilista).")
            return redirect('home')
            
        return view_func(request, *args, **kwargs)
    return wrapper
def admin_or_recepcionista_required(view_func):
    """
    Decora la vista para requerir que el usuario sea Superuser, Staff o Recepcionista.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debe iniciar sesión.")
            return redirect('login')
            
        is_admin_or_staff = request.user.is_superuser or request.user.is_staff
        
        # Asume que el rol de 'reception' está en el campo 'role' del modelo User o Profile
        is_recepcionista = hasattr(request.user, 'role') and request.user.role == 'reception'
        
        if not (is_admin_or_staff or is_recepcionista):
            messages.error(request, "No tiene permisos de Administrador o Recepcionista para realizar esta acción.")
            return redirect('home')
            
        return view_func(request, *args, **kwargs)
    return wrapper
