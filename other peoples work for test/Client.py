import socket
import _thread
import threading
import time
from KeyBoardInput import KBHit

PORT = 7777
UDP_PORT = 37020
GAME_LENGTH = 10 # TODO change to 10 by requirement
MESSAGE_FORMAT = "utf-8"


def raw_input_with_timeout(prompt, connection):
    global user_thread_stop 
    kb = KBHit()
    print(prompt)
    while not user_thread_stop:
        if kb.kbhit():
            c = kb.getch()
            print(c)
            connection.sendall(bytes(c, MESSAGE_FORMAT))
    kb.set_normal_term()


clientUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
# Enable broadcasting mode
clientUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
clientUDP.bind(("", UDP_PORT))
print("Client started, listening for offer requests...")
data, addr = clientUDP.recvfrom(1024)
server_ip_address = addr[0]
print(f"Received offer from {server_ip_address}, attempting to connect...")

clientTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientTCP.connect((server_ip_address, PORT))
# remove this line after debug
msg = clientTCP.recv(1024)
print(msg.decode(MESSAGE_FORMAT))
clientTCP.sendall(bytes("The Tag Parsers\n", MESSAGE_FORMAT))

# welcome message from server
msg = clientTCP.recv(1024)
print(msg.decode(MESSAGE_FORMAT))
# start playing

user_thread_stop = False
user_data = []
thread = threading.Thread(target = raw_input_with_timeout, args=("Game started! smash the keyboard !!!", clientTCP))
thread.start()
time.sleep(GAME_LENGTH)
user_thread_stop = True
thread.join()
print("Job Finished")
# message from server that says who won and ETC

msg = clientTCP.recv(1024)
print(msg.decode(MESSAGE_FORMAT))
clientTCP.close()



