import os
import sys
import json
import time
import random
import socket
import struct
import threading
import ipaddress
import string
from scapy.all import *


# Global final variables
TIMER_LENGTH = 10
MAGIC_COOKIE = 0xfeedbeef
MESSAGE_TYPE = 0x2
NUMBER_OF_TEAMS = 2
UDP_PORT = 13117
INTERVAL = 1
BUFFER_SIZE = 4096
SURPRISE = "\n             ___________\n            '._==_==_=_.'\n            .-\:      /-.\n           | (|:.     |) |\n            '-|:.     |-'\n              \::.    /\n               '::. .'\n                 ) (\n               _.' '._\n               `*****`"
LOGO = " _____ _       _     _   _ \n|  ___(_) __ _| |__ | |_| |\n| |_  | |/ _` | '_ \| __| |\n|  _| | | (_| | | | | |_|_|\n|_|   |_|\__, |_| |_|\__(_)\n         |___/             "
# End of global final variables

# temp values for test
# TIMER_LENGTH = 10 #10 seconds
# MAGIC_COOKIE = 0xefbeedfe
# MESSAGE_TYPE = 0x2
# NUMBER_OF_TEAMS = 2
# UDP_PORT = 51231 #13117
# INTERVAL = 1
# BUFFER_SIZE = 4096

# The players class, to keep track of their sockets and typed words

server_message_color = "\033[38;5;51m"

def color_gen():
    while True:
        print("\033[38;5;1m",end='') #red
        sys.stdout.flush()
        yield 
        print("\033[38;5;208m",end='') #orange
        sys.stdout.flush()
        yield
        print("\033[38;5;11m",end='') #yellow
        sys.stdout.flush()
        yield
        print("\033[38;5;10m",end='') #green
        sys.stdout.flush()
        yield
        print("\033[38;5;27m",end='') #blue
        sys.stdout.flush()
        yield
        print("\033[38;5;129m",end='') #purple
        sys.stdout.flush()
        yield

color = color_gen()
def nice_print(to_print):
    try:
        next(color)
    except:
        pass
    print(to_print)

def reset_color():
    print("\033[0m")

class Player:
    
    def __init__(self, sock, name):
        self.sock = sock
        self.typed = ""
        self.name = name
        self.team = random.randint(1, 2)

    def get_sock(self):
        return self.sock

    def get_typed(self):
        return self.typed
    
    def set_team(self, team):
        self.team = team
    
    def add_typed(self, typed):
        self.typed += typed
    
    def get_team(self):
        return self.team

    def get_name(self):
        return self.name

