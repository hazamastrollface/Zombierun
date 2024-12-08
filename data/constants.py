import curses
import logging

# Configure logging for this module
logging.basicConfig(filename='game.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')


# Define MONSTER_TABLE
MONSTER_TABLE = {
    "Standard Zombie": {
        "type": "zombie",
        "health": 1,
        "attack_power": 10,
        "symbol": "Z",
        "color": "green"
    },
    "Fast Zombie": {
        "type": "zombie",
        "health": 1,
        "attack_power": 5,
        "speed": 2,
        "symbol": "F",
        "color": "yellow"
    },
    "Strong Zombie": {
        "type": "zombie",
        "health": 3,
        "attack_power": 20,
        "symbol": "S",
        "color": "red"
    },
    "Crawler": {
        "type": "crawler",
        "health": 2,
        "attack_power": 8,
        "symbol": "C",
        "color": "cyan"
    },
    "Mutant": {
        "type": "mutant",
        "health": 5,
        "attack_power": 15,
        "speed": 1,
        "symbol": "M",
        "color": "magenta"
    },
}

# Define ITEM_TABLE
# We add weapons here with their own drop rates and symbols
ITEM_TABLE = [
    {"name": "Medkit", "symbol": "*", "type": "healing", "drop_rate": 0.1, "color": "yellow_item"},
    {"name": "Ammo Pack", "symbol": "=", "type": "ammo", "drop_rate": 0.2, "color": "yellow_item"},
    {"name": "Frag Grenade", "symbol": "0", "type": "grenade", "drop_rate": 0.05, "color": "yellow_item"},
    {"name": "Smoke Grenade", "symbol": "o", "type": "grenade", "drop_rate": 0.05, "color": "yellow_item"},
    {"name": "Armor Plate", "symbol": "]", "type": "armor", "drop_rate": 0.1, "color": "yellow_item"},

    # Add weapons as items so they can spawn in rooms
    {"name": "Pistol", "symbol": "P", "type": "weapon", "drop_rate": 0.05, "color": "yellow_message"},
    {"name": "Flamethrower", "symbol": "F", "type": "weapon", "drop_rate": 0.02, "color": "fire_orange"},
    {"name": "RPG", "symbol": "R", "type": "weapon", "drop_rate": 0.01, "color": "red"},
]

# Define WEAPON_TABLE
WEAPON_TABLE = {
    "Pistol": {
        "ammo": 50,
        "symbol": "P",
        "type": "ranged",
        "color": "yellow_message",
        "description": "A standard sidearm with moderate damage and range."
    },
    "Flamethrower": {
        "ammo": 20,
        "symbol": "F",
        "type": "ranged",
        "color": "fire_orange",
        "description": "Emits a continuous stream of fire, effective against multiple enemies."
    },
    "RPG": {
        "ammo": 5,
        "symbol": "R",
        "type": "ranged",
        "color": "red",
        "description": "Launches explosive projectiles, dealing area damage."
    },
}

# Define COLOR_TABLE
COLOR_TABLE = {
    "player": 1,
    "monster": 2,
    "fire_red": 3,
    "fire_orange": 4,
    "tree": 5,
    "grass": 6,
    "border_red": 7,
    "border_green": 8,
    "dirt": 9,
    "yellow_item": 10,
    "green": 11,
    "magenta": 12,
    "cyan": 13,
    "red": 14,
    "yellow_message": 15,
    "yellow": 16,
    "pistol_color": 17,
    "flamethrower_color": 18,
    "rpg_color": 19,
}

# Define TERRAIN_SYMBOLS
TERRAIN_SYMBOLS = {
    "grass": ".",
    "tree": "T",
    "fire_red": "^",
    "fire_orange": "~",
    "wall": "#",
    "dirt": "~",
}

def initialize_colors():
    """
    Initialize curses color pairs for rendering, with a fallback for unsupported terminals.
    """
    if not curses.has_colors():
        logging.error("Terminal does not support colors.")
        raise Exception("Your terminal does not support color.")

    curses.start_color()

    try:
        curses.init_pair(COLOR_TABLE["player"], curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["monster"], curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["fire_red"], curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["fire_orange"], curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["tree"], curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["grass"], curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["border_red"], curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["border_green"], curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["dirt"], curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["yellow_item"], curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["green"], curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["magenta"], curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["cyan"], curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["red"], curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["yellow_message"], curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["yellow"], curses.COLOR_YELLOW, curses.COLOR_BLACK)

        curses.init_pair(COLOR_TABLE["pistol_color"], curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["flamethrower_color"], curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TABLE["rpg_color"], curses.COLOR_RED, curses.COLOR_BLACK)
    except KeyError as e:
        logging.error(f"Color initialization failed. Missing color key: {e}")
        raise KeyError(f"Color '{e.args[0]}' is not defined in COLOR_TABLE.")


def validate_color_table():
    """
    Validates that all colors used in MONSTER_TABLE, ITEM_TABLE, and WEAPON_TABLE are defined in COLOR_TABLE.
    Raises ValueError if any color is missing.
    """
    missing_colors = set()

    # Check colors in MONSTER_TABLE
    for monster in MONSTER_TABLE.values():
        color = monster.get("color")
        if color and color not in COLOR_TABLE:
            missing_colors.add(color)

    # Check colors in ITEM_TABLE
    for item in ITEM_TABLE:
        color = item.get("color")
        if color and color not in COLOR_TABLE:
            missing_colors.add(color)

    # Check colors in WEAPON_TABLE
    for weapon in WEAPON_TABLE.values():
        color = weapon.get("color")
        if color and color not in COLOR_TABLE:
            missing_colors.add(color)

    if missing_colors:
        logging.error(f"Missing color definitions in COLOR_TABLE for: {', '.join(missing_colors)}")
        raise ValueError(f"Missing color definitions in COLOR_TABLE for: {', '.join(missing_colors)}")
    else:
        logging.info("All colors in MONSTER_TABLE, ITEM_TABLE, and WEAPON_TABLE are defined in COLOR_TABLE.")


# Perform validation upon module import
validate_color_table()

def get_terrain_color(terrain_type):
    """
    Maps terrain types to their corresponding color names.
    """
    terrain_to_color = {
        "grass": "grass",
        "tree": "tree",
        "fire_red": "fire_red",
        "fire_orange": "fire_orange",
        "wall": "border_red",
        # Add more mappings if needed, e.g. staircase
    }
    return terrain_to_color.get(terrain_type, "grass")
