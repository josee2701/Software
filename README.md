# GPS Mobile

Código del servicio front-end de la aplicación.

## Instrucciones de ejecución

> El archivo Dockerfile se encuentra en pruebas, por favor no intente ejecutar el proyecto creando una imagen de Docker a partir de este archivo, ya que arroja errores.

- Instale el driver de [Microsoft SQL Server ODBC](https://docs.microsoft.com/en-us/sql/connect/odbc/microsoft-odbc-driver-for-sql-server) para la Windows o Linux.
- Cree un entorno virtual de Python e instale las librerías de _requirements.txt_.

  ```python
  python manage.py makemigrations
  python manage.py migrate
  ```

  > **NOTA:** La migración por defecto se realiza directamente a una base de datos de local tipo SQLite. Si desea migrar o trabajar con la base de datos de prueba de SQL Server, ejecute el siguiente comando:

  ```python
  python manage.py migrate --database=server
  ```

## Características

### **Política de código limpio**

- Se siguen las convenciones estilístas del estandar para Python [PEP8](https://peps.python.org/pep-0008/)
- `autopep8` y `black` con líneas de código hasta 99 caracteres
- Nombres de variables unicamente en inglés, usando la convención _snake_case_
- Comentarios de modulo, clases y funciones en español. Apoyarse con las librerías `Mintlify` y `Spell Right`
- Implemente las etiquetas de traducción en los textos visibles para el usuario. Ver la sección de [Escribir código traducible](#escribir-código-traducible)
- Documentación de la aplicación generada con la librería [Sphinx](https://www.sphinx-doc.org/en/master/)

### **Escribir código traducible**

La opción de multilenguas, internacionalización (i18n) y localización (i10n) usa la librería estándar de Django `gettext`. Django facilita la traducción de texto, y el cambio de formato de fecha/moneda de acuerdo a las zonas horarias configuradas. Esto es posible solo si el código escrito en Python, HTML (templates) y Javascript incorpora las etiquetas de traducción para cada porción de texto visible para el usuario.

- Para mayor claridad conceptual, por favor lea cuidadosamente estos apartados de la documentación de Django:
  - [Internationalization and localization](https://docs.djangoproject.com/en/4.1/topics/i18n/)
  - [Translation](https://docs.djangoproject.com/en/4.1/topics/i18n/translation/)
- Para el proyecto tenga en cuenta lo siguiente:
  - Los textos se escriben unicamente en inglés. Use el traductor en línea [DeepL](https://www.deepl.com/es/translator)
  - Instale `gettext` en [Linux](./utils/gettext.sh) o [Windows](https://docs.djangoproject.com/en/3.2/topics/i18n/translation/#gettext-on-windows).
  - Usamos la librería [django-rosetta](https://django-rosetta.readthedocs.io/), interfaz para hacer control de las traducciones desde el Admin (en pruebas)
- Para entender como hacer control y soporte a las traducciones en el proyecto, tenga en cuenta el siguiente tutorial:
  - [Supporting Multiple Languages in Django](https://testdriven.io/blog/multiple-languages-in-django/)

#### **Uso en el código de Django (Python)**

De acuerdo a cada necesidad, Django implementa diferentes funciones para traducir textos:

- `gettext()`: función de uso estándar. Prestar atención al uso de [marcadores de posición](https://docs.djangoproject.com/en/4.1/topics/i18n/translation/#standard-translation) en situaciones de fechas.
- `gettext_lazy()`: usar en las definiciones de modelos (`verbose name`, `help_text`) y formularios (`label`, `placeholder`). Ver [ejemplo](https://docs.djangoproject.com/en/4.1/topics/i18n/translation/#lazy-translation)
- `ngettext()`: usar en situaciones donde la pluralización de una frase sea compleja y sea necesario ofrecer a Django más de una opción. Ver [ejemplo](https://docs.djangoproject.com/en/4.1/topics/i18n/translation/#pluralization)
- `pgettext()`: usar cuando una palabra tiene más de un significado y es necesario ofrecer a Django el contexto de la palabra. Ver [ejemplo](https://docs.djangoproject.com/en/4.1/topics/i18n/translation/#contextual-markers)
- Dar formato a fechas y usos horarios: [Format localization](https://docs.djangoproject.com/en/4.1/topics/i18n/formatting/)

> NOTA: Importe las funciones `gettext()` y `gettext_lazy()` siguiendo la convección `_()`. Por ejemplo:
>
> ```python
> from django.utils.translation import gettext as _
> output = _('Hi, there.')
> ```

#### **Uso en el código de HTML (templates)**

- Siempre implemente la etiqueta `{% load i18n %}` al inicio del archivo
- Siempre use la etiqueta `{% trans %}` en cada texto visible. Ver [ejemplo](https://docs.djangoproject.com/en/4.1/topics/i18n/translation/#translate-template-tag)
- Siempre use la etiqueta `{% blocktrans %}` para traducir variables. Ver [ejemplo](https://docs.djangoproject.com/en/4.1/topics/i18n/translation/#blocktranslate-template-tag)

Para usos más concretos donde requiera especificar el idioma o aplicar filtros, revise la documentación de las funciones `get_available_languages` o `get_current_language`, [aquí](https://docs.djangoproject.com/en/4.1/topics/i18n/translation/#switching-language-in-templates).

#### **Uso en el código de JavaScript**

- Leer la [documentación](https://docs.djangoproject.com/en/4.1/topics/i18n/translation/#internationalization-in-javascript-code)

#### **Compilación de la traducción**

El proyecto actualiza las traducciones en la carpeta `locale` del directorio raíz ejecutando los siguientes comandos. Cada idioma/dialecto genera un paquete de los mensajes visibles para el usuario.

- `django-admin makemessages --all`: crea los archivos `.po` de cada idioma. Se deben escribir las traducciones para cada porción de texto (mensajes).
- `django-admin compilemessages`: crea los archivos `.mo` que guarda los mensajes compilados.

Para más opciones en cada comando, consulte el apartado de [Localization: how to create language files](https://docs.djangoproject.com/en/4.1/topics/i18n/translation/#localization-how-to-create-language-files).

### **Estructura de directorios**

El proyecto se codifica mediante la siguiente estructura de directorios:

```plaintext
.
├── apps
│   ├── api
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── __pycache__
│   │   │   ├── admin.cpython-312.pyc
│   │   │   ├── apps.cpython-312.pyc
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── models.cpython-312.pyc
│   │   │   └── urls.cpython-312.pyc
│   │   ├── serializers
│   │   │   ├── authentication.py
│   │   │   ├── checkpoint.py
│   │   │   ├── __pycache__
│   │   │   │   └── authentication.cpython-312.pyc
│   │   │   └── realtime_tracking.py
│   │   ├── signals.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views
│   │       ├── authentication.py
│   │       ├── checkpoint.py
│   │       ├── __pycache__
│   │       │   └── authentication.cpython-312.pyc
│   │       └── realtime_tracking.py
│   ├── authentication
│   │   ├── admin.py
│   │   ├── apis.py
│   │   ├── apps.py
│   │   ├── fixtures
│   │   │   └── authentication.json
│   │   ├── forms.py
│   │   ├── __init__.py
│   │   ├── middleware.py
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   ├── __init__.py
│   │   │   └── __pycache__
│   │   │       ├── 0001_initial.cpython-310.pyc
│   │   │       ├── 0001_initial.cpython-312.pyc
│   │   │       ├── 0002_initial.cpython-310.pyc
│   │   │       ├── 0002_initial.cpython-312.pyc
│   │   │       ├── 0003_alter_user_monitor_alter_user_process_type.cpython-310.pyc
│   │   │       ├── 0003_alter_user_process_type.cpython-310.pyc
│   │   │       ├── 0003_alter_user_process_type.cpython-312.pyc
│   │   │       ├── 0004_remove_user_monitor.cpython-310.pyc
│   │   │       ├── 0004_remove_user_monitor.cpython-312.pyc
│   │   │       ├── 0005_crear_rol.cpython-310.pyc
│   │   │       ├── 0005_user_monitor.cpython-310.pyc
│   │   │       ├── 0005_user_rol.cpython-310.pyc
│   │   │       ├── 0005_user_rol.cpython-312.pyc
│   │   │       ├── 0006_alter_user_rol.cpython-310.pyc
│   │   │       ├── 0006_remove_user_monitor.cpython-310.pyc
│   │   │       ├── __init__.cpython-310.pyc
│   │   │       └── __init__.cpython-312.pyc
│   │   ├── models.py
│   │   ├── __pycache__
│   │   │   ├── admin.cpython-312.pyc
│   │   │   ├── apis.cpython-312.pyc
│   │   │   ├── apps.cpython-312.pyc
│   │   │   ├── forms.cpython-312.pyc
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── middleware.cpython-312.pyc
│   │   │   ├── models.cpython-312.pyc
│   │   │   ├── signals.cpython-312.pyc
│   │   │   ├── sql.cpython-312.pyc
│   │   │   ├── translation.cpython-312.pyc
│   │   │   ├── urls.cpython-312.pyc
│   │   │   └── views.cpython-312.pyc
│   │   ├── signals.py
│   │   ├── sql.py
│   │   ├── tests.py
│   │   ├── translation.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── checkpoints
│   │   ├── admin.py
│   │   ├── api.py
│   │   ├── apps.py
│   │   ├── fixtures
│   │   │   ├── itmes.json
│   │   │   └── Results.json
│   │   ├── forms.py
│   │   ├── __init__.py
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   ├── __init__.py
│   │   │   └── __pycache__
│   │   │       ├── 0001_initial.cpython-310.pyc
│   │   │       ├── 0001_initial.cpython-312.pyc
│   │   │       ├── 0002_initial.cpython-310.pyc
│   │   │       ├── 0002_initial.cpython-312.pyc
│   │   │       ├── 0003_initial.cpython-310.pyc
│   │   │       ├── 0003_initial.cpython-312.pyc
│   │   │       ├── 0004_alter_driver_personal_identification_number.cpython-310.pyc
│   │   │       ├── 0004_alter_driver_personal_identification_number.cpython-312.pyc
│   │   │       ├── 0005_alter_driveranalytic_date_joined_and_more.cpython-310.pyc
│   │   │       ├── 0005_alter_driveranalytic_date_joined_and_more.cpython-312.pyc
│   │   │       ├── 0006_advanced_analytical.cpython-310.pyc
│   │   │       ├── 0006_advanced_analytical.cpython-312.pyc
│   │   │       ├── 0007_advanced_analytical_is_report_and_more.cpython-310.pyc
│   │   │       ├── 0007_advanced_analytical_is_report_and_more.cpython-312.pyc
│   │   │       ├── 0007_prueba.cpython-310.pyc
│   │   │       ├── 0008_alter_advanced_analytical_id_workspace.cpython-310.pyc
│   │   │       ├── 0008_alter_advanced_analytical_id_workspace.cpython-312.pyc
│   │   │       ├── 0008_remove_prueba_name_prueba_nombre.cpython-310.pyc
│   │   │       ├── __init__.cpython-310.pyc
│   │   │       └── __init__.cpython-312.pyc
│   │   ├── models.py
│   │   ├── postgres.py
│   │   ├── __pycache__
│   │   │   ├── admin.cpython-312.pyc
│   │   │   ├── api.cpython-312.pyc
│   │   │   ├── apps.cpython-312.pyc
│   │   │   ├── forms.cpython-312.pyc
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── models.cpython-312.pyc
│   │   │   ├── postgres.cpython-312.pyc
│   │   │   ├── signals.cpython-312.pyc
│   │   │   ├── sql.cpython-312.pyc
│   │   │   ├── urls.cpython-312.pyc
│   │   │   └── views.cpython-312.pyc
│   │   ├── serializer.py
│   │   ├── sql.py
│   │   ├── templatetags
│   │   │   ├── dict_filters.py
│   │   │   ├── __init__.py
│   │   │   └── __pycache__
│   │   │       ├── dict_filters.cpython-312.pyc
│   │   │       └── __init__.cpython-312.pyc
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── events
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── fixtures
│   │   │   └── events.json
│   │   ├── forms.py
│   │   ├── __init__.py
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   ├── __init__.py
│   │   │   └── __pycache__
│   │   │       ├── 0001_initial.cpython-310.pyc
│   │   │       ├── 0001_initial.cpython-312.pyc
│   │   │       ├── 0002_event_modified_by_event_visible.cpython-312.pyc
│   │   │       ├── 0002_initial.cpython-310.pyc
│   │   │       ├── 0002_initial.cpython-312.pyc
│   │   │       ├── 0003_alter_eventfeature_alias_and_more.cpython-312.pyc
│   │   │       ├── 0003_alter_eventfeature_type_alarm_sound.cpython-310.pyc
│   │   │       ├── 0003_alter_eventfeature_type_alarm_sound.cpython-312.pyc
│   │   │       ├── 0004_alter_eventfeature_alias_and_more.cpython-312.pyc
│   │   │       ├── __init__.cpython-310.pyc
│   │   │       └── __init__.cpython-312.pyc
│   │   ├── models.py
│   │   ├── __pycache__
│   │   │   ├── admin.cpython-312.pyc
│   │   │   ├── apis.cpython-312.pyc
│   │   │   ├── apps.cpython-312.pyc
│   │   │   ├── forms.cpython-312.pyc
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── models.cpython-312.pyc
│   │   │   ├── sql.cpython-312.pyc
│   │   │   ├── urls.cpython-312.pyc
│   │   │   └── views.cpython-312.pyc
│   │   ├── sql.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── log
│   │   ├── migrations
│   │   │   └── __pycache__
│   │   │       ├── 0001_initial.cpython-312.pyc
│   │   │       ├── 0002_alter_auditlog_after_alter_auditlog_before.cpython-312.pyc
│   │   │       └── __init__.cpython-312.pyc
│   │   └── __pycache__
│   │       ├── admin.cpython-312.pyc
│   │       ├── apps.cpython-312.pyc
│   │       ├── __init__.cpython-312.pyc
│   │       ├── mixins.cpython-312.pyc
│   │       ├── models.cpython-312.pyc
│   │       └── utils.cpython-312.pyc
│   ├── media
│   │   ├── backgrounds
│   │   │   ├── login-1.png
│   │   │   ├── logo.png
│   │   │   └── sidebar-1.jpg
│   │   └── Perfil
│   │       └── IMG_20230613_231200.jpg
│   ├── powerbi
│   │   ├── migrations
│   │   │   └── __pycache__
│   │   │       └── __init__.cpython-312.pyc
│   │   └── __pycache__
│   │       ├── admin.cpython-312.pyc
│   │       ├── apps.cpython-312.pyc
│   │       ├── azure_utils.cpython-312.pyc
│   │       ├── embed_service.cpython-312.pyc
│   │       ├── __init__.cpython-312.pyc
│   │       ├── models.cpython-312.pyc
│   │       ├── urls.cpython-312.pyc
│   │       └── views.cpython-312.pyc
│   ├── realtime
│   │   ├── admin.py
│   │   ├── apis.py
│   │   ├── apps.py
│   │   ├── direccion.py
│   │   ├── fixtures
│   │   │   ├── realtime.json
│   │   │   └── uec_fixtures.json
│   │   ├── forms.py
│   │   ├── __init__.py
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   ├── __init__.py
│   │   │   └── __pycache__
│   │   │       ├── 0001_initial.cpython-310.pyc
│   │   │       ├── 0001_initial.cpython-312.pyc
│   │   │       ├── 0002_initial.cpython-310.pyc
│   │   │       ├── 0002_initial.cpython-312.pyc
│   │   │       ├── 0003_alter_device_serial_number.cpython-310.pyc
│   │   │       ├── 0003_alter_device_serial_number.cpython-312.pyc
│   │   │       ├── 0004_alter_device_imei_alter_vehicle_model.cpython-310.pyc
│   │   │       ├── 0004_alter_device_imei_alter_vehicle_model.cpython-312.pyc
│   │   │       ├── 0005_brands_assets_line_assets_types_assets_and_more.cpython-310.pyc
│   │   │       ├── 0005_brands_assets_line_assets_types_assets_and_more.cpython-312.pyc
│   │   │       ├── __init__.cpython-310.pyc
│   │   │       └── __init__.cpython-312.pyc
│   │   ├── models.py
│   │   ├── __pycache__
│   │   │   ├── admin.cpython-312.pyc
│   │   │   ├── apis.cpython-312.pyc
│   │   │   ├── apps.cpython-312.pyc
│   │   │   ├── direccion.cpython-312.pyc
│   │   │   ├── forms.cpython-312.pyc
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── models.cpython-312.pyc
│   │   │   ├── realtrack.cpython-312.pyc
│   │   │   ├── serializer.cpython-312.pyc
│   │   │   ├── sql.cpython-312.pyc
│   │   │   ├── urls.cpython-312.pyc
│   │   │   └── views.cpython-312.pyc
│   │   ├── realtrack.py
│   │   ├── serializer.py
│   │   ├── sql.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── socketmap
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── consumers.py
│   │   ├── __init__.py
│   │   ├── migrations
│   │   │   ├── __init__.py
│   │   │   └── __pycache__
│   │   │       ├── 0001_initial.cpython-310.pyc
│   │   │       ├── 0001_initial.cpython-312.pyc
│   │   │       ├── __init__.cpython-310.pyc
│   │   │       └── __init__.cpython-312.pyc
│   │   ├── models.py
│   │   ├── __pycache__
│   │   │   ├── admin.cpython-312.pyc
│   │   │   ├── apps.cpython-312.pyc
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── models.cpython-312.pyc
│   │   │   ├── urls.cpython-312.pyc
│   │   │   └── views.cpython-312.pyc
│   │   ├── routing.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── static
│   │   ├── assets
│   │   │   ├── css
│   │   │   │   ├── bug_bd_postgresql.css
│   │   │   │   ├── estilos_templates.css
│   │   │   │   ├── geozona.css
│   │   │   │   ├── material-dashboard.css
│   │   │   │   ├── material-dashboard.css.map
│   │   │   │   ├── material-dashboard.min.css
│   │   │   │   ├── navbar_options.css
│   │   │   │   ├── nucleo-icons.css
│   │   │   │   ├── nucleo-svg.css
│   │   │   │   ├── report
│   │   │   │   │   └── report_today.css
│   │   │   │   └── report_configuration.css
│   │   │   ├── fonts
│   │   │   │   ├── nucleo.eot
│   │   │   │   ├── nucleo-icons.eot
│   │   │   │   ├── nucleo-icons.svg
│   │   │   │   ├── nucleo-icons.ttf
│   │   │   │   ├── nucleo-icons.woff
│   │   │   │   ├── nucleo-icons.woff2
│   │   │   │   ├── nucleo.ttf
│   │   │   │   ├── nucleo.woff
│   │   │   │   └── nucleo.woff2
│   │   │   ├── img
│   │   │   │   ├── apple-icon.png
│   │   │   │   ├── bg-pricing.jpg
│   │   │   │   ├── bg-smart-home-1.jpg
│   │   │   │   ├── bg-smart-home-2.jpg
│   │   │   │   ├── bruce-mars.jpg
│   │   │   │   ├── down-arrow-dark.svg
│   │   │   │   ├── down-arrow.svg
│   │   │   │   ├── down-arrow-white.svg
│   │   │   │   ├── drake.jpg
│   │   │   │   ├── favicon.png
│   │   │   │   ├── home-decor-1.jpg
│   │   │   │   ├── home-decor-2.jpg
│   │   │   │   ├── home-decor-3.jpg
│   │   │   │   ├── icons
│   │   │   │   │   └── flags
│   │   │   │   │       ├── AU.png
│   │   │   │   │       ├── BR.png
│   │   │   │   │       ├── DE.png
│   │   │   │   │       ├── GB.png
│   │   │   │   │       └── US.png
│   │   │   │   ├── illustrations
│   │   │   │   │   ├── chat.png
│   │   │   │   │   ├── danger-chat-ill.png
│   │   │   │   │   ├── dark-lock-ill.png
│   │   │   │   │   ├── error-404.png
│   │   │   │   │   ├── error-500.png
│   │   │   │   │   ├── illustration-lock.jpg
│   │   │   │   │   ├── illustration-reset.jpg
│   │   │   │   │   ├── illustration-signin.jpg
│   │   │   │   │   ├── illustration-signup.jpg
│   │   │   │   │   ├── illustration-verification.jpg
│   │   │   │   │   ├── lock.png
│   │   │   │   │   ├── pattern-tree.svg
│   │   │   │   │   └── rocket-white.png
│   │   │   │   ├── ivana-square.jpg
│   │   │   │   ├── ivana-squares.jpg
│   │   │   │   ├── ivancik.jpg
│   │   │   │   ├── kal-visuals-square.jpg
│   │   │   │   ├── login-2.jpg
│   │   │   │   ├── logo-ct-dark.png
│   │   │   │   ├── logo-ct.png
│   │   │   │   ├── logos
│   │   │   │   │   ├── gray-logos
│   │   │   │   │   │   ├── logo-coinbase.svg
│   │   │   │   │   │   ├── logo-nasa.svg
│   │   │   │   │   │   ├── logo-netflix.svg
│   │   │   │   │   │   ├── logo-pinterest.svg
│   │   │   │   │   │   ├── logo-spotify.svg
│   │   │   │   │   │   └── logo-vodafone.svg
│   │   │   │   │   ├── mastercard.png
│   │   │   │   │   └── visa.png
│   │   │   │   ├── marie.jpg
│   │   │   │   ├── meeting.jpg
│   │   │   │   ├── office-dark.jpg
│   │   │   │   ├── product-12.jpg
│   │   │   │   ├── products
│   │   │   │   │   ├── product-11.jpg
│   │   │   │   │   ├── product-1-min.jpg
│   │   │   │   │   ├── product-2-min.jpg
│   │   │   │   │   ├── product-3-min.jpg
│   │   │   │   │   ├── product-4-min.jpg
│   │   │   │   │   ├── product-5-min.jpg
│   │   │   │   │   ├── product-6-min.jpg
│   │   │   │   │   ├── product-7-min.jpg
│   │   │   │   │   ├── product-details-1.jpg
│   │   │   │   │   ├── product-details-2.jpg
│   │   │   │   │   ├── product-details-3.jpg
│   │   │   │   │   ├── product-details-4.jpg
│   │   │   │   │   └── product-details-5.jpg
│   │   │   │   ├── shapes
│   │   │   │   │   ├── pattern-lines.svg
│   │   │   │   │   └── waves-white.svg
│   │   │   │   ├── small-logos
│   │   │   │   │   ├── bootstrap.svg
│   │   │   │   │   ├── creative-tim.svg
│   │   │   │   │   ├── devto.svg
│   │   │   │   │   ├── github.svg
│   │   │   │   │   ├── google-webdev.svg
│   │   │   │   │   ├── icon-bulb.svg
│   │   │   │   │   ├── icon-sun-cloud.png
│   │   │   │   │   ├── logo-asana.svg
│   │   │   │   │   ├── logo-atlassian.svg
│   │   │   │   │   ├── logo-invision.svg
│   │   │   │   │   ├── logo-jira.svg
│   │   │   │   │   ├── logo-slack.svg
│   │   │   │   │   ├── logo-spotify.svg
│   │   │   │   │   └── logo-xd.svg
│   │   │   │   ├── team-1.jpg
│   │   │   │   ├── team-2.jpg
│   │   │   │   ├── team-3.jpg
│   │   │   │   ├── team-4.jpg
│   │   │   │   ├── team-5.jpg
│   │   │   │   ├── tesla-model-s.png
│   │   │   │   └── vr-bg.jpg
│   │   │   ├── js
│   │   │   │   ├── configuration_report
│   │   │   │   │   ├── add_items_by_company.js
│   │   │   │   │   └── update_configuration_report.js
│   │   │   │   ├── core
│   │   │   │   │   ├── bootstrap.bundle.min.js
│   │   │   │   │   ├── bootstrap.min.js
│   │   │   │   │   └── popper.min.js
│   │   │   │   ├── dialog.js
│   │   │   │   ├── dynamic-scrollable-content.js
│   │   │   │   ├── material-dashboard.js
│   │   │   │   ├── material-dashboard.js.map
│   │   │   │   ├── material-dashboard.min.js
│   │   │   │   ├── plugins
│   │   │   │   │   ├── bootstrap-notify.js
│   │   │   │   │   ├── Chart.extension.js
│   │   │   │   │   ├── chartjs.min.js
│   │   │   │   │   ├── perfect-scrollbar.min.js
│   │   │   │   │   ├── smooth-scrollbar.min.js
│   │   │   │   │   └── world.js
│   │   │   │   ├── realtime
│   │   │   │   │   ├── device
│   │   │   │   │   │   └── filtro.js
│   │   │   │   │   ├── simcard
│   │   │   │   │   │   └── filtro.js
│   │   │   │   │   └── vehicle
│   │   │   │   │       └── filtro.js
│   │   │   │   ├── report_today
│   │   │   │   │   ├── apis.js
│   │   │   │   │   ├── exportar.js
│   │   │   │   │   ├── lock_page.js
│   │   │   │   │   ├── paginate.js
│   │   │   │   │   └── utc_user.js
│   │   │   │   ├── search.js
│   │   │   │   ├── sending_commands
│   │   │   │   │   └── add_sending_commands.js
│   │   │   │   ├── user
│   │   │   │   │   ├── filtro_process.js
│   │   │   │   │   └── monitor.js
│   │   │   │   └── utc_local.js
│   │   │   ├── scripts
│   │   │   │   ├── dashboard
│   │   │   │   │   ├── dashboard.css
│   │   │   │   │   └── dashboard.js
│   │   │   │   └── geozone
│   │   │   │       ├── geozona_add.js
│   │   │   │       ├── geozona_update.js
│   │   │   │       ├── geozone.css
│   │   │   │       └── geozone.js
│   │   │   └── scss
│   │   │       ├── material-dashboard
│   │   │       │   ├── _alert.scss
│   │   │       │   ├── _avatars.scss
│   │   │       │   ├── _badge.scss
│   │   │       │   ├── bootstrap
│   │   │       │   │   ├── _accordion.scss
│   │   │       │   │   ├── _alert.scss
│   │   │       │   │   ├── _badge.scss
│   │   │       │   │   ├── bootstrap.css
│   │   │       │   │   ├── bootstrap.css.map
│   │   │       │   │   ├── bootstrap-grid.css
│   │   │       │   │   ├── bootstrap-grid.css.map
│   │   │       │   │   ├── bootstrap-grid.scss
│   │   │       │   │   ├── bootstrap-reboot.css
│   │   │       │   │   ├── bootstrap-reboot.css.map
│   │   │       │   │   ├── bootstrap-reboot.scss
│   │   │       │   │   ├── bootstrap.scss
│   │   │       │   │   ├── bootstrap-utilities.css
│   │   │       │   │   ├── bootstrap-utilities.css.map
│   │   │       │   │   ├── bootstrap-utilities.scss
│   │   │       │   │   ├── _breadcrumb.scss
│   │   │       │   │   ├── _button-group.scss
│   │   │       │   │   ├── _buttons.scss
│   │   │       │   │   ├── _card.scss
│   │   │       │   │   ├── _carousel.scss
│   │   │       │   │   ├── _close.scss
│   │   │       │   │   ├── _containers.scss
│   │   │       │   │   ├── _dropdown.scss
│   │   │       │   │   ├── forms
│   │   │       │   │   │   ├── _floating-labels.scss
│   │   │       │   │   │   ├── _form-check.scss
│   │   │       │   │   │   ├── _form-control.scss
│   │   │       │   │   │   ├── _form-range.scss
│   │   │       │   │   │   ├── _form-select.scss
│   │   │       │   │   │   ├── _form-text.scss
│   │   │       │   │   │   ├── _input-group.scss
│   │   │       │   │   │   ├── _labels.scss
│   │   │       │   │   │   └── _validation.scss
│   │   │       │   │   ├── _forms.scss
│   │   │       │   │   ├── _functions.scss
│   │   │       │   │   ├── _grid.scss
│   │   │       │   │   ├── helpers
│   │   │       │   │   │   ├── _clearfix.scss
│   │   │       │   │   │   ├── _color-bg.scss
│   │   │       │   │   │   ├── _colored-links.scss
│   │   │       │   │   │   ├── _position.scss
│   │   │       │   │   │   ├── _ratio.scss
│   │   │       │   │   │   ├── _stacks.scss
│   │   │       │   │   │   ├── _stretched-link.scss
│   │   │       │   │   │   ├── _text-truncation.scss
│   │   │       │   │   │   ├── _visually-hidden.scss
│   │   │       │   │   │   └── _vr.scss
│   │   │       │   │   ├── _helpers.scss
│   │   │       │   │   ├── _images.scss
│   │   │       │   │   ├── _list-group.scss
│   │   │       │   │   ├── _maps.scss
│   │   │       │   │   ├── mixins
│   │   │       │   │   │   ├── _alert.scss
│   │   │       │   │   │   ├── _backdrop.scss
│   │   │       │   │   │   ├── _border-radius.scss
│   │   │       │   │   │   ├── _box-shadow.scss
│   │   │       │   │   │   ├── _breakpoints.scss
│   │   │       │   │   │   ├── _buttons.scss
│   │   │       │   │   │   ├── _caret.scss
│   │   │       │   │   │   ├── _clearfix.scss
│   │   │       │   │   │   ├── _color-scheme.scss
│   │   │       │   │   │   ├── _container.scss
│   │   │       │   │   │   ├── _deprecate.scss
│   │   │       │   │   │   ├── _forms.scss
│   │   │       │   │   │   ├── _gradients.scss
│   │   │       │   │   │   ├── _grid.scss
│   │   │       │   │   │   ├── _image.scss
│   │   │       │   │   │   ├── _list-group.scss
│   │   │       │   │   │   ├── _lists.scss
│   │   │       │   │   │   ├── _pagination.scss
│   │   │       │   │   │   ├── _reset-text.scss
│   │   │       │   │   │   ├── _resize.scss
│   │   │       │   │   │   ├── _table-variants.scss
│   │   │       │   │   │   ├── _text-truncate.scss
│   │   │       │   │   │   ├── _transition.scss
│   │   │       │   │   │   ├── _utilities.scss
│   │   │       │   │   │   └── _visually-hidden.scss
│   │   │       │   │   ├── _mixins.scss
│   │   │       │   │   ├── _modal.scss
│   │   │       │   │   ├── _navbar.scss
│   │   │       │   │   ├── _nav.scss
│   │   │       │   │   ├── _offcanvas.scss
│   │   │       │   │   ├── _pagination.scss
│   │   │       │   │   ├── _placeholders.scss
│   │   │       │   │   ├── _popover.scss
│   │   │       │   │   ├── _progress.scss
│   │   │       │   │   ├── _reboot.scss
│   │   │       │   │   ├── _root.scss
│   │   │       │   │   ├── _spinners.scss
│   │   │       │   │   ├── _tables.scss
│   │   │       │   │   ├── _toasts.scss
│   │   │       │   │   ├── _tooltip.scss
│   │   │       │   │   ├── _transitions.scss
│   │   │       │   │   ├── _type.scss
│   │   │       │   │   ├── utilities
│   │   │       │   │   │   └── _api.scss
│   │   │       │   │   ├── _utilities.scss
│   │   │       │   │   ├── _variables.scss
│   │   │       │   │   └── vendor
│   │   │       │   │       └── _rfs.scss
│   │   │       │   ├── _breadcrumbs.scss
│   │   │       │   ├── _buttons.scss
│   │   │       │   ├── cards
│   │   │       │   │   ├── card-background.scss
│   │   │       │   │   └── card-rotate.scss
│   │   │       │   ├── _cards.scss
│   │   │       │   ├── custom
│   │   │       │   │   ├── _styles.scss
│   │   │       │   │   └── _variables.scss
│   │   │       │   ├── _dark-version.scss
│   │   │       │   ├── _dropdown.scss
│   │   │       │   ├── _dropup.scss
│   │   │       │   ├── _fixed-plugin.scss
│   │   │       │   ├── _footer.scss
│   │   │       │   ├── forms
│   │   │       │   │   ├── _form-check.scss
│   │   │       │   │   ├── _form-select.scss
│   │   │       │   │   ├── _forms.scss
│   │   │       │   │   ├── _form-switch.scss
│   │   │       │   │   ├── _input-group.scss
│   │   │       │   │   ├── _inputs.scss
│   │   │       │   │   └── _labels.scss
│   │   │       │   ├── _forms.scss
│   │   │       │   ├── _gradients.scss
│   │   │       │   ├── _header.scss
│   │   │       │   ├── _icons.scss
│   │   │       │   ├── _info-areas.scss
│   │   │       │   ├── _misc.scss
│   │   │       │   ├── mixins
│   │   │       │   │   ├── _badge.scss
│   │   │       │   │   ├── _buttons.scss
│   │   │       │   │   ├── _colored-shadows.scss
│   │   │       │   │   ├── _hover.scss
│   │   │       │   │   ├── mixins.css
│   │   │       │   │   ├── mixins.css.map
│   │   │       │   │   ├── mixins.scss
│   │   │       │   │   ├── _social-buttons.scss
│   │   │       │   │   └── _vendor.scss
│   │   │       │   ├── _navbar.scss
│   │   │       │   ├── _navbar-vertical.scss
│   │   │       │   ├── _nav.scss
│   │   │       │   ├── _pagination.scss
│   │   │       │   ├── plugins
│   │   │       │   │   └── free
│   │   │       │   │       ├── _flatpickr.scss
│   │   │       │   │       ├── _nouislider.scss
│   │   │       │   │       ├── _perfect-scrollbar.scss
│   │   │       │   │       ├── plugins.scss
│   │   │       │   │       └── _prism.scss
│   │   │       │   ├── _popovers.scss
│   │   │       │   ├── _progress.scss
│   │   │       │   ├── _ripple.scss
│   │   │       │   ├── _rtl.scss
│   │   │       │   ├── _social-buttons.scss
│   │   │       │   ├── _tables.scss
│   │   │       │   ├── theme.scss
│   │   │       │   ├── _tilt.scss
│   │   │       │   ├── _timeline.scss
│   │   │       │   ├── _tooltips.scss
│   │   │       │   ├── _typography.scss
│   │   │       │   ├── _utilities-extend.scss
│   │   │       │   ├── _utilities.scss
│   │   │       │   ├── variables
│   │   │       │   │   ├── _animations.scss
│   │   │       │   │   ├── _avatars.scss
│   │   │       │   │   ├── _badge.scss
│   │   │       │   │   ├── _breadcrumb.scss
│   │   │       │   │   ├── _cards-extend.scss
│   │   │       │   │   ├── _cards.scss
│   │   │       │   │   ├── _choices.scss
│   │   │       │   │   ├── _dark-version.scss
│   │   │       │   │   ├── _dropdowns.scss
│   │   │       │   │   ├── _fixed-plugin.scss
│   │   │       │   │   ├── _form-switch.scss
│   │   │       │   │   ├── _full-calendar.scss
│   │   │       │   │   ├── _header.scss
│   │   │       │   │   ├── _info-areas.scss
│   │   │       │   │   ├── _misc-extend.scss
│   │   │       │   │   ├── _misc.scss
│   │   │       │   │   ├── _navbar.scss
│   │   │       │   │   ├── _navbar-vertical.scss
│   │   │       │   │   ├── _pagination.scss
│   │   │       │   │   ├── _ripple.scss
│   │   │       │   │   ├── _rtl.scss
│   │   │       │   │   ├── _social-buttons.scss
│   │   │       │   │   ├── _table.scss
│   │   │       │   │   ├── _timeline.scss
│   │   │       │   │   ├── _utilities-extend.scss
│   │   │       │   │   ├── _utilities.scss
│   │   │       │   │   └── _virtual-reality.scss
│   │   │       │   └── _variables.scss
│   │   │       ├── material-dashboard.css
│   │   │       ├── material-dashboard.css.map
│   │   │       └── material-dashboard.scss
│   │   ├── composer.json
│   │   ├── gulpfile.js
│   │   └── package.json
│   ├── templates
│   │   ├── authentication
│   │   │   ├── base.html
│   │   │   ├── dashboard.html
│   │   │   ├── dashboard_test.html
│   │   │   ├── index.html
│   │   │   ├── login.html
│   │   │   ├── logout.html
│   │   │   ├── password_change_done.html
│   │   │   ├── password_change.html
│   │   │   ├── password_reset_complete.html
│   │   │   ├── password_reset_confirm.html
│   │   │   ├── password_reset_done.html
│   │   │   ├── password_reset_form.html
│   │   │   ├── permissionscompany_confirm_delete.html
│   │   │   ├── permissionscompany_update.html
│   │   │   ├── signup.html
│   │   │   └── users
│   │   │       ├── add_user.html
│   │   │       ├── delete_user.html
│   │   │       ├── password_user.html
│   │   │       ├── profile_user.html
│   │   │       ├── update_permissions.html
│   │   │       ├── update_user.html
│   │   │       ├── user_main.html
│   │   │       └── user_permissions.html
│   │   ├── Bugs
│   │   │   └── No_conection_bd.html
│   │   ├── checkpoints
│   │   │   ├── driver
│   │   │   │   ├── add_driver.html
│   │   │   │   ├── delete_driver.html
│   │   │   │   ├── list_drivers_company.html
│   │   │   │   ├── main_drivers.html
│   │   │   │   └── update_driver.html
│   │   │   ├── driver_analytic
│   │   │   │   ├── assign_driver.html
│   │   │   │   ├── button_view.html
│   │   │   │   ├── update_assign.html
│   │   │   │   └── update_vehicle_assign.html
│   │   │   ├── reportes
│   │   │   │   ├── report_driver.html
│   │   │   │   ├── report_today_copy.html
│   │   │   │   └── report_today.html
│   │   │   └── score_configuration
│   │   │       ├── list_score_configuration_companies.html
│   │   │       ├── main_score_configuration.html
│   │   │       └── update_score_configuration.html
│   │   ├── events
│   │   │   ├── base_events.html
│   │   │   ├── predefined_events
│   │   │   │   ├── add_events.html
│   │   │   │   ├── delete_events.html
│   │   │   │   ├── main_events.html
│   │   │   │   └── update_events.html
│   │   │   └── user_events
│   │   │       ├── add_user_events.html
│   │   │       ├── delete_user_events.html
│   │   │       ├── main_user_events.html
│   │   │       └── update_user_events.html
│   │   ├── layouts
│   │   │   ├── basedashboard.html
│   │   │   ├── base.html
│   │   │   ├── estilos.html
│   │   │   ├── loader.html
│   │   │   ├── navbardashboard.html
│   │   │   └── navbar.html
│   │   ├── realtime
│   │   │   ├── custom_report
│   │   │   │   ├── add_configuration_report.html
│   │   │   │   └── update_configuration_report.html
│   │   │   ├── dataplan
│   │   │   │   ├── add_dataplan.html
│   │   │   │   ├── delete_dataplan.html
│   │   │   │   ├── main_dataplan.html
│   │   │   │   └── update_dataplan.html
│   │   │   ├── devices
│   │   │   │   ├── add_device.html
│   │   │   │   ├── delete_devices.html
│   │   │   │   ├── main_devices.html
│   │   │   │   └── update_device.html
│   │   │   ├── geozones
│   │   │   │   ├── add_geozone.html
│   │   │   │   ├── API_geozone.html
│   │   │   │   ├── geozone_main.html
│   │   │   │   ├── list_geozone_created.html
│   │   │   │   ├── main_geozone.html
│   │   │   │   └── update_geozone.html
│   │   │   ├── group_vehicles
│   │   │   │   ├── add_group_vehicles.html
│   │   │   │   ├── delete_group_vehicles.html
│   │   │   │   ├── list_group_vehicles_created.html
│   │   │   │   ├── main_group_vehicles.html
│   │   │   │   └── update_group_vehicles.html
│   │   │   ├── response_commands
│   │   │   │   └── main_response_commands.html
│   │   │   ├── sending_commands
│   │   │   │   ├── add_sending_commands.html
│   │   │   │   └── main_sending_commands.html
│   │   │   ├── simcards
│   │   │   │   ├── add_simcard.html
│   │   │   │   ├── delete_simcard.html
│   │   │   │   ├── main_simcard.html
│   │   │   │   └── update_simcard.html
│   │   │   └── vehicles
│   │   │       ├── add_vehicle.html
│   │   │       ├── delete_vehicle.html
│   │   │       ├── list_vehicles_created.html
│   │   │       ├── main_vehicles.html
│   │   │       └── update_vehicle.html
│   │   └── whitelabel
│   │       ├── companies
│   │       │   ├── add_company.html
│   │       │   ├── company_delete.html
│   │       │   ├── company_main.html
│   │       │   ├── company_update.html
│   │       │   ├── company_update_logo.html
│   │       │   └── keymap.html
│   │       ├── module
│   │       │   ├── delete_module.html
│   │       │   ├── list_create_module.html
│   │       │   ├── main_module.html
│   │       │   └── update_module.html
│   │       ├── process
│   │       │   ├── delete_process.html
│   │       │   ├── main_process.html
│   │       │   └── update_process.html
│   │       ├── theme
│   │       │   └── theme.html
│   │       └── tickets
│   │           ├── add_ticket.html
│   │           ├── closed_tickets.html
│   │           ├── comment_ticket.html
│   │           ├── list_tickets.html
│   │           ├── main_ticket.html
│   │           └── view_ticket.html
│   └── whitelabel
│       ├── admin.py
│       ├── apps.py
│       ├── fixtures
│       │   └── whitelabel_data.json
│       ├── forms.py
│       ├── __init__.py
│       ├── migrations
│       │   ├── 0001_initial.py
│       │   ├── __init__.py
│       │   └── __pycache__
│       │       ├── 0001_initial.cpython-310.pyc
│       │       ├── 0001_initial.cpython-312.pyc
│       │       ├── 0002_alter_attachment_file.cpython-310.pyc
│       │       ├── 0002_alter_attachment_file.cpython-312.pyc
│       │       ├── 0002_alter_module_price.cpython-312.pyc
│       │       ├── 0003_alter_attachment_file_alter_theme_lock_screen_image_and_more.cpython-312.pyc
│       │       ├── 0003_alter_theme_lock_screen_image_and_more.cpython-310.pyc
│       │       ├── 0003_alter_theme_lock_screen_image_and_more.cpython-312.pyc
│       │       ├── 0004_alter_ticket_priority.cpython-310.pyc
│       │       ├── 0004_alter_ticket_priority.cpython-312.pyc
│       │       ├── 0005_alter_attachment_file.cpython-310.pyc
│       │       ├── 0005_alter_attachment_file.cpython-312.pyc
│       │       ├── __init__.cpython-310.pyc
│       │       └── __init__.cpython-312.pyc
│       ├── models.py
│       ├── __pycache__
│       │   ├── admin.cpython-312.pyc
│       │   ├── apis.cpython-312.pyc
│       │   ├── apps.cpython-312.pyc
│       │   ├── forms.cpython-312.pyc
│       │   ├── __init__.cpython-312.pyc
│       │   ├── models.cpython-312.pyc
│       │   ├── serializer.cpython-312.pyc
│       │   ├── sql.cpython-312.pyc
│       │   ├── urls.cpython-312.pyc
│       │   └── views.cpython-312.pyc
│       ├── serializer.py
│       ├── sql.py
│       ├── tests.py
│       ├── urls.py
│       └── views.py
├── arbol_proyecto.txt
├── azure-commands
│   └── azure-deploy.sh
├── config
│   ├── asgi.py
│   ├── azureblob.py
│   ├── __init__.py
│   ├── pagination.py
│   ├── __pycache__
│   │   ├── azureblob.cpython-312.pyc
│   │   ├── filtro.cpython-312.pyc
│   │   ├── __init__.cpython-312.pyc
│   │   ├── pagination.cpython-312.pyc
│   │   ├── settings.cpython-312.pyc
│   │   └── urls.cpython-312.pyc
│   ├── settings.py
│   ├── urls.py
│   ├── verificar_path.py
│   └── wsgi.py
├── docker-compose.yml
├── Dockerfile
├── docs
│   ├── build
│   │   ├── doctrees
│   │   │   ├── environment.pickle
│   │   │   └── index.doctree
│   │   └── html
│   │       ├── genindex.html
│   │       ├── index.html
│   │       ├── objects.inv
│   │       ├── search.html
│   │       ├── searchindex.js
│   │       ├── _sources
│   │       │   └── index.rst.txt
│   │       └── _static
│   │           ├── alabaster.css
│   │           ├── basic.css
│   │           ├── custom.css
│   │           ├── doctools.js
│   │           ├── documentation_options.js
│   │           ├── file.png
│   │           ├── jquery-3.6.0.js
│   │           ├── jquery.js
│   │           ├── language_data.js
│   │           ├── minus.png
│   │           ├── plus.png
│   │           ├── pygments.css
│   │           ├── searchtools.js
│   │           ├── sphinx_highlight.js
│   │           ├── _sphinx_javascript_frameworks_compat.js
│   │           ├── underscore-1.13.1.js
│   │           └── underscore.js
│   ├── make.bat
│   ├── Makefile
│   └── source
│       ├── conf.py
│       ├── events
│       │   └── index.rst
│       └── index.rst
├── entrypoint.sh
├── k8s
│   ├── front-deploy.yaml
│   ├── frontend-ingress.yaml
│   └── migrate-job.yaml
├── k8s_update.sh
├── locale
│   ├── en
│   │   └── LC_MESSAGES
│   │       ├── django.mo
│   │       └── django.po
│   ├── es
│   │   └── LC_MESSAGES
│   │       ├── django.mo
│   │       └── django.po
│   ├── es_co
│   │   └── LC_MESSAGES
│   │       ├── django.mo
│   │       └── django.po
│   ├── es_es
│   │   └── LC_MESSAGES
│   │       ├── django.mo
│   │       └── django.po
│   └── es_mx
│       └── LC_MESSAGES
│           ├── django.mo
│           └── django.po
├── manage.py
├── middleware
│   └── __pycache__
│       └── htmx_middleware.cpython-312.pyc
├── README.md
├── requirements.txt
├── target
│   └── pylist.json
└── utils
    ├── apt-dependencies.sh
    ├── gettext.sh
    ├── migrations.sh
    ├── python-dependencies.sh
    └── sql-driver.sh

149 directories, 777 files
```
