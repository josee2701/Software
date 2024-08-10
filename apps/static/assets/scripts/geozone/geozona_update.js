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

        // Configura el mapa y las funcionalidades adicionales.
        this.initMap();
    }

    initMap() {
        const center = { lat: 4.6236454, lng: -74.0570064 };
        this.map = new google.maps.Map(document.getElementById('map'), {
            center: center,
            zoom: 11,
        });

        this.initializeDrawingManager();
        // this.initializeAutocomplete();
        this.setupColorChangeListeners();
        // Asegúrate de que estos métodos se llamen después de la inicialización del mapa.
        this.checkShapeType();
        this.setupInitialShape();
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
            strokeColor: document.getElementById('id_color_edges').value,
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
            drawingControl: false,
            drawingControlOptions: {
                position: google.maps.ControlPosition.TOP_CENTER,
                drawingModes: [
                    google.maps.drawing.OverlayType.MARKER,
                    google.maps.drawing.OverlayType.CIRCLE,
                    // google.maps.drawing.OverlayType.POLYGON
                ]
            },
            markerOptions: { draggable: true },
            circleOptions: this.getDefaultCircleOptions(), // Asume una función definida para opciones predeterminadas.
            polygonOptions: this.getDefaultPolygonOptions() // Asume una función definida para opciones predeterminadas.
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
        google.maps.event.addListener(this.drawingManager, 'polygoncomplete', this.onPolygonComplete.bind(this));
    }

    // Actualiza las opciones de color en el DrawingManager y en todas las formas existentes.
    updateDrawingOptions = () => {
        const fillColor = document.getElementById('id_color').value;
        const strokeColor = document.getElementById('id_color_edges').value;

        // Solo una implementación de updateDrawingOptions es necesaria.
        // Asegúrate de actualizar tanto círculos como polígonos aquí.

        this.drawingManager.setOptions({
            circleOptions: {
                fillColor: fillColor,
                strokeColor: strokeColor,
                fillOpacity: 0.4,
                strokeWeight: 3,
                clickable: false,
                editable: true,
                zIndex: 1
            },
            polygonOptions: {
                fillColor: fillColor,
                strokeColor: strokeColor,
                fillOpacity: 0.4,
                strokeWeight: 3,
                clickable: false,
                editable: true,
                zIndex: 1,
                draggable: true
            }
        });

        // Actualiza los colores de todas las formas existentes
    this.allCircles.forEach(circle => {
        circle.setOptions({ fillColor, strokeColor });
    });
    }
    // Configuración general para el manejo de los colores para los circulo y los poligonales

    /**
     * Agrega oyentes para los cambios de color en las formas.
     */
    setupColorChangeListeners() {
        // Asigna los oyentes de eventos para cambios de color.
        document.getElementById('id_color').addEventListener('input', this.updateDrawingOptions.bind(this));
        document.getElementById('id_color_edges').addEventListener('input', this.updateDrawingOptions.bind(this));
    }
    checkShapeType = () => {
        const shapeType = document.getElementById('id_shape_type').value;

        // Ocultar o mostrar campos basados en shapeType
        const displayStyle = shapeType === '0' ? 'none' : '';
        document.getElementById('id_speed').parentNode.style.display = displayStyle;
        document.getElementById('id_color').parentNode.style.display = displayStyle;
        document.getElementById('id_color_edges').parentNode.style.display = displayStyle;

        // Crear marcador o círculo basado en shapeType
        if (shapeType === '0') {
            // Limpia círculos existentes si es necesario.
            this.clearCircles();
            // Asegurarse de que no haya un marcador existente
            if (!this.marker) {
                this.initializeMarker();
            }
        } else if (shapeType === '1') {
            // Limpia el marcador existente si es necesario.
            this.clearMarker();
            // Asegurarse de que no haya un círculo existente
                this.createInitialCircle();
        }
    }
    // Ejemplo de cómo podrías limpiar los círculos
    clearCircles() {
        this.allCircles.forEach(circle => circle.setMap(null));
        this.allCircles = [];
    }

    // Ejemplo de cómo podrías limpiar el marcador
    clearMarker() {
        if (this.marker) {
            this.marker.setMap(null);
            this.marker = null;
        }
    }

