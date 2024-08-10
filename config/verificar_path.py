import os
import pathlib

import dotenv

# Ubicación del archivo .env
CURRENT_DIR = pathlib.Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
ENV_FILE_PATH = BASE_DIR / ".env"

# Cargar las variables de entorno desde el archivo .env
dotenv.read_dotenv(str(ENV_FILE_PATH))

print("Verifico ruta del archivo .env", ENV_FILE_PATH)
# Verificar si una variable de entorno está definida e imprimirla
if "AZURE_ACCOUNT_NAME" in os.environ:
    print("AZURE_ACCOUNT_NAME:", os.environ["AZURE_ACCOUNT_NAME"])
else:
    print("AZURE_ACCOUNT_NAME no se encuentra en las variables de entorno.")

# Verificar si otra variable de entorno está definida e imprimirla
if "DEBUG" in os.environ:
    print("DEBUG:", os.environ["DEBUG"])
else:
    print("DEBUG no se encuentra en las variables de entorno.")
