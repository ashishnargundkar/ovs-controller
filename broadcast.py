import time
import select
import socket
import signal
import threading

from broadcast_config import *


server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((MY_IP_ADDR, SDN_COMM_PORT))
server_socket.listen(5)

bcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
bcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
bcast_socket.connect((BCAST_ADDR, SDN_COMM_PORT))

sockets = [server_socket]

keep_serving = True
keep_sending = True


def stop_activity():
    keep_serving = False
    keep_sending = False


signal.signal(signal.SIGINT, stop_activity)
signal.signal(signal.SIGTERM, stop_activity)


def server_loop():
    print "Entering server loop..."

    while keep_serving:
        socs_to_read, _1, _2 = select.select(sockets, list(), list())

        for sock in socs_to_read:
            if sock is server_socket:
                client_socket, client_addrinfo = server_socket.accept()
                sockets.append(client_socket)
                print "Accepted a new connection from" \
                    "{}".format(client_addrinfo)
            else:
                data, sender = client_socket.recvfrom(1024)
                print "Received data \"{}\" from \"{}\"".format(data, sender)

    print "Exited server loop"


def do_broadcast():
    print "Entering broadcasting loop..."

    while keep_sending:
        bcast_socket.sendall("BCAST_MSG from {}".format(MY_IP_ADDR))
        print "Sent broadcast message"
        time.sleep(SEND_SLEEP)

    print "Exited broadcasting loop"


if __name__ == "__main__":
    server_t = threading.Thread(target=server_loop)
    sender_t = threading.Thread(target=do_broadcast)

    server_t.start()
    sender_t.start()

    server_t.join()
    sender_t.join()
