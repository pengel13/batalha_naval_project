# jogo.py
import queue
from grid import Grid
from p2p_node import P2PNode


class BatalhaNaval:
    def __init__(self):
        self.callback_queue = queue.Queue()
        self.grid = Grid()
        self.p2p_node = P2PNode(self.callback_queue)
        self.grids_oponentes = {}
        self.jogo_ativo = True
        self.meu_ip = self.p2p_node.MEU_IP

    def setup_jogo(self):
        """Configura o tabuleiro do jogador."""
        print("--- Batalha Naval P2P ---")
        while True:
            escolha = input("Posicionar navios aleatoriamente? (s/n): ").strip().lower()
            if escolha == "s":
                self.grid.posicionar_navios_aleatorio()
                break
            elif escolha == "n":

                self.grid.posicionar_navios_manual()
                break
        self.grid.imprimir_meu_grid()

    def processar_eventos_rede(self):
        """Verifica a fila de callbacks da rede e atualiza o jogo."""
        try:
            while not self.callback_queue.empty():
                evento = self.callback_queue.get_nowait()
                tipo, *dados = evento

                if tipo == "novo_participante":
                    ip = dados[0]
                    print(f"\n[REDE] Novo jogador entrou: {ip}")
                    self.grids_oponentes[ip] = self.grid._criar_grid_vazio()
                    print(f"Lista de participantes atualizada.")

                elif tipo == "lista_participantes":
                    ips = dados[0]
                    print(f"\n[REDE] Recebida lista de participantes: {ips}")
                    for ip in ips:
                        if ip != self.meu_ip and ip not in self.grids_oponentes:
                            self.grids_oponentes[ip] = self.grid._criar_grid_vazio()
                    print(f"Lista de participantes atualizada.")

                elif tipo == "jogador_saiu" or tipo == "erro_conexao":
                    ip = dados[0]
                    print(f"\n[REDE] Jogador {ip} saiu ou desconectou.")
                    self.grids_oponentes.pop(ip, None)

                elif tipo == "jogador_perdeu":
                    ip = dados[0]
                    print(f"\n[JOGO] {ip} perdeu (todos os navios destruídos)!")

                    self.grids_oponentes.pop(ip, None)

                elif tipo == "tiro_recebido":
                    ip_atacante, x, y = dados
                    print(f"\n[JOGO] Tiro recebido de {ip_atacante} em ({x},{y}).")
                    resultado = self.grid.processar_tiro(x, y)

                    if resultado == "game_over":
                        self.p2p_node.enviar_resposta_tcp(ip_atacante, "destroyed")
                        self.p2p_node.broadcast_udp("lost")
                        self.jogo_ativo = False
                    elif resultado != "repeat" and resultado != "miss":

                        self.p2p_node.enviar_resposta_tcp(ip_atacante, resultado)

                elif tipo == "resultado_tiro":
                    ip_vitima, resultado = dados
                    print(f"\n[JOGO] Resposta de {ip_vitima}: {resultado.upper()}!")
                    if resultado in ["hit", "destroyed"]:
                        self.grid.score_jogadores_que_atingi.add(ip_vitima)

        except queue.Empty:
            pass

    def acao_atirar(self):
        """
        Permite ao usuário escolher o alvo e a coordenada do tiro.
        """
        oponentes = self.p2p_node.get_participantes()
        if not oponentes:
            print("\n[JOGO] Nenhum oponente encontrado para atirar.")
            return

        print("\nOponentes disponíveis:")
        for i, ip in enumerate(oponentes):
            print(f"  {i+1}: {ip}")

        ip_alvo = None
        while ip_alvo is None:
            try:
                escolha = int(input("Em quem atirar? (digite o número): "))
                if 1 <= escolha <= len(oponentes):
                    ip_alvo = oponentes[escolha - 1]
                else:
                    print("Número inválido.")
            except ValueError:
                print("Entrada inválida.")

        x, y = None, None
        while x is None:
            coord_str = input(
                f"Digite a coordenada para atirar em {ip_alvo} (ex: A5): "
            ).strip()
            x, y = self.grid._parse_coord(coord_str)
            if x is None:
                print("Coordenada inválida. Tente novamente.")

        print(f"[JOGO] Atirando em {ip_alvo} na posição ({coord_str.upper()})...")
        self.p2p_node.enviar_tiro(ip_alvo, x, y)

    def loop_principal(self):
        """Loop principal da interface do jogo."""
        try:
            self.p2p_node.start()
            self.p2p_node.broadcast_udp(self.p2p_node.MSG_CONECTANDO)

            print("\nComandos:")
            print("  'g' - Ver meus grids")
            print("  'o' - Ver grids dos oponentes (lista)")
            print("  'a' - Atirar (Ponto 3)")
            print("  's' - Sair do jogo")

            while self.jogo_ativo:

                self.processar_eventos_rede()

                cmd = input("\nDigite um comando (g, o, a, s): ").strip().lower()

                if cmd == "s":
                    print("Saindo do jogo...")
                    self.jogo_ativo = False
                    break
                elif cmd == "g":
                    self.grid.imprimir_meu_grid()
                elif cmd == "o":
                    print(f"Oponentes: {list(self.grids_oponentes.keys())}")

                elif cmd == "a":
                    self.acao_atirar()
                else:
                    pass

        except KeyboardInterrupt:
            print("\nSaindo (Ctrl+C)...")
            self.jogo_ativo = False

        finally:
            self.p2p_node.stop()
            self.grid.calcular_score_final()
            print("Jogo encerrado.")


if __name__ == "__main__":
    jogo = BatalhaNaval()
    jogo.setup_jogo()
    jogo.loop_principal()
