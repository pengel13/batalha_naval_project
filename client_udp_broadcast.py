# client.py
# Start UDP and TCP servers, UI (pygame), periodic shots every 10s,
# handle join/leave/shot/hit/destroyed/lost/saindo
# Run: python client.py

import threading
import socket
import time
import random
import pygame
from grid import Grid
from server_udp import UDPServer, udp_broadcast, udp_send_to
from server_tcp import TCPServer, tcp_send

LOCAL_UDP_PORT = 5000
LOCAL_TCP_PORT = 5001

SEND_INTERVAL = 10  # seconds for sending shots


class PeerGame:
    def __init__(self):
        # participants as set of ip strings
        self.participants = set()
        self.participants_lock = threading.Lock()
        # stats
        self.hits_given = {}  # ip -> bool (True if hit at least once)
        self.hits_count_per_ip = {}  # how many times hit them (for log)
        self.times_been_hit = 0

        # grid
        self.grid = Grid()

        # Pergunta ao jogador se prefere manual ou automático
        try:
            choice = input('Deseja posicionar os barcos manualmente? (S/N): ').strip().lower()
        except Exception:
            # em contextos sem stdin, cai para automático
            choice = 'n'
        if choice == 's':
            self.grid.place_ships_manual()
        else:
            self.grid.place_ships_random()

        # network
        self.udp_server = UDPServer(self.handle_udp)
        self.tcp_server = TCPServer(self.handle_tcp)

        # flags
        self.running = True
        self.game_lost_announced = False

        # local ip
        self.local_ip = self._get_local_ip()

        # log lines
        self.log = []
        self.log_lock = threading.Lock()

    def _get_local_ip(self):
        # get outbound IP without external requests
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    def start(self):
        print(f"[Game] Local IP: {self.local_ip}")
        self.udp_server.start()
        self.tcp_server.start()
        time.sleep(0.2)
        # broadcast connecting
        self.log_msg("Broadcasting 'Conectando'")
        udp_broadcast("Conectando")
        # start shooter thread
        threading.Thread(target=self._periodic_shots, daemon=True).start()

    def stop(self):
        # send saindo
        self.log_msg("Enviando 'saindo' para participantes")
        with self.participants_lock:
            for p in list(self.participants):
                udp_send_to(p, "saindo")
        self.running = False
        try:
            self.udp_server.stop()
            self.tcp_server.stop()
        except:
            pass
        self.print_score()

    def log_msg(self, text):
        ts = time.strftime("%H:%M:%S")
        with self.log_lock:
            self.log.append(f"[{ts}] {text}")
            print(self.log[-1])

    def handle_udp(self, addr, message, sock):
        ip = addr[0]
        msg = message.strip()
        self.log_msg(f"UDP from {ip}: {msg}")

        if msg == "Conectando":
            # add origin and reply via TCP with participants list
            added = False
            with self.participants_lock:
                if ip != self.local_ip and ip not in self.participants:
                    self.participants.add(ip)
                    added = True
            if added:
                self.log_msg(f"Adicionado participante: {ip}")
                self.print_participants()
            # reply with TCP sending participants list
            with self.participants_lock:
                plist = list(self.participants) + [self.local_ip]
            # ensure unique and sorted-ish
            plist = list(dict.fromkeys(plist))
            msgtcp = f"participantes: {plist}"
            success = tcp_send(ip, msgtcp)
            self.log_msg(
                f"Enviado participantes via TCP para {ip} ({'ok' if success else 'fail'})"
            )
            return

        if msg.startswith("shot:"):
            try:
                coords = msg.split(":", 1)[1]
                x_str, y_str = coords.split(",")
                x = int(x_str)
                y = int(y_str)
            except:
                return
            res, ship_id = self.grid.receive_shot(x, y)
            if res == "miss":
                self.log_msg(f"Shot miss at ({x},{y}) from {ip}")
                return
            elif res == "hit":
                self.log_msg(f"Shot HIT at ({x},{y}) from {ip}")
                # reply TCP "hit"
                tcp_send(ip, "hit")
                # record been hit
                self.times_been_hit += 1
            elif res == "destroyed":
                self.log_msg(f"Ship DESTROYED by {ip} at ({x},{y})")
                tcp_send(ip, "destroyed")
                self.times_been_hit += 1

            if self.grid.all_ships_destroyed() and not self.game_lost_announced:
                self.log_msg("Todas embarcações destruídas. Enviando 'lost' via UDP")
                with self.participants_lock:
                    for p in list(self.participants):
                        udp_send_to(p, "lost")
                self.game_lost_announced = True
            return

        if msg == "lost":
            # someone lost; we might want to stop shooting them
            with self.participants_lock:
                if ip in self.participants:
                    self.participants.remove(ip)
                    self.log_msg(f"Participante {ip} perdeu e foi removido")
                    self.print_participants()
            return

        if msg == "saindo":
            with self.participants_lock:
                if ip in self.participants:
                    self.participants.remove(ip)
                    self.log_msg(f"Participante {ip} saiu (saindo).")
                    self.print_participants()
            return

    def handle_tcp(self, addr, message, conn):
        ip = addr[0]
        msg = message.strip()
        self.log_msg(f"TCP from {ip}: {msg}")
        if msg.startswith("participantes:"):
            # parse list
            try:
                # message like: participantes: ['ip1','ip2']
                right = msg.split(":", 1)[1].strip()
                # naive eval but safe enough for this academic exercise
                plist = eval(right)
                if isinstance(plist, (list, tuple)):
                    with self.participants_lock:
                        for p in plist:
                            if p != self.local_ip and p not in self.participants:
                                self.participants.add(p)
                                self.log_msg(
                                    f"Adicionado participante (via lista): {p}"
                                )
                    self.print_participants()
            except Exception as e:
                self.log_msg(f"Erro parse participantes: {e}")
            return

        if msg == "hit":
            # a peer confirmed we hit them; track unique hits
            with self.participants_lock:
                self.hits_given.setdefault(ip, False)
                if not self.hits_given[ip]:
                    self.hits_given[ip] = True
                    self.log_msg(f"Confirmado: hit em {ip} (contabilizado)")
                else:
                    self.log_msg(f"Confirmado: hit em {ip} (já contabilizado antes)")
                self.hits_count_per_ip[ip] = self.hits_count_per_ip.get(ip, 0) + 1
            return

        if msg == "destroyed":
            with self.participants_lock:
                self.hits_given.setdefault(ip, False)
                if not self.hits_given[ip]:
                    self.hits_given[ip] = True
                self.hits_count_per_ip[ip] = self.hits_count_per_ip.get(ip, 0) + 1
            self.log_msg(f"Confirmado: destroyed reported by {ip}")
            return

    def print_participants(self):
        with self.participants_lock:
            self.log_msg(f"Participantes: {list(self.participants)}")

    def _periodic_shots(self):
        while self.running:
            # sleep SEND_INTERVAL (but jitter a little so not all at same time)
            jitter = random.random() * 2 - 1
            time.sleep(max(1, SEND_INTERVAL + jitter))
            # pick a target from participants
            with self.participants_lock:
                targets = list(self.participants)
            if not targets:
                self.log_msg("Nenhum participante para atirar.")
                continue
            for t in targets:
                # random shot coordinates 0..9
                x = random.randint(0, 9)
                y = random.randint(0, 9)
                msg = f"shot:{x},{y}"
                self.log_msg(f"Enviando UDP '{msg}' para {t}")
                udp_send_to(t, msg)
            # loop continues

    def print_score(self):
        with self.participants_lock:
            players_hit_count = sum(1 for v in self.hits_given.values() if v)
            times_hit = self.times_been_hit
            final_score = players_hit_count - times_hit
            print("=== SCORE ===")
            print(f"Players atingidos (únicos): {players_hit_count}")
            print(f"Vezes que fui atingido: {times_hit}")
            print(f"Score final = {players_hit_count} - {times_hit} = {final_score}")
            print("Detalhe por jogador (hits dados):")
            for ip, cnt in self.hits_count_per_ip.items():
                print(f"  {ip}: {cnt}")
            print("================")


