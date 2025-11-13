import random


class Grid:
    GRID_SIZE = 10
    SHIP_CONFIG = {
        "porta-avioes": 5,
        "bombardeiro": 4,
        "submarino": 3,
        "lancha": 2,
    }

    SYM_AGUA = "~"
    SYM_NAVIO = "N"
    SYM_ATINGIDO = "X"
    SYM_ERRO = "O"

    def __init__(self):
        self.meu_grid = self._criar_grid_vazio()
        self.meus_navios_saude = {}
        self.score_vezes_fui_atingido = 0
        self.score_jogadores_que_atingi = set()

    def _criar_grid_vazio(self):
        """Cria um grid 10x10 preenchido com água."""
        return [
            [self.SYM_AGUA for _ in range(self.GRID_SIZE)]
            for _ in range(self.GRID_SIZE)
        ]

    def imprimir_meu_grid(self):
        """Imprime o grid que mostra meus navios."""
        print("\n--- MEU GRID (N=Navio, X=Atingido, O=Erro, ~=Agua) ---")
        self._imprimir_grid(self.meu_grid)

    def imprimir_grid_oponente(self, grid_oponente):
        """Imprime o grid que mostra meus tiros no oponente."""
        print("\n--- GRID OPONENTE (X=Acerto, O=Erro, ~=Nao atirou) ---")
        self._imprimir_grid(grid_oponente)

    def _imprimir_grid(self, grid):
        """Função helper universal para imprimir um grid."""
        header = "   " + " ".join([str(i) for i in range(self.GRID_SIZE)])
        print(header)
        print("  " + "-" * (self.GRID_SIZE * 2 + 1))

        for i, linha in enumerate(grid):
            print(f"{chr(ord('A') + i):>2}|", end=" ")
            for celula in linha:
                if celula in [self.SYM_AGUA, self.SYM_ATINGIDO, self.SYM_ERRO]:
                    print(celula, end=" ")
                else:
                    print(self.SYM_NAVIO, end=" ")
            print("|")
        print("  " + "-" * (self.GRID_SIZE * 2 + 1))

    def _parse_coord(self, coord_str):
        """
        Converte input do usuário para coordenadas corretas para o programa
        Exemplo:
        Converte 'A5' para (x=5, y=0)."""
        try:
            col_str = coord_str[0].upper()
            lin_str = coord_str[1:]

            y = ord(col_str) - ord("A")
            x = int(lin_str)

            if not (0 <= x < self.GRID_SIZE and 0 <= y < self.GRID_SIZE):
                return None, None
            return x, y
        except Exception:
            return None, None

    def _validar_posicao(self, x, y, tamanho, orientacao):
        """Verifica se um navio pode ser colocado em (x, y)."""
        if orientacao == "h":
            if x + tamanho > self.GRID_SIZE:
                return False
            for i in range(tamanho):
                if self.meu_grid[y][x + i] != self.SYM_AGUA:
                    return False
        else:
            if y + tamanho > self.GRID_SIZE:
                return False
            for i in range(tamanho):
                if self.meu_grid[y + i][x] != self.SYM_AGUA:
                    return False
        return True

    def _posicionar_navio(self, nome, x, y, tamanho, orientacao):
        """Coloca o navio no grid."""
        self.meus_navios_saude[nome] = tamanho
        if orientacao == "h":
            for i in range(tamanho):
                self.meu_grid[y][x + i] = nome
        else:
            for i in range(tamanho):
                self.meu_grid[y + i][x] = nome
        print(f"[JOGO] {nome} posicionado.")

    def posicionar_navios_aleatorio(self):
        """Preenche 'meu_grid' e 'meus_navios' aleatoriamente."""
        print("[JOGO] Posicionando navios aleatoriamente...")
        for nome_navio, tamanho in self.SHIP_CONFIG.items():
            posicionado = False
            while not posicionado:
                orientacao = random.choice(["h", "v"])
                x = random.randint(0, self.GRID_SIZE - 1)
                y = random.randint(0, self.GRID_SIZE - 1)

                if self._validar_posicao(x, y, tamanho, orientacao):
                    self._posicionar_navio(nome_navio, x, y, tamanho, orientacao)
                    posicionado = True

    def posicionar_navios_manual(self):
        """
        Permite ao usuário posicionar navios manualmente.
        """
        print("[JOGO] Posicionamento manual de navios.")
        for nome_navio, tamanho in self.SHIP_CONFIG.items():
            posicionado = False
            while not posicionado:
                self.imprimir_meu_grid()
                print(f"Posicione seu: {nome_navio} (tamanho {tamanho})")

                # 1. Pega coordenada
                # <--- MUDANÇA AQUI: Atualiza o exemplo
                coord_str = input(
                    "  Digite a coordenada inicial (ex: A5, C0): "
                ).strip()
                x, y = self._parse_coord(coord_str)
                if x is None:
                    print("Coordenada inválida. Tente novamente.")
                    continue

                # 2. Pega orientação
                orient_str = (
                    input(
                        "  Digite a orientação (h para horizontal, v para vertical): "
                    )
                    .strip()
                    .lower()
                )
                if orient_str not in ["h", "v"]:
                    print("Orientação inválida. Tente novamente.")
                    continue

                # 3. Valida e posiciona
                if self._validar_posicao(x, y, tamanho, orient_str):
                    self._posicionar_navio(nome_navio, x, y, tamanho, orient_str)
                    posicionado = True
                else:
                    print(
                        "Posição inválida (fora do grid ou sobreposição). Tente novamente."
                    )

    def processar_tiro(self, x, y):
        """
        Processa um tiro recebido em (x, y).
        Retorna: 'miss', 'hit', 'destroyed', 'game_over', 'repeat'
        """
        if not (0 <= x < self.GRID_SIZE and 0 <= y < self.GRID_SIZE):
            return "miss"

        celula = self.meu_grid[y][x]

        if celula == self.SYM_AGUA:
            self.meu_grid[y][x] = self.SYM_ERRO
            return "miss"

        if celula in [self.SYM_ATINGIDO, self.SYM_ERRO]:
            return "repeat"

        if celula in self.meus_navios_saude:
            nome_navio = celula
            self.meu_grid[y][x] = self.SYM_ATINGIDO
            self.meus_navios_saude[nome_navio] -= 1
            self.score_vezes_fui_atingido += 1

            print(f"[JOGO] Fomos atingidos em {nome_navio}!")

            if self.meus_navios_saude[nome_navio] == 0:
                print(f"[JOGO] Nosso {nome_navio} foi destruído!")
                if all(saude == 0 for saude in self.meus_navios_saude.values()):
                    print("[JOGO] TODOS OS NOSSOS NAVIOS FORAM DESTRUÍDOS!")
                    return "game_over"
                return "destroyed"

            return "hit"

        return "miss"  # Fallback

    def calcular_score_final(self):
        """Calcula e imprime o score final."""
        score_final = (
            len(self.score_jogadores_que_atingi) - self.score_vezes_fui_atingido
        )
        print("\n--- SCORE FINAL ---")
        print(
            f"Jogadores únicos que você atingiu: {len(self.score_jogadores_que_atingi)}"
        )
        print(f"Número de vezes que você foi atingido: {self.score_vezes_fui_atingido}")
        print(f"Pontuação Final (Atingidos - Vezes Atingido): {score_final}")
        print("-------------------")
