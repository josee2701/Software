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

```bash
< front_np >
   |
   |-- api/                                 # API exclusiva para los servicios de `checkpoint` y `realtime`
   |    |-- serializers
   |    |--  |-- ...
   |    |-- views                           # Cada archivo en las vistas hace referencia a un servicio
   |    |--  |-- checkpoint.py
   |    |--  |-- realtime.py
   |    |--  |-- ...
   |
   |-- apps/                                # Carpeta principal de los módulos/microservicios de la aplicación
   |    |-- authentication/                 # Gestiona las rutas de autenticación (inicio de sesión y registro)
   |    |    |-- urls.py                    # Define las rutas de autenticación
   |    |    |-- views.py                   # Gestiona el inicio de sesión y el registro
   |    |    |-- forms.py                   # Define los formularios de la librería `auth` (inicio de sesión y registro)
   |    |
   |    |-- static/
   |    |    |-- <css, JS, images>          # Archivos de Imagen, CSS, Javascripts
   |    |
   |    |-- templates/                      # Plantillas utilizadas para representar las páginas
   |         |-- includes/                  # Trozos y componentes HTML
   |         |    |-- navigation.html       # Componente del menú superior
   |         |    |-- sidebar.html          # Componente de la barra lateral
   |         |    |-- footer.html           # Pie de página de la aplicación
   |         |    |-- scripts.html          # Scripts comunes a todas las páginas
   |         |
   |         |-- layouts/                   # Páginas maestras
   |         |    |-- base-fullscreen.html  # Utilizado por las páginas de autenticación
   |         |    |-- base.html             # Utilizado por las páginas comunes
   |
   |-- config/                              # Implementa la configuración de la aplicación
   |    |-- settings.py                     # Define la configuración global
   |    |-- wsgi.py                         # Inicia la aplicación en producción
   |    |-- urls.py                         # Define las URLs servidas por todas las aplicaciones/nodos
   |
   |-- docs/                                # Documentación generada con Sphinx
   |    |-- build/
   |    |-- source/
   |    ...
   |
   |-- locale/                              # Idiomas y dialectos de la aplicación
   |    |-- en/...
   |    |-- es_co/LC_MESSAGES               # Cada idioma genera un paquete de los mensajes visibles para el usuario
   |    |    |-- django.mo                  # Archivo de mensajes compilados
   |    |    |-- django.po                  # Archivo de mensajes, permite el control de la traducción
   |    |-- es_es/...
   |    |-- es_mx/...
   |
   |-- requirements.txt                     # Dependencias
   |
   |-- .env                                 # Configuración a través de variables de entorno
   |-- manage.py                            # Iniciar la aplicación - Script de inicio por defecto de Django
   |
   |-- ...
```
