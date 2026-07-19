/*
 * order_form.js
 * Lógica del formulario de orden de servicio técnico.
 * - Buscar repuestos del inventario (descuenta stock al confirmar en el servidor).
 * - Agregar repuestos manuales (sin inventario).
 * - Recalcular costo de repuestos, IVA y total en tiempo real.
 */
(function () {
    'use strict';

    const form = document.getElementById('ordenForm');
    if (!form) return;

    const productosUrl = form.dataset.productosUrl;

    const productoBuscar = document.getElementById('productoBuscar');
    const productoResultados = document.getElementById('productoResultados');
    const partesBody = document.getElementById('partesBody');
    const filaVacia = document.getElementById('filaVacia');
    const filaTemplate = document.getElementById('filaParteTemplate');
    const agregarManual = document.getElementById('agregarManual');

    const manoObraInput = document.getElementById('id_mano_obra');
    const ivaInput = document.getElementById('id_iva_porcentaje');

    const resRepuestos = document.getElementById('resRepuestos');
    const resManoObra = document.getElementById('resManoObra');
    const resIva = document.getElementById('resIva');
    const resTotal = document.getElementById('resTotal');

    function formatear(valor) {
        const n = Math.round((parseFloat(valor) || 0));
        return '$ ' + n.toLocaleString('es-CO');
    }

    function debounce(fn, ms) {
        let t;
        return function () {
            const args = arguments;
            clearTimeout(t);
            t = setTimeout(() => fn.apply(this, args), ms);
        };
    }

    // ============ Buscar productos ============
    const buscarProductos = debounce(function () {
        const q = productoBuscar.value.trim();
        if (q.length < 1) { productoResultados.style.display = 'none'; return; }
        fetch(productosUrl + '?q=' + encodeURIComponent(q))
            .then(r => r.json())
            .then(data => {
                productoResultados.innerHTML = '';
                if (!data.resultados.length) {
                    productoResultados.innerHTML = '<span class="list-group-item text-muted">Sin resultados</span>';
                } else {
                    data.resultados.forEach(p => {
                        const item = document.createElement('button');
                        item.type = 'button';
                        item.className = 'list-group-item list-group-item-action d-flex justify-content-between';
                        const agotado = p.stock <= 0;
                        item.innerHTML = '<span><strong>' + p.nombre + '</strong> <small class="text-muted">' +
                            p.codigo + '</small></span><span class="' + (agotado ? 'text-danger' : 'text-muted') +
                            ' small">Stock: ' + p.stock + ' · ' + formatear(p.precio_venta) + '</span>';
                        if (agotado) {
                            item.classList.add('disabled');
                        } else {
                            item.addEventListener('click', () => agregarParte(p));
                        }
                        productoResultados.appendChild(item);
                    });
                }
                productoResultados.style.display = 'block';
            });
    }, 250);

    if (productoBuscar) productoBuscar.addEventListener('input', buscarProductos);

    function crearFila() {
        const clon = filaTemplate.content.cloneNode(true);
        const fila = clon.querySelector('tr');
        fila.querySelector('.cantidad').addEventListener('input', () => { validarStock(fila); recalcularFila(fila); recalcularTotales(); });
        fila.querySelector('.precio').addEventListener('input', () => { recalcularFila(fila); recalcularTotales(); });
        fila.querySelector('.quitar').addEventListener('click', () => { fila.remove(); toggleVacia(); recalcularTotales(); });
        if (filaVacia) filaVacia.style.display = 'none';
        partesBody.appendChild(fila);
        return fila;
    }

    function agregarParte(p) {
        const existente = partesBody.querySelector('.parte-fila .prod-id[value="' + p.id + '"]');
        if (existente) {
            const fila = existente.closest('tr');
            const cant = fila.querySelector('.cantidad');
            cant.value = parseInt(cant.value || '0', 10) + 1;
            validarStock(fila);
            recalcularFila(fila);
            recalcularTotales();
        } else {
            const fila = crearFila();
            fila.querySelector('.descripcion').value = p.nombre;
            fila.querySelector('.prod-id').value = p.id;
            fila.querySelector('.precio').value = p.precio_venta;
            fila.querySelector('.info-stock').textContent = p.codigo + ' · Stock: ' + p.stock;
            fila.dataset.stock = p.stock;
            recalcularFila(fila);
            recalcularTotales();
        }
        productoResultados.style.display = 'none';
        productoBuscar.value = '';
    }

    if (agregarManual) {
        agregarManual.addEventListener('click', () => {
            const fila = crearFila();
            fila.dataset.stock = '999999';
            fila.querySelector('.descripcion').focus();
            recalcularTotales();
        });
    }

    function validarStock(fila) {
        const stock = parseInt(fila.dataset.stock || '999999', 10);
        const cantInput = fila.querySelector('.cantidad');
        let cant = parseInt(cantInput.value || '0', 10);
        if (cant > stock) {
            cantInput.value = stock;
            cantInput.classList.add('is-invalid');
            setTimeout(() => cantInput.classList.remove('is-invalid'), 1200);
        }
    }

    function toggleVacia() {
        if (!partesBody.querySelector('.parte-fila') && filaVacia) {
            filaVacia.style.display = '';
        }
    }

    function recalcularFila(fila) {
        const cant = parseFloat(fila.querySelector('.cantidad').value) || 0;
        const precio = parseFloat(fila.querySelector('.precio').value) || 0;
        const subtotal = cant * precio;
        fila.querySelector('.subtotal-celda').textContent = formatear(subtotal);
    }

    function recalcularTotales() {
        let repuestos = 0;
        partesBody.querySelectorAll('.parte-fila').forEach(fila => {
            const cant = parseFloat(fila.querySelector('.cantidad').value) || 0;
            const precio = parseFloat(fila.querySelector('.precio').value) || 0;
            repuestos += cant * precio;
        });
        const manoObra = parseFloat(manoObraInput.value) || 0;
        const ivaPct = parseFloat(ivaInput.value) || 0;
        const base = repuestos + manoObra;
        const ivaValor = base * ivaPct / 100;
        const total = base + ivaValor;

        resRepuestos.textContent = formatear(repuestos);
        resManoObra.textContent = formatear(manoObra);
        resIva.textContent = formatear(ivaValor);
        resTotal.textContent = formatear(total);
    }

    if (manoObraInput) manoObraInput.addEventListener('input', recalcularTotales);
    if (ivaInput) ivaInput.addEventListener('input', recalcularTotales);

    document.addEventListener('click', function (e) {
        if (productoResultados && !productoResultados.contains(e.target) && e.target !== productoBuscar) {
            productoResultados.style.display = 'none';
        }
    });

    form.addEventListener('submit', function (e) {
        const cliente = document.getElementById('id_cliente');
        if (cliente && !cliente.value) {
            e.preventDefault();
            alert('Debes seleccionar un cliente.');
        }
    });

    recalcularTotales();
})();
