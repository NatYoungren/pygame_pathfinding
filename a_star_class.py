import numpy as np

# TODO: Implement non-grid version of A* (i.e. for a continuous space or graph)
# TODO: Implement teleportation to allow for non-grid movement (i.e. portals), must be factored into heuristic calculation

class A_Star():
    
    def __init__(self, w:int=20, h:int=20,
                 start_pos:(int, int)=None, end_pos:(int, int)=None,
                 default_cost:int=1, wall_cost:int=-1) -> None:
        
         # Width and height of grid
        self.w, self.h = w, h
        
        # Start and end positions
        self.start_pos, self.end_pos = start_pos, end_pos
        
        # Distance multiplier of each tile, used to define terrain
        self.default_cost = default_cost    # 1 = normal, 2 = twice as hard to travel through, etc.
        
        # TODO: Remove all reference to wall_cost, as it should be handled externally?
        self.wall_cost = wall_cost          # If cost is negative, cells are impassable (i.e. walls)
        
        # # #
        # These vars are all set to an (w, h) array of their respective values in reset()
        #
        self.state_grid = None  # Holds status of each tile, 0 = unvisited, 1 = searchable, -1 = searched
        self.cost_grid = None   # Cost to travel through each tile, used to define terrain
        self.h_grid = None      # Heuristic distance from each tile to the end, (could be precomputed)
        self.g_grid = None      # Distance from start to each tile, based on shortest path found so far
        self.f_grid = None      # Sum of G and H, represents ideal path lengths from start to end
        self.p_grid = None      # Parent of each tile, used to reconstruct path. (stored as (x, y) coords)
        # # #
        
        self.step_count = 0
        
        self.reset()


    def reset(self):
        """ Set all grids/counters to default values.
                Will be used to initialize and reset between searches.
                Max integer value is a stand-in for infinity.
        """
        self.state_grid = np.zeros((self.w, self.h), dtype=int)
        self.cost_grid = np.full((self.w, self.h), fill_value=self.default_cost, dtype=int)
        self.h_grid = np.full((self.w, self.h), fill_value=np.iinfo(int).max, dtype=int)
        self.g_grid = np.full((self.w, self.h), fill_value=np.iinfo(int).max, dtype=int)
        self.f_grid = np.full((self.w, self.h), fill_value=np.iinfo(int).max, dtype=int)
        self.p_grid = np.full((self.w, self.h, 2), fill_value=-1, dtype=int)
        self.step_count = 0


    def step(self):
        """ Progress pathfinding by one step, selecting and exploring a single cell.

        Returns:
            bool, (int, int), list: Bool of whether the end has been reached, coordinate of cell explored, and path to explored cell.
        """

        # TODO: Add a finished flag to the class, to prevent further steps after the end has been found.
        if not any(self.state_grid.flatten() == 1):
            print('No more positions to check.')
            return
        
        next_pos = self.select_next_pos()                       # Find next cell to search
        self.add_neighbors_to_frontier(next_pos)  # Add neighbors to searchable cells
        self.state_grid[next_pos] = -1                          # Mark cell as searched
        self.step_count += 1                                    # Increment step counter
        
        # TODO: Returning 3 things is excessive, have a class flag for finished instead.
        return next_pos == self.end_pos, next_pos, self.reconstruct_path(next_pos)


    def select_next_pos(self):
        """ Selects most promising cell from viable frontier cells.
                > Frontier cell -> lowest f -> lowest h
                > i.e. Unexplored cell that could be on the shortest path that is closest to the end.

        Returns:
            tuple: (int x, int y) coordinate of next cell to search
        """
        masked_f = np.ma.masked_where(self.state_grid != 1, self.f_grid)         # Mask to only searchable cells
        masked_h = np.ma.masked_where(masked_f != np.min(masked_f), self.h_grid) # Mask further to only cells with the lowest f
        return_pos = np.argmin(masked_h)                                         # Return argument that is closest to the end cell
        return tuple(np.unravel_index(return_pos, self.h_grid.shape))            # Return coordinate in 2D
    
    
    def add_neighbors_to_frontier(self, pos):
        """ Adds all direct neighbors of a cell to the frontier.
                > x = origin, o = neighbor, . = not added
            . . . . .
            . o o o .
            . o x o .
            . o o o .
            . . . . .
        Args:
            pos (int, int): origin cell
        """
        for w in range(-1, 2):
            for h in range(-1, 2):
                if w == 0 and h == 0: # Skip if origin cell
                    continue
                
                neighbor_pos = (pos[0] + w, pos[1] + h)
                self.add_to_frontier(neighbor_pos, pos)


    def add_to_frontier(self, pos, prev_pos=None):
        """ Calculate f, g, and h values for a given cell and set its state to searchable.

        Args:
            pos (int, int): Position of cell to add
            prev_pos ((int, int), optional): Position of parent cell, to track prior path. Defaults to None.
        """
        # If position is not in grid, abort.
        if pos[0] < 0 or pos[0] >= self.w or pos[1] < 0 or pos[1] >= self.h:
            return
        
        # If cost of cell is negative, it is considered impassable.
        if self.cost_grid[pos] < 0:
            return
        
        # If cell has already been searched, abort.
        if self.state_grid[pos] == -1:
            return
        
        # Calculate distance from start to this cell, and update if it is shorter than the previous value
        #   > g = (distance from prev cell to start) + (distance from this cell to prev cell * cost of this cell)
        self.g_grid[pos] = min(self.calculate_g(pos, prev_pos), self.g_grid[pos])

        # If we have not yet calculated the distance from this cell to the end, do so now
        if self.h_grid[pos] == np.iinfo(int).max:
            self.h_grid[pos] = self.distance_heuristic(pos, self.end_pos)
        
        # Our f is the sum of our g and h, representing an ideal shortest path from start to end through this cell
        f = self.g_grid[pos] + self.h_grid[pos]

        if f < self.f_grid[pos]:
            self.f_grid[pos] = f
            # self.g_grid[pos] = g
            # H_GRID[pos] = h
            # P_GRID[pos] = prev_pos
            # NOTE: May need to update the entire chain of children, if one exists?
            self.state_grid[pos] = 1
            
            if prev_pos is not None:
                self.p_grid[pos] = prev_pos
                    
    
    def calculate_g(self, pos, prev_pos):         
        if prev_pos is None:
            return 0
        else:
            return self.g_grid[prev_pos] + self.distance_heuristic(pos, prev_pos) * self.cost_grid[pos]
    
    def distance_heuristic(self, pos1, pos2, orthogonal_cost=10, diagonal_cost=14):
        """ Provides a heuristic distance between 2 cells, assuming no obstructions.
            One cell of diagonal movement costs 14, horizontal/vertical movement is 10.
                > This is roughly sqrt(2) and 1, upscaled to remove float innacuracy.
                > Diagonal movement is the most efficient way to travel, and will be prioritized.
                
        Args:
            pos1 (int, int): Cell coordinate.
            pos2 (int, int): Cell coordinate.
            orthogonal_cost (int, optional): Cost of horizontal/vertical travel. Defaults to 10.
            diagonal_cost (int, optional): Cost of diagonal travel. Defaults to 14.

        Returns:
            int: Heuristic distance between pos1 and pos2.
        """
        # Convert to distance vector
        vector = np.abs(np.array(pos1) - np.array(pos2))
        
        # Orthogonal movement is the difference between h and v travel, diagonal is the overlap.
        return int(orthogonal_cost * abs(vector[0] - vector[1]) + diagonal_cost * min(vector))


    def reconstruct_path(self, pos):
        path = [pos]
        while -1 not in self.p_grid[pos]:
            pos = tuple(self.p_grid[pos])
            path.append(pos)
        return path[::-1] # Reversed to give path from start -> end
        
if __name__ == '__main__':
    a = A_Star()