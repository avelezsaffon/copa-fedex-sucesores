// ======================================================================
//        INICIO: PAGINADOR PARA LA PÁGINA DE HANDICAP (CORREGIDO)
// ======================================================================
function inicializarPaginadorHandicap() {
    // CORRECCIÓN: Usamos el mismo selector que la función searchData para garantizar que lo encuentre.
    const cuerpoTabla = document.querySelector("#miTablaContenedor .tabla-datos tbody");
    if (!cuerpoTabla) {
        console.error("Paginador Handicap: No se encontró el cuerpo de la tabla.");
        return;
    }

    const contenedorPaginador = document.getElementById('paginador-container');
    if (!contenedorPaginador) {
        console.error("Paginador Handicap: No se encontró el contenedor del paginador.");
        return;
    }

    const todasLasFilas = Array.from(cuerpoTabla.querySelectorAll('tr'));
    
    contenedorPaginador.innerHTML = '';
    
    if (todasLasFilas.length === 0) return;

    let paginaActual = 1;
    const resultadosPorPagina = 10;

    function mostrarPagina(pagina) {
        paginaActual = pagina;
        const inicio = (pagina - 1) * resultadosPorPagina;
        const fin = inicio + resultadosPorPagina;
        
        todasLasFilas.forEach((fila, indice) => {
            fila.style.display = (indice >= inicio && indice < fin) ? '' : 'none';
        });
        actualizarPaginador();
    }

    function actualizarPaginador() {
        contenedorPaginador.innerHTML = '';
        const totalPaginas = Math.ceil(todasLasFilas.length / resultadosPorPagina);
        if (totalPaginas <= 1) return;

        // El resto de la lógica es la misma...
        const btnAnterior = document.createElement('a');
        btnAnterior.innerHTML = '&laquo; Anterior';
        if (paginaActual > 1) {
            btnAnterior.href = "#";
            btnAnterior.addEventListener('click', (e) => { e.preventDefault(); mostrarPagina(paginaActual - 1); });
        } else {
            btnAnterior.classList.add('deshabilitado');
        }
        contenedorPaginador.appendChild(btnAnterior);

        for (let i = 1; i <= totalPaginas; i++) {
            const btnPagina = document.createElement('a');
            btnPagina.innerText = i;
            btnPagina.href = "#";
            btnPagina.classList.add('numero-pagina');
            if (i === paginaActual) {
                btnPagina.classList.add('activo');
            } else {
                btnPagina.addEventListener('click', (e) => { e.preventDefault(); mostrarPagina(i); });
            }
            contenedorPaginador.appendChild(btnPagina);
        }

        const btnSiguiente = document.createElement('a');
        btnSiguiente.innerHTML = 'Siguiente &raquo;';
        if (paginaActual < totalPaginas) {
            btnSiguiente.href = "#";
            btnSiguiente.addEventListener('click', (e) => { e.preventDefault(); mostrarPagina(paginaActual + 1); });
        } else {
             btnSiguiente.classList.add('deshabilitado');
        }
        contenedorPaginador.appendChild(btnSiguiente);
    }
    
    mostrarPagina(1);
}


// ======================================================================
//        INICIO: PAGINADOR PARA LA PÁGINA DE RANKING (VERSIÓN FINAL CORREGIDA)
// ======================================================================
function inicializarPaginadorRanking() {
    const cuerpoTabla = document.querySelector(".ranking-table tbody");
    if (!cuerpoTabla) {
        console.error("Paginador Ranking: No se encontró el cuerpo de la tabla.");
        return;
    }

    const contenedorPaginador = document.getElementById('paginador-ranking-container');
    if (!contenedorPaginador) {
        console.error("Paginador Ranking: No se encontró el contenedor del paginador.");
        return;
    }

    const todasLasFilas = Array.from(cuerpoTabla.querySelectorAll('tr'));
    
    contenedorPaginador.innerHTML = '';
    
    if (todasLasFilas.length === 0) return;

    let paginaActual = 1;
    const resultadosPorPagina = 10; 

    function mostrarPagina(pagina) {
        paginaActual = pagina;
        const inicio = (pagina - 1) * resultadosPorPagina;
        const fin = inicio + resultadosPorPagina;
        
        todasLasFilas.forEach((fila, indice) => {
            fila.style.display = (indice >= inicio && indice < fin) ? '' : 'none';
        });
        actualizarPaginador();
    }

    function actualizarPaginador() {
        contenedorPaginador.innerHTML = '';
        const totalPaginas = Math.ceil(todasLasFilas.length / resultadosPorPagina);
        if (totalPaginas <= 1) return;

        const paginasPorGrupo = 5;

        const grupoActual = Math.ceil(paginaActual / paginasPorGrupo);
        let finDelGrupo = grupoActual * paginasPorGrupo;

     
        let inicioDelGrupo = finDelGrupo - paginasPorGrupo + 1;
        
        finDelGrupo = Math.min(finDelGrupo, totalPaginas);

        // --- Botón "Anterior" ---
        const btnAnterior = document.createElement('a');
        btnAnterior.innerHTML = '&laquo; Anterior';
        if (paginaActual > 1) {
            btnAnterior.href = "#";
            btnAnterior.addEventListener('click', (e) => { e.preventDefault(); mostrarPagina(paginaActual - 1); });
        } else {
            btnAnterior.classList.add('deshabilitado');
        }
        contenedorPaginador.appendChild(btnAnterior);
        
        // Botón para ir al inicio "1..."
        if (inicioDelGrupo > 1) {
            const btnPrimera = document.createElement('a');
            btnPrimera.innerText = '1';
            btnPrimera.href = "#";
            btnPrimera.classList.add('numero-pagina');
            btnPrimera.addEventListener('click', (e) => { e.preventDefault(); mostrarPagina(1); });
            contenedorPaginador.appendChild(btnPrimera);

            const puntosInicio = document.createElement('span');
            puntosInicio.innerText = '...';
            puntosInicio.classList.add('puntos');
            contenedorPaginador.appendChild(puntosInicio);
        }

        // --- Números de Página del grupo actual ---
        for (let i = inicioDelGrupo; i <= finDelGrupo; i++) {
            const btnPagina = document.createElement('a');
            btnPagina.innerText = i;
            btnPagina.href = "#";
            btnPagina.classList.add('numero-pagina');
            if (i === paginaActual) {
                btnPagina.classList.add('activo');
            } else {
                btnPagina.addEventListener('click', (e) => { e.preventDefault(); mostrarPagina(i); });
            }
            contenedorPaginador.appendChild(btnPagina);
        }
        
        // Botón para ir al final "...29"
        if (finDelGrupo < totalPaginas) {
             const puntosFinal = document.createElement('span');
            puntosFinal.innerText = '...';
            puntosFinal.classList.add('puntos');
            contenedorPaginador.appendChild(puntosFinal);

            const btnUltima = document.createElement('a');
            btnUltima.innerText = totalPaginas;
            btnUltima.href = "#";
            btnUltima.classList.add('numero-pagina');
            btnUltima.addEventListener('click', (e) => { e.preventDefault(); mostrarPagina(totalPaginas); });
            contenedorPaginador.appendChild(btnUltima);
        }

        // --- Botón "Siguiente" ---
        const btnSiguiente = document.createElement('a');
        btnSiguiente.innerHTML = 'Siguiente &raquo;';
        if (paginaActual < totalPaginas) {
            btnSiguiente.href = "#";
            btnSiguiente.addEventListener('click', (e) => { e.preventDefault(); mostrarPagina(paginaActual + 1); });
        } else {
             btnSiguiente.classList.add('deshabilitado');
        }
        contenedorPaginador.appendChild(btnSiguiente);
    }
    
    mostrarPagina(1);
}

