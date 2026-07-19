/**
 * Loading Screen global de la aplicación.
 *
 * Oculta con fade-out el overlay #erp-loading-screen cuando la ventana
 * termina de cargar (window.load: HTML + CSS + imágenes, incluido el
 * logo), y lo elimina del DOM al finalizar la transición para que no
 * quede bloqueando clics.
 *
 * Archivo aislado: no depende de ni modifica ningún otro script del ERP.
 */
(function () {
    var DURACION_FADE_MS = 400;

    function ocultarLoading() {
        var overlay = document.getElementById('erp-loading-screen');
        if (!overlay) {
            return;
        }
        overlay.classList.add('erp-loading-oculto');
        document.body.classList.remove('erp-loading-activo');

        window.setTimeout(function () {
            if (overlay && overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        }, DURACION_FADE_MS);
    }

    window.addEventListener('load', ocultarLoading);

    // Salvaguarda: si por alguna razón 'load' ya se disparó antes de que
    // este script se ejecute (poco común), ocultamos igual sin esperar.
    if (document.readyState === 'complete') {
        ocultarLoading();
    }
})();
