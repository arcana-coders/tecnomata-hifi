# Tecnomata Hi-Fi

Reproductor de escritorio para Windows inspirado en los minicomponentes de los años 80 y 90. Se conecta a una biblioteca propia de Navidrome mediante la API Subsonic; no incluye música ni una cuenta de servidor.

Ofrece barra horizontal o dock lateral, listas y búsqueda, display VFD, controles de reproducción y letras desde Navidrome, LRCLIB o lyrics.ovh. El ecualizador es una animación decorativa: no analiza el audio. Es un proyecto independiente y no está afiliado a Sony ni a Navidrome.

## Instalación

Requiere Windows, Python 3.10 o posterior y acceso a un servidor Navidrome compatible.

```powershell
git clone https://github.com/arcana-coders/tecnomata-hifi.git
cd tecnomata-hifi
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

También puedes abrir `iniciar.bat` después de instalar las dependencias. Introduce la dirección de tu servidor, usuario y contraseña en el formulario. No hay instalador distribuido; el funcionamiento con otros servidores Subsonic o en Linux no se ha validado en esta publicación.

## Datos y privacidad

La configuración se guarda en `%USERPROFILE%\.config\tecnomata-hifi\config.json` y la caché de letras en la carpeta `lyrics` junto a ella. **La contraseña se guarda codificada en Base64, no cifrada**: cualquier persona con acceso al archivo puede recuperarla. Utiliza una cuenta de equipo protegida y una contraseña exclusiva. No compartas el archivo de configuración ni el registro `crash.log` sin revisarlos. Prefiere una conexión HTTPS de confianza para acceder a tu servidor.

Al buscar letras, la aplicación puede enviar el nombre de artista y canción a LRCLIB y lyrics.ovh. La reproducción depende de los formatos compatibles con el sistema y del servidor. El streaming FLAC y el uso prolongado requieren más pruebas; no se ofrece un binario firmado.
