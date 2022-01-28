import serial
import time
import sys
import os
import threading

BAUDRATE = 9600
PUERTO1 = "/dev/pts/1"
PUERTO2 = "/dev/pts/5"

active_port = None
num_jugador = None
nombre_jugador = None
nombre_jugador_remoto = None
turno = False


def conn(puerto):

    ser = serial.Serial(
        puerto,
        baudrate=BAUDRATE,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=None,
    )

    return ser


def init(puerto):

    global active_port, turno

    puertos = {"1": PUERTO1, "2": PUERTO2}

    error = False
    print("Iniciando")

    try:
        active_port = conn(puertos[puerto])
    except Exception as e:
        error = True

    if error:
        print("Puerto en uso", puertos[puerto])
    else:
        if(puerto == '1'):
            turno = True
        print("Conectado", puertos[puerto])


def leer():

    global nombre_jugador_remoto, turno

    while True:

        time.sleep(0.1)
        if active_port:
            length = active_port.in_waiting

            if length:
                x = active_port.read(length).decode("utf-8", errors="ignore")
                if x:
                    x = x.split(":")
                    code, data = x[0], x[1]
                    if code == "X001":
                        nombre_jugador_remoto = data
                    elif code == "X002":
                        turno = True
                        print(data)


def enviar(data):

    active_port.write(data.encode("utf-8", errors="ignore"))


def clear_console():

    os.system("cls" if os.name == "nt" else "clear")


def pintar_grid(data, player):

    grid_size = 10
    c = 65
    character = "~"

    # First row
    print()
    print(player)
    print(f"{(grid_size*4+4)*'-'}")
    print(f"  ", end="")
    for j in range(grid_size):
        print(f"| {j+1} ", end="")
    print(f"| ", end="")
    print()
    print(f"{(grid_size*4+4)*'-'}")

    # Other rows
    for i in range(grid_size):
        print(f"{chr(c+i)} ", end="")
        for j in range(grid_size):
            print(f"| {character} ", end="")
        print(f"| ", end="")
        print()
        print(f"{(grid_size*4+4)*'-'}")


clear_console()
print("Menú de opciones")
print("1. Empezar a jugar")
print("2. Salir")
input_data = input("> ")

tleer = threading.Thread(target=leer, args=())
tleer.setDaemon(True)
tleer.start()

while True:
    if input_data == "2":
        sys.exit()
    else:
        clear_console()
        while not num_jugador:
            input_jugador = input("¿Jugador (1) o (2)? ")
            if input_jugador == "1" or input_jugador == "2":
                num_jugador = input_jugador
                init(num_jugador)
                while not nombre_jugador:
                    nombre_jugador = input("¿Cuál es tu nombre? ")
                enviar("X001:" + nombre_jugador)
        if nombre_jugador:
            pintar_grid(data=None, player=nombre_jugador)
        if nombre_jugador_remoto:
            enviar("X001:" + nombre_jugador)
            pintar_grid(data=None, player=nombre_jugador_remoto)
            if turno:
                coord = input("Indica una coordenada ")
                enviar("X002:" + coord)
                turno = False
            else:
                print("Esperando jugada de " + nombre_jugador_remoto)
                while not turno:
                    time.sleep(0.1)
                    pass
        else:
            print("Esperando a que alguien se una a la partida")
            while not nombre_jugador_remoto:
                time.sleep(0.1)
                pass
