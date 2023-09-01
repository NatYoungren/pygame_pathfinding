import numpy as np


# NOTE: Currently only integers are used for accuracy, no floats.
# TODO: Encapsulate in class for simple resetting/initialization




# Grid size
GRID_W, GRID_H = 100, 100


# Cost to travel through each tile, used to define terrain
DEFAULT_COST = 1 # Default cost of each tile, serves as a 'distance' multiplier
WALL_COST = -1   # If cost is negative, cells are impassable (i.e. walls)
                 # TODO: Negative movement cost would be interesting, does it break A*?
COST_GRID = np.full((GRID_W, GRID_H), fill_value=DEFAULT_COST, dtype=int)

# Heuristic distance from each tile to the end, (can be precomputed, but not necessary)
H_GRID = np.full((GRID_W, GRID_H), fill_value=np.inf, dtype=int)

# Distance from start to each tile, based on shortest path found so far
G_GRID = np.full((GRID_W, GRID_H), fill_value=np.inf, dtype=int)

# Sum of G and H
F_GRID = np.full((GRID_W, GRID_H), fill_value=np.inf, dtype=int)

# Parent of each tile, used to reconstruct path. (stored as (x, y) coords)
P_GRID = np.full((GRID_W, GRID_H, 2), fill_value=-1, dtype=int)

# Holds status of each tile, 0 = unvisited, 1 = frontier, -1 = searched
FRONTIER = np.zeros((GRID_W, GRID_H), dtype=int)

# TODO: Maybe remove and leave for visualization to track.
STORED_PATH = []

# Track number of steps
STEP_COUNT = 0


def reset_grids():
    COST_GRID.fill(DEFAULT_COST)
    H_GRID.fill(np.inf)
    G_GRID.fill(np.inf)
    F_GRID.fill(np.inf)
    P_GRID.fill(-1)
    FRONTIER.fill(0)
    STORED_PATH.clear()
    
    global STEP_COUNT
    STEP_COUNT = 0


def step(end_pos, path_var=None):
    """ Progress pathfinding by one step, selecting and exploring a single cell.

    Args:
        end_pos (int, int): Position of end cell, for heuristic calculation
        path_var (list, optional): Will reset path_var and populate with shortest path to chosen cell. Defaults to None.

    Returns:
        bool: True if end_pos was explored this step, False otherwise
    """
    if not any(FRONTIER.flatten() == 1):
        print('No more positions to check')
        return
    
    next_pos = select_next_pos()
    add_neighbors_to_frontier(next_pos, end_pos)
    FRONTIER[next_pos] = -1 # Mark as searched
    if path_var is not None:
        path_var[:] = reconstruct_path(next_pos)

    return next_pos == end_pos


def select_next_pos():
    """ Selects most promising cell from viable frontier cells
            > Frontier cell -> lowest f -> lowest h
            > i.e. Unexplored cell that could be on the shortest path that is closest to the end.

    Returns:
        tuple: (int x, int y) coordinate of next cell to search
    """

    masked_f = np.ma.masked_where(FRONTIER != 1, F_GRID)                # Mask to only unexplored frontier nodes
    masked_h = np.ma.masked_where(masked_f != np.min(masked_f), H_GRID) # Mask further to only nodes with the lowest f
    return_pos = np.argmin(masked_h)                                    # Return argument that is closest to the end node
    return tuple(np.unravel_index(return_pos, H_GRID.shape))            # Return coordinate in 2D


def add_neighbors_to_frontier(pos, end_pos):
    """ Adds all direct neighbors of a cell to the frontier.
            > x = origin, o = neighbor, . = not added
        . . . . .
        . o o o .
        . o x o .
        . o o o .
        . . . . .
    Args:
        pos (int, int): origin cell
        end_pos (int, int): Coordinates of the end cell, for heuristic calculation
    """
    for w in range(-1, 2):
        for h in range(-1, 2):
            if w == 0 and h == 0: # Skip if origin cell
                continue
            
            neighbor_pos = (pos[0] + w, pos[1] + h)
            add_to_frontier(neighbor_pos, end_pos, pos)


