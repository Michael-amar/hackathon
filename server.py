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
UDP_PORT = 13119
INTERVAL = 1
BUFFER_SIZE = 4096
TINY_INTERVAL = 0.15
MASK = 16
SURPRISE = "\n             ___________\n            '._==_==_=_.'\n            .-\:      /-.\n           | (|:.     |) |\n            '-|:.     |-'\n              \::.    /\n               '::. .'\n                 ) (\n               _.' '._\n               `*****`"
LOGO = " _____ _       _     _   _ \n|  ___(_) __ _| |__ | |_| |\n| |_  | |/ _` | '_ \| __| |\n|  _| | | (_| | | | | |_|_|\n|_|   |_|\__, |_| |_|\__(_)\n         |___/             "
# End of global final variables

#COLORS:
RED = "\033[38;5;1m"
ORANGE = "\033[38;5;208m"
YELLOW = "\033[38;5;11m"
GREEN = "\033[38;5;10m"
BLUE = "\033[38;5;27m"
PURPLE = "\033[38;5;129m"
GROUP_1 = "\033[38;5;1m"
GROUP_2 = "\033[38;5;27m"
SERVER_MESSAGE_COLOR = "\033[38;5;51m"

# color generator, for some fun colors in the server!
def color_gen():
    while True:
        print(RED,end='') #red
        sys.stdout.flush()
        yield 
        print(ORANGE,end='') #orange
        sys.stdout.flush()
        yield
        print(YELLOW,end='') #yellow
        sys.stdout.flush()
        yield
        print(GREEN,end='') #green
        sys.stdout.flush()
        yield
        print(BLUE,end='') #blue
        sys.stdout.flush()
        yield
        print(PURPLE,end='') #purple
        sys.stdout.flush()
        yield

color = color_gen() 
def nice_print(to_print): #prints with the colors
    try:
        next(color)
    except:
        pass
    print(to_print)

def reset_color():
    print("\033[0m")

# The players class, to keep track of their sockets and typed words