// ======================================================================
//       FINAL: PAGINADORES
// ======================================================================





document.addEventListener("DOMContentLoaded", function () {
    const baseURL = 'https://servicios.federacioncolombianadegolf.com/';
    // Asegúrate de que jQuery esté cargado en tu página
    jQuery(document).ready(function($) {
        // Capturar el formulario usando el data-form-id
        let usuarioGuardado = JSON.parse(localStorage.getItem('usuario'));
        let usuarioInfo = null;
        let firstLoad = true;
        let categoriesRanking = null;

        if($('.page-id-3191').length > 0) {
            var form = $("form[id='formulario-busqueda-elementor']");
            const params = getQueryParams();
            let resultPlayers = null;
            $('.tabla-contenedor').css('display', 'none');
            if(Object.keys(params).length > 0) {
                
                
                var paramsFormData = new FormData();
                for (const key in params) {
                    if (params.hasOwnProperty(key)) {
                        paramsFormData.append(key, params[key]);
                    }
                }
                searchData(obj_ajax.ajaxurl, paramsFormData);
                
            }
            // Verificar si el formulario existe este es el de handicap by name
            if (form.length) {
                //localStorage.removeItem('usuario');
                form.submit(function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    $('.alert-form-search').html("");
                    let select = form.find('select[name="tipo_busqueda"]');
                    let input  = form.find('input[name="termino_busqueda"]');

                    if ((select.val() == "" || select.val() == null) || input.val().trim() === "") {
                        $('.alert-form-search').html("Por favor, completa todos los campos antes de continuar.")
                        .css('font-size', '18px');
                        return;
                    }
                    
                    var formData = new FormData(form[0]);
                    searchData(obj_ajax.ajaxurl, formData)
                });
            }
        }

        if( $('.page-id-540').length > 0) {
            $('.btn-search-calendar').on('click', function(){
                sendSearchCalendar();
            });
            
            $("select[name='select_month']").on('change', function(){
                sendSearchCalendar();
            });
            $("select[name='select_divisional']").on('change', function(){
                sendSearchCalendar();
            });

            $("#form_calendar").on('submit', function(e){
                e.preventDefault();
                e.stopPropagation();
                sendSearchCalendar();
                return false;
            });

            $('#formulario-busqueda-elementor').submit(function(e) {
                e.preventDefault();  
                e.stopPropagation();
                const form = $('#formulario-busqueda-elementor');
                // Validar campos
                let select = form.find('select[name="tipo_busqueda"]');  // ajusta name o id
                let input  = form.find('input[name="termino_busqueda"]');    // ajusta name o id

                if ((select.val() == "" || select.val() == null) || input.val().trim() === "") {
                    //alert("Por favor, completa todos los campos antes de continuar.");
                     $('.alert-form-search').html("Por favor, completa todos los campos antes de continuar.")
                    .css('font-size', '18px');
                    return; // Detiene el proceso
                }else if (isNaN(input.val()) && select.val() == "cod") {
                    $('.alert-form-search').html("Por favor, en el código debes poner un número.")
                    .css('font-size', '18px');
                }

                $('.alert-form-search').html("")
                var formData = new FormData(form[0]);
                searchData(obj_ajax.ajaxurl, formData, function(response){
                    form[0].submit();
                })
                // Si pasa validación, se envía el formulario normalmente
                //form[0].submit();
            });

            getDivisional(obj_ajax.ajaxurl, null);
        }

        if($('.page-id-3218').length > 0) {
            
            $('select[name="filtro_ranking"]').on('change', function(event){
                event.preventDefault();
                const gender = $(this).val();
                const selectCategory =  $('select[name="filtro_categoria"]')
                if(gender == "")
                    return;
                
                selectCategory.find('option:not(:first)').remove();
                categoriesRanking[gender].forEach(category => {
                        const option = $('<option>', {
                        value: category.Id,
                        text: category.Name
                    });
                    selectCategory.append(option);
                });

                selectCategory.prop('disabled', false);
            })

            $('select[name="filtro_categoria"]').on('change', function(event){
                event.preventDefault();
                let IdCategoria = $(this).val();
                
                if(IdCategoria == "")
                    return;

                var paramsFormData = new FormData();
                paramsFormData.append("IdCategoria",IdCategoria);
                paramsFormData.append("action", "get_info_ranking");

                getRanking(obj_ajax.ajaxurl, paramsFormData);
            })

            $(document).on('click', '.ranking-link', function(e) {
                e.preventDefault();

                const slug = $(this).data('slug');
                const rankingUrl = $(this).data('url');

                Object.keys(localStorage)
                .filter((key) => key.startsWith('ranking-'))
                .forEach((key) => localStorage.removeItem(key));
                // Guardar en localStorage con la clave "ranking-slug"
                localStorage.setItem(`ranking-${slug}`, JSON.stringify(rankingUrl));

                // Redirigir a la página de WordPress con el slug
                window.location.href = `/ranking-federado/${slug}`;
            });
            getInfoCategories(obj_ajax.ajaxurl);
        }

        if($('.page-id-3889').length > 0) {
        	if (!usuarioGuardado) 
                window.location.href = "/handicap/";

            $('#club-select').on('change', function(event){
                event.preventDefault();
                const codClub = $(this).val();
                
                if(codClub == "seleccione-club")
                    return;
                
                $('#preloader').css({display: 'block',opacity: 1});
                var paramsFormData = new FormData();
                paramsFormData.append("codClub",codClub);
                paramsFormData.append("action", "get_field");

                sendAjax(obj_ajax.ajaxurl, paramsFormData, function(data) {
                    if (data) {
                        const select = $('#cancha-select');

                        // Limpiar opciones anteriores, excepto la primera
                        select.find('option:not(:first)').remove();
                        // Agregar nuevas opciones
                        data.RetornaCanchasResult.forEach(function(club) {
                            const option = $('<option>', {
                                value: club.codCancha,
                                text: club.NombreCancha
                            });
                            select.append(option);
                        });

                        //console.log("Retorna canchas", data.RetornaCanchasResult.length+"First:"+firstLoad);
                        //if(data.RetornaCanchasResult.length == 1 && firstLoad)
                        //if(firstLoad)
                        select.prop('selectedIndex', 1).trigger('change');
                    }
                });
            })

            $('#cancha-select').on('change', function(event){
                event.preventDefault();
                const codClub = $('#club-select').val();
                const codField = $(this).val();
                
                if(codClub == "seleccione-club" || codField === "seleccione-cancha")
                    return;

                var paramsFormData = new FormData();
                paramsFormData.append("codClub",codClub);
                paramsFormData.append("codCancha",codField);
                paramsFormData.append("action", "get_brand");

                sendAjax(obj_ajax.ajaxurl, paramsFormData, function(data) {
                    if (data) {
                        const select = $('#marca-select');
                        let countBrand = 0;
                        // Limpiar opciones anteriores, excepto la primera
                        select.find('option:not(:first)').remove();
                        // Agregar nuevas opciones
                        data.RetornaMarcasResult.forEach(function(marca) {
                            if(usuarioInfo.Genero__c == marca.Genero){
                                countBrand++;
                                const option = $('<option>', {
                                    value: marca.codMarca,
                                    text: marca.nombreMarca
                                });
                                select.append(option);
                            }
                        });
                        
                        //if(data.RetornaMarcasResult.length == 1 || firstLoad === true) {
                        //console.log("Retorna canchas", data.RetornaMarcasResult.length+"First:"+firstLoad);
                        //if(countBrand > 0 && firstLoad === true) {
                        if(countBrand > 0) {
                            firstLoad = false;
                            select.prop('selectedIndex', 1).trigger('change');
                        }

                    }
                });
            })

            $('#marca-select').on('change', function(event){
                event.preventDefault();
                const codClub = $('#club-select').val();
                const codField = $('#cancha-select').val();
                const codBrand = $(this).val();
                
                if(codClub == "seleccione-club" || codField == "seleccione-cancha" || codBrand === "seleccione-marca")
                    return;

                const fieldJugador = $('#interna-consulta-handicap input[name="termino_busqueda"]').val();
                let codJugador = fieldJugador != "" ? fieldJugador : usuarioGuardado.CodigoJugador__c;
                var paramsFormData = new FormData();
                paramsFormData.append("cod_Club",codClub);
                paramsFormData.append("cod_Cancha",codField);
                paramsFormData.append("cod_marca",codBrand);
                paramsFormData.append("codJugador", codJugador);
                paramsFormData.append("action", "get_handicap");

                searchHandicap(obj_ajax.ajaxurl, paramsFormData)
            })

            $('#interna-consulta-handicap').on("submit", function(e) {
                e.preventDefault();
                const type_search = $('#interna-consulta-handicap select[name="tipo_busqueda"]').val();
                const field_value = $('#interna-consulta-handicap input[name="termino_busqueda"]').val();
                $('.alert-form-search').html("")

                if(type_search == "cod" && isNaN(field_value)) {
                    $('.alert-form-search').html("Por favor, en el código debes poner un número.")
                        .css('font-size', '18px');
                    return;    
                }
                if(type_search == "cod" && field_value != ""){
                    const codClub = $('#club-select').val();
                    const codField = $('#cancha-select').val();
                    const codBrand = $('#marca-select').val();

                    if(codClub == "seleccione-club" || codField=="seleccione-cancha" || codBrand == "seleccione-marca"){
                        $('.alert-form-search').html("Debes seleccionar todos los campos para buscar otro jugador.")
                        .css('font-size', '18px');
                        return;
                    }
                    
                    $('#preloader').css({display: 'block',opacity: 1});
                    var formData = new FormData($(this)[0]);
                    searchData(obj_ajax.ajaxurl, formData, function(response){
                        window.location.href="/handicap?tipo_busqueda="+type_search+"&termino_busqueda="+field_value;
                    })
                    /*
                    var paramsFormData = new FormData();
                    paramsFormData.append("cod_Club",codClub);
                    paramsFormData.append("cod_Cancha",codField);
                    paramsFormData.append("cod_marca",codBrand);
                    paramsFormData.append("codJugador",field_value);
                    paramsFormData.append("action", "get_handicap");

                    searchHandicap(obj_ajax.ajaxurl, paramsFormData);
                    var formSearch = new FormData($(this)[0]);
                    formSearch.append("action", "envio_salesforce");
                    $.ajax({
                        url: obj_ajax.ajaxurl,  // Usa la URL proporcionada por wp_localize_script
                        type: 'POST',
                        data: formSearch,  // Usamos FormData aquí
                        processData: false,  // Important: No proceses los datos
                        contentType: false,  // Important: No se establece contentType automáticamente
                        success: function(response) {
                            if(!response.data.BusquedaResult)
                                return;
                            
                            resultPlayers = response.data.BusquedaResult;
                            
                            if(resultPlayers.length == 1 && resultPlayers[0].Persona == null) {
                                console.log("No encontro el jugador");
                            }else if(resultPlayers.length == 1) {
                                localStorage.setItem('usuario', JSON.stringify(resultPlayers[0].Persona));
                                usuarioGuardado = JSON.parse(localStorage.getItem('usuario'));
                            }
                        }
                    });
                    */     
                }else if(type_search == null || field_value == "") {
                    $('.alert-form-search').html("Por favor, completa todos los campos antes de continuar.")
                        .css('font-size', '18px');
                    return;
                }else {

                    var formData = new FormData($(this)[0]);
                    searchData(obj_ajax.ajaxurl, formData, function(response){
                        window.location.href="/handicap?tipo_busqueda="+type_search+"&termino_busqueda="+field_value;
                    })
                    //$(this).submit();
                }
            })

            $('#abrirHistorialPopup').on('click', function(e){
                if (!usuarioGuardado)
                    return;
                
                $('#fgnp-miPopup iframe').remove();

                const iframeTemplate= `<iframe id="cont-iframe" class="fgnp-popup__iframe" src="https://servicios.federacioncolombianadegolf.com/apex/HistorialJuegoResultadoPp?user=${usuarioGuardado.Id}"></iframe>`
                $('#fgnp-miPopup .fgnp-popup__cerrar').after(iframeTemplate)
            })
            getInfoAfiliado(obj_ajax.ajaxurl, usuarioGuardado.Numero_de_documento__c)
        }

		/*Plantilla interna secciones divisiones*/
        if($('.page-id-5889').length > 0) {
            const pathParts = window.location.pathname.split('/').filter(Boolean);
            const slug = pathParts[pathParts.length - 1];

            getDivisional(obj_ajax.ajaxurl, function(divisional){
                let findDivision = null;
                divisional.forEach(function(division) {
                    const nombre = division.NombreDivision.toLowerCase();
                    const slugLower = slug.toLowerCase();
                    const nombreNormalizado = nombre
                    .toLowerCase()
                    .replace(/\s+/g, '-')        // reemplaza espacios por guiones
                    .replace(/[áéíóú]/g, m => 'aeiou'['áéíóú'.indexOf(m)]);

                    if (nombreNormalizado.includes(slugLower) || (nombreNormalizado == "division-aficionada-senior" && slugLower=="aficionado-senior")) {
                        console.log("¡Coincidencia encontrada!", division);
                        findDivision = division.NombreDivision;
                        return;
                    }
                });

                if(!findDivision) {
                    /*window.location.href = "/divisiones";*/
                    console.log("No existe la division")
                    return;

                }

                const capitalizedClubName = findDivision.charAt(0).toUpperCase() + findDivision.slice(1).toLowerCase();

                $('#title-division h2').text(findDivision)
                $('#breadcrumb-division ul').append(`
                    <li class="elementor-icon-list-item elementor-inline-item">
                            <span class="elementor-icon-list-icon">
                            <svg aria-hidden="true" class="e-font-icon-svg e-fas-chevron-right" viewBox="0 0 320 512" xmlns="http://www.w3.org/2000/svg"><path d="M285.476 272.971L91.132 467.314c-9.373 9.373-24.569 9.373-33.941 0l-22.667-22.667c-9.357-9.357-9.375-24.522-.04-33.901L188.505 256 34.484 101.255c-9.335-9.379-9.317-24.544.04-33.901l22.667-22.667c9.373-9.373 24.569-9.373 33.941 0L285.475 239.03c9.373 9.372 9.373 24.568.001 33.941z"></path></svg>
                            </span>
                            <span class="elementor-icon-list-text">${capitalizedClubName}</span>
                    </li>`)
				
				
                const now = new Date();
                const monthDivisional = String(now.getMonth() + 1).padStart(2, '0'); // "01".."12"
                var formData = new FormData();
                formData.append("month","Mes");
                formData.append("divisional",findDivision);
                formData.append("wordSearch","");
                formData.append("allResults", 1);
				
				
                formData.append("action", "get_calendar_tournament");
				
				
				

                sendAjax(obj_ajax.ajaxurl, formData, function(response){
                    if (response) {
                        const dataTournaments = response;
                        $('#cont-tournaments').html('');
                        dataTournaments.forEach(tournament => {
                            const templateTournament = `
                        <div class="parada-card">  <!--OJO CAMBIO FINAL MAQ INT DIVISIONES -->
                           <div class="parada-info">
                                <img src="${tournament.ClubImage}" alt="${tournament.ClubName}" class="logo" />
                                <div>
                                <p class="etiqueta">${tournament.Name}</p>
                                <h2 class="club">${tournament.ClubName}</h2>
                                <p class="fechas-evento">${tournament.DateTournament}</p>
                                <div class="fechas-inscripcion mobile">
                                    <p>21 de Enero de 2025</p>
                                    <p>09 de Enero de 2025</p>
                                </div>
                                </div>
                            </div>

                            <div class="separador-vertical"></div>

                            <div class="inscripcion-info">
                                <p class="fechas-inscripcion desktop">${tournament.DateTournament}</p>
                                <a href="/torneos?id=${tournament.Id}" class="btn-inscripcion">Información</a>
                            </div>
                        </div>` 
                            $('#cont-tournaments').append(templateTournament);
                        });
                    }
                });
            });
        }
        if($('.page-id-5291').length > 0) {
            
            getDetailTournament(obj_ajax.ajaxurl, function(divisional){
                let findDivision = null;
                divisional.forEach(function(division) {
                    const nombre = division.NombreDivision.toLowerCase();
                    const slugLower = slug.toLowerCase(); // <-- el slug que viene de la URL

                    if (nombre.includes(slugLower)) {
                        console.log("¡Coincidencia encontrada!", division);
                        findDivision = division.NombreDivision;
                        return;
                    }
                });

                if(!findDivision) {
                    /*window.location.href = "/divisiones";*/
                    console.log("No existe la division")
                    return;

                }

                const capitalizedClubName = findDivision.charAt(0).toUpperCase() + findDivision.slice(1).toLowerCase();

                $('#title-division h2').text(findDivision)
                $('#breadcrumb-division ul').append(`
                    <li class="elementor-icon-list-item elementor-inline-item">
                            <span class="elementor-icon-list-icon">
                            <svg aria-hidden="true" class="e-font-icon-svg e-fas-chevron-right" viewBox="0 0 320 512" xmlns="http://www.w3.org/2000/svg"><path d="M285.476 272.971L91.132 467.314c-9.373 9.373-24.569 9.373-33.941 0l-22.667-22.667c-9.357-9.357-9.375-24.522-.04-33.901L188.505 256 34.484 101.255c-9.335-9.379-9.317-24.544.04-33.901l22.667-22.667c9.373-9.373 24.569-9.373 33.941 0L285.475 239.03c9.373 9.372 9.373 24.568.001 33.941z"></path></svg>
                            
                            </span>
                            <span class="elementor-icon-list-text">${capitalizedClubName}</span><div>Prub</div>
                    </li>`)
                const now = new Date();
                const monthDivisional = String(now.getMonth() + 1).padStart(2, '0'); // "01".."12"
                var formData = new FormData();
                formData.append("month",monthDivisional);
                formData.append("divisional",findDivision);
                formData.append("wordSearch","");
				/*formData.append("allResults", 1); Nueva linea*/
                formData.append("action", "get_calendar_tournament");

                sendAjax(obj_ajax.ajaxurl, formData, function(response){
                    if (response) {
                        const dataTournaments = response;
                        $('#cont-tournaments').html('');
                        dataTournaments.forEach(tournament => {
                            const templateTournament = `
                            
                            <div class="parada-info">
                                <img src="/wp-content/uploads/2025/05/mesa-de-yeguas.jpg" alt="Mesa de Yeguas Logo" class="logo" />
                                <div>
                                <p class="etiqueta">${tournament.Name}</p>
                                <h2 class="club">${tournament.ClubName}</h2>
                                <p class="fechas-evento">${tournament.DateTournament}</p>
                                <div class="fechas-inscripcion mobile">
                                    <p>21 de Enero de 2025</p>
                                    <p>09 de Enero de 2025</p>
                                </div>
                                </div>
                            </div>

                            <div class="separador-vertical"></div>

                            <div class="inscripcion-info">
                                <p class="fechas-inscripcion desktop">${tournament.DateTournament}</p>
                                <a href="#" class="btn-inscripcion">Realizar Inscripción</a>
                            </div>` 
                            $('#cont-tournaments').append(templateTournament);
                        });
                    }
                });
            });
        }

        $('.tabla-datos').on('click', '.icono-accion', function(event){
            event.preventDefault();
            let index = $(this).data('index');
            
            localStorage.setItem('usuario', JSON.stringify(resultPlayers[index].Persona));
            window.location.href = "/handicap/consulta-de-handicap";
        })

        /*****CONTACT */
        if($('#contact-form').length > 0){
            $('#contact-form').on('submit', function(e){
                e.preventDefault();  // Prevenir el comportamiento por defecto (enviar el formulario)
                e.stopPropagation();
                // Recoger los datos del formulario
                var formData = new FormData($(this)[0]);  // 'form[0]' se usa para acceder al elemento DOM real
                formData.append("action", "send_contact")
                sendAjax(obj_ajax.ajaxurl, formData, function(response){
                    if(response.success == true)
                            alert("Solicitud de contacto realizado correctamente")
                        else
                            alert("Ocurrio un error intentalo nuevamente")

                })

            })
        }

        /*****AFILICIACION */
        if ($('#form-inscripcion').length > 0) {
            $('#form-inscripcion').on('submit', function(e) {
                e.preventDefault();
                e.stopPropagation();

                if(!isValidForm())
                    return;
                const form = this;
                const files = form.querySelectorAll('input[type="file"]');
                const formData = new FormData(form); // Crear el FormData con los demás campos

                // Convertir archivos a base64 y construir objetos
                const filePromises = Array.from(files).map(input => {
                    const file = input.files[0];
                    if (!file) return null;

                    return new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onload = function(event) {
                            const base64 = event.target.result.split(',')[1]; // eliminar encabezado
                            resolve({
                                archivoBase64: base64,
                                nombreArchivo: input.getAttribute('data-filename'),
                                tipoDocumento: input.getAttribute('data-name') || 'Documento' // puedes personalizarlo
                            });
                        };
                        reader.onerror = error => reject(error);
                        reader.readAsDataURL(file);
                    });
                }).filter(Boolean);

                Promise.all(filePromises).then(archivos => {
                    // Añadir los archivos convertidos al FormData como JSON string
                    formData.append('archivos', JSON.stringify(archivos));
                    formData.append('action', 'send_affiliation'); // importante para WordPress

                    // Enviar usando sendAjax que espera FormData
                    sendAjax(obj_ajax.ajaxurl, formData, function(response){
                        if(response.success == true)
                            alert("Solicitud radicada correctamente")
                        else
                            alert("Ocurrio un error intentalo nuevamente")
                    });

                }).catch(err => {
                    console.error("Error procesando archivos:", err);
                });
            });
        }

        /********CALENDARIO */
        if($('.page-id-6629').length > 0){
            let divisionCalendar = "TODOS";
            $('.calendario-table').hide();
            /*getDivisional(obj_ajax.ajaxurl, function(response){
                $('.container-division').append(`<h3 data-division="TODOS">CALENDARIO TORNEOS 2025</h3>`);
                response.forEach(function(division) {
                    const nombre = division.NombreDivision.toUpperCase();
                    $('.container-division').append(`<h3 data-division="${nombre}">CALENDARIO TORNEOS ${nombre}</h3>`);
                });
            });

            /*$('.container-division').on('click', 'h3', function(event){
                divisionCalendar = $(this).data('division');
                const month = $('select[name="filtro_mes"]').val()
                getCalendarPage(divisionCalendar, month)
            });*/
            let month = $('select[name="filtro_mes"]').val()
            let anio = $('select[name="filtro_anio"]').val()
            $('select[name="filtro_anio"]').on('change', function(event){
                anio = $(this).val()
                getCalendarPage(divisionCalendar, anio, month)
            });

            $('select[name="filtro_mes"]').on('change', function(event){
                month = $(this).val()
                getCalendarPage(divisionCalendar, anio, month)
            });

            getCalendarPage(divisionCalendar, null, null)
            
        }
            
        function getCalendarPage(division, anio, month){
            const now = new Date();
            const monthDivisional = month === null ? "Mes": month; 
            const anioDivisional = anio === null ? "Año": anio; 
            var formData = new FormData();
            formData.append("month",monthDivisional);
            formData.append("year", anioDivisional);
            formData.append("divisional",division);
            formData.append("wordSearch","");
            formData.append("allResults", 1);
            formData.append("action", "get_calendar_tournament");

            sendAjax(obj_ajax.ajaxurl, formData, function(response){
                if (response) {
                    const dataTournaments = response;
                    $('.calendario-table tbody').html('');
                    if(dataTournaments.length == 0) {
                        alert("No existen torneos para los datos seleccionados")
                        return;
                    }

                    dataTournaments.forEach(tournament => {
                        const templateTournament = `
                        <tr>
                            <td>${tournament.Division}</td>
                            <td class="columna-torneo">${tournament.Name}</td> <!-- OJO CAMBIO COLUMNA TONREO EN INTERNA CALENDARIO -->
                            <td class="celda-centrada">${tournament.StartDate}</td>
                            <td class="celda-centrada">${tournament.FinishDate}</td>
                            <td class="col-accion-torneo">
                                <a href="/torneos?id=${tournament.Id}" class="link-ver-torneo">VER TORNEO</a>
                            </td>
                        </tr>` 
                        $('.calendario-table tbody').append(templateTournament);
                    });

                    $('.calendario-table').show();
                }
            });
        }
            
		
		/*Nuevo Calendario Home*/
		function sendSearchCalendar(){
            const monthDivisional = $("select[name='select_month']").val()
            const divisional = $("select[name='select_divisional']").val()
            const wordDivisional = $("input[name='value_search']").val()

            var formData = new FormData();
                formData.append("month",monthDivisional);
                formData.append("divisional",divisional);
                formData.append("wordSearch",wordDivisional);
                formData.append("action", "get_calendar_tournament");

            sendAjax(obj_ajax.ajaxurl, formData, function(response){
                if (response) {
                    const dataTournaments = response;
                    $('.cont-calendar').html(''); // Esto limpia los resultados anteriores
                    
                    // Verificamos si la respuesta está vacía
                    if (dataTournaments.length === 0) {
                        $('.cont-calendar').append('<p>No se encontraron torneos con los criterios seleccionados.</p>');
                        return; // Salimos de la función si no hay torneos
                    }

                    dataTournaments.forEach(tournament => {
                        let urlImg = tournament.SubDivisionImage;
                        
                        // --- NUEVA PLANTILLA Calendario home ---
                        const templateTournament = `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 25px 0; border-bottom: 1px solid #eeeeee; font-family: Arial, sans-serif;">
                                
                                <!-- Columna Izquierda: Información del Torneo -->
                                    <div style="flex: 1; min-width: 0;"> <!-- Ojo cambio -->
                               
                                    <h3 style="font-size: 16px; font-weight: bold; color: #000; margin: 0 0 8px 0;">
                                        ${tournament.Name}
                                    </h3>
                                    <p style="font-size: 16px; color: #888888; margin: 0 0 0 0;">
                                        ${tournament.DateTournament}
                                    </p>
                                    <p style="font-size: 16px; font-weight: bold; color: #333333; margin: 0 0 0 0;">
                                        ${tournament.ClubName}
                                    </p>
                                    <p style="font-size: 16px; color: #888888; margin: 0 0 15px 0;">
                                        ${tournament.ClubCity}
                                    </p>
                                    <a href="/torneos?id=${tournament.Id}" style="font-size: 16px; font-weight: bold; color: #1E7E34; text-decoration: none;">
                                        VER MÁS
                                    </a>
                                </div>

                                <!-- Columna Derecha: Logo del Club -->
                                <div style="flex-shrink: 0; margin-left: 20px;">
                                    <img src="${urlImg}" alt="Logo del Club" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 1px solid #dddddd;">  <!-- Ojo camb-->
                                </div>
                            </div>
                        `;
                        

                        $('.cont-calendar').append(templateTournament);
                    });
                } else {
                    // Manejo de error o si no hay respuesta
                    $('.cont-calendar').html('<p>No se encontraron torneos con los criterios seleccionados.</p>');
                }
            });
        }    
		
        function isValidForm(){
            let formValid = true; // Variable para controlar la validez del formulario
            let formFields = document.querySelectorAll('.form-input'); // Todos los inputs con la clase 'form-input'
            let fileInputs = document.querySelectorAll('input[type="file"]'); // Todos los inputs de tipo file
            formFields.forEach(function(field) {
                let errorMessage = field.nextElementSibling; // Encuentra el mensaje de error (siguiente hermano del input)
                if (!field.value) { // Si el campo está vacío
                    formValid = false;
                    if (!errorMessage) { // Si no tiene mensaje de error, agregar uno
                        errorMessage = document.createElement('span');
                        errorMessage.classList.add('error-message');
                        errorMessage.textContent = 'Este campo es obligatorio';
                        field.parentNode.appendChild(errorMessage); // Añadir el mensaje de error al campo
                    }
                } else {
                    // Eliminar el mensaje de error si el campo tiene valor
                    if (errorMessage) {
                        errorMessage.remove();
                    }
                }
            });

            // Validación de campos de archivo
            fileInputs.forEach(function(input) {
                let errorMessage = document.getElementById('error-' + input.id); // Acceder al mensaje de error correspondiente
                if (input.files.length === 0) { // Si no se ha seleccionado un archivo
                    formValid = false;
                    if (!errorMessage) { // Si no tiene mensaje de error, agregar uno
                        errorMessage = document.createElement('span');
                        errorMessage.classList.add('error-message');
                        errorMessage.textContent = 'Este campo es obligatorio';
                        input.parentNode.appendChild(errorMessage); // Añadir el mensaje de error al campo
                    }
                } else {
                    // Eliminar el mensaje de error si se seleccionó un archivo
                    if (errorMessage) {
                        errorMessage.remove();
                    }
                }
            });

            if (!formValid) {
                return false
            }else
                return true;
        }

        function getInfoAfiliado(url, documento) {
            var formData = new FormData();
                formData.append("documento",documento);
                formData.append("action", "get_afiliado");

            sendAjax(url, formData, function(response) {
                if (response) {
                    if(response.InfoAfiliadoResult[0].Respuesta.Mensaje == "OK") {
                        usuarioInfo = response.InfoAfiliadoResult[0].Persona;
                        getClub(obj_ajax.ajaxurl);
                        
                    }else 
                        usuarioInfo = null;

                }
            });
        }

        function searchHandicap(url, formData) {
            sendAjax(url, formData, function(response) {
                if (response) {
                    if(response.Respuesta.Mensaje == "OK") {
                        $('.perfil-header h1').text(response.Nombre);
                        $('.handicap-valor').text(response.Handicap);
                        $('.parcancha-valor').text(response.ParCancha);
                        $('.parcurva-valor').text(response.PatronCurva);
                        $('.parcampo-valor').text(response.PatronCampo);
                        const urlImg = response.Logo.startsWith("https:") ? response.Logo : baseURL + response.Logo;
                        $('.club-logo').html('<img decoding="async" src="'+urlImg+'" alt="Logo Club"></img>');

                        const text = `  <div class="columna-detalles">
                                            <div class="detalle-item"><span>CÓDIGO</span><span>${response.Codigo}</span></div>
                                            <div class="detalle-item"><span>CLUB</span><span>${response.Club}</span></div>
                                            <div class="detalle-item"><span>CAMPO</span><span>${response.Campo}</span></div>
                                            <div class="detalle-item"><span>MARCA</span><span>${response.Marca}</span></div>
                                        </div>
                                        <div class="columna-detalles">
                                            <div class="detalle-item"><span>CATEGORIA</span><span>${response.Categoria}</span></div>
                                            <div class="detalle-item"><span>ÍNDICE AL CORTE</span><span>${response.IndiceCorte}</span></div>
                                            <div class="detalle-item"><span>ÍNDICE AL DÍA</span><span>${response.IndiceDia}</span></div>
                                            <div class="detalle-item"><span>VALIDO HASTA</span><span>${response.Vigencia}</span></div>
                                        </div>`;

                        $('.detalles-grid').html(text);            
                    }else {
                        alert("No existen registros con estas condiciones de jugador")
                    }
                    $('#preloader').css({display: 'none',opacity: 0});
                    

                }
            });
        }

        function searchData(url, params, callback){
            params.append("action", "envio_salesforce");
            $.ajax({
                url: url,  // Usa la URL proporcionada por wp_localize_script
                type: 'POST',
                data: params,  // Usamos FormData aquí
                processData: false,  // Important: No proceses los datos
                contentType: false,  // Important: No se establece contentType automáticamente
                success: function(response) {
                    if(response.data.BusquedaResult) {
                        resultPlayers = response.data.BusquedaResult;
                        
                        if(resultPlayers.length == 1 && resultPlayers[0].Persona == null) {
                            
                            $('#preloader').css({display: 'none',opacity: 0});
                            alert("No existen registros con estas condiciones de jugador");
                            return;
                        }

                        if(resultPlayers.length == 1) {
                            localStorage.setItem('usuario', JSON.stringify(resultPlayers[0].Persona));
                            window.location.href = "/handicap/consulta-de-handicap";
                            return;
                        }

                        if(callback != null) {
                            callback(response.data);
                            return;
                        }
                        const tbody = document.querySelector("#miTablaContenedor .tabla-datos tbody");
                        tbody.innerHTML = '';
                        
                        response.data.BusquedaResult.forEach((item, index) => {
                            const persona = item.Persona;
                            const tr = document.createElement("tr");

                            const tdIcon = document.createElement("td");
                            tdIcon.innerHTML = `
                                <a href="#" data-index="${index}" class="icono-accion" title="Ver detalles">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"></path>
                                    </svg>
                                </a>
                            `;
                            tr.appendChild(tdIcon);

                            const itemsTd = ["CodigoJugador__c", "FirstName", "LastName", "Categoria__c", "Indice__c"];

                            itemsTd.forEach(function(item) {
                                const td = document.createElement("td");
                                td.classList.add("texto-verde");
                                td.textContent = persona[item];
                                tr.appendChild(td);
                            });
                           
                            tbody.appendChild(tr);
                        });
						
                       inicializarPaginadorHandicap(); //OJO INICIA PAGINADOR HANDICAP

                        $('.tabla-contenedor').css('display', 'block');
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error:', error);
                }
            });
        }

        function getClub(url){
            var formData = new FormData();
            formData.append("action", "get_club");

            sendAjax(url, formData, function(data) {
                if (data) {
                    const select = $('#club-select');

                    select.find('option:not(:first)').remove();
                    let selectedClubCode = null;
                    // Agregar nuevas opciones
                    data.RetornaClubesResult.forEach(function(club) {
                        const option = $('<option>', {
                            value: club.codClub,
                            text: club.NombreClub
                        });
                        select.append(option);
                        
                        if(usuarioInfo.FCG_Club_Federado__c == club.NombreClub)
                            selectedClubCode = club.codClub;

                    });
                    if (selectedClubCode !== null) {
                        select.val(selectedClubCode).trigger('change');
                    }
                }
            });
        }

        function sendAjax(url,params, callback){
            $.ajax({
                url: url, 
                type: 'POST',
                data: params,  
                processData: false,  
                contentType: false,  
                success: function(response) {
                    if (response.success) {
                        callback(response.data);
                    } else {
                        callback(null); // o algún mensaje de error
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error:', error);
                }
            });
        }
        // Función para obtener parámetros GET
        function getQueryParams() {
            const params = new URLSearchParams(window.location.search);
            const obj = {};
            for (const [key, value] of params.entries()) {
                obj[key] = value;
            }
            return obj;
        }
        /****Funciones de torneos *****/
        function getDivisional(url, callback){
            var formData = new FormData();
            formData.append("action", "get_divisional");

            sendAjax(url, formData, function(data) {
                if (data && !callback) {
                    const select = $("select[name='select_divisional'");
                    select.find('option:not(:first)').remove();
                    // Agregar nuevas opciones
                    data.DivisionesResult.forEach(function(division) {
                        const option = $('<option>', {
                            value: division.NombreDivision,
                            text: division.NombreDivision
                        });
                        select.append(option);
                    });
                    sendSearchCalendar();
                }else if(data && callback){
                    callback(data.DivisionesResult);
                }else 
                    alert("ocurrio un error")
            });
        }

        //*********** Funciones ranking */
        function getInfoCategories(url){
            var paramsFormData = new FormData();
                paramsFormData.append("action", "get_categories_ranking");

            sendAjax(url, paramsFormData, function(data) {
                if (data) {
                    const selectGender =  $('select[name="filtro_ranking"]');
                    
                    categoriesRanking = data.categories;
                    // Limpiar opciones anteriores, excepto la primera
                    selectGender.find('option:not(:first)').remove();
                    // Agregar nuevas opciones
                    Object.entries(categoriesRanking).forEach(([key, array]) => {
                        const option = $('<option>', {
                            value: key,
                            text: key
                        });
                        selectGender.append(option);
                    });
                    
                    $('select[name="filtro_categoria"]').prop('disabled', true);
                }
            });
        }

        function getRanking(url, formData) {
            sendAjax(url, formData, function(response) {
                if (Array.isArray(response) && response[0]?.errorCode) {
                    alert("No existen registros para esta categoría");
                    return;
                }    

                if (response && response?.RetornaCategoriasResult) {
                    const dataRanking = response.RetornaCategoriasResult;
                    $('.ranking-table tbody').html('');
                    dataRanking.forEach(ranking => {
                        const base = baseURL+'Ranking_VistaEventosParticipantesPp';
                        const params = new URLSearchParams({
                            participante: ranking.Federado_Id,
                            categoria: response.HeaderCategoriaResult.IdCategoria,
                            posicion: ranking.Posicion,
                            genero: response.HeaderCategoriaResult.Genero_Categoria,
                            popup: 1,
                            publicacion: ranking.Fecha_de_Publicacion
                        });

                        const slug = (ranking.Federado_Name || '')
                        .normalize('NFD')
                        .replace(/[\u0300-\u036f]/g, '') // quita acentos
                        .toLowerCase()
                        .replace(/[^a-z0-9\s-]/g, '') // deja solo letras, números, espacios y guiones
                        .trim()
                        .replace(/\s+/g, '-')
                        .replace(/-+/g, '-');
                        const urlImg = ranking.Federado_Account_Logo.startsWith("https://") ? ranking.Federado_Account_Logo : baseURL + ranking.Federado_Account_Logo;
                        // Resultado más limpio
                        const finalURL = `${base}?${params.toString()}`;
                        const classSpan = quitarTildes(ranking.Movimiento);
                        const posMovement = ranking.Movimiento_Cantidad_De_Posiciones == 0 ? ' - ' : ranking.Movimiento_Cantidad_De_Posiciones;
                        const templateRanking = `
                            <tr>Federado_Account_Logo
                                <td style="text-align:center;">${ranking.Posicion}</td>
                                <td style="text-align:center;" class="mov-${classSpan}">${posMovement}</td>
                                <td><a href="#" class="ranking-link" data-slug="${slug}" data-url='${finalURL}'>
                                    ${ranking.Federado_Name}
                                    </a>
                                </td>
                                <td style="text-align:center;"><img src="${urlImg}" width="100"/></td>
                                <td style="text-align:center;">${ranking.Puntos_Promedio.toFixed(3)}</td>
                                <td style="text-align:center;">${ranking.Divisor_Aplicado}</td>
                            </tr>` 

                        $('.ranking-table tbody').append(templateRanking);
                    });
                    $(".boton-descarga-ranking")
                        .attr("href", response.HeaderCategoriaResult.PDF_URL)
                        .text("Versión Descargable Ranking "+$('select[name="filtro_categoria"] option:selected').text());
                    
                    $("#fecha-publicacion").text(response.HeaderCategoriaResult.FechaPublicacion);
			
			        inicializarPaginadorRanking(); // OJO LLAMA PAGINADOR RANKING

                    $('.ranking-meta, .ranking-table, .boton-descarga-ranking').css('display', 'block');
                }
            });
        }
        function quitarTildes(texto) {
          return texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        }
    });
});