# The server itself
class Server:
    
    def __init__(self):
        self.players_sockets = []
        self.connections_to_close = []
        self.should_stop_looking = False
        self.should_stop_playing = False
        self.data = {}

    def server_start_message(self, ip):
        actual_ip = '127.0.0.1' if ip == '0.0.0.0' else ip
        nice_print(f"Server started, listerning on IP address {actual_ip}\n")

    def get_game_start_message(self):
        group_announcement = ""
        for i in range(1, NUMBER_OF_TEAMS + 1):
            group_announcement += f"Group {i}:\n==\n"
            for p in self.players_sockets:
                if p.get_team() == i:
                    group_announcement += p.get_name()
                    group_announcement += "\n"
            group_announcement += "\n"
        game_start_accounement = "Start pressing keys on your keyboard as fast as you can!"
        return LOGO + "\n" + group_announcement + game_start_accounement

    def offer(self, network_type, tcp_sock):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = struct.pack('>IbH', MAGIC_COOKIE, MESSAGE_TYPE, tcp_sock.getsockname()[1]) #getsockname[1] gets the port
        # nice_print(str(message))
        # Endlessly send a broadcast every @interval seconds
        broadcast_ip = str(ipaddress.ip_network(network_type + '/16', False).broadcast_address)
        # print(message)
        nice_print("Broadcasting on " + broadcast_ip)
        nice_print("Registration ends in:")
        for i in range(1, TIMER_LENGTH + 1):
            sock.sendto(message, (broadcast_ip, UDP_PORT))
            # sock.sendto(message, ('localhost', UDP_PORT))
            nice_print(str(TIMER_LENGTH - i))
            time.sleep(INTERVAL)
        nice_print("\n")
        sock.close()

    def connect_with_specific_client(self, conn, addr):
        try:
            new_player_name = ""
            if not self.should_stop_looking:
                should_exit = False
                while not should_exit:
                    new_player_name += (conn.recv(BUFFER_SIZE)).decode()
                    # if not new_player_name:
                    #     break
                    if "\n" not in new_player_name:
                        continue
                    new_player_name = new_player_name[:new_player_name.index("\n")] # remove the \n
                    should_exit = True
            if not self.should_stop_looking:
                new_player = Player(conn, new_player_name)
                self.players_sockets.append(new_player) # the internet says append is threadsafe
                nice_print(new_player_name + " joined the fight!")
            else:
                conn.close()
        except:
            pass


    def connect_with_client(self, sock):
        try:
            while not self.should_stop_looking:
                conn, addr = sock.accept()
                self.connections_to_close.append(conn)
                connect_with_client_thread = threading.Thread(target = self.connect_with_specific_client, args =(conn, addr,), daemon = True)
                connect_with_client_thread.start()
        except:
            pass
        
    def send_win(self, message):
        for p in self.players_sockets:
            try:
                conn = p.get_sock()
                conn.sendall(message.encode())
            except:
                pass

    def game_over(self):
        if not self.players_sockets: #if no players connected
            nice_print (f"No players played in this round\n\n")
            return
        scores = [0,0]
        for p in self.players_sockets:
            scores[p.get_team() - 1] += len(p.get_typed())
        
        winners = 0
        if scores[0] > scores[1]:
            winners = 0
        else:
            if scores[1] > scores[0]:
                winners = 1
            else:
                winners = -1
        
        winners_names = ""
        for p in self.players_sockets:
            if p.get_team() - 1 == winners:
                winners_names += p.get_name() + "\n"
        win_message = f"{SURPRISE}\nGame over!\nGroup 1 typed in {scores[0]}. Group 2 typed in {scores[1]} characters.\n"
        if winners == -1:
            win_message += "Its a tie!"
        else:
            win_message += f"Group {winners + 1} wins!\n\nGG all, winner winner chicken dinner for:\n==\n{winners_names}"
        nice_print (win_message)
        self.send_win(server_message_color + win_message)

    def close_all_connections(self):
        for conn in self.connections_to_close:
            try:
                conn.close()
            except:
                pass
        for p in self.players_sockets:
            try:
                p.get_sock().close()
            except:
                pass
        self.connections_to_close = []
        self.players_sockets = []

    def pre_game(self, network_type, sock):
        self.should_stop_looking = False
        connect_with_client_thread = threading.Thread(target = self.connect_with_client, args =(sock,), daemon = True)
        connect_with_client_thread.start()
        time.sleep(0.01)
        self.offer(network_type, sock)
        self.should_stop_looking = True

    def client_thread(self, player, message):
        try:
            conn = player.get_sock()
            conn.sendall((server_message_color + message).encode())
            typed = ""
            color_group = "\033[38;5;1m" if player.get_team() == 1 else "\033[38;5;27m"
            while not self.should_stop_playing:
                typed = (conn.recv(BUFFER_SIZE)).decode()
                if not self.should_stop_playing and not typed == "":
                    nice_print(f"{color_group}received {typed} from {player.get_name()}")
                    player.add_typed(typed)
        except:
            nice_print (f"{player.get_name()} disconnected. Don't worry, their score will still count.")

    def shuffle_teams(self):
        random.shuffle(self.players_sockets)
        i = 0
        for p in self.players_sockets:
            p.set_team((i % 2) + 1)
            i += 1

    def game_time(self):
        self.should_stop_playing = False
        self.shuffle_teams()
        message = self.get_game_start_message()
        for player in self.players_sockets:
            player_thread = threading.Thread(target = self.client_thread, args = (player,message,), daemon = True)
            player_thread.start()
        nice_print(f"{self.get_game_start_message()}\nThe game will end in:")
        for i in range (1, TIMER_LENGTH + 1):
            nice_print(TIMER_LENGTH - i)
            time.sleep(1)
        self.should_stop_playing = True


    def initialize_data(self):
        typed = dict( (key, 0) for key in string.printable) # put 0 for each letter
        high_score = 0
        group_with_best_name = ""
        self.data = {}
        self.data["typed"] = typed
        self.data["high_score"] = high_score
        self.data["group_with_best_name"] = group_with_best_name

    def log_statistics(self):
        try:
            if self.players_sockets == []:
                return
            if not self.data:
                self.initialize_data()
            typed = ""
            high_score = 0
            for player in self.players_sockets:
                typed += player.get_typed()
                high_score = max(len(player.get_typed()), high_score)
            for c in typed:
                self.data["typed"][c] += 1
            self.data["high_score"] = max(high_score, self.data["high_score"])
            self.data["group_with_best_name"] = random.choice(self.players_sockets).get_name()
        except:
            pass
            
    def print_statistics(self):
        try:
            group_with_best_name = self.data["group_with_best_name"]
            high_score = self.data["high_score"]
            most_typed_char = max(self.data["typed"].items(), key=operator.itemgetter(1))[0]
            print("")
            nice_print(f"Team with the best name: {group_with_best_name}")
            nice_print(f"Highest score ever for a single team: {high_score}")
            nice_print(f"Most typed character: {most_typed_char}")
            print("")
        except:
            pass
        
    def main_loop(self, network_type):
        sock = ""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 0)) #let the os choose a port for me
            sock.settimeout(10)
            sock.listen(1)
            self.server_start_message(network_type)
            while True:
                while (not self.players_sockets):
                    self.pre_game(network_type, sock)
                if self.players_sockets:
                    self.game_time()
                    self.game_over()
                    self.log_statistics()
                    self.print_statistics()
                    nice_print("GG EZ NOOBS, sending out offer requests...")
                self.close_all_connections()
        except:
            nice_print("\n\gg ez noobs")
            try:
                self.close_all_connections()
                sock.close()
            except:
                pass


server = Server()
server_type = input("Would you like to use the dev channel or test channel? (DEV/test)")

server_ip = 'eth2' if server_type.lower() == 'test' else 'eth1'
# nice_print(get_if_addr(server_ip))
os.system('cls' if os.name == 'nt' else 'clear')
server.main_loop(get_if_addr(server_ip))