class Player:
    
    def __init__(self, sock, name):
        self.sock = sock #connection socket of the player
        self.typed = "" #what the player typed so far
        self.name = name #team name
        self.team = random.randint(1, 2) #team of the player

    def get_sock(self):
        return self.sock

    def get_typed(self):
        return self.typed
    
    def set_team(self, team):
        self.team = team
    
    def add_typed(self, typed): #log the stuff the player writes
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
        #flags for thread termination:
        self.should_stop_looking = False 
        self.should_stop_playing = False
        #data for statistics
        self.data = {}

    #Printing the server initiation
    def server_start_message(self, ip):
        actual_ip = '127.0.0.1' if ip == '0.0.0.0' else ip
        nice_print(f"Server started, listerning on IP address {actual_ip}\n")

    #generate the game message
    def get_game_start_message(self):
        group_announcement = ""
        for i in range(1, NUMBER_OF_TEAMS + 1): #accumulate the teams by groups
            group_announcement += f"Group {i}:\n==\n"
            for p in self.players_sockets:
                if p.get_team() == i:
                    group_announcement += p.get_name()
                    group_announcement += "\n"
            group_announcement += "\n"
        game_start_accounement = "Start pressing keys on your keyboard as fast as you can!"
        return LOGO + "\n" + group_announcement + game_start_accounement

    #send the offer
    def offer(self, network_type, tcp_sock):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        #message is little endian
        message = struct.pack('>IbH', MAGIC_COOKIE, MESSAGE_TYPE, tcp_sock.getsockname()[1]) #getsockname[1] gets the port
        
        # get the broadcast ip from the ip+mask
        broadcast_ip = str(ipaddress.ip_network(network_type + '/' + str(MASK), False).broadcast_address)
        
        nice_print("Broadcasting on " + broadcast_ip)
        nice_print("Registration ends in:")

        # send every INTERVAL seconds, for TIMER_LENGTH seconds
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
                    #get name from the player:
                    new_player_name += (conn.recv(BUFFER_SIZE)).decode()

                    if "\n" not in new_player_name:
                        if not new_player_name == "": 
                            continue
                        else:
                            time.sleep(TINY_INTERVAL)
                    #remove the \n from the end
                    new_player_name = new_player_name[:new_player_name.index("\n")]
                    should_exit = True
            if not self.should_stop_looking:
                #append the player to the player list:
                new_player = Player(conn, new_player_name)
                self.players_sockets.append(new_player) # the internet says append is threadsafe
                nice_print(new_player_name + " joined the fight!")
            else:
                conn.close()
        except:
            try:
                conn.close()
            except:
                pass


    def connect_with_client(self, sock):
        try:
            while not self.should_stop_looking:
                conn, addr = sock.accept()
                self.connections_to_close.append(conn)
                # connect to a player after passing the accept
                connect_with_client_thread = threading.Thread(target = self.connect_with_specific_client, args =(conn, addr,), daemon = True)
                connect_with_client_thread.start()
        except:
            pass
    
    #senc the win message to all players
    def send_win(self, message):
        for p in self.players_sockets:
            try:
                conn = p.get_sock()
                conn.sendall(message.encode())
            except:
                pass

    # game over section
    def game_over(self):
        if not self.players_sockets: #if no players connected
            nice_print (f"No players played in this round\n\n")
            return
        scores = [0,0]

        #accumulate the length of all the typed characters, per group
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

        #handle the send and generation of win message:
        for p in self.players_sockets:
            if p.get_team() - 1 == winners:
                winners_names += p.get_name() + "\n"
        win_message = f"{SURPRISE}\nGame over!\nGroup 1 typed in {scores[0]}. Group 2 typed in {scores[1]} characters.\n"
        if winners == -1:
            win_message += "Its a tie!"
        else:
            win_message += f"Group {winners + 1} wins!\n\nGG all, winner winner chicken dinner for:\n==\n{winners_names}"
        nice_print (win_message)
        self.send_win(SERVER_MESSAGE_COLOR + win_message)

    def close_all_connections(self):
        #close all the connections
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
        #delete all the players from memory
        self.connections_to_close = []
        self.players_sockets = []


    def pre_game(self, network_type, sock):
        self.should_stop_looking = False
        #prepare a tcp connection for the clients to connect to
        connect_with_client_thread = threading.Thread(target = self.connect_with_client, args =(sock,), daemon = True)
        connect_with_client_thread.start()
        #make sure the tcp socket has enough time to open before the server sends offers
        time.sleep(TINY_INTERVAL)
        self.offer(network_type, sock)
        self.should_stop_looking = True

    #get characters from client
    def client_thread(self, player, message):
        try:
            conn = player.get_sock()
            #send the game start message
            conn.sendall((SERVER_MESSAGE_COLOR + message).encode())
            typed = ""
            #pick a color for the team's prints, based on the group
            color_group = GROUP_1 if player.get_team() == 1 else GROUP_2
            while not self.should_stop_playing:
                #receive characters from the player, and if it is not a blank string then add it to the team and print that the team typed it
                typed = (conn.recv(BUFFER_SIZE)).decode()
                if not self.should_stop_playing:
                    if not typed == "":
                        nice_print(f"{color_group}received {typed} from {player.get_name()}")
                        player.add_typed(typed)
                    else:
                        time.sleep(TINY_INTERVAL)
        except:
            nice_print (f"{player.get_name()} disconnected. Don't worry, their score will still count.")

    def shuffle_teams(self):
        random.shuffle(self.players_sockets)
        i = 0
        for p in self.players_sockets:
            p.set_team((i % 2) + 1)
            i += 1

    #game session
    def game_time(self):
        self.should_stop_playing = False
        self.shuffle_teams()
        message = self.get_game_start_message()
        for player in self.players_sockets:
            #send message to each player, and receive data from them
            player_thread = threading.Thread(target = self.client_thread, args = (player,message,), daemon = True)
            player_thread.start()
        nice_print(f"{self.get_game_start_message()}\nThe game will end in:")
        #timer for the game to end
        for i in range (1, TIMER_LENGTH + 1):
            nice_print(TIMER_LENGTH - i)
            time.sleep(1)
        self.should_stop_playing = True

    #data initialization for statistics
    def initialize_data(self):
        typed = dict( (key, 0) for key in string.printable) # put 0 for each letter
        high_score = 0
        group_with_best_name = ""
        self.data = {}
        self.data["typed"] = typed
        self.data["high_score"] = high_score
        self.data["group_with_best_name"] = group_with_best_name

    #log current game to statistics
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
    
    #main game logic
    def main_loop(self, network_type):
        sock = ""
        try:
            #create a tcp socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 0)) #let the os choose a port for me
            sock.settimeout(TIMER_LENGTH)
            sock.listen(1)
            self.server_start_message(network_type)
            while True:
                #try to find players
                while (not self.players_sockets):
                    self.pre_game(network_type, sock)
                if self.players_sockets:
                    #self explanitory
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



#start of the program:
server = Server()
server_type = input("Would you like to use the dev channel or test channel? (DEV/test)")
server_ip = 'eth2' if server_type.lower() == 'test' else 'eth1'
#clear the terminal before the game:
os.system('cls' if os.name == 'nt' else 'clear')
#start of the program
server.main_loop(get_if_addr(server_ip))