import serial
import time
import sys
import os
import threading
import random

BAUDRATE = 9600
PUERTO1 = "/dev/pts/4"
PUERTO2 = "/dev/pts/5"

active_port = None
num_jugador = None
nombre_jugador = None
nombre_jugador_remoto = None
turno = False
matrix_jugador = None
matrix_jugador_remoto = None
w, h = 10, 10


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
        if puerto == "1":
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


def generar_matrix():

    matrix = [[0 for x in range(w)] for y in range(h)]

    return matrix


def generar_jugada():

    matrix = generar_matrix()

    flota = [(4, 1, 4), (3, 3, 3), (2, 3, 2), (1, 2, 1)]

    # itero por los tipos de buques
    for buques in flota:
        tamano, cantidad, letra = buques
        # genero tipo de buques segun cantidad y los coloco en el tablero
        for unidad in range(1, cantidad + 1):
            positioned = False
            while not positioned:
                position = bool(random.getrandbits(1))
                if position:  # vertical
                    relative_pos_x = random.randint(0, w - 1)
                    relative_pos_y = random.randint(0, h - tamano - 1)
                else:  # horizontal
                    relative_pos_x = random.randint(0, w - tamano - 1)
                    relative_pos_y = random.randint(0, h - 1)
                check = 0
                for step in range(0, tamano):
                    if position:  # vertical
                        if matrix[relative_pos_x][relative_pos_y + step] == 0:
                            check = check + 1
                    else:
                        if matrix[relative_pos_x + step][relative_pos_y] == 0:
                            check = check + 1
                    if check == tamano:
                        positioned = True
                if positioned:
                    for step in range(0, tamano):
                        if position:  # vertical
                            matrix[relative_pos_x][relative_pos_y + step] = letra
                        else:
                            matrix[relative_pos_x + step][relative_pos_y] = letra

    return matrix


def grid_char(num):

    character = {
        0: '\x1b[0;33;34m' + ' ~ ' + '\x1b[0m',
        4: '\x1b[1;37;42m' + ' 4 ' + '\x1b[0m',
        3: '\x1b[0;30;46m' + ' 3 ' + '\x1b[0m',
        2: '\x1b[2;30;43m' + ' 2 ' + '\x1b[0m',
        1: '\x1b[0;30;44m' + ' 1 ' + '\x1b[0m',
        8: ' o ',
        9: '\x1b[1;31;6m' + ' x ' + '\x1b[0m',
    }

    return character[num]


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
            print(f"|{grid_char(data[i][j])}", end="")
        print(f"| ", end="")
        print()
        print(f"{(grid_size*4+4)*'-'}")


clear_console()
print("Menú de opciones")
print("1. Empezar a jugar")
print("2. Salir")

matrix_jugador = generar_jugada()
matrix_jugador_remoto = generar_matrix()

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
            pintar_grid(data=matrix_jugador, player=nombre_jugador + " (tú)")
        if nombre_jugador_remoto:
            enviar("X001:" + nombre_jugador)
            pintar_grid(data=matrix_jugador_remoto, player=nombre_jugador_remoto)
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
