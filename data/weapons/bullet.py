import curses
import time
import logging
from constants import COLOR_TABLE, TERRAIN_SYMBOLS  # Import constants

def render_bullet(stdscr, player_x, player_y, direction, room):
    """
    Renders an enhanced bullet animation fired from the player's weapon in the specified direction.
    Returns the number of monsters killed by the bullet.

    Parameters:
    - stdscr: The main curses window.
    - player_x, player_y: Starting coordinates of the bullet (player's position).
    - direction: Tuple (dx, dy) indicating the direction of the bullet.
    - room: The current Room object containing grid, monsters, etc.

    Returns:
    - kills (int): Number of monsters killed by the bullet.
    """
    dx, dy = direction
    # Define bullet symbols based on direction for better visualization
    bullet_symbols = {
        (1, 0): "→",   # Right
        (-1, 0): "←",  # Left
        (0, 1): "↓",   # Down
        (0, -1): "↑",  # Up
        (1, 1): "↘",   # Down-Right
        (-1, 1): "↙",  # Down-Left
        (1, -1): "↗",  # Up-Right
        (-1, -1): "↖", # Up-Left
    }
    bullet_symbol = bullet_symbols.get(direction, ">")  # Default symbol if direction not mapped

    # Define bullet color using COLOR_TABLE
    BULLET_COLOR = curses.color_pair(COLOR_TABLE.get("cyan", 13))  # Use 'cyan' for bullets

    # Initialize bullet position
    bullet_x, bullet_y = player_x, player_y

    kills = 0  # Initialize kill count

    # Animation parameters
    sleep_time = 0.02  # 20 milliseconds between frames
    max_distance = max(room.grid_width, room.grid_height)  # Maximum possible distance

    for distance in range(1, max_distance):
        # Calculate next position
        next_x = bullet_x + dx
        next_y = bullet_y + dy

        # Check boundaries
        if not (0 <= next_x < room.grid_width and 0 <= next_y < room.grid_height):
            logging.debug(f"Bullet exited room boundaries at ({next_x}, {next_y}).")
            break  # Bullet exits the room

        # Check terrain collision
        terrain_symbol = room.grid[next_y][next_x]
        if terrain_symbol in [TERRAIN_SYMBOLS["wall"], TERRAIN_SYMBOLS["tree"]]:
            # Render impact symbol
            try:
                impact_color = curses.color_pair(COLOR_TABLE.get("border_red", 7))
                stdscr.addstr(next_y, next_x, "X", impact_color)
                stdscr.refresh()
                logging.info(f"Bullet impacted terrain '{terrain_symbol}' at ({next_x}, {next_y}).")
            except curses.error:
                logging.error(f"Failed to render impact at ({next_x}, {next_y}).")
            break  # Bullet stops upon hitting terrain

        # Check for collision with monsters
        hit_monster = None
        for monster in room.monsters:
            if (next_x, next_y) == (monster.x, monster.y):
                hit_monster = monster
                break

        if hit_monster:
            # Apply damage to the monster
            monster.take_damage(monster.health)  # Assume take_damage reduces health and checks if dead
            kills += 1
            # Render impact symbol
            try:
                impact_color = curses.color_pair(COLOR_TABLE.get("border_red", 7))
                stdscr.addstr(next_y, next_x, "X", impact_color)
                stdscr.refresh()
                logging.info(f"Bullet hit and killed {hit_monster.name} at ({next_x}, {next_y}).")
            except curses.error:
                logging.error(f"Failed to render monster hit at ({next_x}, {next_y}).")
            break  # Bullet stops after hitting a monster

        # Render bullet
        try:
            stdscr.addstr(next_y, next_x, bullet_symbol, BULLET_COLOR)
            stdscr.refresh()
        except curses.error:
            logging.error(f"Failed to render bullet at ({next_x}, {next_y}).")

        # Update previous bullet position if needed
        if (0 <= bullet_x < room.grid_width and 0 <= bullet_y < room.grid_height):
            # Only restore terrain if the bullet isn't hitting something
            try:
                terrain_color = curses.color_pair(COLOR_TABLE.get(get_terrain_color(room.grid[bullet_y][bullet_x]), 6))
                stdscr.addstr(bullet_y, bullet_x, room.grid[bullet_y][bullet_x], terrain_color)
            except curses.error:
                logging.error(f"Failed to restore terrain at ({bullet_x}, {bullet_y}).")

        # Update bullet position
        bullet_x, bullet_y = next_x, next_y

        # Pause for animation
        time.sleep(sleep_time)

    # Clear the last bullet position if it wasn't an impact
    if (0 <= bullet_x < room.grid_width and 0 <= bullet_y < room.grid_height) and terrain_symbol not in [TERRAIN_SYMBOLS["wall"], TERRAIN_SYMBOLS["tree"]]:
        try:
            stdscr.addstr(bullet_y, bullet_x, room.grid[bullet_y][bullet_x], curses.color_pair(COLOR_TABLE.get(get_terrain_color(room.grid[bullet_y][bullet_x]), 6)))
            stdscr.refresh()
        except curses.error:
            logging.error(f"Failed to clear bullet at ({bullet_x}, {bullet_y}).")

    return kills  # Return the number of kills


def get_terrain_color(symbol):
    """
    Maps terrain symbols to their corresponding color names.

    :param symbol: Terrain symbol character.
    :return: String representing the color name.
    """
    terrain_to_color = {
        ".": "grass",
        "T": "tree",
        "^": "fire_red",
        "#": "border_red",
        "~": "dirt",
    }
    return terrain_to_color.get(symbol, "grass")  # Default to 'grass' if not found
