""" Modelos asociados al módulo de reporte en tiempo real.

Este módulo crea los modelos de la base de datos utilizados para crear vehículos, dispositivos, y
almacenar los datos de las tramas. También crea una tabla de relación entre el tipo de dispositivo,
el número de evento y el evento que reporte el dispositivo (elemento IO).

Para una mayor referencia sobre la creación de modelos en Django, consulte
https://docs.djangoproject.com/en/4.1/topics/db/models/
"""
from colorfield.fields import ColorField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import User


class MobileOperator(models.Model):

    """El modelo tiene un único campo name, que es un campo de caracteres con una longitud máxima
    de 30 caracteres y se etiqueta como name en la interfaz de administración"""

    name = models.CharField(max_length=30, verbose_name=_("name"))

    def __str__(self):
        return self.name


class DataPlan(models.Model):
    """
    Define el modelo de plan de datos para asignar a una tarjeta SIM. Tabla 'realtime_data_plan'.
    """

    name = models.CharField(max_length=30, verbose_name=_("name"))
    coin = models.ForeignKey(
        "whitelabel.Coin", verbose_name=_("coin"), on_delete=models.CASCADE, null=True
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("price")
    )
    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        verbose_name=_("company"),
        null=True,
    )
    operator = models.ForeignKey(
        "MobileOperator",
        verbose_name=_("operator"),
        on_delete=models.CASCADE,
        null=True,
    )
    visible = models.BooleanField(default=True, verbose_name=_("visible"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("last updated"))

    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_dataplan",
        null=True,
    )

    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_dataplan",
        null=True,
    )

    def __str__(self):
        """
        La función __str__ es una función especial que se llama cuando imprime un objeto
        :return: El nombre del objeto
        """
        return self.name + " - " + self.operator.name


class SimCard(models.Model):
    """
    Define el modelo  para la creación de simcards. Tabla 'realtime_simcard`.
    """

    serial_number = models.CharField(
        verbose_name=_("ICCID or serial number"), max_length=20, null=True
    )
    phone_number = models.PositiveBigIntegerField(
        verbose_name=_("phone number"), blank=True, null=True
    )
    is_active = models.BooleanField(default=True, verbose_name=_("active"))
    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        verbose_name=_("company"),
        null=True,
    )
    activate_date = models.DateField(verbose_name=_("activate date"))
    data_plan = models.ForeignKey(
        "realtime.DataPlan",
        on_delete=models.CASCADE,
        verbose_name=_("data plan"),
        null=True,
    )
    iz_az_simcard = models.BooleanField(default=False, verbose_name="AZ simcard")
    last_update = models.DateTimeField(
        verbose_name=_("last update"),
        auto_now=True,
    )
    visible = models.BooleanField(default=True, verbose_name=_("visible"))
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_simcard",
        null=True,
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_simcard",
        null=True,
    )

    class Meta:
        ordering = ["activate_date"]

    def __str__(self):
        """
        La función toma un número de teléfono y el nombre de una empresa, y
        devuelve una cadena que contiene el número de teléfono y el nombre de la empresa.
        :return: El número de teléfono y el nombre de la empresa.
        """
        return f"{self.phone_number}"


class Device(models.Model):
    """
    Define the model for creating devices. Table 'realtime_device'.
    """

    imei = models.CharField(
        primary_key=True,
        max_length=20,
        validators=[MinLengthValidator(15)],
        verbose_name=_("imei"),
    )
    familymodel = models.ForeignKey(
        "FamilyModelUEC",
        on_delete=models.CASCADE,
        verbose_name=_("familymodel"),
        default=1,
    )
    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        verbose_name=_("company"),
        null=True,
    )
    serial_number = models.CharField(
        max_length=30,
        unique=True,
        verbose_name=_("serial number"),
        blank=False,
        null=False,
    )
    firmware = models.CharField(max_length=30, verbose_name=_("firmware"))
    is_active = models.BooleanField(default=True, verbose_name=_("active"))
    simcard = models.ForeignKey(
        SimCard,
        on_delete=models.CASCADE,
        null=True,
        verbose_name=_("simcard"),
    )
    last_update = models.DateTimeField(
        verbose_name=_("last update"),
        auto_now=True,
    )
    create_date = models.DateField(
        verbose_name=_("create date"),
        auto_now_add=True,
        null=True,
        blank=True,
    )
    visible = models.BooleanField(default=True, verbose_name=_("visible"))
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_device",
        null=True,
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_device",
        null=True,
    )
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("ip"))

    def __str__(self):
        return f"{self.imei}"


