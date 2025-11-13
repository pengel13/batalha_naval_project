import pygame



import queue



from grid import Grid



from p2p_node import P2PNode





PRETO = (0, 0, 0)



BRANCO = (255, 255, 255)



CINZA = (100, 100, 100)



AZUL = (0, 0, 150)



VERMELHO = (200, 0, 0)



VERDE = (0, 150, 0)





CELL_SIZE = 30



MARGIN = 5



TOP_MARGIN_Y = 100



BOTTOM_MARGIN_Y = 150





GRID_HEIGHT = (CELL_SIZE + MARGIN) * 10 + MARGIN



GRID_WIDTH = GRID_HEIGHT



SCREEN_WIDTH = GRID_WIDTH * 2 + 200



SCREEN_HEIGHT = TOP_MARGIN_Y + GRID_HEIGHT + BOTTOM_MARGIN_Y





ESTADO_POSICIONANDO = "posicionando"



ESTADO_AGUARDANDO = "aguardando"



ESTADO_ESCOLHENDO_ALVO = "escolhendo_alvo"



ESTADO_ATIRANDO = "atirando"



ESTADO_FIM_DE_JOGO = "fim_de_jogo"





class BatalhaNavalPygame:



    def __init__(self):



        self.callback_queue = queue.Queue()



        self.grid = Grid()



        self.p2p_node = P2PNode(self.callback_queue)



        self.meu_ip = self.p2p_node.MEU_IP



        self.grids_oponentes = {}



        self.jogo_ativo = True



        self.estado_jogo = ESTADO_POSICIONANDO



        self.ip_alvo_atual = None



        self.status_msg = "Posicionando navios..."



        pygame.init()



        pygame.font.init()



        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))



        pygame.display.set_caption("Batalha Naval P2P")



        self.clock = pygame.time.Clock()



        self.font_pequena = pygame.font.SysFont("Consolas", 18)



        self.font_media = pygame.font.SysFont("Consolas", 24)




    def setup_jogo(self):



        self.grid.posicionar_navios_aleatorio()



        self.estado_jogo = ESTADO_AGUARDANDO



        self.status_msg = "Aguardando oponentes. Pressione 'A' para atirar."




    def processar_eventos_rede(self):



        try:



            while not self.callback_queue.empty():



                evento = self.callback_queue.get_nowait()



                tipo, *dados = evento



                if tipo == "novo_participante" or tipo == "lista_participantes":



                    ips = [dados[0]] if tipo == "novo_participante" else dados[0]



                    for ip in ips:



                        if ip != self.meu_ip and ip not in self.grids_oponentes:



                            self.grids_oponentes[ip] = self.grid._criar_grid_vazio()



                            print(f"[REDE] Adicionado oponente: {ip}")




                    self.status_msg = "Novo(s) oponente(s)! Pressione 'A' para atirar."




                elif tipo == "jogador_saiu" or tipo == "erro_conexao":



                    ip = dados[0]



                    self.grids_oponentes.pop(ip, None)



                    self.status_msg = f"Jogador {ip} saiu."




                    if self.ip_alvo_atual == ip:



                        self.ip_alvo_atual = None



                        self.estado_jogo = ESTADO_AGUARDANDO




                elif tipo == "jogador_perdeu":



                    ip = dados[0]



                    self.grids_oponentes.pop(ip, None)



                    self.status_msg = f"Jogador {ip} perdeu!"




                elif tipo == "tiro_recebido":



                    ip_atacante, x, y = dados



                    self.status_msg = f"Tiro recebido de {ip_atacante}!"



                    resultado = self.grid.processar_tiro(x, y)




                    if resultado != "repeat":



                        self.p2p_node.enviar_resposta_tcp(



                            ip_atacante, f"{resultado}:{x}:{y}"



                        )




                    if resultado == "game_over":



                        self.p2p_node.broadcast_udp("lost")



                        self.estado_jogo = ESTADO_FIM_DE_JOGO



                        self.status_msg = "VOCE PERDEU! Fim de jogo."




                elif tipo == "resultado_tiro":



                    ip_vitima, resultado, x, y = dados



                    if ip_vitima in self.grids_oponentes:



                        simbolo = self.grid.SIMBOLO_AGUA



                        if resultado in ["hit", "destroyed"]:



                            simbolo = self.grid.SIMBOLO_ATINGIDO



                            self.grid.score_jogadores_que_atingi.add(ip_vitima)



                        elif resultado == "miss":



                            simbolo = self.grid.SIMBOLO_ERRO




                        self.grids_oponentes[ip_vitima][y][x] = simbolo



                        self.status_msg = (



                            f"Resposta de {ip_vitima}: {resultado.upper()}!"



                        )




        except queue.Empty:
            pass




    def get_coord_from_mouse(self, pos, offset_x, offset_y):



        x_mouse, y_mouse = pos



        x_mouse -= offset_x



        y_mouse -= offset_y



        col = x_mouse // (CELL_SIZE + MARGIN)



        lin = y_mouse // (CELL_SIZE + MARGIN)



        if 0 <= col < Grid.GRID_SIZE and 0 <= lin < Grid.GRID_SIZE:



            return col, lin




        return None, None




    def handle_events(self):



        for event in pygame.event.get():



            if event.type == pygame.QUIT:



                self.jogo_ativo = False




            if event.type == pygame.KEYDOWN:



                if event.key == pygame.K_s:



                    self.jogo_ativo = False




                if self.estado_jogo == ESTADO_AGUARDANDO and event.key == pygame.K_a:



                    self.estado_jogo = ESTADO_ESCOLHENDO_ALVO



                    self.status_msg = "Escolha um oponente (Pressione 1, 2...)"




                elif self.estado_jogo == ESTADO_ESCOLHENDO_ALVO:



                    oponentes = list(self.grids_oponentes.keys())




                    if event.key >= pygame.K_1 and event.key <= pygame.K_9:



                        idx = event.key - pygame.K_1



                        if idx < len(oponentes):



                            self.ip_alvo_atual = oponentes[idx]



                            self.estado_jogo = ESTADO_ATIRANDO



                            self.status_msg = f"Atirando em {self.ip_alvo_atual}. Clique no grid da direita."




            if event.type == pygame.MOUSEBUTTONDOWN:



                if self.estado_jogo == ESTADO_ATIRANDO:



                    offset_oponente_x = GRID_WIDTH + 150



                    offset_oponente_y = TOP_MARGIN_Y



                    shot_x, shot_y = self.get_coord_from_mouse(



                        event.pos, offset_oponente_x, offset_oponente_y



                    )




                    if shot_x is not None:



                        print(



                            f"[JOGO] Atirando em {self.ip_alvo_atual} em ({shot_x},{shot_y})"



                        )



                        self.p2p_node.enviar_tiro(self.ip_alvo_atual, shot_x, shot_y)



                        self.status_msg = f"Tiro enviado para {self.ip_alvo_atual}."



                        self.estado_jogo = ESTADO_AGUARDANDO



                    else:



                        self.status_msg = "Clique dentro do grid do oponente!"




    def draw_grid(self, grid_data, offset_x, offset_y, title):



        self.draw_status_text(title, offset_x, offset_y - 30, color=BRANCO)



        for y in range(Grid.GRID_SIZE):



            for x in range(Grid.GRID_SIZE):



                cor = AZUL



                celula = grid_data[y][x]




                if celula == self.grid.SIMBOLO_ERRO:



                    cor = BRANCO



                elif celula == self.grid.SIMBOLO_ATINGIDO:



                    cor = VERMELHO



                elif celula != self.grid.SIMBOLO_AGUA:



                    cor = CINZA




                pygame.draw.rect(



                    self.screen,



                    cor,



                    [



                        offset_x + MARGIN + x * (CELL_SIZE + MARGIN),



                        offset_y + MARGIN + y * (CELL_SIZE + MARGIN),



                        CELL_SIZE,



                        CELL_SIZE,



                    ],



                )




        for i in range(Grid.GRID_SIZE):



            self.draw_status_text(



                str(i),



                offset_x + i * (CELL_SIZE + MARGIN) + MARGIN + (CELL_SIZE // 3),



                offset_y - 55,



                BRANCO,



            )




            self.draw_status_text(



                chr(ord("A") + i),



                offset_x - 20,



                offset_y + i * (CELL_SIZE + MARGIN) + MARGIN + (CELL_SIZE // 3),



                BRANCO,



            )




    def draw_status_text(self, text, x, y, color=BRANCO, font=None):



        if font is None:



            font = self.font_pequena




        text_surface = font.render(text, True, color)



        self.screen.blit(text_surface, (x, y))




    def draw_ui(self):



        self.screen.fill(PRETO)



        offset_meu_grid_x = 50



        offset_meu_grid_y = TOP_MARGIN_Y



        offset_oponente_x = GRID_WIDTH + 150



        offset_oponente_y = TOP_MARGIN_Y




        self.draw_grid(



            self.grid.meu_grid,



            offset_meu_grid_x,



            offset_meu_grid_y,



            "Meu Grid (Navio=Cinza, Atingido=Branco, Azul=Mar)",



        )



        if self.estado_jogo == ESTADO_ATIRANDO and self.ip_alvo_atual:



            grid_oponente = self.grids_oponentes[self.ip_alvo_atual]



            self.draw_grid(



                grid_oponente,



                offset_oponente_x,



                offset_oponente_y,



                f"Grid Oponente: {self.ip_alvo_atual}",



            )



        else:



            pygame.draw.rect(



                self.screen,



                CINZA,



                [offset_oponente_x, offset_oponente_y, GRID_WIDTH, GRID_HEIGHT],



                5,



            )



            self.draw_status_text(



                "Selecione um alvo ('A')",



                offset_oponente_x + 20,



                offset_oponente_y + 20,



            )




        self.draw_status_text(f"Meu IP: {self.meu_ip}", 20, 20, BRANCO)



        dashboard_y_start = TOP_MARGIN_Y + GRID_HEIGHT + 30



        status_color = BRANCO




        if self.estado_jogo == ESTADO_ATIRANDO:



            status_color = VERDE



        elif self.estado_jogo == ESTADO_FIM_DE_JOGO:



            status_color = VERMELHO




        self.draw_status_text(



            f"Status: {self.status_msg}",



            20,



            dashboard_y_start,



            status_color,



            self.font_media,



        )




        oponentes_y_start = dashboard_y_start + 40



        self.draw_status_text("Oponentes:", 20, oponentes_y_start, BRANCO)



        oponentes = list(self.grids_oponentes.keys())




        if not oponentes:



            self.draw_status_text("  Nenhum", 20, oponentes_y_start + 25)




        for i, ip in enumerate(oponentes):



            label = f"  {i+1}: {ip}"



            if self.estado_jogo == ESTADO_ESCOLHENDO_ALVO:



                self.draw_status_text(



                    label, 20, oponentes_y_start + 25 + (i * 20), VERDE



                )



            else:



                self.draw_status_text(



                    label, 20, oponentes_y_start + 25 + (i * 20), BRANCO



                )



        pygame.display.flip()




    def loop_principal(self):



        try:



            self.p2p_node.start()



            self.p2p_node.broadcast_udp(self.p2p_node.MSG_CONECTANDO)



            self.setup_jogo()



            while self.jogo_ativo:



                self.clock.tick(10)



                self.handle_events()



                self.processar_eventos_rede()



                self.draw_ui()



        except KeyboardInterrupt:



            self.jogo_ativo = False



        finally:



            self.p2p_node.stop()



            self.grid.calcular_score_final()



            pygame.quit()



            print("Jogo encerrado.")





if __name__ == "__main__":



    jogo = BatalhaNavalPygame()



    jogo.loop_principal()



