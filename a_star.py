import numpy as np

# NOTE: INSTRUCTIONS
#
# 1. Initialize the class with the desired grid size, start and end positions, and default cost.
# 2. Set the cost of any impassable tiles to a negative value.
# 3. If using portals, add them to the portals dict.
# 4. Manually call search_cell() to seed a starting cell.
# 5. Step() the simulation until a path is found or no more cells can be traversed.
# 6. Examine pathfinding results with reconstruct_path(), step_count, and path_length.
#

# TODO: Implement non-grid version of A* (i.e. for a continuous space or graph)
# TODO: Use numba to optimize speed?
# TODO: Storing a start_pos is potentially redundant, as multiple starts could be used.

# TODO: Consider a dict to store parents? (i.e. {pos: parent_pos})
# TODO: Alternately, consider a grid to store portals? (i.e. portals[x, y] = (x, y))


class A_Star():
    
    def __init__(self, w:int=20, h:int=20,
                 start_pos:(int, int)=None, end_pos:(int, int)=None,
                 default_cost:int=1) -> None:
        
        # Width and height of grid
        self.w, self.h = w, h
        
        # Start and end positions
        # NOTE: Start position is not required, but is useful for visualizing the algorithm.
        self.start_pos, self.end_pos = start_pos, end_pos
        
        # Distance multiplier of each tile, used to define terrain
        # Negative values are considered impassable
        # Lower cost cells will be contribute to shorter paths and be prioritized by the algorithm
        self.default_cost = default_cost
        
        # # #
        self.state_grid = np.zeros((self.w, self.h), dtype=int)                             # Holds status of each tile, 0 = unsearched, 1 = searched, -1 = traversed
        self.cost_grid = np.full((self.w, self.h), fill_value=self.default_cost, dtype=int) # Cost to travel through each tile, used to define terrain
        self.h_grid = np.full((self.w, self.h), fill_value=np.iinfo(int).max, dtype=int)    # Heuristic distance from each tile to the end, (could be precomputed)
        self.g_grid = np.full((self.w, self.h), fill_value=np.iinfo(int).max, dtype=int)    # Distance from start to each tile, based on shortest path found so far
        self.p_grid = np.full((self.w, self.h, 2), fill_value=-1, dtype=int)                # Parent of each tile, used to reconstruct path. (stored as (x, y) coords)
        # # #
        
        self.step_count = 0     # Number of steps taken
        self.last_path = []     # List of cells traversed in the last step
        self.path_length = 0    # Length of the path found
        self.finished = False   # Flag to indicate if the end has been traversed
        
        
    @property
    def f_grid(self):
        return np.add(self.h_grid, self.g_grid)


    def step(self):
        """ Progress pathfinding by one step, selecting and traversing a single cell.

        Returns:
            (int, int): Coordinate of cell traversed. None, if no more cells can be traversed.
        """

        # TODO: Add a finished flag to the class, to prevent further steps after the end has been found.
        if self.finished:
            print('End has been found, no more steps will be taken.')
            return self.end_pos
        
        if not any(self.state_grid.flatten() == 1):
            print('No more positions to check.')
            self.last_path = []
            return None                                     # NOTE: Could also return start_pos
        
        next_pos = self.select_next_pos()                   # Find next cell to traverse
        self.search_neighbors(next_pos)                     # Add neighbors to searched cells
        self.state_grid[next_pos] = -1                      # Mark cell as traversed
        
        self.step_count += 1                                # Increment step counter
        self.finished = next_pos == self.end_pos            # Check if end has been reached
        self.last_path = self.reconstruct_path(next_pos)    # Reconstruct path to cell
        
        self.path_length = max(self.path_length, self.g_grid[next_pos]/10)  # Divide by 10 to remove the heuristic scalar
        
        return next_pos


    def select_next_pos(self):
        """ Selects most promising cell from viable searched cells.
                > Searched cell -> lowest f -> lowest h
                > i.e. Searched but untraversed cell that may be on a shortest path and is closest to the end.

        Returns:
            tuple: (int x, int y) coordinate of next cell to traverse
        """
        masked_f = np.ma.masked_where(self.state_grid != 1, self.f_grid)         # Mask to only searched cells
        masked_h = np.ma.masked_where(masked_f != np.min(masked_f), self.h_grid) # Mask further to only cells with the lowest f
        return_pos = np.argmin(masked_h)                                         # Return argument that is closest to the end cell
        return tuple(np.unravel_index(return_pos, self.h_grid.shape))            # Return coordinate in 2D
    
    
    def search_neighbors(self, pos):
        """ Searches all direct neighbors of a given cell.
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
                self.search_cell(neighbor_pos, pos)


    def search_cell(self, pos, prev_pos=None):
        """ Calculate f, g, and h values for a given cell and set its state to searched.

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
        
        # If cell has already been traversed, abort.
        if self.state_grid[pos] == -1:
            return
        
        # If we have not yet calculated the distance from this cell to the end, do so now
        if self.h_grid[pos] == np.iinfo(int).max:
            self.h_grid[pos] = self.distance_heuristic(pos, self.end_pos)
        
        
        if prev_pos is None:
            # If we have no parent cell, the distance from our parent is 0 and we do NOT update p_grid.
            self.g_grid[pos] = 0
            
        else:
            # Calculate distance from start position to this cell
            #   > g = (distance from prev cell to start) + (distance from this cell to prev cell * cost of this cell)
            g = self.calculate_g(pos, prev_pos)
            
            # Update g_grid and parent if g is shorter than the previous g
            if g < self.g_grid[pos]:
                self.p_grid[pos] = prev_pos
                self.g_grid[pos] = g
        
        # Cell will remain searched until it is traversed or pathfinding ends.
        self.state_grid[pos] = 1

    
    def calculate_g(self, pos, prev_pos):
        """ Calculate the cumulative traversed distance to a new cell.

        Args:
            pos (int, int): New cell being added to path.
            prev_pos (int, int): Parent cell.

        Returns:
            int: The stored distance from start to prev_pos plus
                    the heuristic distance from prev_pos to pos (multiplied by traversal cost).
        """
        if prev_pos is None:
            return 0
        else:
            return self.g_grid[prev_pos] + self.distance_heuristic(prev_pos, pos) * self.cost_grid[pos]
    
    
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
        """ Generates the list of parent cells leading up to pos.

        Args:
            pos (int, int): Cell coordinate.

        Returns:
            [(int, int), ...]: A list of cell coordinates, from the original parent of pos to pos.
        """
        path = [pos]
        
        # If we encounter a coordinate containing -1, we reached a cell with no parent (i.e. start_pos)
        while -1 not in self.p_grid[pos]:
            pos = tuple(self.p_grid[pos])
            path.append(pos)
            
        return path[::-1] # Reversed to give path from start -> end
        

