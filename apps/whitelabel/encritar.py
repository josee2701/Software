from cryptography.fernet import Fernet

# Generar una clave y mostrarla
print(Fernet.generate_key().decode())
