import curses
import logging
import random
from constants import TERRAIN_SYMBOLS, COLOR_TABLE, WEAPON_TABLE, get_terrain_color

logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

class Sidebar:
    def __init__(self, grid_width, grid_height, sidebar_width=60):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.sidebar_width = sidebar_width

    def render(self, stdscr, player, kill_stats, monster_types, messages):
        # Sidebar positioning
        x_offset = self.grid_width + 2
        sidebar_width = self.sidebar_width
        content_width = sidebar_width - 4  # Account for borders and padding

        # ASCII Art Symbols
        corner_top_left = "╔"
        corner_top_right = "╗"
        corner_bottom_left = "╚"
        corner_bottom_right = "╝"
        tube_horizontal = "═"
        tube_vertical = "║"

        # Colors
        border_color = curses.color_pair(COLOR_TABLE.get("border_green", 8))
        text_color = curses.color_pair(COLOR_TABLE.get("yellow_message", 15))
        health_color = curses.color_pair(COLOR_TABLE.get("fire_red", 3))
        armor_color = curses.color_pair(COLOR_TABLE.get("border_green", 8))
        kills_color = curses.color_pair(COLOR_TABLE.get("monster", 2))
        grenade_color = curses.color_pair(COLOR_TABLE.get("magenta", 12))

        # Draw Header
        try:
            stdscr.addstr(0, x_offset, f"{corner_top_left}{tube_horizontal * (sidebar_width - 2)}{corner_top_right}", border_color)
            title = "☣ CONDITION REPORT ☣"
            stdscr.addstr(1, x_offset + 2, title.center(content_width), text_color)
            stdscr.addstr(2, x_offset, f"{tube_vertical}{' ' * (sidebar_width - 2)}{tube_vertical}", border_color)
        except curses.error:
            logging.warning("Failed to render sidebar header.")

        def print_line(line_y, content, color):
            """
            Prints a single line of text inside the sidebar.
            """
            padded_content = content[:content_width].ljust(content_width)
            line = f"{tube_vertical} {padded_content} {tube_vertical}"
            try:
                stdscr.addstr(line_y, x_offset, line, color)
            except curses.error:
                logging.warning(f"Failed to render line: {content}")

        # Render Player Stats
        print_line(3, f"⚠ Health: {player.get_health_bar()}", health_color)
        print_line(4, f"⚠ Armor:  {player.get_armor_bar()}", armor_color)

        # Render Kills
        total_kills = sum(kill_stats.get("weapons", {}).values()) + sum(kill_stats.get("grenades", {}).values())
        print_line(5, f"☢ Kills: {total_kills}", kills_color)

        # Render Grenades
        line_index = 6
        for grenade_type, count in player.grenades.items():
            if count > 0:
                grenade_text = f"☣ {grenade_type}: {count}"
                print_line(line_index, grenade_text, grenade_color)
                line_index += 1

        # Render Hostiles
        if monster_types:
            print_line(line_index, "Hostiles:", kills_color)
            line_index += 1
            for monster in monster_types:
                if line_index >= self.grid_height - 6:  # Reserve space for messages
                    break  # Avoid exceeding sidebar height
                print_line(line_index, f"- {monster}", kills_color)
                line_index += 1

        # Messages Console
        message_start = self.grid_height - 6  # Reserve the bottom 5 lines for messages
        print_line(message_start, "Messages:", text_color)
        message_index = message_start + 1
        max_messages = 4
        for i, message in enumerate(messages[-max_messages:]):  # Show the last few messages
            print_line(message_index, message, text_color)
            message_index += 1

        # Draw Footer
        footer_y = self.grid_height - 1
        try:
            stdscr.addstr(footer_y, x_offset, f"{corner_bottom_left}{tube_horizontal * (sidebar_width - 2)}{corner_bottom_right}", border_color)
        except curses.error:
            logging.warning("Failed to render sidebar footer.")




