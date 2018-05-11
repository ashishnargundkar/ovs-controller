import time
import socket
import signal
import threading

from broadcast_config import *


server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((BCAST_ADDR, SDN_COMM_PORT))
server_socket.setblocking(0)
# server_socket.listen(5)

bcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
bcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# bcast_socket.connect((BCAST_ADDR, SDN_COMM_PORT))

sockets = [server_socket]

keep_serving = True
keep_sending = True


def stop_activity(signum, frame):
    global keep_serving
    global keep_sending

    print "Stopping activities..."

    keep_serving = False
    keep_sending = False


signal.signal(signal.SIGINT, stop_activity)
signal.signal(signal.SIGTERM, stop_activity)


def server_loop():
    global keep_serving

    print "Entering server loop..."

    while keep_serving:
        try:
            data, sender = server_socket.recvfrom(1024)
            print "Received data \"{}\" from \"{}\"".format(data, sender)
        except socket.error:
            print "Found no data to receive"
            time.sleep(1)

    print "Exited server loop"


def do_broadcast():
    global keep_sending

    print "Entering broadcasting loop..."

    while keep_sending:
        # bcast_socket.sendall("BCAST_MSG from {}".format(MY_IP_ADDR))
        bcast_socket.sendto("BCAST_MSG from {}".format(MY_IP_ADDR),
                            (BCAST_ADDR, SDN_COMM_PORT))
        print "Sent broadcast message"
        time.sleep(SEND_SLEEP)

    print "Exited broadcasting loop"


if __name__ == "__main__":
    server_t = threading.Thread(target=server_loop)
    sender_t = threading.Thread(target=do_broadcast)

    server_t.start()
    sender_t.start()

    # Required for main thread to be able to listen to signals
    while keep_serving or keep_sending:
        pass

    server_t.join()
    sender_t.join()
