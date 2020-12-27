import time
import random
import socket
import struct
import threading
import ipaddress
import string
from scapy.all import *


# Global final variables
TIMER_LENGTH = 10 #seconds
MAGIC_COOKIE = 0xfeedbeef
MESSAGE_TYPE = 0x2
NUMBER_OF_TEAMS = 2
UDP_PORT = 13117
INTERVAL = 1
BUFFER_SIZE = 4096
# End of global final variables

# The players class, to keep track of their sockets and scores
class Player:
    
    def __init__(self, sock: socket, name):
        self.sock: socket = sock
        self.score = 0
        self.name = name
        self.team = random.randint(1, 2)

    def get_sock(self):
        return self.sock

    def get_score(self):
        return self.score
    
    def set_team(self, team):
        self.team = team
    
    def increment_score(self):
        self.score += 1
    
    def get_team(self):
        return self.team

    def get_name(self):
        return self.name

# The server itself
class Server:
    
    def __init__(self):
        self.players_sockets = {}
        self.should_stop_looking = False

    def server_start_message(self, ip):
        print(f"Server started, listerning on IP address {ip}\n")

    def get_game_start_message(self):
        welcome = "Welcome to Keyboard Spamming Battle Royale.\n"
        group_announcement = ""
        for i in range(NUMBER_OF_TEAMS):
            group_announcement += f"Group {i + 1}:\n==\n"
            for p in self.players_sockets.values():
                if p.get_team() == i + 1:
                    group_announcement += p.get_name()
            group_announcement += "\n"
        game_start_accounement = "Start pressing keys on your keyboard as fast as you can!"
        return welcome + group_announcement + game_start_accounement

    def offer(self, network_type, tcp_sock):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        message = struct.pack('I B H', MAGIC_COOKIE, MESSAGE_TYPE, tcp_sock.getsockname()[1]) #getsockname[1] gets the port
        
        # Endlessly send a broadcast every @interval seconds
        broadcast_ip = str(ipaddress.ip_network(get_if_addr(network_type) + '/24').broadcast_address)

        for i in range(round(TIMER_LENGTH/INTERVAL)):
            sock.sendto(message, (broadcast_ip, UDP_PORT))
            time.sleep(INTERVAL)

    def connect_with_client(self, sock):
        while not self.should_stop_looking:
            new_player_name = ""
            conn, addr = sock.accept()
            if self.should_stop_looking:
                while True:
                    new_player_name += conn.recv(BUFFER_SIZE)
                    if not new_player_name:
                        break
                    if not new_player_name.endswith("\n"):
                        continue
                    new_player_name = new_player_name[:-1] # remove the \n
                    break
                new_player = Player(conn, new_player_name)
                self.players_sockets[addr] = new_player

    def game_time(self):
        print('todo')
        # TODO

    def game_over(self):
        scores = [0,0]
        for p in self.players_sockets.values():
            scores[p.get_team() - 1] += p.get_score()
        
        winners = 0
        if scores[0] > scores[1]:
            winners = 0
        else:
            if scores[1] > scores[0]:
                winners = 1
            else:
                winners = -1
        
        winners_names = ""
        for p in self.players_sockets.values():
            if p.get_team() - 1 == winners:
                winners_names += p.get_name() + "\n"
        
        return f"Game over!\n Group 1 typed in {scores[0]}. Group 2 typed in {scores[1]} characters.\n Group {winners + 1} wins!\n\n Congratulations to the winners:\n==\n{winners_names}"

    def close_all_connections(self):
        for conn in self.players_sockets.values():
            conn.get_sock().close()
        self.players_sockets = {}

    def pre_game(self, network_type, sock):
            connect_with_client_thread = threading.Thread(target = self.connect_with_client, args =(sock,), daemon = True)
            connect_with_client_thread.start()
            self.offer(network_type, sock)
            self.should_stop_looking = True

    def main_loop(self, network_type):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0)) #let the os choose a port for me
        sock.listen(1)
        self.server_start_message(network_type)
        while True:
            self.pre_game(network_type, sock)
            self.game_time()
            self.game_over()
            self.close_all_connections()
            print("Game over, sending out offer requests...")
            first_time = False

# TODO implement the game itself, implement try catches
server = Server()
server_type = input("Would you like to use the dev channel or test channel? (DEV/test)")
server_ip = 'eth2' if server_type.lower() == 'test' else 'eth1'
server.main_loop(get_if_addr(server_ip))