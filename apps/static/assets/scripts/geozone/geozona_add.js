/**
 * Inicializa el mapa de Google Maps.
 */
function initMap() {
    new MapManager();
}

/**
* Gestiona la configuración y la interacción con el mapa de Google Maps.
*/
class MapManager {
    constructor() {
        // Inicializa propiedades para manejar diferentes aspectos del mapa.
        this.map = null;
        this.drawingManager = null;
        this.autocomplete = null;
        this.allOverlays = [];
        this.allCircles = [];
        this.allPolygon = [];
        this.marker = null; // Se mantiene un solo marcador activo.

        // Configura el mapa inmediatamente después de crear la instancia.
        this.initMap();
    }

    /**
     * Configura el mapa, estableciendo el centro, el zoom, y las funcionalidades de dibujo y autocompletado.
     */
    initMap() {
        const center = { lat: 4.6236454, lng: -74.0570064 }; // Coordenadas del centro (Bogotá, Colombia).
        this.map = new google.maps.Map(document.getElementById('map'), {
            center: center,
            zoom: 11,
        });
        this.initializeDrawingManager();
        this.setupColorChangeListeners();
        this.initializeAutocomplete(); // Añade la funcionalidad de autocompletado.
    }

    /**
     * Inicializa el autocompletado de Google Places.
     */
    initializeAutocomplete() {
        const input = document.getElementById('pac-input'); // Verifica que este sea el ID correcto para tu input HTML.
        this.autocomplete = new google.maps.places.Autocomplete(input);
        this.autocomplete.bindTo('bounds', this.map); // Vincula el autocompletado a los límites del mapa.

        // Escucha el evento de cambio de lugar en el autocompletado.
        this.autocomplete.addListener('place_changed', () => {
            const place = this.autocomplete.getPlace();
            if (!place.geometry) {
                console.log("Autocomplete's place contains no geometry");
                return;
            }
            if (place.geometry.viewport) {
                this.map.fitBounds(place.geometry.viewport);
            } else {
                this.map.setCenter(place.geometry.location);
                this.map.setZoom(17); // Zoom cercano si no hay viewport.
            }
            // Aquí puedes añadir más lógica, como mostrar un marcador en el lugar seleccionado.
        });
    }
    getDefaultCircleOptions() {
        return {
            fillColor: document.getElementById('id_color').value,
            strokeColor: document.getElementById('id_color_edges').value,
            fillOpacity: 0.4,
            strokeWeight: 3,
            clickable: false,
            editable: true,
            zIndex: 1
        };
    }

    getDefaultPolygonOptions() {
        return {
            fillColor: document.getElementById('id_color').value,
            strokeColor:document.getElementById('id_color_edges').value,
            fillOpacity: 0.4,
            strokeWeight: 3,
            clickable: false,
            editable: true,
            zIndex: 1,
            draggable: true
        };
    }

    /**
     * Configura el DrawingManager para permitir al usuario dibujar en el mapa.
     */
    initializeDrawingManager() {
        this.drawingManager = new google.maps.drawing.DrawingManager({
            drawingMode: null,
            drawingControl: true,
            drawingControlOptions: {
                position: google.maps.ControlPosition.TOP_CENTER,
                drawingModes: [
                    google.maps.drawing.OverlayType.MARKER,
                    google.maps.drawing.OverlayType.CIRCLE,
                ]
            },
            markerOptions: { draggable: true },
            circleOptions: this.getDefaultCircleOptions(), // Asume una función definida para opciones predeterminadas.
            // polygonOptions: this.getDefaultPolygonOptions() // Asume una función definida para opciones predeterminadas.
        });
        this.drawingManager.setMap(this.map);
        this.setupDrawingListeners();
    }

