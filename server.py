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
TIMER_LENGTH = 10 #seconds
MAGIC_COOKIE = 0xfeedbeef
MESSAGE_TYPE = 0x2
NUMBER_OF_TEAMS = 2
UDP_PORT = 13117
INTERVAL = 1
BUFFER_SIZE = 4096
# End of global final variables

# The players class, to keep track of their sockets and typed words
class Player:
    
    def __init__(self, sock: socket, name):
        self.sock: socket = sock
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

    def server_start_message(self, ip):
        actual_ip = '127.0.0.1' if ip == '0.0.0.0' else ip
        print(f"Server started, listerning on IP address {actual_ip}\n")

    def get_game_start_message(self):
        welcome = "Welcome to Keyboard Spamming Battle Royale.\n"
        group_announcement = ""
        for i in range(NUMBER_OF_TEAMS):
            group_announcement += f"Group {i + 1}:\n==\n"
            for p in self.players_sockets:
                if p.get_team() == i + 1:
                    group_announcement += p.get_name()
            group_announcement += "\n"
        game_start_accounement = "Start pressing keys on your keyboard as fast as you can!"
        return welcome + group_announcement + game_start_accounement

    def offer(self, network_type, tcp_sock):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        message = struct.pack('I B H', MAGIC_COOKIE, MESSAGE_TYPE, tcp_sock.getsockname()[1]) #getsockname[1] gets the port
        
        # Endlessly send a broadcast every @interval seconds
        broadcast_ip = 'localhost' if network_type == '0.0.0.0' else str(ipaddress.ip_network(get_if_addr(network_type) + '/24').broadcast_address)

        for i in range(round(TIMER_LENGTH/INTERVAL)):
            sock.sendto(message, (broadcast_ip, UDP_PORT))
            time.sleep(INTERVAL)
        sock.close()

    def connect_with_specific_client(self, conn, addr):
        try:
            new_player_name = ""
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
                self.players_sockets.append(new_player) # the internet says append is threadsafe
        except:
            pass

    def connect_with_client(self, sock):
        while not self.should_stop_looking:
            conn, addr = sock.accept()
            self.connections_to_close.append(conn)
            connect_with_client_thread = threading.Thread(target = self.connect_with_specific_client, args =(conn, addr,), daemon = True)
            connect_with_client_thread.start()
        

    def game_over(self):
        if not self.players_sockets: #if no players connected
            print (f"No players played in this round\n\n")
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
        
        print (f"Game over!\n Group 1 typed in {scores[0]}. Group 2 typed in {scores[1]} characters.\n Group {winners + 1} wins!\n\n Congratulations to the winners:\n==\n{winners_names}")

    def close_all_connections(self):
        for conn in self.connections_to_close:
            try:
                conn.get_sock().close()
            except:
                pass
        self.connections_to_close = []
        self.players_sockets = []

    def pre_game(self, network_type, sock):
        connect_with_client_thread = threading.Thread(target = self.connect_with_client, args =(sock,), daemon = True)
        connect_with_client_thread.start()
        self.offer(network_type, sock)
        self.should_stop_looking = True

    def client_thread(self, player, message):
        try:
            player.get_sock().sendall(message)
            conn, addr = player.get_sock().accept()
            typed = ""
            while True:
                typed = conn.recv(BUFFER_SIZE)
                player.add_typed(typed)
        except:
            print (f"{player.get_name()} disconnected. Don't worry, their score will still count.")

    def game_time(self):
        message = self.get_game_start_message()
        for player in self.players_sockets:
            player_thread = threading.Thread(target = self.client_thread, args = (player,message,), daemon = True)
            player_thread.start()
        time.sleep(TIMER_LENGTH)

    def get_initial_json(self):
        typed = dict( (key, 0) for key in string.printable) # put 0 for each letter
        high_score = -1
        group_with_best_name = ""
        data = {}
        data["typed"] = typed
        data["high_score"] = high_score
        data["group_with_best_name"] = group_with_best_name
        return data

    def log_statistics(self):
        if self.players_sockets == []:
            return
        typed = ""
        high_score = -1
        player_name_list = []
        try:
            file = open('log.json', "a+")
            data = json.load(file)
            if data == {}:
                data = self.get_initial_json()
            for player in self.players_sockets:
                typed += player.get_typed()
                high_score = max(high_score, len(player.get_typed()))
                player_name_list += [player.get_name()]
            for c in typed:
                data["typed"][c] += 1
            data["high_score"] = max(high_score, data["high_score"])
            data["group_with_best_name"] = random.choice(player_name_list + [data["group_with_best_name"]])
            file.seek(0)
            file.write(json.dump(data))
            file.truncate()
            file.close()
        except:
            print("Failed to log the results")
            
    def print_statistics(self):
        try:
            file = open('log.json', "a+")
            data = json.load(file)
            group_with_best_name = data["group_with_best_name"]
            high_score = data["high_score"]
            most_typed_char = max(data["typed"].items(), key=operator.itemgetter(1))[0]
            print(f"Team with the best name: {group_with_best_name}")
            print(f"Highest score ever: {high_score}")
            print(f"Most typed character: {most_typed_char}")
            file.close()
        except:
            pass
        
    def main_loop(self, network_type):
        sock = ""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 0)) #let the os choose a port for me
            sock.listen(1)
            self.server_start_message(network_type)
            while True:
                self.pre_game(network_type, sock)
                self.game_time()
                self.game_over()
                self.log_statistics()
                self.print_statistics()
                self.close_all_connections()
                print("Game over, sending out offer requests...")
        except:
            print("\n\nServer closed. Bye!")
            try:
                sock.close()
            except:
                pass



# TODO implement try catches
server = Server()
server_type = input("Would you like to use the dev channel, test channel or localhost? (DEV/test/localhost)")

server_ip = 'eth2' if server_type.lower() == 'test' else 'localhost' if server_type.lower() == 'localhost' else 'eth1'
server.main_loop(get_if_addr(server_ip))