class Renderer:
    def __init__(self, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.sidebar = Sidebar(grid_width, grid_height, sidebar_width=60)
        self.messages = []
        self.max_messages = 5

    def display_message(self, message):
        if message:
            self.messages.append(message)
            if len(self.messages) > self.max_messages:
                self.messages.pop(0)

    def render_game_area(self, stdscr, player, current_room):
        if current_room:
            monster_positions = {(m.x, m.y): m for m in current_room.monsters}
            item_positions = {(it.x, it.y): it for it in current_room.items.get_items()}
            flame_positions = {tuple(f["position"]): f for f in current_room.lingering_flames}

            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    cell = current_room.grid[y][x]
                    if cell:
                        terrain_type = next((t for t, s in TERRAIN_SYMBOLS.items() if s == cell), "grass")
                        color_name = get_terrain_color(terrain_type)
                        color = curses.color_pair(COLOR_TABLE.get(color_name, 6))
                        try:
                            stdscr.addstr(y, x, cell, color)
                        except curses.error:
                            logging.error(f"Failed to render terrain at ({x}, {y}).")

                    # Player
                    if (x, y) == (player.x, player.y):
                        player_color = curses.color_pair(COLOR_TABLE.get("player", 1))
                        try:
                            stdscr.addstr(y, x, "@", player_color)
                        except curses.error:
                            logging.error(f"Failed to render player at ({x}, {y}).")
                        continue

                    # Monster
                    elif (x, y) in monster_positions:
                        monster = monster_positions[(x, y)]
                        monster_color = curses.color_pair(COLOR_TABLE.get(monster.color, 2))
                        try:
                            stdscr.addstr(y, x, monster.symbol, monster_color)
                        except curses.error:
                            logging.error(f"Failed to render monster {monster.name} at ({x}, {y}).")
                        continue

                    # Item
                    elif (x, y) in item_positions:
                        item = item_positions[(x, y)]
                        if item.item_type == "weapon":
                            item_color_name = WEAPON_TABLE.get(item.name, {}).get("color", "fire_orange")
                            item_color = curses.color_pair(COLOR_TABLE.get(item_color_name, 4))
                        elif item.item_type == "grenade":
                            item_color = curses.color_pair(COLOR_TABLE.get("magenta", 12))
                        else:
                            item_color = curses.color_pair(COLOR_TABLE.get("yellow_message", 15))
                        try:
                            stdscr.addstr(y, x, item.symbol, item_color)
                        except curses.error:
                            logging.error(f"Failed to render item {item.name} at ({x}, {y}).")
                        continue

                    # Flame
                    elif (x, y) in flame_positions:
                        flame = flame_positions[(x, y)]
                        flame_color_name = random.choice(["fire_red", "fire_orange"])
                        flame_color = curses.color_pair(COLOR_TABLE.get(flame_color_name, 3))
                        try:
                            stdscr.addstr(y, x, "^", flame_color)
                        except curses.error:
                            logging.error(f"Failed to render flame at ({x}, {y}).")
                        continue

            self.render_borders(stdscr, current_room)

    def render_borders(self, stdscr, current_room):
        room_x, room_y = current_room.x, current_room.y
        floor_width, floor_height = self.grid_width, self.grid_height
        screen_height, screen_width = stdscr.getmaxyx()
        connection_symbol_top = "^"
        connection_symbol_bottom = "v"
        connection_symbol_left = "<"
        connection_symbol_right = ">"
        wall_symbol = TERRAIN_SYMBOLS.get("wall", "#")

        for x in range(self.grid_width):
            if x >= screen_width:
                continue
            y = 0
            if room_y > 0:
                try:
                    stdscr.addstr(y, x, connection_symbol_top, curses.color_pair(COLOR_TABLE.get("border_green", 8)))
                except curses.error:
                    logging.warning(f"Failed to render top connection symbol.")
            else:
                try:
                    stdscr.addstr(y, x, wall_symbol, curses.color_pair(COLOR_TABLE.get("border_red", 7)))
                except curses.error:
                    logging.warning("Failed to render top wall symbol.")

            bottom_y = self.grid_height - 1
            if bottom_y < screen_height:
                if room_y < floor_height - 1:
                    try:
                        stdscr.addstr(bottom_y, x, connection_symbol_bottom, curses.color_pair(COLOR_TABLE.get("border_green", 8)))
                    except curses.error:
                        logging.warning("Failed to render bottom connection symbol.")
                else:
                    try:
                        stdscr.addstr(bottom_y, x, wall_symbol, curses.color_pair(COLOR_TABLE.get("border_red", 7)))
                    except curses.error:
                        logging.warning("Failed to render bottom wall symbol.")

        for y in range(self.grid_height):
            if y >= screen_height:
                continue
            if room_x > 0:
                try:
                    stdscr.addstr(y, 0, connection_symbol_left, curses.color_pair(COLOR_TABLE.get("border_green", 8)))
                except curses.error:
                    logging.warning("Failed to render left connection symbol.")
            else:
                try:
                    stdscr.addstr(y, 0, wall_symbol, curses.color_pair(COLOR_TABLE.get("border_red", 7)))
                except curses.error:
                    logging.warning("Failed to render left wall symbol.")

            right_x = self.grid_width - 1
            if right_x < screen_width:
                if room_x < floor_width - 1:
                    try:
                        stdscr.addstr(y, right_x, connection_symbol_right, curses.color_pair(COLOR_TABLE.get("border_green", 8)))
                    except curses.error:
                        logging.warning("Failed to render right connection symbol.")
                else:
                    try:
                        stdscr.addstr(y, right_x, wall_symbol, curses.color_pair(COLOR_TABLE.get("border_red", 7)))
                    except curses.error:
                        logging.warning("Failed to render right wall symbol.")

    def render_messages(self, stdscr):
        sidebar_x = self.grid_width + 2
        left_col_width = 30
        right_col_x = sidebar_x + left_col_width + 1

        displayed_messages = self.messages[-self.max_messages:]
        for idx, message in enumerate(displayed_messages):
            line_y = idx
            if line_y < self.grid_height - 2:
                try:
                    stdscr.addstr(line_y, right_col_x, message.ljust(self.sidebar.sidebar_width - left_col_width - 2),
                                  curses.color_pair(COLOR_TABLE.get("yellow_message", 15)))
                except curses.error:
                    logging.error(f"Failed to render message: {message}")
            else:
                logging.warning("Not enough vertical space for messages in right column!")
                break

    def display_game_over(self, stdscr):
        game_over_text = "GAME OVER"
        message = "You have been defeated! Press any key to exit."
        screen_height, screen_width = stdscr.getmaxyx()
        try:
            stdscr.addstr(screen_height // 2 - 1, (screen_width - len(game_over_text)) // 2,
                          game_over_text, curses.A_BOLD | curses.color_pair(COLOR_TABLE.get("border_red", 7)))
            stdscr.addstr(screen_height // 2, (screen_width - len(message)) // 2,
                          message, curses.A_BOLD | curses.color_pair(COLOR_TABLE.get("border_green", 8)))
            stdscr.refresh()
            stdscr.getch()
        except curses.error:
            logging.error("Failed to render game over screen.")
