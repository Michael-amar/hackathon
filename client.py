import socket
import sys
import asyncore
from scapy.all import get_if_addr
import select
import termios
import tty

BroadcastlistenPort = 13117
TeamName = "Team A"
messageSize = 7

def get_network_ip():
    while True:
        try:
            network = int (input("press 1 for eth1 or 2 for eth2:"))
            if network ==1 or network ==2 :
                network = get_if_addr("eth"+str(network))
                break
            else:
                print("invalid input")
        except:
            print("invalid input")
    return network

def get_offers():
    udpSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) #check for problems with AF_INET
    udpSocket.bind(('',BroadcastlistenPort)) #check for problems with ''
    print("Client started, listening for offer requests...")
    while True: #wait for offers
        message, (serverIp,_) = udpSocket.recvfrom(2048) # check for problems with 2048
        print((message.hex()))
        if len(message)==messageSize and message[:5] == b'\xfe\xed\xbe\xef\x02':
            serverTcpPort = int.from_bytes(message[5:],"big")
            break
    udpSocket.close()
    return (serverIp,serverTcpPort)

class GameSession(asyncore.dispatcher):

    def __init__(self,serverIp,serverTcpPort):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        # while True:
        try:
            self.connect((serverIp,serverTcpPort))
            print("connected")
            self.buffer=""
            print("initialized buffer")
            self.send(TeamName+"\n")
            print("sent team name")
            # break
        except:
            e = sys.exc_info()[0]
            print(e)
            print("failed to connect to server")

    def handle_connect(self):
        pass

    def pressed_key(self):
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    def get_char(self):
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            c = sys.stdin.read(1)
            return c
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            return ""

    def handle_close(self):
        self.close()
    
    def handle_read(self):
        print (self.recv(8192))

    def handle_write(self):
        self.buffer += self.get_char()
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]
    
    def writable(self):
        return self.pressed_key()

    def start_game(self):
        asyncore.loop() #check set timeout for 10~12 seconds?

# main loop
my_ip = get_network_ip()
while True:
    (serverIp,serverTcpPort) = get_offers()
    gameSession = GameSession(serverIp,serverTcpPort)
    gameSession.start_game()








# While True:

# print("server address:" + str(serverAddress))
# print("server port:" + str(serverTcpPort))