class Manufacture(models.Model):
    """
    Nombre que representa un fabricante.
    """

    name = models.CharField(max_length=15, verbose_name=_("Manufacture"))

    def __str__(self):
        return self.name


class ModelUEC(models.Model):
    """
    Un modelo que representa un modelo de familia de dispositivos.
    """

    name = models.CharField(max_length=20, verbose_name=_("model"))
    family_uec = models.CharField(max_length=20, verbose_name=_("family_uec"))
    network_type = models.CharField(max_length=10, verbose_name=_("network type"))

    def __str__(self):
        return f"{self.name}: {self.network_type}"


class FamilyModelUEC(models.Model):
    manufacture = models.ForeignKey(
        "Manufacture",
        verbose_name=_("manufacture"),
        on_delete=models.CASCADE,
        null=True,
    )
    model = models.ForeignKey(
        "ModelUEC", verbose_name=_("model"), on_delete=models.CASCADE, null=True
    )

    def __str__(self):
        return (
            f"{self.manufacture.name} - {self.model.name} ({self.model.network_type})"
        )


class Vehicle(models.Model):
    """
    Define el modelo para la creación de vehículos. Tabla `realtime_vehicle`.
    """

    class FuelType(models.TextChoices):
        gasoline = "Gasoline", _("Gasoline")
        diesel = "Diesel", _("Diesel")
        gas = "Gas", _("Gas")
        electric = "Electric", _("Electric")
        hybrid = "Hybrid", _("Hybrid")

    license = models.CharField(
        max_length=10,
        verbose_name=_("license "),
        default="",
        null=False,
        blank=False,
    )
    chassis = models.CharField(
        max_length=25,
        blank=True,
        verbose_name=_("chassis"),
    )
    cylinder_capacity = models.PositiveIntegerField(
        verbose_name=_("cylinder capacity"), null=True, blank=True
    )
    km_per_gallon = models.PositiveIntegerField(
        verbose_name=_("km per gallon"), null=True, blank=True
    )
    vehicle_type = models.CharField(max_length=25, verbose_name=_("vehicle type"))
    model = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("model"),
        validators=[MaxValueValidator(9999)],
    )
    brand = models.CharField(
        max_length=25,
        blank=True,
        verbose_name=_("brand"),
    )
    engine_serial = models.CharField(
        max_length=25, blank=True, verbose_name=_("engine serial")
    )
    fuel_type = models.CharField(
        max_length=20,
        verbose_name=_("fuel type"),
        choices=FuelType.choices,
    )
    max_speed_allowed = models.PositiveIntegerField(
        verbose_name=_("max speed allowed"), null=True, blank=True
    )
    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        verbose_name=_("company"),
        null=True,
    )
    insurance = models.CharField(
        max_length=25, verbose_name=_("insurance"), null=True, blank=True
    )
    owner = models.CharField(
        max_length=50, verbose_name=_("owner"), null=True, blank=True
    )
    fuel_tank_capacity = models.IntegerField(
        verbose_name=_("fuel tank capacity"), null=True, blank=True
    )
    icon = models.ImageField(
        # Donde 'Iconos_vehicles/' es el subdirectorio de MEDIA_ROOT donde se almacenarán las imágenes.
        upload_to="Iconos_vehicles/",
        verbose_name=_("icon"),
        null=True,
        blank=True,
        default="https://sadevnp.blob.core.windows.net/media/Iconos_vehicles/coche%20(1).png",
    )
    is_active = models.BooleanField(default=True, verbose_name=_("active"))
    color = models.CharField(max_length=10, blank=True, verbose_name=_("color"))
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, verbose_name=_("device"), null=True
    )
    line = models.CharField(max_length=50, blank=True, verbose_name=_("line"))
    camera = models.BooleanField(default=False, verbose_name=_("camera"))
    asset_type = models.BooleanField(default=True, verbose_name=_("asset type"))
    microphone = models.BooleanField(default=False, verbose_name=_("microphone"))
    remote_shutdown = models.BooleanField(
        default=False, verbose_name=_("remote shutdown")
    )
    installation_date = models.DateField(
        verbose_name=_("Installation date"),
    )
    visible = models.BooleanField(default=True, verbose_name=_("Visible"))
    capacity = models.PositiveIntegerField(
        blank=True,
        verbose_name=_("Capacity"),
        null=True,
    )
    n_interno = models.CharField(
        max_length=20,
        verbose_name=_("N° internal"),
        null=True,
    )
    alias = models.CharField(max_length=10, verbose_name=_("Alias"), blank=True)
    last_update = models.DateTimeField(
        verbose_name=_("last update"),
        auto_now=True,
    )
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_vehicle",
        null=True,
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_vehicle",
        null=True,
    )

    def __str__(self):
        return f"{self.license}"