    /**
     * Configura los oyentes de eventos para las formas dibujadas por el usuario.
     */
    setupDrawingListeners() {
        google.maps.event.addListener(this.drawingManager, 'markercomplete', this.onMarkerComplete.bind(this));
        google.maps.event.addListener(this.drawingManager, 'circlecomplete', this.onCircleComplete.bind(this));
        // google.maps.event.addListener(this.drawingManager, 'polygoncomplete', this.onPolygonComplete.bind(this));
    }





    // Configuración general para el manejo de los colores para los circulo y los poligonales

    /**
     * Agrega oyentes para los cambios de color en las formas.
     */
    setupColorChangeListeners() {
        document.getElementById('id_color').addEventListener('input', this.updateDrawingOptions.bind(this));
        document.getElementById('id_color_edges').addEventListener('input', this.updateDrawingOptions.bind(this));
    }

    /**
     * Actualiza las opciones de color en el DrawingManager y en todas las formas existentes.
     */
    updateDrawingOptions() {
        const fillColor = document.getElementById('id_color').value;
        const strokeColor = document.getElementById('id_color_edges').value;

        this.updateShapeOptions('circleOptions', fillColor, strokeColor);
        // this.updateShapeOptions('polygonOptions', fillColor, strokeColor);
        this.updateExistingShapesColor(this.allCircles, fillColor, strokeColor);
        // this.updateExistingShapesColor(this.allPolygon, fillColor, strokeColor);
    }
    // Este método actualiza los colores en el DrawingManager y en todas las formas existentes
    updateDrawingOptions() {
        const fillColor = document.getElementById('id_color').value;
        const strokeColor = document.getElementById('id_color_edges').value;

        // Actualiza las opciones de formas en DrawingManager
        const circleOptions = this.drawingManager.get('circleOptions');
        circleOptions.fillColor = fillColor;
        circleOptions.strokeColor = strokeColor;
        this.drawingManager.set('circleOptions', circleOptions);

        // const polygonOptions = this.drawingManager.get('polygonOptions');
        // polygonOptions.fillColor = fillColor;
        // polygonOptions.strokeColor = strokeColor;
        // this.drawingManager.set('polygonOptions', polygonOptions);

        // Actualiza los colores de todas las formas existentes
        this.updateExistingShapesColor(this.allCircles, fillColor, strokeColor);
        // Suponiendo que allPolygon es una propiedad que contiene todos los polígonos
        // this.updateExistingShapesColor(this.allPolygon, fillColor, strokeColor);
    }

    /**
     * Actualiza el color de todas las formas existentes de un tipo específico.
     * @param {Array} shapes - Arreglo de formas (círculos o polígonos) a actualizar.
     * @param {string} fillColor - Color de relleno.
     * @param {string} strokeColor - Color del borde.
     */
    updateExistingShapesColor(shapes, fillColor, strokeColor) {
        shapes.forEach(shape => {
            shape.setOptions({ fillColor, strokeColor });
        });
    }

//-------------------------------------------------------------------------------------------------


    // Inicio de codigo para la realizacion de punto de control

    /**
     * Se llama cuando el usuario completa el dibujo de un marcador.
     * @param {google.maps.Marker} newMarker - El nuevo marcador creado.
     */
    onMarkerComplete(newMarker) {
        if (this.marker) {
            this.marker.setMap(null); // Elimina el marcador anterior del mapa.
        }
        this.marker = newMarker; // Almacena la referencia del nuevo marcador.
        this.drawingManager.setDrawingMode(null);
        this.drawingManager.setOptions({ drawingControl: false }); // Desactiva el control de dibujo.   .
        this.addMarkerListeners(this.marker); // Agrega oyentes para el nuevo marcador.
        this.updateMarkerFields(this.marker); // Actualiza los campos de latitud y longitud.
    }

    /**
     * Agrega un oyente para el evento 'dragend' del marcador, para actualizar los campos de formulario.
     * @param {google.maps.Marker} marker - El marcador a escuchar.
     */
    addMarkerListeners(marker) {
        google.maps.event.addListener(marker, 'dragend', () => this.updateMarkerFields(marker));
    }

