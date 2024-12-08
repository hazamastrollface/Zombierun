import time
import curses
import random
import logging
from constants import COLOR_TABLE

def throw_frag_grenade(stdscr, player_x, player_y, direction, room):
    """
    Simulates throwing a frag grenade in the specified direction.
    Shows an explosion animation, damages monsters in the area,
    and leaves behind lingering flames.

    :param stdscr: The curses window object.
    :param player_x: X-coordinate of the player (starting position).
    :param player_y: Y-coordinate of the player (starting position).
    :param direction: Tuple (dx, dy) indicating the direction of the throw.
    :param room: The current Room object.
    :return: Number of monsters killed by the explosion.
    """
    dx, dy = direction
    kills = 0

    # Calculate impact point
    grenade_x = player_x + dx
    grenade_y = player_y + dy

    # Check bounds
    if not (0 <= grenade_x < room.grid_width and 0 <= grenade_y < room.grid_height):
        logging.warning(f"Frag grenade went out of bounds at ({grenade_x}, {grenade_y}).")
        return kills

    # Define explosion area (3x3)
    explosion_coords = [(grenade_x + i, grenade_y + j) for i in range(-1, 2) for j in range(-1, 2)]

    # Explosion animation steps
    # We'll show an expanding pattern of '*' and then revert to the original cells
    # Original chars need to be stored to restore after animation
    original_chars = {}
    for (ex, ey) in explosion_coords:
        if 0 <= ex < room.grid_width and 0 <= ey < room.grid_height:
            original_chars[(ex, ey)] = room.grid[ey][ex]

    # Animation phases
    explosion_chars = ["*", "+", "X"]
    for phase_char in explosion_chars:
        for (ex, ey) in explosion_coords:
            if 0 <= ex < room.grid_width and 0 <= ey < room.grid_height:
                # Attempt to display the explosion char
                try:
                    stdscr.addstr(ey, ex, phase_char, curses.color_pair(COLOR_TABLE.get("fire_red", 3)))
                except curses.error:
                    pass
        stdscr.refresh()
        curses.napms(100)  # Small delay between phases

    # Restore original chars (not strictly necessary if we overwrite them anyway)
    for (ex, ey) in explosion_coords:
        if 0 <= ex < room.grid_width and 0 <= ey < room.grid_height:
            orig_char = original_chars.get((ex, ey), ".")
            # We'll overwrite this anyway after calculating damage, but let's restore to avoid screen glitches
            try:
                stdscr.addstr(ey, ex, orig_char)
            except curses.error:
                pass
    stdscr.refresh()

    # Apply damage and set fire ('^') or leave flames
    for (ex, ey) in explosion_coords:
        if 0 <= ex < room.grid_width and 0 <= ey < room.grid_height:
            # Damage monsters
            for monster in room.monsters[:]:
                if monster.x == ex and monster.y == ey:
                    room.monsters.remove(monster)
                    kills += 1
                    logging.info(f"Frag grenade killed {monster.name} at ({ex}, {ey}).")

            # Replace terrain with a fire symbol
            # Instead of permanently setting '^', let's just restore grass '.' and then add flames.
            # The flames will be shown in the renderer as '^' anyway if implemented there.
            room.grid[ey][ex] = "."  # Revert to grass
            # Random chance to leave a lingering flame (50% chance)
            if random.random() < 0.5:
                # Duration can be adjusted as needed
                flame_duration = random.randint(3, 7)
                room.add_lingering_flame(ex, ey, duration=flame_duration)

    logging.info(f"Frag grenade explosion at ({grenade_x}, {grenade_y}) with {kills} monster(s) killed.")
    return kills
