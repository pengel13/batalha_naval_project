# tcp_server.py
# TCP server on port 5001, also TCP client helper (connect & send single message)

import socket
import threading

TCP_PORT = 5001
BUFFER_SIZE = 4096


class TCPServer(threading.Thread):
    def __init__(self, handler_callback):
        super().__init__(daemon=True)
        self.handler = handler_callback  # function(client_addr, message, sock)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", TCP_PORT))
        self.sock.listen(5)
        self.running = True

    def run(self):
        while self.running:
            try:
                conn, addr = self.sock.accept()
                threading.Thread(
                    target=self._handle_conn, args=(conn, addr), daemon=True
                ).start()
            except Exception as e:
                print(f"[TCP Server] accept error: {e}")

    def _handle_conn(self, conn: socket.socket, addr):
        try:
            data = b""
            while True:
                chunk = conn.recv(BUFFER_SIZE)
                if not chunk:
                    break
                data += chunk
                if len(chunk) < BUFFER_SIZE:
                    break
            message = data.decode("utf-8", errors="ignore")
            # callback
            self.handler(addr, message, conn)
        except Exception as e:
            print(f"[TCP Server] error handling {addr}: {e}")
        finally:
            try:
                conn.close()
            except:
                pass

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass


def tcp_send(ip: str, message: str, port: int = TCP_PORT, timeout=2):
    """Send a TCP message (connect, send, close). Returns True on success"""
    try:
        with socket.create_connection((ip, port), timeout=timeout) as s:
            s.sendall(message.encode("utf-8"))
        return True
    except Exception as e:
        # print or ignore
        # print(f"[tcp_send] to {ip}:{port} failed: {e}")
        return False
