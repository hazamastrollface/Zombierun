# weapons/rpg.py

import logging
from constants import TERRAIN_SYMBOLS, COLOR_TABLE

def fire_rpg(player_x, player_y, direction, room):
    """
    Fires an RPG rocket in the specified direction. The rocket travels in a straight line,
    and upon contact with a wall or monster, explodes in a 15x15 area, killing monsters and
    updating room state.

    :param player_x: Player's X coordinate
    :param player_y: Player's Y coordinate
    :param direction: Tuple (dx, dy) indicating firing direction
    :param room: The current Room object
    :return: Number of monsters killed
    """
    dx, dy = direction
    rocket_symbol = {
        (1, 0): "→",   # Right
        (-1, 0): "←",  # Left
        (0, -1): "↑",  # Up
        (0, 1): "↓"    # Down
    }.get(direction, "*")  # Default to "*" if direction is not found

    x, y = player_x, player_y
    kills = 0

    # Simulate rocket movement
    while 0 <= x < room.grid_width and 0 <= y < room.grid_height:
        # Check for monster at current position
        monster_hit = next((m for m in room.monsters if m.x == x and m.y == y), None)
        if monster_hit:
            kills += explode_rpg(x, y, room)
            return kills

        # Check for collision with terrain (non-grass)
        if room.grid[y][x] != TERRAIN_SYMBOLS["grass"]:
            kills += explode_rpg(x, y, room)
            return kills

        # Move rocket forward
        x += dx
        y += dy

    # If rocket goes out of bounds, explode at the last valid position
    kills += explode_rpg(x - dx, y - dy, room)
    return kills

def explode_rpg(center_x, center_y, room):
    """
    Handles the explosion of the RPG, damaging all monsters in a 15x15 area
    and adding lingering fire effects.

    :param center_x: The X coordinate of the explosion center
    :param center_y: The Y coordinate of the explosion center
    :param room: The current Room object
    :return: Number of monsters killed
    """
    explosion_radius = 7  # 15x15 area -> radius of 7 from the center
    explosion_symbol = "*"  # Symbol representing explosion
    kills = 0

    for dy in range(-explosion_radius, explosion_radius + 1):
        for dx in range(-explosion_radius, explosion_radius + 1):
            x = center_x + dx
            y = center_y + dy
            if 0 <= x < room.grid_width and 0 <= y < room.grid_height:
                # Add lingering fire effect
                room.add_lingering_flame(x, y, duration=4)

                # Check if a monster is hit
                monster_hit = next((m for m in room.monsters if m.x == x and m.y == y), None)
                if monster_hit:
                    room.monsters.remove(monster_hit)
                    kills += 1
                    logging.info(f"RPG explosion hit and killed {monster_hit.name} at ({x}, {y}).")

    logging.info(f"RPG exploded at ({center_x}, {center_y}), killing {kills} monster(s).")
    return kills