class VehicleGroup(models.Model):
    name = models.CharField(max_length=60, blank=False, verbose_name=_("name"))
    vehicles = models.ManyToManyField(
        "Vehicle", verbose_name=_("vehicles"), blank=False
    )
    visible = models.BooleanField(default=True, verbose_name=_("Visible"))
    last_update = models.DateTimeField(
        verbose_name=_("last update"),
        auto_now=True,
    )
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_vehiclegroup",
        null=True,
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_vehiclegroup",
        null=True,
    )

    def __str__(self):
        return f"{self.name}"


class AVLData(models.Model):
    """
    Define el modelo para almacenar la información de las tramas que reportan los dispositivos.
    Tabla `realtime_avldata`.
    """

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("device"),
    )

    main_event = models.IntegerField(null=False, verbose_name=_("main event"))
    server_date = models.DateTimeField(null=True, verbose_name=_("server date"))
    # The code provided is not valid Python code. It seems to be a comment with the text "signal_date" followed by a
    # series of pound signs. It does not perform any specific action or functionality in Python.
    signal_date = models.DateTimeField(
        null=True, auto_now_add=True, verbose_name=_("signal date")
    )
    odometer = models.FloatField(null=True, verbose_name=_("odometer"))
    latitude = models.FloatField(null=False, verbose_name=_("latitude"))
    longitude = models.FloatField(null=False, verbose_name=_("longitude"))
    calculated_speed = models.PositiveSmallIntegerField(
        null=False, verbose_name=_("calculated speed")
    )
    angle = models.PositiveSmallIntegerField(null=True, verbose_name=_("angle"))
    data_stream = models.CharField(
        max_length=4000, null=True, verbose_name=_("data stream")
    )
    info = models.CharField(max_length=2000, null=True, verbose_name=_("info"))

    class Meta:
        db_table = "realtime_avl_data"

    def __str__(self):
        return f"{self.device} --> [ {self.server_date} ]"


class Last_Avl(models.Model):
    """
    Define el modelo para almacenar la información de las tramas que reportan los dispositivos.
    Tabla `realtime_avldata`.
    """

    imei = models.CharField(max_length=20, verbose_name=_("imei"))
    manufacturer = models.CharField(max_length=20, verbose_name=_("manufacturer"))
    uec_model = models.CharField(max_length=20, verbose_name=_("model"))
    license = models.CharField(max_length=20, verbose_name=_("license"))
    conn_type = models.CharField(max_length=20, verbose_name=_("conn_type"))
    ip = models.CharField(max_length=20, verbose_name=_("ip"))
    port = models.IntegerField(null=True, verbose_name=_("port"))
    socket = models.IntegerField(null=False, verbose_name=_("socket"))
    company = models.IntegerField(null=False, verbose_name=_("company"))
    main_event = models.IntegerField(null=False, verbose_name=_("main_event"))
    event_name = models.CharField(max_length=200, verbose_name=_("event_name"))
    server_date = models.DateTimeField(null=True, verbose_name=_("server_date"))
    signal_date = models.DateTimeField(null=True, verbose_name=_("signal_date"))
    latitude = models.FloatField(null=False, verbose_name=_("latitude"))
    longitude = models.FloatField(null=False, verbose_name=_("longitude"))
    altitude = models.FloatField(null=False, verbose_name=_("altitude"))
    speed = models.FloatField(null=False, verbose_name=_("speed"))
    angle = models.FloatField(null=False, verbose_name=_("angle"))
    odometer = models.FloatField(null=False, verbose_name=_("odometer"))
    satellites = models.IntegerField(null=False, verbose_name=_("satellites"))
    central_alarm = models.BooleanField(default=False, verbose_name=_("central_alarm"))
    user_alarm = models.BooleanField(default=False, verbose_name=_("user_alarm"))
    geofence = models.CharField(max_length=200, verbose_name=_("geofence"))
    nearly = models.CharField(max_length=200, verbose_name=_("nearly"))
    status_events = models.CharField(max_length=2000, verbose_name=_("status_events"))
    info_events = models.CharField(max_length=2000, null=True, verbose_name=_("info"))
    unrecognized_events = models.CharField(
        max_length=2000, verbose_name=_("unrecognized_events")
    )
    # widgets_reports = models.CharField(
    #     max_length=2000, null=True, verbose_name=_("widgets_reports")
    # )

    class Meta:
        db_table = "realtime_last_avl"

    def __str__(self):
        return f"{self.imei} --> [ {self.ip} ]"


