import random
import os
import logging
from constants import TERRAIN_SYMBOLS, ITEM_TABLE, MONSTER_TABLE

# Configure logging
logging.basicConfig(
    filename='game.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

class Item:
    def __init__(self, name, symbol, item_type, color, x, y):
        """
        Represents an item on the ground (weapons, ammo, healing items, grenades, etc.).
        :param name: Name of the item.
        :param symbol: Symbol representing the item on the grid.
        :param item_type: e.g., 'healing', 'ammo', 'grenade', 'armor', 'weapon'...
        :param color: Color name from COLOR_TABLE.
        :param x: X-coordinate of the item.
        :param y: Y-coordinate of the item.
        """
        self.name = name
        self.symbol = symbol
        self.item_type = item_type
        self.color = color
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Item(name={self.name}, symbol={self.symbol}, type={self.item_type}, position=({self.x}, {self.y}))"


class RoomItems:
    def __init__(self, room):
        """
        Initializes RoomItems for a given room by placing items randomly based on ITEM_TABLE drop rates.
        """
        self.items = []
        self.generate_items(room)

    def generate_items(self, room):
        grid_width = room.grid_width
        grid_height = room.grid_height
        num_items = 5  # Adjust as needed

        for _ in range(num_items):
            # Select an item or weapon based on drop rates
            item_choice = random.choices(
                ITEM_TABLE,
                weights=[item["drop_rate"] for item in ITEM_TABLE],
                k=1
            )[0]

            # Try placing the item at a random position
            attempts = 0
            while attempts < 100:
                x = random.randint(1, grid_width - 2)
                y = random.randint(1, grid_height - 2)

                if self.is_position_empty(x, y, room):
                    # Create and place the item/weapon
                    item = Item(
                        name=item_choice["name"],
                        symbol=item_choice["symbol"],
                        item_type=item_choice["type"],
                        color=item_choice["color"],
                        x=x,
                        y=y
                    )
                    self.items.append(item)
                    room.grid[y][x] = item.symbol
                    logging.info(f"Placed '{item.name}' ({item.item_type}) at ({x}, {y}) in room ({room.x}, {room.y}) on floor {room.floor}.")
                    break

                attempts += 1
            else:
                logging.warning(f"Failed to place '{item_choice['name']}' in room at ({room.x}, {room.y}) after 100 attempts.")

    def is_position_empty(self, x, y, room):
        """
        Checks if a position is empty: grass terrain, no monsters, no items.
        """
        if room.grid[y][x] != TERRAIN_SYMBOLS["grass"]:
            return False
        if any(monster.x == x and monster.y == y for monster in room.monsters):
            return False
        if any(item.x == x and item.y == y for item in self.items):
            return False
        return True

    def get_items(self):
        return self.items


class Room:
    def __init__(self, grid_width, grid_height, floor_number=0, x=0, y=0, has_staircase=False):
        """
        Initializes a Room instance with monsters, items, lingering flames, and optional staircase.
        :param grid_width: Width of the room grid.
        :param grid_height: Height of the room grid.
        :param floor_number: The floor number this room is on.
        :param x, y: Coordinates of the room in the floor layout.
        :param has_staircase: Whether the room contains a staircase.
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.floor = floor_number
        self.x = x
        self.y = y
        self.has_staircase = has_staircase
        self.grid = self._create_empty_grid()
        self.monsters = []
        self.items = RoomItems(self)
        self.lingering_flames = []

        self.generate_terrain()
        if self.has_staircase:
            self.place_staircase()
        self.generate_monsters()

    def _create_empty_grid(self):
        grid = [[TERRAIN_SYMBOLS["grass"] for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        return grid

    def generate_terrain(self):
        num_walls = random.randint(5, 15)
        num_trees = random.randint(5, 20)
        num_fires = random.randint(0, 5)

        # Place walls
        for _ in range(num_walls):
            x = random.randint(1, self.grid_width - 2)
            y = random.randint(1, self.grid_height - 2)
            if self.grid[y][x] == TERRAIN_SYMBOLS["grass"]:
                self.grid[y][x] = TERRAIN_SYMBOLS["wall"]

        # Place trees
        for _ in range(num_trees):
            x = random.randint(1, self.grid_width - 2)
            y = random.randint(1, self.grid_height - 2)
            if self.grid[y][x] == TERRAIN_SYMBOLS["grass"]:
                self.grid[y][x] = TERRAIN_SYMBOLS["tree"]

        # Place lingering flames (passable, damage externally handled)
        for _ in range(num_fires):
            x = random.randint(1, self.grid_width - 2)
            y = random.randint(1, self.grid_height - 2)
            if self.grid[y][x] == TERRAIN_SYMBOLS["grass"]:
                self.add_lingering_flame(x, y, duration=5)

    def place_staircase(self):
        attempts = 0
        while attempts < 100:
            x = random.randint(1, self.grid_width - 2)
            y = random.randint(1, self.grid_height - 2)
            if self.grid[y][x] == TERRAIN_SYMBOLS["grass"]:
                self.grid[y][x] = "S"
                break
            attempts += 1
        else:
            logging.warning(f"Failed to place staircase in room at ({self.x}, {self.y}) on floor {self.floor} after 100 attempts.")

    def generate_monsters(self):
        spawn_chance = 0.3
        for monster_name, monster_info in MONSTER_TABLE.items():
            if random.random() < spawn_chance:
                x, y = self.get_random_empty_position()
                if x is not None and y is not None:
                    from monster import create_monster
                    monster = create_monster(x, y, monster_name)
                    self.monsters.append(monster)
                    self.grid[y][x] = monster.symbol
                    logging.info(f"Spawned {monster.name} at ({x}, {y}) in room ({self.x}, {self.y}) on floor {self.floor}.")

    def get_random_empty_position(self):
        attempts = 100
        for _ in range(attempts):
            x = random.randint(1, self.grid_width - 2)
            y = random.randint(1, self.grid_height - 2)
            if (
                self.grid[y][x] == TERRAIN_SYMBOLS["grass"] and
                not any(monster.x == x and monster.y == y for monster in self.monsters) and
                not any(item.x == x and item.y == y for item in self.items.get_items())
            ):
                return x, y
        logging.warning("Failed to find an empty position after multiple attempts.")
        return None, None

    def remove_item(self, item):
        if item in self.items.items:
            self.items.items.remove(item)
            try:
                self.grid[item.y][item.x] = TERRAIN_SYMBOLS["grass"]
                logging.info(f"Removed item '{item.name}' from ({item.x}, {item.y}) in room ({self.x}, {self.y}) on floor {self.floor}.")
            except IndexError:
                logging.error(f"Attempted to remove item '{item.name}' at invalid position ({item.x}, {item.y}).")

    def add_lingering_flame(self, x, y, duration=5):
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            # Do not modify the grid cell. Just record flame presence.
            self.lingering_flames.append({"position": (x, y), "remaining_turns": duration})

    def update_lingering_flames(self):
        remaining_flames = []
        for flame in self.lingering_flames:
            x, y = flame["position"]
            flame["remaining_turns"] -= 1
            if flame["remaining_turns"] > 0:
                remaining_flames.append(flame)
            else:
                logging.info(f"Lingering flame at ({x}, {y}) has extinguished.")
        self.lingering_flames = remaining_flames


    def check_for_staircase(self, player):
        return self.has_staircase and self.grid[player.y][player.x] == "S"

    def get_flame_damage_at(self, x, y):
        """
        Returns total damage from all flames at (x, y).
        Each flame deals 5 damage per turn.
        """
        damage = 0
        for flame in self.lingering_flames:
            if flame["position"] == (x, y):
                damage += 5
        return damage

    def __repr__(self):
        return f"Room(monsters={self.monsters}, items={self.items}, lingering_flames={len(self.lingering_flames)}, has_staircase={self.has_staircase})"


class RoomManager:
    def __init__(self, grid_width=80, grid_height=24, floor_width=5, floor_height=5, save_dir="saves"):
        """
        Manages a grid of rooms and floor transitions.
        :param grid_width: room width
        :param grid_height: room height
        :param floor_width: how many rooms horizontally
        :param floor_height: how many rooms vertically
        :param save_dir: directory for saving/loading
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.floor_width = floor_width
        self.floor_height = floor_height
        self.rooms = {}
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            logging.info(f"Created save directory at '{self.save_dir}'.")
        self.floor_staircases = {}  # floor -> (x, y) of staircase room

    def get_room(self, floor, x, y):
        key = (floor, x, y)
        if key not in self.rooms:
            self.create_room(floor, x, y)
        return self.rooms[key]

    def create_room(self, floor, x, y):
        # If no staircase assigned for this floor yet, assign one random room on that floor
        if floor not in self.floor_staircases:
            staircase_x = random.randint(0, self.floor_width - 1)
            staircase_y = random.randint(0, self.floor_height - 1)
            self.floor_staircases[floor] = (staircase_x, staircase_y)
            logging.debug(f"Assigned staircase to room ({staircase_x}, {staircase_y}) on floor {floor}.")

        staircase_x, staircase_y = self.floor_staircases[floor]
        has_staircase = (x, y) == (staircase_x, staircase_y)

        room = Room(self.grid_width, self.grid_height, floor, x, y, has_staircase)
        self.rooms[(floor, x, y)] = room
        logging.debug(f"Created new room at ({x}, {y}) on floor {floor} with has_staircase={has_staircase}.")
        return room

    def transition_room(self, current_room, player, direction):
        dx, dy = 0, 0
        if direction == "left":
            dx = -1
        elif direction == "right":
            dx = 1
        elif direction == "up":
            dy = -1
        elif direction == "down":
            dy = 1
        else:
            logging.error(f"Invalid direction '{direction}' for room transition.")
            return None

        new_x = current_room.x + dx
        new_y = current_room.y + dy

        if 0 <= new_x < self.floor_width and 0 <= new_y < self.floor_height:
            new_room = self.get_room(current_room.floor, new_x, new_y)
            logging.info(f"Player moved to room at ({new_x}, {new_y}) on floor {current_room.floor}")
            return new_room
        else:
            logging.warning(f"Attempted to move outside the floor grid to ({new_x}, {new_y}) on floor {current_room.floor}.")
            return None

    def should_have_staircase(self, floor):
        # By design we assign one staircase room per floor when first needed
        return (floor not in self.floor_staircases)

    def __repr__(self):
        return f"RoomManager(floor_staircases={self.floor_staircases}, rooms={len(self.rooms)})"
