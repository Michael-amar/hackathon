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
TIMER_LENGTH = 10 #10 seconds
MAGIC_COOKIE = 0xfeedbeef
MESSAGE_TYPE = 0x2
NUMBER_OF_TEAMS = 2
UDP_PORT = 13117
INTERVAL = 1
BUFFER_SIZE = 4096
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
    next(color)
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

    def server_start_message(self, ip):
        actual_ip = '127.0.0.1' if ip == '0.0.0.0' else ip
        nice_print(f"Server started, listerning on IP address {actual_ip}\n")

    def get_game_start_message(self):
        welcome = "Welcome to Keyboard Spamming Battle Royale.\n"
        group_announcement = ""
        for i in range(1, NUMBER_OF_TEAMS + 1):
            group_announcement += f"Group {i}:\n==\n"
            for p in self.players_sockets:
                if p.get_team() == i:
                    group_announcement += p.get_name()
                    group_announcement += "\n"
            group_announcement += "\n"
        game_start_accounement = "Start pressing keys on your keyboard as fast as you can!"
        return welcome + group_announcement + game_start_accounement

    def offer(self, network_type, tcp_sock):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = struct.pack('=IbH', MAGIC_COOKIE, MESSAGE_TYPE, tcp_sock.getsockname()[1]) #getsockname[1] gets the port
        # nice_print(str(message))
        # Endlessly send a broadcast every @interval seconds
        broadcast_ip = str(ipaddress.ip_network(network_type + '/16', False).broadcast_address)
        nice_print("Broadcasting on " + broadcast_ip)
        nice_print("Registration ends in:")
        for i in range(1, TIMER_LENGTH + 1):
            sock.sendto(message, (broadcast_ip, UDP_PORT))
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
                    if not new_player_name:
                        break
                    if "\n" not in new_player_name:
                        continue
                    new_player_name = new_player_name[:new_player_name.index("\n")] # remove the \n
                    should_exit = True
                new_player = Player(conn, new_player_name)
                self.players_sockets.append(new_player) # the internet says append is threadsafe
                nice_print(new_player_name + " joined the fight!")
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
        win_message = f"Game over!\nGroup 1 typed in {scores[0]}. Group 2 typed in {scores[1]} characters.\n"
        if winners == -1:
            win_message += "Its a tie!"
        else:
            win_message += f"Group {winners + 1} wins!\n\nGG all, and congratulations to the winners:\n==\n{winners_names}"
        nice_print (win_message)
        self.send_win(win_message)

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
        self.offer(network_type, sock)
        self.should_stop_looking = True

    def client_thread(self, player, message):
        try:
            conn = player.get_sock()
            conn.setblocking(0)
            conn.recv(BUFFER_SIZE) #clear the buffer to stop cheaters!
            conn.setblocking(1) 
            conn.sendall(message.encode())
            typed = ""
            while not self.should_stop_playing:
                typed = (conn.recv(BUFFER_SIZE)).decode()
                if not self.should_stop_playing:
                    nice_print(f"received {typed} from {player.get_name()}")
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
        nice_print("The game started! It will end in:")
        for i in range (1, TIMER_LENGTH + 1):
            nice_print(TIMER_LENGTH - i)
            time.sleep(1)
        self.should_stop_playing = True


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
        high_score = 0
        try:
            file = open('log.json', "a+")
            data = {}
            try:
                data = json.load(file)
            except:
                data = self.get_initial_json()
            for player in self.players_sockets:
                typed += player.get_typed()
                high_score = max(len(player.get_typed()), high_score)
            for c in typed:
                data["typed"][c] += 1
            data["high_score"] = max(high_score, data["high_score"])
            data["group_with_best_name"] = random.choice([(random.choice(self.players_sockets).get_name())] + [data["group_with_best_name"]])
            file.seek(0)
            file.write(json.dump(data))
            file.truncate()
            file.close()
        except:
            nice_print("Failed to log the results")
            
    def print_statistics(self):
        try:
            file = open('log.json', "a+")
            data = json.load(file)
            group_with_best_name = data["group_with_best_name"]
            high_score = data["high_score"]
            most_typed_char = max(data["typed"].items(), key=operator.itemgetter(1))[0]
            nice_print(f"Team with the best name: {group_with_best_name}")
            nice_print(f"Highest score ever for a single team: {high_score}")
            nice_print(f"Most typed character: {most_typed_char}")
            file.close()
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
                    nice_print("Game over, sending out offer requests...")
                self.close_all_connections()
        except:
            nice_print("\n\nServer closed. GG G2G")
            try:
                sock.close()
            except:
                pass



# TODO fix the broadcast
server = Server()
server_type = input("Would you like to use the dev channel or test channel? (DEV/test)")

server_ip = 'eth2' if server_type.lower() == 'test' else 'eth1'
# nice_print(get_if_addr(server_ip))
server.main_loop(get_if_addr(server_ip))