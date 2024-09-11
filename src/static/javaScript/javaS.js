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
    /*
    // Código específico para otra página
    if (pageTitle.includes('Tipos de Basura')) {
        function mostrarNombreDirectorio() {
            const input = document.getElementById('Dataset');
            if (input.files.length > 0) {
                const fullPath = input.files[0].webkitRelativePath || input.files[0].name;
                const directoryPath = fullPath.split('/').slice(0, -1).join('/');
        
                // Si quieres mostrar la ruta absoluta
                const absolutePath = input.files[0].path || directoryPath;
        
                // Mostrar la ruta completa en el campo de texto
                document.getElementById('nombre-Dataset').value = absolutePath;
            }
        }
    }*/
});