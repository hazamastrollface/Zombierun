import logging
from constants import MONSTER_TABLE, TERRAIN_SYMBOLS, COLOR_TABLE

# Configure logging for this module
logging.basicConfig(filename='game.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')

class Monster:
    def __init__(self, name, type, health, attack_power, symbol, color, x, y, speed=1):
        self.name = name
        self.type = type
        self.health = health
        self.attack_power = attack_power
        self.symbol = symbol
        self.color = color
        self.x = x
        self.y = y
        self.speed = speed

    def move_towards_player(self, player, room):
        for _ in range(self.speed):
            old_x, old_y = self.x, self.y
            new_x, new_y = self.x, self.y

        # Determine direction towards player
        if self.x < player.x:
            new_x += 1
        elif self.x > player.x:
            new_x -= 1

        if self.y < player.y:
            new_y += 1
        elif self.y > player.y:
            new_y -= 1

        if new_x == player.x and new_y == player.y:
            # Swap positions with the player
            player.x, player.y = self.x, self.y
            self.x, self.y = new_x, new_y
            logging.info(f"{self.name} swapped positions with the player at ({new_x}, {new_y}).")
            return

        # Check terrain and other monsters
        if room.grid[new_y][new_x] not in ["#", "T", "S"] and not any(
            m.x == new_x and m.y == new_y for m in room.monsters if m != self
        ):
            room.grid[old_y][old_x] = TERRAIN_SYMBOLS.get("grass", ".")
            self.x, self.y = new_x, new_y
            room.grid[self.y][self.x] = self.symbol
            logging.debug(f"{self.name} moved from ({old_x}, {old_y}) to ({new_x}, {new_y}).")
            return

        logging.debug(f"{self.name} blocked at ({new_x}, {new_y}).")

    def check_flame_damage(self, room):
        """
        Check if the monster is standing on a lingering flame and apply damage if so.
        Flames are in room.lingering_flames as a list of dicts with {'position':(x,y), 'remaining_turns': n}.
        We treat flames as passable but harmful.
        """
        for flame in room.lingering_flames:
            fx, fy = flame["position"]
            if fx == self.x and fy == self.y:
                # Monster is standing on flame, deal damage
                flame_damage = 5  # Adjust as needed
                was_dead = self.take_damage(flame_damage)
                logging.info(f"{self.name} took {flame_damage} flame damage standing at ({fx}, {fy}). Health now {self.health}.")
                if was_dead:
                    # Monster died due to flame damage; remove it from room handled in MonsterManager
                    return

    def attack_player(self, player, stdscr):
        damage = self.attack_power
        message, is_dead = player.take_damage(damage)
        logging.info(f"{self.name} attacked player for {damage} damage.")
        # Optionally display message with Renderer if needed

    def take_damage(self, damage):
        self.health -= damage
        logging.debug(f"{self.name} took {damage} damage. Health now {self.health}.")
        if self.health <= 0:
            self.die()
            return True
        return False

    def die(self):
        logging.info(f"{self.name} has been slain.")


def create_monster(x, y, monster_name):
    monster_info = MONSTER_TABLE.get(monster_name)
    if not monster_info:
        raise ValueError(f"Monster '{monster_name}' not found in MONSTER_TABLE.")
    return Monster(
        name=monster_name,
        type=monster_info["type"],
        health=monster_info["health"],
        attack_power=monster_info["attack_power"],
        symbol=monster_info["symbol"],
        color=monster_info["color"],
        x=x,
        y=y,
        speed=monster_info.get("speed", 1)
    )


class MonsterManager:
    def __init__(self, room, player, stdscr):
        self.room = room
        self.player = player
        self.stdscr = stdscr

    def handle_monsters(self):
        # Iterate over a copy since we might remove monsters
        for monster in self.room.monsters[:]:
            # Monster moves
            monster.move_towards_player(self.player, self.room)

            # Check adjacency for attack
            if self.is_adjacent(monster, self.player):
                monster.attack_player(self.player, self.stdscr)
                if self.player.health <= 0:
                    logging.info(f"{monster.name} has defeated the player.")

            # Check if monster died (due to flames or other damage)
            if monster.health <= 0:
                self.room.monsters.remove(monster)
                if 0 <= monster.x < self.room.grid_width and 0 <= monster.y < self.room.grid_height:
                    self.room.grid[monster.y][monster.x] = TERRAIN_SYMBOLS.get("grass", ".")
                logging.info(f"Removed monster '{monster.name}' from room at ({monster.x}, {monster.y}).")

    def is_adjacent(self, monster, player):
        return abs(monster.x - player.x) <= 1 and abs(monster.y - player.y) <= 1

    def update_room(self, new_room):
        self.room = new_room
        logging.info(f"MonsterManager updated to new room ({new_room.x}, {new_room.y}) on floor {new_room.floor}.")
