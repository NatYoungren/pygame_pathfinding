import numpy as np
import pygame as pg

# TODO: Move all constants to a separate file

MANUAL_CONTROL = False
AUTO_STEPS_PER_SECOND = 100

SCREEN_W, SCREEN_H = 500, 500

BORDER_PX = 1
GRID_W, GRID_H = 10, 10

BG_COLOR = (0, 0, 0) # Black
CELL_COLORS = (255, 255, 255), (255, 255, 255) 
SEARCHED_COLORS = (200, 255, 200), (200, 255, 200)
FRONTIER_COLORS = (100, 255, 100), (100, 255, 100) # Green tinted red, green tinted blue
WALL_COLOR = (15, 15, 15) # Dark gray
PATH_COLOR = (255, 0, 0) # Red

START_COLOR = (100, 150, 100) # Dark green
END_COLOR = (150, 100, 100) # Dark red

DEFAULT_COST = 1
WALL_COST = 255

CELL_W, CELL_H = SCREEN_W / GRID_W, SCREEN_H / GRID_H


COST_GRID = np.full((GRID_W, GRID_H), fill_value=DEFAULT_COST, dtype=np.uint8)
TRAVEL_GRID = np.full((GRID_W, GRID_H), fill_value=np.inf, dtype=np.float32)



# Heuristic distance from each tile to the end, (can be precomputed, but not necessary)
H_GRID = np.full((GRID_W, GRID_H), fill_value=np.inf, dtype=np.float32)

# Distance from start to each tile, based on shortest path found so far
G_GRID = np.full((GRID_W, GRID_H), fill_value=np.inf, dtype=np.float32)

# Sum of G and H
F_GRID = np.full((GRID_W, GRID_H), fill_value=np.inf, dtype=np.float32)

# Parent of each tile, used to reconstruct path, 1D array
P_GRID = np.full((GRID_W, GRID_H, 2), fill_value=-1, dtype=int)

# Holds status of each tile, 0 = unvisited, 1 = frontier, -1 = searched
FRONTIER = np.zeros((GRID_W, GRID_H), dtype=int)

STORED_PATH = []

def reset_grids():
    COST_GRID.fill(DEFAULT_COST)
    TRAVEL_GRID.fill(np.inf)
    H_GRID.fill(np.inf)
    G_GRID.fill(np.inf)
    F_GRID.fill(np.inf)
    P_GRID.fill(-1)
    FRONTIER.fill(0)
    STORED_PATH.clear()

