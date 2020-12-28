import socket
import sys
import asyncore
from scapy.all import get_if_addr

BroadcastlistenPort = 13117

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
        # print((message.hex()))
        if len(message)==7 and message[:5] == b'\xfe\xed\xbe\xef\x02':
            serverTcpPort = int.from_bytes(message[5:],"big")
            break
    udpSocket.close()
    return (serverIp,serverTcpPort)

class Game(asyncore.dispatcher):

    def __init__(self,serverIp,serverTcpPort):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                self.connect((serverIp,serverTcpPort))
                self.send("Team A\n")
                break
            except:
                    e = sys.exc_info()[0]
                    print(e)
                    print("failed to connect to server")
    
   def handle_connect(self):
        pass

    def handle_close(self):
        self.close()
    
    def handle_read(self):
        print self.recv(8192)

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]
    
    def writable(self):
        return len("".join(self.output_buffer)) > 0

    def start_game(self):
        while True:
            

    my_ip = get_network_ip()
    while True:
        (serverIp,serverTcpPort) = get_offers()
        tcpSocket = connect_to_server(serverIp,serverTcpPort)
        if tcpSocket != ():
            start_game(tcpSocket)







# While True:

# print("server address:" + str(serverAddress))
# print("server port:" + str(serverTcpPort))