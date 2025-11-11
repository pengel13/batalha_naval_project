# grid.py
# Helper: grid 10x10, navios, verificar hits, estados

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

    def manual_place_ship(self, name: str, size: int, x: int, y: int, is_horizontal: bool) -> bool:
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