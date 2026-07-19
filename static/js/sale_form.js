/*
 * sale_form.js
 * Lógica del formulario dinámico de creación de ventas.
 * - Autocompletado de clientes y productos.
 * - Agregar/quitar ítems.
 * - Recalcular subtotal, descuento, IVA, total y ganancia en tiempo real.
 */
(function () {
    'use strict';

    const form = document.getElementById('ventaForm');
    if (!form) return;

    const clientesUrl = form.dataset.clientesUrl;
    const productosUrl = form.dataset.productosUrl;

    // --- Elementos del DOM ---
    const clienteBuscar = document.getElementById('clienteBuscar');
    const clienteResultados = document.getElementById('clienteResultados');
    const clienteSelect = document.getElementById('id_cliente');
    const clienteSeleccionado = document.getElementById('clienteSeleccionado');
    const clienteNombre = document.getElementById('clienteNombre');
    const clienteLimpiar = document.getElementById('clienteLimpiar');

    const productoBuscar = document.getElementById('productoBuscar');
    const productoResultados = document.getElementById('productoResultados');

    const itemsBody = document.getElementById('itemsBody');
    const filaVacia = document.getElementById('filaVacia');
    const filaTemplate = document.getElementById('filaItemTemplate');

    const descPctInput = document.getElementById('id_descuento_porcentaje');
    const ivaPctInput = document.getElementById('id_iva_porcentaje');

    const resSubtotal = document.getElementById('resumenSubtotal');
    const resDescuento = document.getElementById('resumenDescuento');
    const resIva = document.getElementById('resumenIva');
    const resTotal = document.getElementById('resumenTotal');
    const resGanancia = document.getElementById('resumenGanancia');

    // --- Utilidades ---
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

    // ================= Autocompletado de clientes =================
    const buscarClientes = debounce(function () {
        const q = clienteBuscar.value.trim();
        if (q.length < 1) { clienteResultados.style.display = 'none'; return; }
        fetch(clientesUrl + '?q=' + encodeURIComponent(q))
            .then(r => r.json())
            .then(data => {
                clienteResultados.innerHTML = '';
                if (!data.resultados.length) {
                    clienteResultados.innerHTML = '<span class="list-group-item text-muted">Sin resultados</span>';
                } else {
                    data.resultados.forEach(c => {
                        const item = document.createElement('button');
                        item.type = 'button';
                        item.className = 'list-group-item list-group-item-action';
                        item.innerHTML = '<strong>' + c.nombre + '</strong> <small class="text-muted">' +
                            c.documento + (c.telefono ? ' · ' + c.telefono : '') + '</small>';
                        item.addEventListener('click', () => seleccionarCliente(c));
                        clienteResultados.appendChild(item);
                    });
                }
                clienteResultados.style.display = 'block';
            });
    }, 250);

    function seleccionarCliente(c) {
        clienteSelect.value = c.id;
        clienteNombre.textContent = c.nombre + ' (' + c.documento + ')';
        clienteSeleccionado.classList.remove('d-none');
        clienteBuscar.classList.add('d-none');
        clienteResultados.style.display = 'none';
    }

    if (clienteBuscar) {
        clienteBuscar.addEventListener('input', buscarClientes);
    }
    if (clienteLimpiar) {
        clienteLimpiar.addEventListener('click', () => {
            clienteSelect.value = '';
            clienteSeleccionado.classList.add('d-none');
            clienteBuscar.classList.remove('d-none');
            clienteBuscar.value = '';
            clienteBuscar.focus();
        });
    }

    // ================= Autocompletado de productos =================
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
                            p.codigo + '</small></span>' +
                            '<span class="' + (agotado ? 'text-danger' : 'text-muted') + ' small">Stock: ' + p.stock +
                            ' · ' + formatear(p.precio_venta) + '</span>';
                        if (agotado) {
                            item.classList.add('disabled');
                        } else {
                            item.addEventListener('click', () => agregarProducto(p));
                        }
                        productoResultados.appendChild(item);
                    });
                }
                productoResultados.style.display = 'block';
            });
    }, 250);

    if (productoBuscar) {
        productoBuscar.addEventListener('input', buscarProductos);
    }

    function agregarProducto(p) {
        // Si ya existe la fila, solo incrementa cantidad
        const existente = itemsBody.querySelector('.item-fila .prod-id[value="' + p.id + '"]');
        if (existente) {
            const fila = existente.closest('tr');
            const cant = fila.querySelector('.cantidad');
            cant.value = parseInt(cant.value || '0', 10) + 1;
            recalcularFila(fila);
            productoResultados.style.display = 'none';
            productoBuscar.value = '';
            recalcularTotales();
            return;
        }

        const clon = filaTemplate.content.cloneNode(true);
        const fila = clon.querySelector('tr');
        fila.querySelector('.nombre-prod').textContent = p.nombre;
        fila.querySelector('.codigo-prod').textContent = p.codigo + ' · Stock: ' + p.stock;
        fila.querySelector('.prod-id').value = p.id;
        fila.querySelector('.precio-compra').value = p.precio_compra;
        fila.querySelector('.precio').value = p.precio_venta;
        fila.dataset.stock = p.stock;
        fila.dataset.precioCompra = p.precio_compra;

        // Eventos de la fila
        fila.querySelector('.cantidad').addEventListener('input', () => { validarStock(fila); recalcularFila(fila); recalcularTotales(); });
        fila.querySelector('.precio').addEventListener('input', () => { recalcularFila(fila); recalcularTotales(); });
        fila.querySelector('.descuento').addEventListener('input', () => { recalcularFila(fila); recalcularTotales(); });
        fila.querySelector('.quitar').addEventListener('click', () => { fila.remove(); toggleVacia(); recalcularTotales(); });

        if (filaVacia) filaVacia.style.display = 'none';
        itemsBody.appendChild(fila);
        recalcularFila(fila);
        recalcularTotales();

        productoResultados.style.display = 'none';
        productoBuscar.value = '';
    }

    function validarStock(fila) {
        const stock = parseInt(fila.dataset.stock || '0', 10);
        const cantInput = fila.querySelector('.cantidad');
        let cant = parseInt(cantInput.value || '0', 10);
        if (cant > stock) {
            cantInput.value = stock;
            cantInput.classList.add('is-invalid');
            setTimeout(() => cantInput.classList.remove('is-invalid'), 1200);
        }
    }

    function toggleVacia() {
        if (!itemsBody.querySelector('.item-fila') && filaVacia) {
            filaVacia.style.display = '';
        }
    }

    function recalcularFila(fila) {
        const cant = parseFloat(fila.querySelector('.cantidad').value) || 0;
        const precio = parseFloat(fila.querySelector('.precio').value) || 0;
        const desc = parseFloat(fila.querySelector('.descuento').value) || 0;
        const subtotal = Math.max(cant * precio - desc, 0);
        fila.querySelector('.subtotal-celda').textContent = formatear(subtotal);
        fila.dataset.subtotal = subtotal;
    }

    // ================= Totales globales =================
    function recalcularTotales() {
        let subtotal = 0;
        let ganancia = 0;
        itemsBody.querySelectorAll('.item-fila').forEach(fila => {
            const cant = parseFloat(fila.querySelector('.cantidad').value) || 0;
            const precio = parseFloat(fila.querySelector('.precio').value) || 0;
            const desc = parseFloat(fila.querySelector('.descuento').value) || 0;
            const precioCompra = parseFloat(fila.dataset.precioCompra) || 0;
            subtotal += Math.max(cant * precio - desc, 0);
            ganancia += (precio - precioCompra) * cant - desc;
        });

        const descPct = parseFloat(descPctInput.value) || 0;
        const ivaPct = parseFloat(ivaPctInput.value) || 0;
        const descValor = subtotal * descPct / 100;
        const baseGravable = subtotal - descValor;
        const ivaValor = baseGravable * ivaPct / 100;
        const total = baseGravable + ivaValor;
        const gananciaNeta = ganancia - descValor;

        resSubtotal.textContent = formatear(subtotal);
        resDescuento.textContent = '- ' + formatear(descValor);
        resIva.textContent = formatear(ivaValor);
        resTotal.textContent = formatear(total);
        resGanancia.textContent = formatear(gananciaNeta);
    }

    if (descPctInput) descPctInput.addEventListener('input', recalcularTotales);
    if (ivaPctInput) ivaPctInput.addEventListener('input', recalcularTotales);

    // Cerrar dropdowns al hacer clic fuera
    document.addEventListener('click', function (e) {
        if (clienteResultados && !clienteResultados.contains(e.target) && e.target !== clienteBuscar) {
            clienteResultados.style.display = 'none';
        }
        if (productoResultados && !productoResultados.contains(e.target) && e.target !== productoBuscar) {
            productoResultados.style.display = 'none';
        }
    });

    // ================= Validación al enviar =================
    form.addEventListener('submit', function (e) {
        if (!clienteSelect.value) {
            e.preventDefault();
            alert('Debes seleccionar un cliente.');
            return;
        }
        if (!itemsBody.querySelector('.item-fila')) {
            e.preventDefault();
            alert('Debes agregar al menos un producto.');
            return;
        }
    });

    recalcularTotales();
})();