def add_to_frontier(pos, end_pos, prev_pos=None):
    """ Adds a cell to the frontier, calculating its f, g, and h values.

    Args:
        pos (int, int): Position of cell to add
        end_pos (int, int): Position of end cell, for heuristic calculation
        prev_pos ((int, int), optional): Position of parent cell, to track prior path. Defaults to None.
    """
    # If out of bounds, 
    if pos[0] < 0 or pos[0] >= GRID_W or pos[1] < 0 or pos[1] >= GRID_H:
        return
    
    # If cost of tile is negative, it is impassable.
    if COST_GRID[pos] < 0:
        return
    
    if prev_pos is None:
        # If prev pos is None, we are at the starting node
        g = 0
    else:
        # Otherwise, calculate distance from start to this node
        #   > g = (distance from prev node to start) + (distance from this node to prev node * cost of this node)
        g = G_GRID[prev_pos] + distance_heuristic(pos, prev_pos) * COST_GRID[pos]
    
    
    # If we have not yet calculated the distance from this node to the end, do so now
    if np.isinf(H_GRID[pos]):
        H_GRID[pos] = distance_heuristic(pos, end_pos)
    
    # Our f is the sum of our g and h, representing an ideal shortest path from start to end through this node
    f = g + H_GRID[pos]

    if f < F_GRID[pos]:
        F_GRID[pos] = f
        G_GRID[pos] = g
        # H_GRID[pos] = h
        # P_GRID[pos] = prev_pos
        # NOTE: May need to update the entire chain of children, if one exists
        FRONTIER[pos] = 1
        
        if prev_pos is not None:
            P_GRID[pos] = prev_pos

def distance_heuristic(pos1, pos2, orthogonal_cost=10, diagonal_cost=14):
    """ Provides a heuristic distance between 2 cells, assuming no obstructions.
        One cell of diagonal movement costs 14, horizontal/vertical movement is 10.
        This is roughly sqrt(2) and 1, while removing float innacuracy.
        Diagonal movement is the most efficient way to travel, and will be prioritized
            

    Args:
        pos1 (int, int): Cell coordinate
        pos2 (int, int): Cell coordinate
        orthogonal_cost (int, optional): Cost of horizontal/vertical travel. Defaults to 10.
        diagonal_cost (int, optional): Cost of diagonal travel. Defaults to 14.

    Returns:
        int: Heuristic distance between the 2 cells
    """
    # Convert to distance vector
    vector = np.abs(np.array(pos1) - np.array(pos2))
    
    # Orthogonal movement is the difference between h and v travel, diagonal is the overlap.
    return int(orthogonal_cost * abs(vector[0] - vector[1]) + diagonal_cost * min(vector))

    # NOTE: Estimating and casting to integer vastly reduces cell recalculations due to float innacuracy/minute differences

    # # Old grid heuristic, still used floats and had innacuracy as a result.
    # return abs(vector[0] - vector[1]) + 1.4 * min(vector)

    # # Original heuristic, used euclidean distance which is not 1-to-1 with grid travel distance
    # return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)


def reconstruct_path(pos):
    
    path = [pos]
    while -1 not in P_GRID[pos]:
        pos = tuple(P_GRID[pos])
        path.append(pos)
    return path[::-1] # Reversed to give path from start -> end

# NOTE: Leave at top level
# def get_tile(pos, screen_h, screen_w):
#     pos = np.array(pos)
#     np.clip(pos[:1], 0, SCREEN_W-1, out=pos[:1])
#     np.clip(pos[0:], 0, SCREEN_H-1, out=pos[0:])
#     return (int(pos[0] / CELL_W), int(pos[1] / CELL_H))