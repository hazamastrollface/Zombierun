import curses
import logging
from constants import COLOR_TABLE, TERRAIN_SYMBOLS
from renderer import get_terrain_color

def look_mode(stdscr, room, renderer, player):
    """
    Allows the player to move a yellow 'X' around the room to inspect.
    Press 'l' to deactivate look mode.
    """
    look_x, look_y = player.x, player.y
    look_color = curses.color_pair(COLOR_TABLE.get("border_green", 8))

    DIRECTIONS = {
        ord('7'): (-1, -1),
        ord('8'): (0, -1),
        ord('9'): (1, -1),
        ord('4'): (-1, 0),
        ord('6'): (1, 0),
        ord('1'): (-1, 1),
        ord('2'): (0, 1),
        ord('3'): (1, 1),
    }

    while True:
        stdscr.clear()

        look_x = max(0, min(look_x, room.grid_width - 1))
        look_y = max(0, min(look_y, room.grid_height - 1))

        renderer.render_game_area(stdscr, player, room)

        # Highlight look position
        try:
            stdscr.addstr(look_y, look_x, "X", look_color)
        except curses.error:
            logging.warning(f"Failed to render look indicator at ({look_x}, {look_y}).")

        render_look_info(stdscr, room, look_x, look_y, renderer)

        stdscr.refresh()

        key = stdscr.getch()
        if key == ord('l'):
            logging.info("Look mode deactivated.")
            break

        if key in DIRECTIONS:
            dx, dy = DIRECTIONS[key]
            look_x += dx
            look_y += dy
            logging.info(f"Look mode moved to: dx={dx}, dy={dy}")

def render_look_info(stdscr, room, look_x, look_y, renderer):
    """
    Displays detailed info about terrain, items, or monsters at look_x, look_y.
    """
    info_y = 0
    sidebar_x = room.grid_width + 2

    # Position
    try:
        stdscr.addstr(info_y, sidebar_x, f"Position: ({look_x}, {look_y})", curses.color_pair(COLOR_TABLE.get("border_red", 7)))
    except curses.error:
        logging.warning(f"Failed to render position info at ({look_x}, {look_y}).")
    info_y += 1

    # Terrain details
    terrain_symbol = room.grid[look_y][look_x]
    terrain_type = next((t for t, sym in TERRAIN_SYMBOLS.items() if sym == terrain_symbol), None)

    if terrain_type:
        terrain_color = get_terrain_color(terrain_type)
        try:
            stdscr.addstr(info_y, sidebar_x, f"Terrain: {terrain_type}", curses.color_pair(COLOR_TABLE.get(terrain_color, 6)))
        except curses.error:
            logging.warning(f"Failed to render terrain info at ({look_x}, {look_y}).")
        info_y += 1
    else:
        try:
            stdscr.addstr(info_y, sidebar_x, "Terrain: Unknown", curses.color_pair(COLOR_TABLE.get("yellow_message", 15)))
        except curses.error:
            logging.warning(f"Failed to render unknown terrain info at ({look_x}, {look_y}).")
        info_y += 1

    # Check for items at look position
    item_found = False
    weapon_found = False
    grenade_found = False

    for item in room.items.get_items():
        if (item.x, item.y) == (look_x, look_y):
            # Check item_type to distinguish between regular items, weapons, and grenades
            if item.item_type == "weapon":
                weapon_found = True
                display_text = f"Weapon: {item.name}"
                color_key = 9  # or some color key for weapons
            elif item.item_type == "grenade":
                grenade_found = True
                display_text = f"Grenade: {item.name}"
                color_key = 11  # or some color key for grenades
            else:
                item_found = True
                display_text = f"Item: {item.name}"
                color_key = 10  # default item color key

            try:
                stdscr.addstr(info_y, sidebar_x, display_text, curses.color_pair(COLOR_TABLE.get(item.color, color_key)))
            except curses.error:
                logging.warning(f"Failed to render {item.item_type} info: {item.name} at ({look_x}, {look_y}).")
            info_y += 1

    # Check for monsters
    monster_found = False
    for monster in room.monsters:
        if (monster.x, monster.y) == (look_x, look_y):
            try:
                stdscr.addstr(info_y, sidebar_x, f"Monster: {monster.name}", curses.color_pair(COLOR_TABLE.get("monster", 2)))
            except curses.error:
                logging.warning(f"Failed to render monster info: {monster.name} at ({look_x}, {look_y}).")
            info_y += 1
            monster_found = True

    # If nothing found
    if not (item_found or weapon_found or grenade_found or monster_found):
        try:
            stdscr.addstr(info_y, sidebar_x, "Nothing here...", curses.color_pair(COLOR_TABLE.get("yellow_message", 15)))
        except curses.error:
            logging.warning(f"Failed to render 'Nothing here...' at ({look_x}, {look_y}).")
