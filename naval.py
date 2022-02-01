import serial
import time
import sys
import os
import threading
import random
import re

BAUDRATE = 9600
PORT1 = "/dev/pts/3"
PORT2 = "/dev/pts/4"

active_port = None
player_number = None
local_player_name = None
remote_player_name = None
player_turn = False
matrix_local_player = None
matrix_remote_player = None
match_ready = False
refresh_board = False
maximum_hit = 21
total_hit = 0
w, h = 10, 10


def conn(port):

    ser = serial.Serial(
        port,
        baudrate=BAUDRATE,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=None,
    )

    return ser


def init(port):

    global active_port, player_turn

    ports = {"1": PORT1, "2": PORT2}

    error = False
    print("Iniciando")

    try:
        active_port = conn(ports[port])
    except Exception as e:
        error = True

    if error:
        print("Puerto en uso", ports[port])
    else:
        if port == "1":
            player_turn = True
        print("Conectado", ports[port])


def read_port():

    global remote_player_name, player_turn, match_ready, refresh_board, total_hit

    while True:

        time.sleep(0.1)
        if active_port:
            length = active_port.in_waiting

            if length:
                x = active_port.read(length).decode("utf-8", errors="ignore")
                if x:
                    print("DEBUG: ", x)
                    x = x.split(":")
                    code, data = x[0], x[1]
                    if code == "X001":
                        if local_player_name and not match_ready:
                            write_port("X001:" + local_player_name)
                        remote_player_name = data
                        match_ready = local_player_name and remote_player_name
                    elif code == "X002":
                        res = check_play(data, matrix_local_player)
                        if res:
                            process_play(data, matrix_local_player)
                            write_port("X003:" + data)
                            refresh_board = True
                            player_turn = False
                            total_hit += 1
                        else:
                            process_play(data, matrix_local_player, 8)
                            write_port("X004:" + data)
                            refresh_board = True
                            player_turn = True
                    elif code == "X003":
                        process_play(data, matrix_remote_player)
                        player_turn = True
                        total_hit += 1
                    elif code == "X004":
                        player_turn = False


def convert_coordinate(coord):

    letter_to_number = {
        "a": 0,
        "b": 1,
        "c": 2,
        "d": 3,
        "e": 4,
        "f": 5,
        "g": 6,
        "h": 7,
        "i": 8,
        "j": 9,
    }

    letter = coord[0]
    number = coord[1:]

    return (letter_to_number[letter.lower()], int(number))


def check_play(coord, matrix):

    pos = convert_coordinate(coord)

    if matrix[pos[0]][pos[1]] > 0:
        return True

    return False


def process_play(coord, matrix, val = 9):

    pos = convert_coordinate(coord)

    matrix[pos[0]][pos[1]] = val


def write_port(data):

    data = data + "\r"
    active_port.write(data.encode("utf-8", errors="ignore"))


def clear_console():

    os.system("cls" if os.name == "nt" else "clear")


def generate_matrix():

    matrix = [[0 for x in range(w)] for y in range(h)]

    return matrix


def generate_play():

    global maximum_hit

    matrix = generate_matrix()

    flota = [(4, 1, 4), (3, 3, 3), (2, 3, 2), (1, 2, 1)]

    # itero por los tipos de vessels
    for vessels in flota:
        size, quantity, letter = vessels
        # genero tipo de vessels segun quantity y los coloco en el tablero
        for unidad in range(1, quantity + 1):
            positioned = False
            while not positioned:
                position = bool(random.getrandbits(1))
                if position:  # vertical
                    relative_pos_x = random.randint(0, w - 1)
                    relative_pos_y = random.randint(0, h - size - 1)
                else:  # horizontal
                    relative_pos_x = random.randint(0, w - size - 1)
                    relative_pos_y = random.randint(0, h - 1)
                check = 0
                for step in range(0, size):
                    if position:  # vertical
                        if matrix[relative_pos_x][relative_pos_y + step] == 0:
                            check = check + 1
                    else:
                        if matrix[relative_pos_x + step][relative_pos_y] == 0:
                            check = check + 1
                    if check == size:
                        positioned = True
                if positioned:
                    for step in range(0, size):
                        if position:  # vertical
                            matrix[relative_pos_x][relative_pos_y + step] = letter
                        else:
                            matrix[relative_pos_x + step][relative_pos_y] = letter

    return matrix


def grid_char(num):

    character = {
        0: "\x1b[0;33;34m" + " ~ " + "\x1b[0m",
        4: "\x1b[1;37;42m" + " 4 " + "\x1b[0m",
        3: "\x1b[0;30;46m" + " 3 " + "\x1b[0m",
        2: "\x1b[2;30;43m" + " 2 " + "\x1b[0m",
        1: "\x1b[0;30;44m" + " 1 " + "\x1b[0m",
        8: " o ",
        9: "\x1b[1;31;6m" + " x " + "\x1b[0m",
    }

    return character[num]


def check_coordinate(coord):

    pattern = r"(^[A-Ja-j]{1}[0-9]{1}$){1}"
    r = re.compile(pattern)
    match = r.match(coord)

    return bool(match)


def print_grid(data, player):

    grid_size = 10
    c = 65

    # First row
    print()
    print(player)
    print(f"{(grid_size*4+4)*'-'}")
    print(f"  ", end="")
    for j in range(grid_size):
        print(f"| {j} ", end="")
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

matrix_local_player = generate_play()
matrix_remote_player = generate_matrix()

input_data = input("> ")

tread_port = threading.Thread(target=read_port, args=())
tread_port.setDaemon(True)
tread_port.start()

while True:
    if input_data == "2":
        sys.exit()
    else:
        refresh_board = False
        clear_console()
        while not player_number:
            time.sleep(0.1)
            input_jugador = input("¿Jugador (1) o (2)? ")
            if input_jugador == "1" or input_jugador == "2":
                player_number = input_jugador
                init(player_number)
                while not local_player_name:
                    local_player_name = input("¿Cuál es tu nombre? ")

                if local_player_name:
                    write_port("X001:" + local_player_name)

        if local_player_name:
            print_grid(data=matrix_local_player, player=local_player_name + " (tú)")
        if remote_player_name:
            print_grid(data=matrix_remote_player, player=remote_player_name)

        if not match_ready:
            print("Esperando a que alguien se una a la partida")
            while not remote_player_name:
                time.sleep(0.1)
                pass
        else:
            if total_hit == maximum_hit:
                print("FIN DE PARTIDA")
                sys.exit()
            else:
                if player_turn:
                    invalid_coord = True
                    coord = None
                    while invalid_coord:
                        coord = input("Indica una coordenada ")
                        invalid_coord = not check_coordinate(coord)

                    if coord:
                        write_port("X002:" + coord)
                        player_turn = False
                else:
                    print("Esperando jugada de " + remote_player_name)
                    while not player_turn:
                        if refresh_board:
                            break
                        time.sleep(0.1)
                        pass
