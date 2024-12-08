# weapons/flamethrower.py

import time
import curses
import random
import logging  # Ensure logging is imported
from constants import COLOR_TABLE, WEAPON_TABLE

def fire_flamethrower(stdscr, player_x, player_y, direction, room):
    """
    Fires a flamethrower cone in the specified direction with an expanding width.
    The flame alternates colors, leaves lingering fire randomly, and updates room state.

    :param stdscr: The curses standard screen object
    :param player_x: Player's X coordinate
    :param player_y: Player's Y coordinate
    :param direction: Tuple (dx, dy) for firing direction
    :param room: The current Room object
    :return: Number of monsters killed
    """
    dx, dy = direction
    max_length = WEAPON_TABLE["Flamethrower"]["ammo"]  # Using ammo as max_length for example
    kills = 0
    lingering_probability = 0.3  # Probability of a flame remaining as a lingering flame

    for i in range(1, max_length + 1):  # i = 1 to max_length
        for j in range(-i, i + 1):  # Horizontal spread increases with i
            if dx == 0:  # Firing up/down
                x, y = player_x + j, player_y + i * dy
            elif dy == 0:  # Firing left/right
                x, y = player_x + i * dx, player_y + j
            else:  # Diagonal fire
                x, y = player_x + i * dx, player_y + i * dy + j

            if 0 <= x < room.grid_width and 0 <= y < room.grid_height:
                # Decide if this flame should remain as a lingering flame
                if random.random() < lingering_probability:
                    duration = random.randint(4, 6)
                    room.add_lingering_flame(x, y, duration)

                # Render flame using red and orange colors to depict fire
                color_choice = random.choice(["fire_red", "fire_orange"])
                color = curses.color_pair(COLOR_TABLE.get(color_choice, 3))
                try:
                    stdscr.addstr(y, x, "^", color)
                except curses.error:
                    # Handle rendering error, possibly log it
                    pass
                stdscr.refresh()
                time.sleep(0.02)

                # Check if a monster is hit
                monster_hit = next((m for m in room.monsters if m.x == x and m.y == y), None)
                if monster_hit:
                    room.monsters.remove(monster_hit)
                    kills += 1
                    logging.info(f"Flamethrower hit and killed {monster_hit.name} at ({x}, {y}).")

    return kills
