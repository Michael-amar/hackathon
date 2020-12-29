import sys
import socket
import struct

MAGIC_COOKIE = 0xfeedbeef
MESSAGE_TYPE = 0x2
UDP_PORT = 15183
BUFFER_SIZE = 4096
TCP_PORT = 12000

def bigEndianOffer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    message = struct.pack('>IbH', MAGIC_COOKIE, MESSAGE_TYPE, TCP_PORT) 
    print (message)
    print("sent message:" + str(message))
    sock.sendto(message, ('127.0.0.1', UDP_PORT))
    print("Sent broadcast msg")
    sock.close()

def littleEndianOffer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    message = struct.pack('<IbH', MAGIC_COOKIE, MESSAGE_TYPE, TCP_PORT,) 
    print("sent message:" + str(message))
    sock.sendto(message, ('127.0.0.1', UDP_PORT))
    print("Sent broadcast msg")
    sock.close()




message = struct.pack('=IbH', MAGIC_COOKIE, MESSAGE_TYPE, TCP_PORT) 
print ("cookie:" + str(message[:4]))
print("type:" + str(message[4:5]))
print("port:" + str(message[5:]))
# bigEndianOffer()
# serverSocket = socket.socket(socket.AF_INET ,socket.SOCK_STREAM)
# serverSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
# serverSocket.bind(('127.0.0.1',TCP_PORT))
# serverSocket.listen(1)
# i = 1
# print("waiting for connection")
# connectionSocket,addr = serverSocket.accept()
# print("Connection established")
# while True:
#     msg = connectionSocket.recv(1024)
#     print(msg.decode())
#     if i/10 == 0 :
#         connectionSocket.send("Recieved another 10 messages\n".encode())
#     i+=1

