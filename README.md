This is Zombierun Pre-Alpha_0.1.2, Devs are welcome

To run the game you must have pyton installed, open terminal in the game directory and type:

python3 game.py

Changelog:

-GamePlay-

Larger grid

Death now possible

Health and Armor work

Rooms and Floors are generated, 1 staircase per floor, find it to move down a floor

MORE MONSTERS

Player and Monsters will displace eachother, no more stacking monsters on you.

Fixed Some Colors

Better Flamethrowers that leave behind lingering flames

Better Lingering Flames,

Better Sidebar that lists Monsters in the room

Look Feature, press L to look at items/terrain/monsters to see what they are

-Other Changes-

Colors work

Error handling and logging

Constants.py holds all color item and terrain dictionaries as well as weapons and their defaukt

Better Item Pickup Check,

Player Class overhaul

Updated Room.py significantly

MANY modularity changes

Massive Room.py overhaul

Terrain is now pulled from constants.py, along with items and monsters

All zombie.py is refactored into of monster.py for modularity

render.py now uses terrain.py and works with new monster.py


