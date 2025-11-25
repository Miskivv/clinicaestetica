// clinicapp/static/js/reserva.js

document.addEventListener('DOMContentLoaded', function() {
    const servicioSelect = document.getElementById('servicio_id');
    const especialistaSelect = document.getElementById('especialista_id');
    const fechaInput = document.getElementById('fecha_hora');
    
    // Obtenemos los datos de estilistas y servicios que pasamos desde Django
    // Esto es un placeholder; en un entorno real, usarías AJAX para obtener datos en vivo.
    const especialistasPorServicio = {
        // Ejemplo de cómo se verían los datos si los pasaras:
        // '1': ['Estilista_A_ID', 'Estilista_B_ID'], // Servicio ID 1
        // '2': ['Estilista_C_ID']                     // Servicio ID 2
    };

    // --- Función de Filtrado de Estilistas ---
    function filtrarEstilistas() {
        const servicioSeleccionadoId = servicioSelect.value;
        const especialistasDisponibles = especialistasPorServicio[servicioSeleccionadoId] || [];

        // Ocultar o deshabilitar todos los estilistas inicialmente
        Array.from(especialistaSelect.options).forEach(option => {
            if (option.value !== "") { // Ignorar la opción por defecto
                option.style.display = 'none';
                option.disabled = true;
            }
        });

        // Mostrar solo los estilistas disponibles para el servicio
        especialistasDisponibles.forEach(especialistaId => {
            const option = especialistaSelect.querySelector(`option[value="${especialistaId}"]`);
            if (option) {
                option.style.display = '';
                option.disabled = false;
            }
        });

        // Seleccionar la primera opción válida si ninguna está seleccionada
        if (!especialistasDisponibles.includes(especialistaSelect.value)) {
            especialistaSelect.value = "";
        }
    }

    // --- Simulación de Comprobación de Disponibilidad (Fechas) ---
    function verificarDisponibilidad() {
        // En una aplicación real, esta función haría una llamada AJAX a una vista de Django
        // (ej. /api/check-disponibilidad/) para verificar si el estilista
        // seleccionado está libre en la `fechaInput.value`.
        // Si hay un conflicto, mostraría un mensaje de error o deshabilitaría el botón de reserva.
        
        const fecha = fechaInput.value;
        const estilistaId = especialistaSelect.value;
        
        if (fecha && estilistaId) {
            console.log(`Verificando disponibilidad para Estilista ${estilistaId} en ${fecha}...`);
            // Simulación de validación (debería ser asíncrona)
            // alert('Disponibilidad verificada. ¡Aceptado!');
        }
    }

    servicioSelect.addEventListener('change', filtrarEstilistas);
    especialistaSelect.addEventListener('change', verificarDisponibilidad);
    fechaInput.addEventListener('change', verificarDisponibilidad);

    // Ejecutar al cargar para inicializar el filtro
    // filtrarEstilistas(); 
});