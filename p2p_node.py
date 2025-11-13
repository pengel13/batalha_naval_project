import socket
import threading
import time


class P2PNode:
    UDP_PORT = 5000
    TCP_PORT = 5001
    BROADCAST_ADDR = "<broadcast>"
    MSG_CONECTANDO = "Conectando"

    def __init__(self, callback_queue):
        self.participantes = set()
        self.lock = threading.Lock()
        self.running = True
        self.MEU_IP = self._get_meu_ip_local()

        self.callback_queue = callback_queue

        with self.lock:
            self.participantes.add(self.MEU_IP)

    def _get_meu_ip_local(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    def _parse_lista_ips(self, message_body):
        ips_recebidos = []
        try:
            if len(message_body) <= 2:
                return []
            ips_str_limpa = message_body[1:-1]
            ips_brutos = ips_str_limpa.split(",")
            for ip_bruto in ips_brutos:
                ip_limpo = ip_bruto.strip().strip("'")
                if ip_limpo:
                    ips_recebidos.append(ip_limpo)
            return ips_recebidos
        except:
            return []

    def _enviar_tcp(self, mensagem, ip):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_tcp_out:
                s_tcp_out.settimeout(2.0)
                s_tcp_out.connect((ip, self.TCP_PORT))
                s_tcp_out.sendall(mensagem.encode("utf-8"))
        except socket.error as e:
            self.callback_queue.put(("erro_conexao", ip))

    def _enviar_udp(self, mensagem, ip):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s_udp_out:
                s_udp_out.sendto(mensagem.encode("utf-8"), (ip, self.UDP_PORT))
        except Exception:
            pass

    def start(self):
        print(f"[REDE] Iniciando listeners... Meu IP: {self.MEU_IP}")
        threading.Thread(target=self._udp_listener, daemon=True).start()
        threading.Thread(target=self._tcp_listener, daemon=True).start()
        time.sleep(1)

    def stop(self):
        print("[REDE] Encerrando... Avisando participantes.")
        self.running = False
        self.broadcast_udp("saindo")

    def broadcast_udp(self, mensagem):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s_udp_bcast:
                s_udp_bcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s_udp_bcast.sendto(
                    mensagem.encode("utf-8"), (self.BROADCAST_ADDR, self.UDP_PORT)
                )
        except Exception as e:
            print(f"[BROADCAST ERRO] {e}")

    def enviar_tiro(self, ip_alvo, x, y):
        msg = f"shot:{x},{y}"
        self._enviar_udp(msg, ip_alvo)

    def enviar_resposta_tcp(self, ip_alvo, mensagem):
        threading.Thread(target=self._enviar_tcp, args=(mensagem, ip_alvo)).start()

    def get_participantes(self):
        with self.lock:
            return list(p for p in self.participantes if p != self.MEU_IP)

    def _udp_listener(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s_udp_in:
                s_udp_in.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s_udp_in.bind(("", self.UDP_PORT))
                s_udp_in.settimeout(1.0)

                while self.running:
                    try:
                        data, addr = s_udp_in.recvfrom(1024)
                        mensagem = data.decode("utf-8")
                        ip_origem = addr[0]
                        if ip_origem == self.MEU_IP:
                            continue

                        if mensagem == self.MSG_CONECTANDO:
                            novo = False
                            with self.lock:
                                if ip_origem not in self.participantes:
                                    self.participantes.add(ip_origem)
                                    novo = True
                                lista_atual = list(self.participantes)
                            if novo:
                                self.callback_queue.put(
                                    ("novo_participante", ip_origem)
                                )
                            self.enviar_resposta_tcp(
                                ip_origem, f"participantes: {lista_atual}"
                            )

                        elif mensagem.startswith("shot:"):
                            try:
                                coords = mensagem.split(":", 1)[1]
                                x, y = map(int, coords.split(","))
                                self.callback_queue.put(
                                    ("tiro_recebido", ip_origem, x, y)
                                )
                            except:
                                pass

                        elif mensagem == "lost":
                            self.callback_queue.put(("jogador_perdeu", ip_origem))

                        elif mensagem == "saindo":
                            with self.lock:
                                self.participantes.discard(ip_origem)
                            self.callback_queue.put(("jogador_saiu", ip_origem))

                    except socket.timeout:
                        continue
                    except Exception:
                        pass
        except Exception as e:
            if self.running:
                print(f"[ERRO FATAL UDP] {e}")

    def _handle_tcp_client(self, conn, addr):
        ip_origem = addr[0]
        try:
            with conn:
                data = conn.recv(1024)
                if not data:
                    return
                mensagem = data.decode("utf-8")

                if mensagem.startswith("participantes:"):
                    list_str = mensagem.split(":", 1)[1].strip()
                    ips_recebidos = self._parse_lista_ips(list_str)
                    novos_encontrados = []
                    with self.lock:
                        for ip in ips_recebidos:
                            if ip != self.MEU_IP and ip not in self.participantes:
                                self.participantes.add(ip)
                                novos_encontrados.append(ip)
                    if novos_encontrados:
                        self.callback_queue.put(
                            ("lista_participantes", novos_encontrados)
                        )

                elif mensagem in ["hit", "destroyed"]:
                    self.callback_queue.put(("resultado_tiro", ip_origem, mensagem))

        except socket.error:
            pass

    def _tcp_listener(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_tcp_in:
                s_tcp_in.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s_tcp_in.bind(("", self.TCP_PORT))
                s_tcp_in.listen(5)
                s_tcp_in.settimeout(1.0)

                while self.running:
                    try:
                        conn, addr = s_tcp_in.accept()
                        threading.Thread(
                            target=self._handle_tcp_client,
                            args=(conn, addr),
                            daemon=True,
                        ).start()
                    except socket.timeout:
                        continue
        except Exception as e:
            if self.running:
                print(f"[ERRO FATAL TCP] {e}")