def main():
    step_count = 0
    reset_grids()

    pg.init()
    pg.display.set_caption('Pathfinding')
    screen = pg.display.set_mode((SCREEN_W, SCREEN_H))
    
    running = True
    searching = False
    found_end = False
    
    
    start_pos = None
    end_pos = None
    
    # Timer to step the simulation
    pg.time.set_timer(pg.USEREVENT+1, 1000//AUTO_STEPS_PER_SECOND)

    # Main loop
    while running:
        screen.fill(BG_COLOR)
        
        set_board(screen)
        
        
        draw_search(screen)
        
        draw_walls(screen)
        
        
        draw_path(screen)
        
        draw_start_end(screen, start_pos, end_pos)
        
        # Handle input events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
                
            # Handle keypresses
            elif event.type == pg.KEYDOWN:
                
                # Escape key quits
                if event.key == pg.K_ESCAPE:
                    running = False
                    
                # Spacebar steps the simulation if manual control is enabled
                elif not found_end and event.key == pg.K_SPACE:
                    if start_pos is None or end_pos is None:
                        print('Please select a start and end position')
                        continue
                    
                    if searching and MANUAL_CONTROL:
                        step(end_pos=end_pos, path_var=STORED_PATH)
                        step_count += 1
                        if found_end: print('STEPS: ', step_count)
                        continue
                    
                    searching = True
                    
                    
                # R key resets the simulation
                elif event.key == pg.K_r:
                    print('r')
                    return main()
            
            elif event.type == pg.MOUSEBUTTONDOWN:
                clicked_tile = get_tile(event.pos)
                print(clicked_tile)
                if start_pos is None:
                    start_pos = clicked_tile
                    
                elif end_pos is None:
                    end_pos = clicked_tile
                    add_to_frontier(start_pos, end_pos)

            if not searching and start_pos is not None and end_pos is not None: # Before searching, allow user to place walls
                try:
                    if pg.mouse.get_pressed()[0]:
                        clicked_tile = get_tile(pg.mouse.get_pos())
                        if clicked_tile == start_pos or clicked_tile == end_pos:
                            continue
                        COST_GRID[clicked_tile[0], clicked_tile[1]] = WALL_COST
                    if pg.mouse.get_pressed()[2]:
                        clicked_tile = get_tile(pg.mouse.get_pos())
                        if clicked_tile == start_pos or clicked_tile == end_pos:
                            continue
                        COST_GRID[clicked_tile[0], clicked_tile[1]] = DEFAULT_COST
                        
                except AttributeError:
                    pass
                
            if not found_end and not MANUAL_CONTROL and searching and event.type == pg.USEREVENT+1:
                found_end = step(end_pos=end_pos, path_var=STORED_PATH)
                step_count += 1
                if found_end: print('STEPS: ', step_count)
        pg.display.flip()
        


def distance_heuristic(pos, end_pos):
    # Use 1.4 for diagonal distance, 1 for horizontal/vertical
    # vector = np.abs(np.array(pos) - np.array(end_pos))
    # return abs(vector[0] - vector[1]) + 1.4 * min(vector)
    
    return np.sqrt((pos[0] - end_pos[0])**2 + (pos[1] - end_pos[1])**2)


def add_to_frontier(pos, end_pos, prev_pos=None):

    if pos[0] < 0 or pos[0] >= GRID_W or pos[1] < 0 or pos[1] >= GRID_H:
        return
    
    if COST_GRID[pos] == WALL_COST:
        return
    
    if prev_pos is None:
        g = 0
    else:
        g = G_GRID[prev_pos] + distance_heuristic(pos, prev_pos)*COST_GRID[pos] # TODO: Multiple tile cost by distance_heuristic to add extra diagonal cost
    
    # Technically we may be recalculating this value, but it's not a big deal
    h = distance_heuristic(pos, end_pos)
    f = g + h
    # print(pos, f, g, h)
    if f < F_GRID[pos]:
        F_GRID[pos] = f
        G_GRID[pos] = g
        H_GRID[pos] = h
        # P_GRID[pos] = prev_pos
        # NOTE: May need to update the entire chain of children, if one exists
        FRONTIER[pos] = 1
        
        if prev_pos is not None:
            P_GRID[pos] = prev_pos

    

    

def add_neighbors_to_frontier(pos, end_pos):
    for w in range(-1, 2):
        for h in range(-1, 2):
            if w == 0 and h == 0:
                continue
            neighbor_pos = (pos[0] + w, pos[1] + h)
            
            add_to_frontier(neighbor_pos, end_pos, pos)
            


def select_next_pos():
    masked_f = np.ma.masked_where(FRONTIER != 1, F_GRID)
    masked_h = np.ma.masked_where(masked_f != np.min(masked_f), H_GRID)
    # print(masked_f, masked_f.shape)
    # print(masked_h, masked_h.shape)
    return_pos = np.argmin(masked_h)
    return tuple(np.unravel_index(return_pos, H_GRID.shape))

    
    
def step(end_pos, path_var=None):

    # print('Stepping...')
    # Implement A* here
    if not any(FRONTIER.flatten() == 1):
        print('No more positions to check')
        return
    
    p = select_next_pos()
    print(p)
    add_neighbors_to_frontier(p, end_pos)
    FRONTIER[p] = -1 
    if path_var is not None:
        path_var[:] = reconstruct_path(p)

    return p == end_pos
    
    
# TODO: Consolidate all the draw functions into one
def set_board(screen):
    for w in range(GRID_W):
        for h in range(GRID_H):
            pg.draw.rect(screen, CELL_COLORS[(h + w) % 2], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))

def draw_start_end(screen, start_pos=None, end_pos=None):
    if start_pos is not None:
        pg.draw.rect(screen, START_COLOR, (start_pos[0]*CELL_W+BORDER_PX, start_pos[1]*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
    if end_pos is not None:
        pg.draw.rect(screen, END_COLOR, (end_pos[0]*CELL_W+BORDER_PX, end_pos[1]*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))

def draw_walls(screen):
    for w in range(GRID_W):
        for h in range(GRID_H):
            if COST_GRID[w, h] == WALL_COST:
                pg.draw.rect(screen, WALL_COLOR, (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))



def draw_search(screen):
    for w in range(GRID_W):
        for h in range(GRID_H):
            if FRONTIER[w, h] == 1:
                pg.draw.rect(screen, FRONTIER_COLORS[(h + w) % 2], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
            elif FRONTIER[w, h] == -1:
                pg.draw.rect(screen, SEARCHED_COLORS[(h + w) % 2], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
            # if TRAVEL_GRID[w, h] != np.inf:
            #     pg.draw.rect(screen, SEARCHED_COLORS[(h + w) % 2], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
                
# def draw_frontier(screen):
#     for w in range(GRID_W):
#         for h in range(GRID_H):
#             if (w, h) in FRONTIER:
#                 pg.draw.rect(screen, FRONTIER_COLORS[(h + w) % 2], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))

def reconstruct_path(pos):
    # print(pos)
    path = [pos]
    while -1 not in P_GRID[pos]:
        pos = tuple(P_GRID[pos])
        path.append(pos)
    return path[::-1]

def draw_path(screen):
    for i, (w, h) in enumerate(STORED_PATH):
        if i == 0 or i == len(STORED_PATH)-1:
            pg.draw.rect(screen, (200,0,0), (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
        else:
            pg.draw.rect(screen, PATH_COLOR, (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))

def get_tile(pos):
    pos = np.array(pos)
    np.clip(pos[:1], 0, SCREEN_W-1, out=pos[:1])
    np.clip(pos[0:], 0, SCREEN_H-1, out=pos[0:])
    return (int(pos[0] / CELL_W), int(pos[1] / CELL_H))

if __name__ == '__main__':
    main()
