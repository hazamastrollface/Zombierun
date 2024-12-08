import time
import curses
import random

def throw_molitov(stdscr, player_x, player_y, direction, room):
    """
    Simulates throwing a Molotov cocktail in a specified direction.
    The Molotov lands and creates a fire that covers a radius, damaging monsters
    and leaving lingering flames.
    """
    dx, dy = direction
    grenade_path = []
    kills = 0  # Initialize kills counter

    # Calculate Molotov landing point, stopping if it hits a wall or a monster
    for step in range(6):  # Max Molotov range is 6 spaces
        x = player_x + dx * step
        y = player_y + dy * step
        if 0 <= x < room.grid_width and 0 <= y < room.grid_height:
            grenade_path.append((x, y))
            # Stop if a monster is in the path
            if next((m for m in room.monsters if (m.x, m.y) == (x, y)), None):
                break
        else:
            break  # Stop if Molotov goes out of bounds

    # Render the Molotov trajectory
    for i, (x, y) in enumerate(grenade_path):
        # Render Molotov symbol
        stdscr.addstr(y, x, "o", curses.color_pair(4))  # Molotov symbol in orange
        stdscr.refresh()
        time.sleep(0.1)  # Delay for trajectory animation

        # Restore previous position with the terrain
        if i > 0:
            prev_x, prev_y = grenade_path[i - 1]
            stdscr.addstr(prev_y, prev_x, room.grid[prev_y][prev_x])  # Restore terrain symbol
            stdscr.refresh()

    # The Molotov lands at the last valid position
    if grenade_path:
        fire_x, fire_y = grenade_path[-1]

        # Define the fire area as a 6x6 radius centered on the landing point
        fire_radius = 3
        for i in range(-fire_radius, fire_radius + 1):
            for j in range(-fire_radius, fire_radius + 1):
                x = fire_x + i
                y = fire_y + j
                if 0 <= x < room.grid_width and 0 <= y < room.grid_height:
                    distance = abs(i) + abs(j)
                    if distance <= fire_radius:
                        # Render fire effect
                        stdscr.addstr(y, x, "^", curses.color_pair(3))  # Fire symbol in red
                        stdscr.refresh()

                        # Damage monsters within the fire radius
                        monster_hit = next((m for m in room.monsters if (m.x, m.y) == (x, y)), None)
                        if monster_hit:
                            monster_hit.take_damage(2)  # Apply Molotov damage
                            if monster_hit.health <= 0:  # Remove dead monsters
                                room.monsters.remove(monster_hit)
                                kills += 1

                        # Add lingering flames
                        room.add_lingering_flame(x, y)

        time.sleep(0.5)  # Pause for fire effect

    return kills  # Return the count of monsters killed
