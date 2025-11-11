# udp_server.py
# UDP listener (port 5000), broadcast client helper

import socket
import threading

UDP_PORT = 5000
BUFFER_SIZE = 4096


class UDPServer(threading.Thread):
    def __init__(self, handler_callback):
        super().__init__(daemon=True)
        self.handler = handler_callback  # function(addr, message, sock)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind to all interfaces on UDP_PORT
        self.sock.bind(("", UDP_PORT))
        self.running = True

    def run(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(BUFFER_SIZE)
                message = data.decode("utf-8", errors="ignore")
                threading.Thread(
                    target=self.handler, args=(addr, message, self.sock), daemon=True
                ).start()
            except Exception as e:
                print(f"[UDP Server] recv error: {e}")

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass


def udp_broadcast(message: str, port: int = UDP_PORT):
    """Send a broadcast UDP message to the network"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(message.encode("utf-8"), ("<broadcast>", port))
        s.close()
    except Exception as e:
        print(f"[udp_broadcast] error: {e}")


def udp_send_to(ip: str, message: str, port: int = UDP_PORT):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(message.encode("utf-8"), (ip, port))
        s.close()
    except Exception as e:
        print(f"[udp_send_to] error sending to {ip}:{e}")