#
#
# # # # # # # # # # # # #
#  A* with Portals      #
# # # # # # # # # # # # #
#
#

class A_Star_Portals(A_Star):
    
    def __init__(self, w:int=20, h:int=20,
                 start_pos:(int, int)=None, end_pos:(int, int)=None,
                 default_cost:int=1) -> None:
        super().__init__(w, h, start_pos, end_pos, default_cost)
        
        # Dict of portal entrances and exits, stored as (x, y) coordinates
        self.portals = {}
        
    
    def search_neighbors(self, pos):
        """ Seach neighbors of a given cell, and if the cell is a portal, search the corresponding exit cell as well.

        Args:
            pos (int, int): _description_
        """
        super().search_neighbors(pos)
        
        # If the cell is a portal, search the corresponding exit cell as well.
        if pos in self.portals:
            self.search_cell(self.portals[pos], pos)
            
    
    def distance_heuristic(self, pos1, pos2, orthogonal_cost=10, diagonal_cost=14):
        """ Calculates distance between cells, with the additional consideration of multi-portal shortcuts.
                This version of the heuristic is more expensive than the original.
                This version (as portals are one-way) is specifically the distance from pos1 to pos2, not vice-versa.

        Args:
            pos1 (int, int): Cell coordinate.
            pos2 (int, int): Cell coordinate.
            orthogonal_cost (int, optional): Cost of horizontal/vertical travel. Defaults to 10.
            diagonal_cost (int, optional): Cost of diagonal travel. Defaults to 14.

        Returns:
            int: Heuristic distance between pos1 and pos2.
        """
        
        return self.recursive_portal_heuristic(pos1, pos2, portals=self.portals, orthogonal_cost=orthogonal_cost, diagonal_cost=diagonal_cost)
    
    
    def recursive_portal_heuristic(self, pos1, pos2, portals={}, **kwargs):
        """ Recursive function to calculate the heuristic distance between two cells, considering portal permutations.
                Runtime is O(n!) where n is the number of portals, could potentially be improved.
                One possibility is to store the shortest distance to each portal, and only recurse if that distance can be reduced.

        Args:
            pos1 (int, int): Cell coordinate.
            pos2 (int, int): Cell coordinate.
            portals (dict, optional): Dict of remaining portals to try, reduced by each recursion. Defaults to {}.

        Returns:
            int: Heuristic distance between pos1 and pos2
        """
        # Begin with the heuristic distance between the two cells
        shortest_dist = super().distance_heuristic(pos1, pos2, **kwargs)
        
        # For each portal, calculate the distance from pos1 to the portal entrance, and from the portal exit to pos2
        for portal_entry, portal_exit in portals.items():
            
            # Calculate distance from pos1 to portal entrance
            to_entrance = super().distance_heuristic(pos1, portal_entry, **kwargs)

            # Avoid pointless recursion if the distance to the portal entrance is longer than the shortest distance
            if to_entrance < shortest_dist:
                
                # Remove portal from dict to prevent infinite recursion
                sub_portals = {en:ex for en, ex in portals.items() if en != portal_entry} # TODO: Is there a faster way to do this?

                # Recursively calculate distance from portal exit to pos2, considering all unused portals
                from_exit = self.recursive_portal_heuristic(portal_exit, pos2, sub_portals, **kwargs)

                # Retain the shortest distance found so far
                shortest_dist = min(shortest_dist, to_entrance + from_exit)
        
        return shortest_dist

        

if __name__ == '__main__':
    # Check initialization
    a1 = A_Star()
    a2 = A_Star_Portals()