def run_pygame_ui(game: PeerGame):
    pygame.init()
    size = (600, 500)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Batalha Naval P2P")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 20)
    grid_size = 300
    cell = grid_size // 10
    grid_origin = (20, 20)

    while game.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    game.running = False

        screen.fill((30, 30, 30))
        # draw grid
        gx, gy = grid_origin
        # draw cells
        for y in range(10):
            for x in range(10):
                rect = pygame.Rect(gx + x * cell, gy + y * cell, cell - 2, cell - 2)
                val = game.grid.cells[y][x]
                if val == 0:
                    color = (70, 130, 180)  # water
                else:
                    color = (120, 120, 120)  # ship present (show own ships)
                pygame.draw.rect(screen, color, rect)
        # draw labels
        ip_surf = font.render(f"IP: {game.local_ip}", True, (255, 255, 255))
        screen.blit(ip_surf, (350, 20))

        # participants
        y0 = 60
        screen.blit(font.render("Participantes:", True, (255, 255, 255)), (350, y0))
        with game.participants_lock:
            for i, p in enumerate(list(game.participants)):
                screen.blit(
                    font.render(p, True, (200, 200, 200)), (350, y0 + 20 + 18 * i)
                )

        # log
        with game.log_lock:
            logs = game.log[-10:]
        for i, line in enumerate(reversed(logs)):
            screen.blit(font.render(line, True, (220, 220, 220)), (20, 340 + i * 16))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


def main():
    game = PeerGame()
    game.start()
    try:
        run_pygame_ui(game)
    except KeyboardInterrupt:
        pass
    game.stop()


if __name__ == "__main__":
    main()
