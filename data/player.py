import logging
import curses
from constants import COLOR_TABLE, WEAPON_TABLE, ITEM_TABLE, TERRAIN_SYMBOLS
from weapons.flamethrower import fire_flamethrower
from grenades.frag import throw_frag_grenade
from weapons.rpg import fire_rpg
from grenades.molitov import throw_molitov
from weapons.bullet import render_bullet  # For the Bullet weapon

class Player:
    def __init__(self, x, y, room_manager):
        """
        Initializes the Player instance with default attributes.
        :param x: Initial X-coordinate of the player.
        :param y: Initial Y-coordinate of the player.
        :param room_manager: The RoomManager instance.
        """
        self.x = x
        self.y = y
        self.room_manager = room_manager
        self.floor = 0  # Player starts on floor 0
        self.health = 100
        self.max_health = 100
        self.armor = 50
        self.max_armor = 100
        self.weapon = "Pistol"
        self.weapon_ammo = WEAPON_TABLE.get(self.weapon, {}).get("ammo", WEAPON_TABLE.get("Pistol", {}).get("ammo", 0))

        # Initialize grenades with 2 each for every grenade type
        self.grenades = {grenade["name"]: 2 for grenade in ITEM_TABLE if grenade["type"] == "grenade"}

        # Initialize kill_stats for weapons and grenades
        self.kill_stats = {
            "weapons": {w: 0 for w in WEAPON_TABLE},
            "grenades": {g["name"]: 0 for g in ITEM_TABLE if g["type"] == "grenade"}
        }

    def get_health_bar(self):
        bar_length = 20
        health_percentage = self.health / self.max_health
        filled_length = int(bar_length * health_percentage)
        return f"[{'#' * filled_length}{'.' * (bar_length - filled_length)}]"

    def get_armor_bar(self):
        bar_length = 20
        armor_percentage = self.armor / self.max_armor
        filled_length = int(bar_length * armor_percentage)
        return f"[{'=' * filled_length}{'.' * (bar_length - filled_length)}]"

    def get_status_bars(self):
        return (self.get_health_bar(), self.get_armor_bar())

    def move(self, dx, dy, room):
        new_x = self.x + dx
        new_y = self.y + dy

        if 0 <= new_x < room.grid_width and 0 <= new_y < room.grid_height:
            # Check if a monster is in the target position
            monster_in_position = next((m for m in room.monsters if m.x == new_x and m.y == new_y), None)

            if monster_in_position:
                # Swap positions with the monster
                monster_in_position.x, monster_in_position.y = self.x, self.y
                self.x, self.y = new_x, new_y
                logging.info(f"Player swapped positions with {monster_in_position.name} at ({new_x}, {new_y}).")
                return f"Swapped positions with {monster_in_position.name}.", 0

            # Check terrain and other rules for movement
            terrain_symbol = room.grid[new_y][new_x]
            if terrain_symbol not in ["#", "T", "S", "~"]:  # Impassable terrain
                room.grid[self.y][self.x] = TERRAIN_SYMBOLS.get("grass", ".")
                self.x, self.y = new_x, new_y
                room.grid[self.y][self.x] = "@"
                logging.info(f"Player moved to ({self.x}, {self.y}) in room ({room.x}, {room.y}).")
                return f"Moved to ({self.x}, {self.y}).", 0

            logging.debug(f"Blocked by terrain '{terrain_symbol}' at ({new_x}, {new_y}).")
            return "Movement blocked by terrain.", 0
        else:
            # Trigger room transition
            current_room_x, current_room_y = room.x, room.y
            new_room_x = current_room_x + (1 if new_x >= room.grid_width else -1 if new_x < 0 else 0)
            new_room_y = current_room_y + (1 if new_y >= room.grid_height else -1 if new_y < 0 else 0)

            new_room = self.room_manager.get_room(self.floor, new_room_x, new_room_y)
            self.x = new_x % room.grid_width
            self.y = new_y % room.grid_height

            logging.info(f"Player moved to new room ({new_room_x}, {new_room_y}) at position ({self.x}, {self.y}).")
            return f"Entered new room at ({new_room_x}, {new_room_y}).", 0, new_room

    def use_staircase(self, direction, room):
        """
        Uses the staircase to move between floors if on one.
        :param direction: 'up' or 'down'
        :param room: The current Room object.
        :return: (message, kills, new_room) if moved floors, else (message, kills, room)
        """
        if not room.check_for_staircase(self):
            logging.debug("Attempted staircase without being on one.")
            return ("You are not on a staircase.", 0, room)

        if direction == "up":
            new_floor = self.floor + 1
        elif direction == "down":
            new_floor = self.floor - 1
        else:
            logging.error(f"Invalid staircase direction '{direction}'.")
            return ("Invalid direction for staircase usage.", 0, room)

        if direction == "down" and new_floor < 0:
            logging.debug("Attempted to go below floor 0.")
            return ("You are already on the lowest floor.", 0, room)

        staircase_coords = self.room_manager.floor_staircases.get(new_floor)
        if not staircase_coords:
            logging.error(f"No staircase for floor {new_floor}.")
            return (f"No staircase found for floor {new_floor}.", 0, room)

        staircase_room_x, staircase_room_y = staircase_coords
        new_room = self.room_manager.get_room(new_floor, staircase_room_x, staircase_room_y)

        staircase_pos = self.find_staircase_position(new_room)
        if not staircase_pos:
            logging.error(f"Staircase pos not found in new room ({staircase_room_x}, {staircase_room_y}).")
            return ("Staircase position not found in the new room.", 0, room)

        # Clear old pos
        room.grid[self.y][self.x] = TERRAIN_SYMBOLS.get("grass", ".")
        self.floor = new_floor
        self.x, self.y = staircase_pos
        new_room.grid[self.y][self.x] = "@"
        logging.info(f"Player moved {direction} to floor {self.floor}. Coords: ({self.x}, {self.y}) in room ({new_room.x}, {new_room.y}).")
        return (f"Moved {direction} to floor {self.floor}.", 0, new_room)

    def find_staircase_position(self, room):
        for y in range(room.grid_height):
            for x in range(room.grid_width):
                if room.grid[y][x] == "S":
                    return (x, y)
        return None

    def fire_weapon(self, direction, room, stdscr):
        """
        Fires the equipped weapon in a direction.
        :param direction: (dx, dy) direction tuple.
        :param room: The current Room object.
        :param stdscr: curses window
        :return: (message, kills)
        """
        weapon_name = self.weapon
        if self.weapon_ammo <= 0:
            logging.debug(f"No ammo for {weapon_name}.")
            return (f"No ammo left for {weapon_name}!", 0)

        self.weapon_ammo -= 1
        logging.info(f"Player fired {weapon_name}. Ammo: {self.weapon_ammo}")
        kills = 0
        message = ""

        if weapon_name == "Pistol":
            kills = render_bullet(stdscr, self.x, self.y, direction, room)
            message = f"Fired {weapon_name}! Ammo: {self.weapon_ammo}"
        elif weapon_name == "Flamethrower":
            kills = fire_flamethrower(self.x, self.y, direction, room)
            self.kill_stats["weapons"]["Flamethrower"] += kills
            message = f"Fired Flamethrower! Kills: {kills}"
        elif weapon_name == "RPG":
            kills = fire_rpg(self.x, self.y, direction, room)
            self.kill_stats["weapons"]["RPG"] += kills
            message = f"Fired RPG! Kills: {kills}"
        else:
            message = f"Fired {weapon_name}!"
            logging.warning(f"Weapon '{weapon_name}' not fully implemented.")

        return (message, kills)

    def equip_weapon_by_index(self, index):
        weapon_names = list(WEAPON_TABLE.keys())
        if 0 <= index < len(weapon_names):
            selected_weapon_name = weapon_names[index]
            selected_weapon = WEAPON_TABLE.get(selected_weapon_name)
            if selected_weapon:
                self.weapon = selected_weapon_name
                self.weapon_ammo = selected_weapon["ammo"]
                logging.info(f"Equipped {selected_weapon_name}.")
                return (f"Equipped {selected_weapon_name}!", True)
            else:
                logging.error(f"Weapon {selected_weapon_name} not found in WEAPON_TABLE.")
                return (f"Weapon {selected_weapon_name} not found!", False)
        else:
            logging.debug(f"Invalid weapon index: {index}")
            return ("Invalid weapon selection.", False)

    def take_damage(self, damage):
        effective_damage = max(damage - self.armor, 0)
        self.armor = max(self.armor - damage, 0)
        self.health = max(self.health - effective_damage, 0)
        logging.info(f"Player took {effective_damage} damage. Health: {self.health}, Armor: {self.armor}")

        if effective_damage > 0:
            message = f"Hit! Health: {self.health}, Armor: {self.armor}"
        else:
            message = f"Hit! Armor: {self.armor}"

        is_dead = self.health <= 0
        if is_dead:
            message += " You have been defeated!"
            logging.info("Player has been defeated.")
        return (message, is_dead)

    def update_kill_stats(self, kills):
        if self.weapon in self.kill_stats["weapons"]:
            self.kill_stats["weapons"][self.weapon] += kills
        if kills > 0:
            logging.info(f"Kills updated. Total for {self.weapon}: {self.kill_stats['weapons'][self.weapon]}")

    def get_kill_stats(self):
        return self.kill_stats

    def use_grenade(self, grenade_type, room, direction, stdscr):
        """
        Throws a grenade of the specified type in the given direction, showing an animation
        of the grenade traveling up to 6 spaces (or until hitting an obstacle) before exploding.

        If the grenade encounters a monster or an impassable terrain tile, it stops immediately
        and explodes at that location.

        :param grenade_type: Type of grenade (e.g., "Frag Grenade", "Molitov Cocktail")
        :param room: The current Room object
        :param direction: (dx, dy) tuple indicating the throw direction
        :param stdscr: curses window object
        :return: (message, kills)
        """
        dx, dy = direction
        kills = 0
        message = ""

        # Check if player has the grenade
        if grenade_type not in self.grenades or self.grenades[grenade_type] <= 0:
            logging.debug(f"No {grenade_type}s left.")
            return (f"No {grenade_type}s left!", kills)

        # Deduct one grenade
        self.grenades[grenade_type] -= 1

        # Choose a grenade symbol for the animation
        grenade_symbol_map = {
            "Frag Grenade": "0",
            "Molitov Cocktail": "o"
        }
        grenade_symbol = grenade_symbol_map.get(grenade_type, "0")

        # Starting position for animation is player position
        gx, gy = self.x, self.y

        # Define impassable terrain
        impassable_terrain = ["#", "T", "S", "~"]

        # Animate the grenade traveling up to 6 steps
        steps = 6
        final_x, final_y = self.x, self.y  # Where it ends up
        for step in range(1, steps + 1):
            gx = self.x + dx * step
            gy = self.y + dy * step

            # If out of bounds, break early
            if not (0 <= gx < room.grid_width and 0 <= gy < room.grid_height):
                # Grenade stops at last valid position
                gx = self.x + dx * (step - 1)
                gy = self.y + dy * (step - 1)
                break

            # Check the cell we are throwing into
            original_char = room.grid[gy][gx]

            # Temporarily display the grenade symbol
            try:
                stdscr.addstr(gy, gx, grenade_symbol,
                            curses.color_pair(COLOR_TABLE.get("yellow_item", 10)))
            except curses.error:
                logging.debug(f"Failed to render grenade at ({gx}, {gy}).")

            stdscr.refresh()
            curses.napms(100)  # Small delay for animation

            # Restore the original cell content
            try:
                stdscr.addstr(gy, gx, original_char)
            except curses.error:
                pass

            # Now check if this cell has a monster or is impassable terrain
            # Check for monster presence
            hit_monster = False
            for monster in room.monsters:
                if monster.x == gx and monster.y == gy:
                    hit_monster = True
                    break

            if hit_monster or original_char in impassable_terrain:
                # Grenade hits something and stops here
                final_x, final_y = gx, gy
                break
            else:
                # If not hit and not impassable, just continue until next step
                final_x, final_y = gx, gy

        # After animation/hit detection, the grenade lands at (final_x, final_y)
        # Trigger the actual grenade effect
        if grenade_type == "Frag Grenade":
            kills = throw_frag_grenade(stdscr, final_x, final_y, direction, room)
            self.kill_stats["grenades"]["Frag Grenade"] += kills
            message = f"Thrown Frag Grenade! Kills: {kills}"
        elif grenade_type == "Molitov Cocktail":
            kills = throw_molitov(stdscr, final_x, final_y, direction, room)
            self.kill_stats["grenades"]["Molitov Cocktail"] += kills
            message = f"Thrown Molitov Cocktail! Kills: {kills}"
        else:
            message = f"Unknown grenade type: {grenade_type}"
            logging.warning(f"Unknown grenade type: {grenade_type}")

        logging.info(message)
        return (message, kills)


    def pickup_item(self, room):
        """
        Attempts to pick up an item at the player's current position.
        :param room: The current Room object.
        :return: (message, kills) or possibly (message, kills, new_room) if item triggers room change.
        """
        cell_char = room.grid[self.y][self.x]
        if cell_char in ["^", "~"]:
            return ("No item here.", 0)

        items_here = [item for item in room.items.get_items() if (item.x, item.y) == (self.x, self.y)]
        if items_here:
            item = items_here[0]
            # Logic for what the item does
            if item.item_type == "healing":
                self.health = min(self.max_health, self.health + 20)
                message = f"Picked up {item.name} and healed. Health: {self.health}"
            elif item.item_type == "ammo":
                # Assume Ammo Pack adds ammo to current weapon
                added_ammo = 10
                self.weapon_ammo += added_ammo
                message = f"Picked up {item.name}, +{added_ammo} ammo. Ammo: {self.weapon_ammo}"
            elif item.item_type == "grenade":
                # Increase grenade count by 1
                if item.name in self.grenades:
                    self.grenades[item.name] += 1
                else:
                    self.grenades[item.name] = 1
                message = f"Picked up {item.name}. You now have {self.grenades[item.name]}."
            elif item.item_type == "armor":
                self.armor = min(self.max_armor, self.armor + 20)
                message = f"Picked up {item.name}, Armor: {self.armor}"
            else:
                message = f"Picked up {item.name}."

            room.remove_item(item)
            logging.info(message)
            return (message, 0)
        else:
            return ("No item here.", 0)

    def select_grenade_type(self, stdscr):
        """
        Prompt user to select a grenade type if multiple available.
        For now, assume we only have 'Frag Grenade' and 'Molitov Cocktail'.

        Modify as needed for actual UI.
        """
        grenades_available = [g for g, cnt in self.grenades.items() if cnt > 0]
        if not grenades_available:
            return None

        # If only one type available, return it directly
        if len(grenades_available) == 1:
            return grenades_available[0]

        # Otherwise, prompt user to choose. Here we just pick the first for simplicity.
        # Implement UI selection as needed.
        return grenades_available[0]
