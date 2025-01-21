document.addEventListener('DOMContentLoaded', function () {
    const pageTitle = document.title;

    if (pageTitle.includes('Experimentador')) {
        //Activar y desactivar los elementos del formulario, dependiendo de la tecnología seleccionada.
        const elemento = document.getElementById('YOLO');
        if (elemento) {
            elemento.addEventListener('change', function() {
                console.log('Evento de cambio disparado en YOLO');
                if (this.checked) {
                    document.querySelectorAll('.Tres-Columnas input').forEach(function(input) {
                        input.disabled = false;
                    });
                } else {
                    document.querySelectorAll('.Tres-Columnas input').forEach(function(input) {
                        input.disabled = true;
                    });
                }
            });
        }
    }
});