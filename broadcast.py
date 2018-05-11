import time
import socket
import signal
import threading


BCAST_ADDR = "10.244.39.255"
SDN_COMM_PORT = 9898
SEND_SLEEP = 10  # in seconds

bcast_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
bcast_socket.bind((BCAST_ADDR, SDN_COMM_PORT))

keep_listening = True
keep_sending = True


def stop_listening():
    keep_listening = False


def stop_sending():
    keep_sending = False


signal.signal(signal.SIGINT, stop_listening)
signal.signal(signal.SIGTERM, stop_listening)


def socket_listener():
    while keep_listening:
        data, sender = bcast_socket.recvfrom(1024)
        print "Received data \"{}\" from \"{}\"".format(data, sender)


def do_broadcast():
    while keep_sending:
        bcast_socket.sendto("BCAST_MSG from {}".format(socket.gethostname()),
                            BCAST_ADDR)
        time.sleep(SEND_SLEEP)


if __name__ == "__main__":
    sender_t = threading.Thread(target=do_broadcast)
    receiver_t = threading.Thread(target=socket_listener)

    sender_t.start()
    receiver_t.start()

    sender_t.join()
    receiver_t.join()
