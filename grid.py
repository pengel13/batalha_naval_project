import random
from typing import List, Tuple, Dict


class Ship:
    def __init__(self, name: str, size: int, positions: List[Tuple[int, int]]):
        self.name = name
        self.size = size
        self.positions = positions  # list of (x,y)
        self.hits = set()  # positions hit

    def register_shot(self, pos: Tuple[int, int]) -> str:
        """Return 'miss'|'hit'|'destroyed'"""
        if pos in self.positions:
            self.hits.add(pos)
            if self.is_destroyed():
                return "destroyed"
            else:
                return "hit"
        return "miss"

    def is_destroyed(self) -> bool:
        return len(self.hits) >= self.size


class Grid:
    WIDTH = 10
    HEIGHT = 10

    def __init__(self):
        # 0: water, otherwise ship id
        self.cells = [[0] * self.WIDTH for _ in range(self.HEIGHT)]
        self.ships: Dict[int, Ship] = {}
        self._next_ship_id = 1
        self.total_ship_cells = 0
        self.hits_received = 0

    def place_ships_random(self):
        self.ships = {}
        self.cells = [[0] * self.WIDTH for _ in range(self.HEIGHT)]
        self._next_ship_id = 1
        for name, size in [
            ("porta_avioes", 5),
            ("bombardeiro", 4),
            ("submarino", 3),
            ("lancha", 2),
        ]:
            placed = False
            while not placed:
                placed = self._try_place_ship_random(name, size)

    def _try_place_ship_random(self, name, size):
        is_horizontal = random.choice([True, False])
        if is_horizontal:
            x = random.randint(0, self.WIDTH - size)
            y = random.randint(0, self.HEIGHT - 1)
            coords = [(x + i, y) for i in range(size)]
        else:
            x = random.randint(0, self.WIDTH - 1)
            y = random.randint(0, self.HEIGHT - size)
            coords = [(x, y + i) for i in range(size)]

        # check collision
        for cx, cy in coords:
            if self.cells[cy][cx] != 0:
                return False

        ship_id = self._next_ship_id
        self._next_ship_id += 1
        self.ships[ship_id] = Ship(name, size, coords)
        for cx, cy in coords:
            self.cells[cy][cx] = ship_id
        self.total_ship_cells += size
        return True

    def manual_place_ship(
        self, name: str, size: int, x: int, y: int, is_horizontal: bool
    ) -> bool:
        coords = (
            [(x + i, y) for i in range(size)]
            if is_horizontal
            else [(x, y + i) for i in range(size)]
        )

        # bounds check
        for cx, cy in coords:
            if cx < 0 or cx >= self.WIDTH or cy < 0 or cy >= self.HEIGHT:
                return False
            if self.cells[cy][cx] != 0:
                return False

        ship_id = self._next_ship_id
        self._next_ship_id += 1
        self.ships[ship_id] = Ship(name, size, coords)
        for cx, cy in coords:
            self.cells[cy][cx] = ship_id
        self.total_ship_cells += size
        return True

    def receive_shot(self, x: int, y: int) -> Tuple[str, int]:
        """Process incoming shot, return ('miss'|'hit'|'destroyed', ship_id or 0)"""
        if x < 0 or x >= self.WIDTH or y < 0 or y >= self.HEIGHT:
            return ("miss", 0)

        cell = self.cells[y][x]
        if cell == 0:
            return ("miss", 0)

        ship = self.ships.get(cell)
        if ship is None:
            return ("miss", 0)

        res = ship.register_shot((x, y))
        if res in ("hit", "destroyed"):
            self.hits_received += 1
        return (res, cell)

    def all_ships_destroyed(self) -> bool:
        # either check hits_received >= total_ship_cells or each ship destroyed
        return self.hits_received >= self.total_ship_cells

    def get_ship_positions(self) -> Dict[str, List[Tuple[int, int]]]:
        d = {}
        for sid, ship in self.ships.items():
            d[ship.name] = ship.positions
        return d

    def place_ships_manual(self):
        # Interactive manual placement of ships via terminal input.
        #        The player must provide initial and final coordinates for each ship (x1,y1) -> (x2,y2).
        #       Coordinates must form a straight line (horizontal or vertical) and match the ship size.

        self.ships = {}
        self.cells = [[0] * self.WIDTH for _ in range(self.HEIGHT)]
        self._next_ship_id = 1
        self.total_ship_cells = 0

        ship_defs = [
            ("porta_avioes", 5, "Porta-aviões"),
            (
                "bombardeiro",
                4, "Bombardeiro"
            ),
            (
                "submarino",
                3, "Submarino"
            ),
            (
                "lancha",
                2, "Lancha Militar"
            ),
        ]

        print(
            "\nPosicione suas embarcações manualmente (coordenadas x e y entre 0 e 9).\n"
        )

        for internal_name, size, display_name in ship_defs:
            placed = False
            while not placed:
                print(f"➡️  {display_name} (tamanho {size})")
                try:
                    raw = input(
                        "Digite x1 y1 x2 y2 separados por espaço (ou 'c' para cancelar): "
                    ).strip()
                    if raw.lower() == "c":
                        print(
                            "Cancelado pelo usuário. Reiniciando posicionamento deste navio."
                        )
                        continue
                    parts = raw.split()
                    if len(parts) != 4:
                        print("  ❌ Entrada inválida — informe 4 números: x1 y1 x2 y2.")
                        continue
                    x1, y1, x2, y2 = map(int, parts)
                except ValueError:
                    print("  ❌ Entrada inválida. Use números inteiros entre 0 e 9.")
                    continue

                # bounds check
                coords_ok = all(0 <= v < self.WIDTH for v in (x1, y1, x2, y2))
                if not coords_ok:
                    print("  ❌ Coordenadas fora dos limites (0-9). Tente novamente.")
                    continue

                # must be straight line
                if x1 != x2 and y1 != y2:
                    print(
                        "  ❌ O barco deve estar em linha reta (horizontal ou vertical). Tente novamente."
                    )
                    continue

                # determine orientation and length
                if x1 == x2:
                    is_horizontal = False
                    length = abs(y2 - y1) + 1
                    x = x1
                    y = min(y1, y2)
                else:
                    is_horizontal = True
                    length = abs(x2 - x1) + 1
                    x = min(x1, x2)
                    y = y1

                if length != size:
                    print(
                        f"  ❌ Comprimento informado ({length}) não corresponde ao tamanho do {display_name} ({size}). Tente novamente."
                    )
                    continue

                # attempt to place using existing manual_place_ship validation
                ok = self.manual_place_ship(internal_name, size, x, y, is_horizontal)
                if not ok:
                    print(
                        "  ❌ Posição inválida ou colisão com outro barco. Tente outra posição."
                    )
                    continue

                placed = True
                print(f"  ✅ {display_name} posicionado com sucesso.\n")

        print("Todos os navios posicionados com sucesso!\n")
