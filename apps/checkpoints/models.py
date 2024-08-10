""" Modelos asociados al módulo puntos de control.

Este módulo crea los modelos para los puntos de control, las rutas, el control de fatiga y los
datos para análisis de los conductores.

Para una mayor referencia sobre la creación de modelos en Django, consulte
https://docs.djangoproject.com/en/4.1/topics/db/models/
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Driver(models.Model):
    """
    Modelo de la tabla driver. Almacena la información asociada a cada conductor
    de la empresa cliente.
    """

    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        verbose_name=_("company"),
        default=1,
    )
    last_update = models.DateTimeField(
        verbose_name=_("last update"),
        auto_now=True,
    )
    personal_identification_number = models.PositiveBigIntegerField(
        verbose_name=_("personal ID"),
        null=False,
        blank=False,
    )
    first_name = models.CharField(
        max_length=30,
        verbose_name=_("first name"),
        default="",
    )
    last_name = models.CharField(
        max_length=30,
        verbose_name=_("last name"),
        default="",
    )
    address = models.CharField(
        max_length=30,
        verbose_name=_("address"),
        default="",
        blank=True,
    )
    phone_number = models.PositiveBigIntegerField(
        verbose_name=_("movil number"),
        default="",
    )
    password = models.CharField(
        max_length=10,
        verbose_name=_("password"),
        default="",
        null=True,
    )
    date_joined = models.DateField(verbose_name=_("date joined"))
    is_active = models.BooleanField(default=False, verbose_name=_("Active"))
    visible = models.BooleanField(default=True, verbose_name=_("visible"))
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_driver",
        null=True,
    )

    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_driver",
        null=True,
    )

    def __str__(self):
        return f"{self.first_name}   {self.last_name}"


class DriverAnalytic(models.Model):
    """
    Modelo de la tabla driver_analytic. Almacena la información asociada a la asignación
    y desasignación de conductores a vehiculos.
    """

    vehicle = models.ForeignKey(
        "realtime.Vehicle",
        on_delete=models.CASCADE,
        verbose_name=_("vehicle"),
        null=True,
    )
    driver = models.ForeignKey(
        "Driver", on_delete=models.CASCADE, verbose_name=_("driver"), null=True
    )
    date_joined = models.DateTimeField(
        verbose_name=_("date joined"),
        null=True,
    )
    date_leaving = models.DateTimeField(
        verbose_name=_("date leaving"),
        blank=True,
        null=True,
    )
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_driver_analytic",
        null=True,
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_driver_analytic",
        null=True,
    )
    last_update = models.DateTimeField(
        verbose_name=_("last update"),
        auto_now=True,
    )

    def __str__(self):
        return f"{self.vehicle} --> Driver: {self.driver}"


class ItemScore(models.Model):
    """
    Modelo de la tabla item_score. Almacena los items predefinidos sobre los cuales
    se califica a los conductores.
    """

    item = models.CharField(
        verbose_name=_("item"),
        max_length=50,
    )
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_items",
        null=True,
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_items",
        null=True,
    )
    last_updated = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("last updated"),
        null=True,
    )

    def __str__(self):
        return f"{self.item}"


class CompanyScoreSetup(models.Model):
    """
    Modelo de la tabla company_score_setup Almacena el puntaje que cada empresa
    establece para calificar a sus conductores.
    """

    company = models.ForeignKey(
        "whitelabel.Company",
        on_delete=models.CASCADE,
        verbose_name=_("company"),
        null=True,
    )
    min_score = models.FloatField(
        verbose_name=_("minimum score"),
        blank=True,
        default=0,
    )
    max_score = models.FloatField(
        verbose_name=_("maximum score"),
        blank=True,
        default=0,
    )
    cotoff_date = models.IntegerField(
        verbose_name=_("cutoff date"),
        default=1,
        choices=[(day, day) for day in range(1, 31)],
    )
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_Companyscoresetup",
        null=True,
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_companyscoresetup",
        null=True,
    )
    last_update = models.DateTimeField(
        verbose_name=_("last update"),
        auto_now=True,
    )

    def __str__(self):
        return f" {self.company} --> Score: [ {self.min_score} , {self.max_score},{self.cotoff_date}]"


class ItemScoreSetup(models.Model):
    """
    Modelo de la tabla item_score_setup. Almacena el porcentaje que representa en la nota total
    cada item a evaluar.
    """

    item = models.ForeignKey(
        "ItemScore",
        on_delete=models.CASCADE,
        verbose_name=_("item"),
        default=1,
    )
    company_score = models.ForeignKey(
        "CompanyScoreSetup",
        on_delete=models.CASCADE,
        verbose_name=_("company score"),
        null=True,
    )
    points_item_score = models.FloatField(
        verbose_name=_("points score item"),
        blank=True,
        default=0,
    )
    maximum_infractions = models.IntegerField(
        verbose_name=_("maximum infractions"),
        blank=True,
        default=0,
    )
    subtract_points = models.FloatField(
        verbose_name=_("subtract points"),
        blank=True,
        default=0,
    )
    modified_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("modified by"),
        related_name="modified_itemsscoresetup",
        null=True,
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        verbose_name=_("created by"),
        related_name="created_itemsscoresetup",
        null=True,
    )
    last_update = models.DateTimeField(
        verbose_name=_("last update"),
        auto_now=True,
    )

    def __str__(self):
        return f" {self.company_score}---{self.item} --> Percentage:[ {self.points_item_score}] -- "


class FatigueControl(models.Model):

    """
    Modelo de el cual realiza el calculo de la calificacion del conductor con el modelo DriverAnalytic
    de acuerdo a los parametros que se hayan establecido en el modelo ItemScoreSetup y se valida
    de acuerdo a la información que envie el divice al modelo Avldata
    """

    driver = models.ForeignKey(
        "DriverAnalytic", on_delete=models.CASCADE, verbose_name=_("Driver"), null=True
    )
    items_score = models.ForeignKey(
        "ItemScoreSetup",
        on_delete=models.CASCADE,
        verbose_name=_("Items_score"),
        null=True,
    )
    avl_data = models.ForeignKey(
        "realtime.AVLData",
        on_delete=models.CASCADE,
        verbose_name=_("AVLData"),
        null=True,
    )
    vehicle = models.ForeignKey(
        "realtime.Vehicle",
        on_delete=models.CASCADE,
        verbose_name=_("Vehicle"),
        default=None,
    )

    def __str__(self):
        return f" {self.driver} --> {self.items_score} --> {self.avl_data}"


class Report(models.Model):
    # No necesitas definir permisos en la clase Meta para los permisos básicos
    class Meta:
        verbose_name_plural = "reports"
