import socket
import sys
import asyncore
from scapy.all import get_if_addr
import select
import termios
import tty
import struct
import time
import ipaddress

BroadcastlistenPort = 13117
TeamName = "DNAce"
formatMessageSize = 7
magicCookieBigEndian = b'\xfe\xed\xbe\xef'
magicCookeLittleEndian = b'\xef\xbe\xed\xfe'
offerType = b'\x02'
udpRcvWindow = 2048 
tcpRcvWindow = 2048
LittleEndian = "LittleEndian"
BigEndian = "BigEndian"

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

def reset_color():
    print("\033[0m",end="\n")
    sys.stdout.flush()

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

def move_to_single_char_mode():
    tty.setcbreak(sys.stdin.fileno())
    settings = termios.tcgetattr(sys.stdin)
    settings[3] = settings[3] | termios.ECHO
    termios.tcsetattr(sys.stdin,termios.TCSANOW,settings)

def disable_echo():
    settings = termios.tcgetattr(sys.stdin)
    settings[3] = settings[3] & ~termios.ECHO
    termios.tcsetattr(sys.stdin,termios.TCSANOW,settings)

def verify_msg_format(msg,mode):
    if len(msg) == formatMessageSize:
        if mode == LittleEndian:
            cookie,typ,_ = struct.unpack('<4sbH',msg)
            if (cookie == magicCookeLittleEndian) and (typ==int.from_bytes(offerType,"little")) :
                return True
        elif mode == BigEndian:
            cookie,typ,_ = struct.unpack('>4sbH',msg)
            if (cookie == magicCookieBigEndian) and (typ==int.from_bytes(offerType,"big")) :
                return True
    return False

def get_offers(ip):
    udpSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) #check for problems with AF_INET
    udpSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) #important line!!! allows to reuse the address
    udpSocket.bind((str(ipaddress.ip_network(ip + '/16', False).broadcast_address),BroadcastlistenPort))
    print("Client started, listening for offer requests...")
    while True: #wait for offers
        message, (serverIp,_) = udpSocket.recvfrom(udpRcvWindow) 
        if (verify_msg_format(message,LittleEndian)):
            _,_,serverTcpPort = struct.unpack('<4sbH',message)
            break
        elif (verify_msg_format(message,BigEndian)):
            _,_,serverTcpPort = struct.unpack('>4sbH',message)
            break
    udpSocket.close()
    return (serverIp,serverTcpPort)

class GameSession(asyncore.dispatcher):
    
    def __init__(self,serverIp,serverTcpPort):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.color = color_gen()
        failed_to_connect=False
        for i in range(0,3):
            try:
                self.connect((serverIp,serverTcpPort))
                break
            except:
                failed_to_connect = True
                self.socket.close()
                e = sys.exc_info()[0]
                print(e)
                print("failed to connect to server")
                raise
        if not failed_to_connect:
            print("connected, game starts in few seconds...")
            try:
                self.send((TeamName+"\n").encode())
            except:
                self.socket.close()
                raise
            self.buffer=bytes()
            self.input_buffer = bytes() 


    def handle_connect(self):
        move_to_single_char_mode()

    def pressed_key(self):
        return select.select([sys.stdin,],[],[],0.0)[0]

    def get_char(self):           
        return sys.stdin.read(1)  

    def handle_close(self):
        self.close()
    
    def handle_read(self):
        print(self.recv(tcpRcvWindow).decode())
        sys.stdout.flush()
        reset_color()

    def handle_write(self):
        c = self.get_char()
        next(self.color)
        self.buffer += c.encode()
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

    def writable(self):
        return self.pressed_key()

    def start_game(self):
        asyncore.loop(timeout=0.01,use_poll=True,count=2000)

old_settings = termios.tcgetattr(sys.stdin)
ip = get_network_ip()
disable_echo()
while True:
    serverIp,serverTcpPort = get_offers(ip)
    try:
        gameSession = GameSession(serverIp,serverTcpPort)
        failed_to_connect = False
    except:
        print("failed to connect to server")
        failed_to_connect = True
    if not failed_to_connect:
        try:
            gameSession.start_game()
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            gameSession.close()
            reset_color()
            print("Server disconnected, listening for offer requests...")
            disable_echo()