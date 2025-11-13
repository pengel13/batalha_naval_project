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
        return [
            [self.SYM_AGUA for _ in range(self.GRID_SIZE)]
            for _ in range(self.GRID_SIZE)
        ]

    def _parse_coord(self, coord_str):
        try:
            col_str = coord_str[0].upper()
            lin_str = coord_str[1:]

            y = ord(col_str) - ord("A")
            x = int(lin_str)

            if not (0 <= x < self.GRID_SIZE and 0 <= y < self.GRID_SIZE):
                return None, None
            return x, y
        except:
            return None, None

    def _validar_posicao(self, x, y, tamanho, orientacao):
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
        self.meus_navios_saude[nome] = tamanho
        if orientacao == "h":
            for i in range(tamanho):
                self.meu_grid[y][x + i] = nome
        else:
            for i in range(tamanho):
                self.meu_grid[y + i][x] = nome

    def posicionar_navios_aleatorio(self):
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
        print("Posicionamento manual não suportado nesta versão, usando aleatório.")
        self.posicionar_navios_aleatorio()

    def processar_tiro(self, x, y):
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

            if self.meus_navios_saude[nome_navio] == 0:
                if all(saude == 0 for saude in self.meus_navios_saude.values()):
                    return "game_over"
                return "destroyed"

            return "hit"

        return "miss"

    def calcular_score_final(self):
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