class Commands(models.Model):
    """
    Define el modelo para almacenar los comandos que se envian a los dispositivos.
    Tabla `realtime_commands`.
    """

    model = models.ForeignKey(
        FamilyModelUEC,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("model"),
    )
    command = models.CharField(max_length=1000, null=True, verbose_name=_("command"))
    name = models.CharField(max_length=1000, null=True, verbose_name=_("name"))

    def __str__(self):
        return self.name


class Sending_Commands(models.Model):
    """
    Define el modelo para almacenar los comandos que se envian a los dispositivos.
    Tabla `realtime_sending_commands`.
    """

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        blank=False,
        null=True,
        verbose_name=_("device"),
    )
    command = models.ForeignKey(
        Commands,
        on_delete=models.CASCADE,
        blank=False,
        null=True,
        verbose_name=_("command"),
    )
    status = models.BooleanField(default=False, verbose_name=_("status"))

    shipping_date = models.DateTimeField(
        null=True, auto_now_add=True, verbose_name=_("shipping date")
    )
    answer_date = models.DateTimeField(
        null=True, blank=True, verbose_name=_("answer date")
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_commands",
        null=True,
    )

    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        verbose_name=_("company"),
        null=True,
    )

    def __str__(self):
        return f"{self.device} --> [ {self.command} ]"


class Command_response(models.Model):
    device = models.ForeignKey(
        "Device",
        on_delete=models.CASCADE,
        blank=False,
        null=True,
        verbose_name=_("device"),
    )
    response = models.CharField(
        max_length=1000, null=True, blank=True, verbose_name=_("response")
    )
    answer_date = models.DateTimeField(
        null=True, blank=True, verbose_name=_("answer date")
    )
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("ip"))
    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        verbose_name=_("company"),
        null=True,
    )


class Geozones(models.Model):
    class Type_event(models.TextChoices):
        Entry = _("Entry"), _("Entry")
        Exit = _("Exit"), _("Exit")
        Entry_and_Exit = _("Entry and Exit"), _("Entry and Exit")

    name = models.CharField(max_length=255, verbose_name=_("name"))
    description = models.TextField(verbose_name=_("description"), blank=True)
    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        verbose_name=_("company"),
        null=True,
    )
    type_event = models.CharField(
        max_length=20,
        verbose_name=_("fuel type"),
        choices=Type_event.choices,
        default=Type_event.Entry,
    )
    radius = models.IntegerField(verbose_name=_("radius"), blank=True, null=True)
    speed = models.IntegerField(verbose_name=_("speed"), null=True, blank=True)
    latitude = models.FloatField(null=True, verbose_name=_("latitude"))
    longitude = models.FloatField(null=True, verbose_name=_("longitude"))
    # polygon = PolygonField(verbose_name=_("geographical polygon"), null=True, blank=True)
    polygon = models.TextField(
        verbose_name=_("geographical polygon"), null=True, blank=True
    )
    color = ColorField(
        blank=True,
        null=True,
        format="hex",
        default="#FF0000",
        verbose_name=_("color de geozona"),
    )
    color_edges = ColorField(
        format="hex",
        default="#FF0000",
        blank=True,
        null=True,
        verbose_name=_("color de borde"),
    )
    alarma = models.BooleanField(verbose_name=_("alarma"), blank=True, default=False)
    notification_by_mail = models.BooleanField(
        verbose_name=_("notification by mail"), blank=True, default=False
    )
    shape_type = models.IntegerField(
        verbose_name=_("shape type"), blank=True, null=True
    )
    last_update = models.DateTimeField(
        verbose_name=_("last update"),
        auto_now=True,
    )
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_geozone",
        null=True,
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_geozone",
        null=True,
    )
    visible = models.BooleanField(default=True, verbose_name=_("Visible"))

    def __str__(self):
        return f"{self.name}"

    # def save_polygon_coordinates(self, polygon):
    #     vertices = polygon.getPath().getArray()
    #     polygon_coordinates = []

    #     for vertex in vertices:
    #         polygon_coordinates.append({"lat": vertex.lat(), "lng": vertex.lng()})

    #     self.geographical_polygon = str(polygon_coordinates)


