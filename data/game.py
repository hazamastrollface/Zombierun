import curses
import logging
from constants import COLOR_TABLE, WEAPON_TABLE, ITEM_TABLE, TERRAIN_SYMBOLS, initialize_colors
from room import RoomManager
from player import Player
from renderer import Renderer
from monster import MonsterManager  # Handles monster behaviors
from look import look_mode, render_look_info  # Handles look mode

# Configure logging
logging.basicConfig(
    filename='game.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

def exit_game():
    """
    Log and exit the game. curses.wrapper() handles endwin().
    """
    logging.info("Exiting the game.")
    exit(0)

def get_fire_direction(stdscr):
    direction_mapping = {
        ord('7'): (-1, -1),
        ord('8'): (0, -1),
        ord('9'): (1, -1),
        ord('4'): (-1, 0),
        ord('6'): (1, 0),
        ord('1'): (-1, 1),
        ord('2'): (0, 1),
        ord('3'): (1, 1),
    }

    prompt_text = "Select direction (use numpad keys 1-9): "
    try:
        stdscr.addstr(0, 0, prompt_text)
    except curses.error:
        logging.warning("Failed to render direction prompt.")

    stdscr.refresh()
    key = stdscr.getch()
    direction = direction_mapping.get(key)
    if direction:
        logging.info(f"Direction selected: {direction}")
    else:
        logging.warning("Invalid direction selected.")
    return direction

def handle_user_input(key, player, room_manager, current_room, stdscr, grid_width, fire_mode_active):
    message, kills = None, 0

    movement_mapping = {
        ord('7'): (-1, -1),
        ord('8'): (0, -1),
        ord('9'): (1, -1),
        ord('4'): (-1, 0),
        ord('6'): (1, 0),
        ord('1'): (-1, 1),
        ord('2'): (0, 1),
        ord('3'): (1, 1),
    }

    if key in movement_mapping:
        dx, dy = movement_mapping[key]
        direction = (dx, dy)
        if fire_mode_active:
            # Fire weapon in the given direction
            result = player.fire_weapon(direction, current_room, stdscr)
            message, kills = result
            logging.info(f"Fired weapon towards {direction}")
        else:
            # Move the player
            result = player.move(dx=dx, dy=dy, room=current_room)
            if len(result) == 3:
                m, k, new_room = result
                message = m
                kills = k
                current_room = new_room
            else:
                message, kills = result
            logging.info(f"Movement input: dx={dx}, dy={dy}")

            # After moving, auto-pickup items if any
            pickup_result = player.pickup_item(current_room)
            if pickup_result:
                if len(pickup_result) == 3:
                    p_msg, p_k, p_new_room = pickup_result
                    message = (message + " " + p_msg) if message else p_msg
                    kills += p_k
                    current_room = p_new_room
                else:
                    p_msg, p_k = pickup_result
                    message = (message + " " + p_msg) if message else p_msg
                    kills += p_k

    elif key == ord('g'):  # Grenade
        grenade_type = player.select_grenade_type(stdscr)
        if grenade_type:
            direction = get_fire_direction(stdscr)
            if direction:
                result = player.use_grenade(grenade_type, current_room, direction, stdscr)
                if len(result) == 3:
                    message, kills, new_room = result
                    current_room = new_room
                else:
                    message, kills = result
                logging.info(f"Grenade thrown: {grenade_type} towards {direction}")
            else:
                message, kills = "No direction selected for grenade.", 0
                logging.warning("Grenade thrown without direction.")
        else:
            message, kills = "No grenade type selected.", 0
            logging.warning("No grenade type chosen.")

    elif key in [ord('u'), ord('d')]:  # Staircase
        direction = "up" if key == ord('u') else "down"
        result = player.use_staircase(direction, current_room)
        if len(result) == 3:
            message, kills, new_room = result
            current_room = new_room
        else:
            message, kills = result
        logging.info(f"Staircase used: {direction}")

    else:
        logging.debug(f"Unrecognized key pressed: {key}")
        message, kills = "Unrecognized action.", 0

    return (message, kills, current_room)

def setup_window(stdscr):
    try:
        initialize_colors()
    except Exception as e:
        logging.error(f"Color initialization failed: {e}")
        print(str(e))
        return

    curses.curs_set(0)

    grid_width, grid_height = 80, 24
    room_manager = RoomManager(grid_width, grid_height)
    current_room = room_manager.get_room(0, 0, 0)
    player = Player(x=grid_width // 2, y=grid_height // 2, room_manager=room_manager)
    renderer = Renderer(grid_width, grid_height)
    monster_manager = MonsterManager(room=current_room, player=player, stdscr=stdscr)

    look_mode_active = False
    fire_mode_active = False

    while True:
        stdscr.clear()

        # Render game area
        renderer.render_game_area(stdscr, player, current_room)
        unique_monster_types = {monster.type for monster in current_room.monsters}

        # Render sidebar with messages
        renderer.sidebar.render(
            stdscr,
            player,
            player.kill_stats,
            unique_monster_types,
            renderer.messages  # Pass messages to the sidebar
        )

        # Update lingering flames
        current_room.update_lingering_flames()
        stdscr.refresh()

        # Handle monsters
        monster_manager.handle_monsters()
        if player.health <= 0:
            renderer.display_game_over(stdscr)
            curses.napms(3000)
            return

        # Get user input
        key = stdscr.getch()

        if key == ord('q'):
            logging.info("Player quit.")
            return

        # Enter look mode
        if key == ord('l') and not look_mode_active:
            logging.info("Look mode activated.")
            look_mode_active = True
            look_mode(stdscr, current_room, renderer, player)
            look_mode_active = False
            logging.info("Look mode deactivated.")
            continue

        # Toggle fire mode
        if key == ord('z'):
            fire_mode_active = not fire_mode_active
            message = "Fire mode activated!" if fire_mode_active else "Fire mode deactivated!"
            renderer.display_message(message)
            logging.info(f"Fire mode {'activated' if fire_mode_active else 'deactivated'}.")
            continue

        # Handle other inputs
        if not look_mode_active and key != ord('l'):
            message, kills, possibly_new_room = handle_user_input(
                key, player, room_manager, current_room, stdscr, grid_width, fire_mode_active
            )

            if possibly_new_room != current_room:
                current_room = possibly_new_room
                monster_manager.update_room(current_room)
                renderer.display_message(f"Entered new room at ({current_room.x}, {current_room.y}).")
                logging.info(f"Room transitioned to ({current_room.x}, {current_room.y}).")

            if message:
                renderer.display_message(message)
                logging.info(f"Message displayed: {message}")

            if kills > 0:
                player.update_kill_stats(kills)
                logging.info(f"Kills updated: {kills} kill(s).")

def main():
    curses.wrapper(setup_window)
    exit_game()

if __name__ == "__main__":
    main()
