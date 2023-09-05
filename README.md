# pygame_pathfinding
Implementation and visualization of A* pathfinding algorithm.


main.py drives a pygame window through which the pathfinding simulation may be controlled and reset.

Generic A* implementation has been extended to account for variable terrain cost and portal movement.

Optimal pathing (presumably) through multiple portals is possible due to modifications to the A* heuristic calculation, although runtime complexity suffers as the number of portals increases.

Numba implementation, further logical improvements, and reducing the need for duplicate heuristic calculations could further improve runtime.

Dependencies:
-- numpy == '1.24.4'
-- pygame == '2.5.1'