class Vehcile_geozone(models.Model):
    vehicle = models.ForeignKey(
        "Vehicle", on_delete=models.CASCADE, verbose_name=_("vehicle"), null=True
    )
    geozones = models.ForeignKey(
        "Geozones", on_delete=models.CASCADE, verbose_name=_("geozones"), null=True
    )
    visible = models.BooleanField(default=True, verbose_name=_("Visible"))
    email = models.EmailField(verbose_name=_("email"), blank=True, null=True)
    contact_name = models.CharField(
        max_length=50,
        verbose_name=_("contact name"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.vehicle} --> [ {self.geozones} ]"


class Report_geozone(models.Model):
    geozone = models.ForeignKey(
        "Geozones", on_delete=models.CASCADE, verbose_name=_("geozone"), null=True
    )
    vehicle = models.ForeignKey(
        "Vehicle", on_delete=models.CASCADE, verbose_name=_("vehicle"), null=True
    )
    time_entry = models.DateTimeField(
        verbose_name=_("time entry"),
        auto_now=True,
    )
    time_exit = models.DateTimeField(
        verbose_name=_("time exit"),
        auto_now=True,
    )


class Io_items_report(models.Model):
    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        verbose_name=_("company"),
        null=True,
    )
    info_reports = models.CharField(
        max_length=2000, null=True, verbose_name=_("info_reports")
    )
    info_widgets = models.CharField(
        max_length=2000, null=True, verbose_name=_("info_widgets")
    )
    info_io = models.CharField(max_length=2000, null=True, verbose_name=_("info_io"))


class Types_assets(models.Model):
    asset_name = models.CharField(
        max_length=200, null=True, verbose_name=_("asset_name")
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("last updated"),
        null=True,
    )

    def __str__(self):
        return self.asset_name

    class Meta:
        verbose_name_plural = _("Types assets")


class Brands_assets(models.Model):
    brand = models.CharField(max_length=100, verbose_name=_("Brand"))
    type_asset = models.ForeignKey(
        "realtime.Types_assets",
        on_delete=models.CASCADE,
        verbose_name=_("Types assets"),
        null=True,
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("last updated"),
        null=True,
    )

    def __str__(self):
        return f"{self.brand}"

    class Meta:
        verbose_name = _("Brands asset")
        verbose_name_plural = _("Brands assets")


class Line_assets(models.Model):
    line = models.CharField(max_length=100, verbose_name=_("Line"))
    brand_asset = models.ForeignKey(
        "realtime.Brands_assets",
        on_delete=models.CASCADE,
        verbose_name=_("brands assets"),
        null=True,
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("last updated"),
        null=True,
    )

    def __str__(self):
        return f"{self.line}"


class Type_brand_line(models.Model):
    type_asset = models.ForeignKey(
        "realtime.Types_assets",
        on_delete=models.CASCADE,
        verbose_name=_("types assets"),
        null=True,
    )
    brand_asset = models.ForeignKey(
        "realtime.Brands_assets",
        on_delete=models.CASCADE,
        verbose_name=_("brands assets"),
        null=True,
    )
    line_asset = models.ForeignKey(
        "realtime.Line_assets",
        on_delete=models.CASCADE,
        verbose_name=_("line assets"),
        null=True,
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("last updated"),
        null=True,
    )