    /**
     * Actualiza los campos de formulario con los valores de latitud y longitud del marcador.
     * @param {google.maps.Marker} marker - El marcador del cual obtener la posición.
     */
    updateMarkerFields(marker) {
        const position = marker.getPosition();
        document.getElementById('id_latitude').value = position.lat().toFixed(5);
        document.getElementById('id_longitude').value = position.lng().toFixed(5);
        document.getElementById('id_radius').value = Math.round(500); // Redondeo al entero más cercano
        document.getElementById('id_shape_type').value = 0;
        document.getElementById('id_speed').parentNode.style.display = 'none'; // Oculta el campo de velocidad
        document.getElementById('id_color').parentNode.style.display = 'none';
        document.getElementById('id_color_edges').parentNode.style.display = 'none';
        // Aquí puedes actualizar más campos relacionados con el marcador si es necesario.
    }


//-------------------------------------------------------------------------------------------------
    // inicio de codigo para la realizacion de Geozonas circulares
    /**
 * Maneja la creación de un nuevo círculo, validando su tamaño y actualizando la interfaz.
 * @param {Object} circle - Círculo creado
 */

    onCircleComplete(circle) {
        // Aplica los colores seleccionados actualmente al círculo recién creado
        const fillColor = document.getElementById('id_color').value;
        const strokeColor = document.getElementById('id_color_edges').value;
        circle.setOptions({
            fillColor: fillColor,
            strokeColor: strokeColor
        });
        this.allCircles.push(circle); // Asegúrate de usar this.allCircles
        this.drawingManager.setDrawingMode(null);
        this.drawingManager.setOptions({ drawingControl: false }); // Desactiva el control de dibujo.
        this.addCircleListeners(circle); // Debe ser this.addCircleListeners
        this.validateCircleSize(circle); // Valida y ajusta el tamaño antes de actualizar los campos
        this.updateCircleFields(circle); // Debe ser this.updateCircleFields
    }
    addCircleListeners(circle) {
        google.maps.event.addListener(circle, 'radius_changed', () => {
            this.validateCircleSize(circle); // Valida y ajusta el tamaño si es necesario
            this.updateCircleFields(circle); // Actualiza los campos con el nuevo radio
        });
        google.maps.event.addListener(circle, 'center_changed', () => {
            this.updateCircleFields(circle); // Actualiza los campos con el nuevo centro
        });
    }
    updateCircleFields(circle) {
        const center = circle.getCenter();
        const radius = circle.getRadius();
        document.getElementById('id_latitude').value = center.lat().toFixed(5);
        document.getElementById('id_longitude').value = center.lng().toFixed(5);
        document.getElementById('id_radius').value = Math.round(radius); // Redondeo al entero más cercano
        document.getElementById('id_shape_type').value = 1; // Asumiendo que quieres almacenar el tipo de forma como 'circle'
    }

    // Utiliza this para referirte a las propiedades de la clase.
    validateCircleSize(circle) {
        let adjusted = false;
        if (circle.getRadius() > 5000) {
            alert("El radio no puede ser mayor a 5000 metros.");
            circle.setRadius(5000);
            adjusted = true;
        }
        if (circle.getRadius() < 5) {
            alert("El radio no puede ser menor que 5 metros.");
            circle.setRadius(5);
            adjusted = true;
        }
        if (adjusted) {
            // Si se ajustó el tamaño del círculo, actualiza los campos de inmediato
            this.updateCircleFields(circle);
        }
        return !adjusted;
    }

//-------------------------------------------------------------------------------------------------

    // Inicio de codigo para la realizacion de Geozonas poligonales

    // /**
    // * Maneja la creación de un nuevo polígono.
    // * @param {Object} polygon - Polígono creado
    // */

    // onPolygonComplete(polygon) {
    //     if (shouldDeleteExistingShapes()) {
    //         deleteAllShapes();
    //     }
    //     allPolygon.push(polygon);
    //     drawingManager.setDrawingMode(null);
    // }

}
