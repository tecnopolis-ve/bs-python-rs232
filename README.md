# LINUX ONLY!

Instalar socat

`sudo apt-get install socat -y`

Crear los puertos

`socat -d -d pty,raw,echo=0 pty,raw,echo=0`

Una vez ejecutado el comando anterior, se listan los puertos creados, estos deben ser colocados en `PUERTO1` y `PUERTO2` del archivo naval.py