//-------------------------------------------------------------------------------------------------

    // Inicio de codigo para la realizacion de punto de control

    // Inicializa el marcador en el mapa basado en los valores de los campos de latitud y longitud
    initializeMarker() {
        const latitude = parseFloat(document.getElementById('id_latitude').value);
        const longitude = parseFloat(document.getElementById('id_longitude').value);

        if (!isNaN(latitude) && !isNaN(longitude)) {
            const position = new google.maps.LatLng(latitude, longitude);
            this.map.setCenter(position);
        this.map.setZoom(17); // Puedes ajustar el nivel de zoom según tus necesidades
            if (this.marker) {
                this.marker.setPosition(position); // Si el marcador ya existe, actualiza su posición.

            } else {
                // Crea un nuevo marcador si no existe uno.
                this.marker = new google.maps.Marker({
                    position: position,
                    map: this.map,
                    draggable: true, // Asegúrate de que el marcador sea arrastrable
                });
                this.addMarkerListeners(this.marker); // Agrega los oyentes al nuevo marcador.
            }
        }
    }

    // Agrega un oyente para el evento 'dragend' del marcador, para actualizar los campos de formulario.
    addMarkerListeners = (marker) => {
        google.maps.event.addListener(marker, 'dragend', () => this.updateMarkerFields(marker));

    }

    /**
     * Actualiza los campos de formulario con los valores de latitud y longitud del marcador.
     * @param {google.maps.Marker} marker - El marcador del cual obtener la posición.
     */
    updateMarkerFields = (marker) => {
        const position = marker.getPosition();
        document.getElementById('id_latitude').value = position.lat().toFixed(5);
        document.getElementById('id_longitude').value = position.lng().toFixed(5);
        // Actualiza otros campos según sea necesario.
        this.checkShapeType(); // Verifica y actualiza la visibilidad de los campos según id_shape_type.

}



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


//-------------------------------------------------------------------------------------------------


    // inicio de codigo para la realizacion de Geozonas circulares

    createInitialCircle() {
        // Obtiene los valores de los campos.
        const latitude = parseFloat(document.getElementById('id_latitude').value);
        const longitude = parseFloat(document.getElementById('id_longitude').value);
        const radius = parseFloat(document.getElementById('id_radius').value);
        const fillColor = document.getElementById('id_color').value;
        const strokeColor = document.getElementById('id_color_edges').value;

        if (!isNaN(latitude) && !isNaN(longitude) && !isNaN(radius)) {
            const circleOptions = {
                strokeColor: strokeColor,
                fillColor: fillColor,
                fillOpacity: 0.4,
                map: this.map,
                center: new google.maps.LatLng(latitude, longitude),
                radius: radius,
                editable: true,
                draggable: true,
            };

            const circle = new google.maps.Circle(circleOptions);
            this.allCircles.push(circle); // Agrega el círculo al array para su posterior gestión.
            this.addCircleListeners(circle); // Añade listeners para cambios en el círculo.
            // Ajusta el mapa para que el círculo completo sea visible
        this.map.fitBounds(circle.getBounds());
        } else {
            console.log("Los valores de latitud, longitud o radio no son válidos.");
        }
    }
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
        // Asegúrate de que el círculo recién creado se actualice con los colores actuales.
    this.updateDrawingOptions();
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
    updateCircleFields = (circle) => {
        const center = circle.getCenter();
        const radius = circle.getRadius();
        document.getElementById('id_latitude').value = center.lat().toFixed(5);
        document.getElementById('id_longitude').value = center.lng().toFixed(5);
        document.getElementById('id_radius').value = Math.round(radius);


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

    /**
    * Maneja la creación de un nuevo polígono.
    * @param {Object} polygon - Polígono creado
    */

    onPolygonComplete(polygon) {
        if (shouldDeleteExistingShapes()) {
            deleteAllShapes();
        }
        allPolygon.push(polygon);
        drawingManager.setDrawingMode(null);
    }

}
