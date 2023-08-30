import numpy as np
import pygame as pg

# TODO: Move all constants to a separate file

MANUAL_CONTROL = True

SCREEN_W, SCREEN_H = 500, 500

BORDER_PX = 1
GRID_W, GRID_H = 5, 5

BG_COLOR = (0, 0, 0) # Black
CELL_COLORS = (255, 240, 240), (240, 240, 255) # Light red, light blue
SEARCHED_COLORS = (240, 200, 200), (200, 200, 240) # Less light red, less light blue
FRONTIER_COLORS = (220, 255, 180), (180, 255, 220) # Green tinted red, green tinted blue
WALL_COLOR = (15, 15, 15) # Dark gray

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



def main():

    pg.init()
    pg.display.set_caption('Pathfinding')
    screen = pg.display.set_mode((SCREEN_W, SCREEN_H))
    
    running = True
    searching = False
    
    
    
    start_pos = None
    end_pos = None
    
                
    
    # pg.draw.rect(screen, START_COLOR, (START_POS[0]*CELL_W, START_POS[1]*CELL_H, CELL_W, CELL_H))
    # pg.draw.rect(screen, END_COLOR, (END_POS[0]*CELL_W, END_POS[1]*CELL_H, CELL_W, CELL_H))

    # Render current state

    # Main loop
    while running:
        screen.fill(BG_COLOR)
        
        set_board(screen)
        
        draw_walls(screen)
        
        draw_search(screen)
        
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
                elif event.key == pg.K_SPACE:
                    if start_pos is None or end_pos is None:
                        print('Please select a start and end position')
                        continue
                    
                    if searching and MANUAL_CONTROL:
                        step(end_pos=end_pos)
                        continue
                    
                    searching = True
                    
                    print('Searching...')
                    
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
                        COST_GRID[clicked_tile[0], clicked_tile[1]] = WALL_COST
                    if pg.mouse.get_pressed()[2]:
                        clicked_tile = get_tile(pg.mouse.get_pos())
                        COST_GRID[clicked_tile[0], clicked_tile[1]] = DEFAULT_COST
                        
                except AttributeError:
                    pass
        pg.display.flip()


def distance_heuristic(pos, end_pos):
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
    print(pos, f, g, h)
    if f < F_GRID[pos]:
        F_GRID[pos] = f
        G_GRID[pos] = g
        H_GRID[pos] = h
        # P_GRID[pos] = prev_pos
        # NOTE: May need to update the entire chain of children, if one exists
        FRONTIER[pos] = 1
        
        if prev_pos is not None:
            P_GRID[pos] = prev_pos

        # FRONTIER[prev_pos] = -1
    if pos == end_pos:
        print('Found end position')
        return
    

def add_neighbors_to_frontier(pos, end_pos):
    for w in range(-1, 2):
        for h in range(-1, 2):
            if w == 0 and h == 0:
                continue
            neighbor_pos = (pos[0] + w, pos[1] + h)
            
            
            # if FRONTIER[neighbor_pos] == 0:
            add_to_frontier(neighbor_pos, end_pos, pos)
            


def select_next_pos():
    masked_f = np.ma.masked_where(FRONTIER != 1, F_GRID)
    masked_h = np.ma.masked_where(masked_f != np.min(masked_f), H_GRID)
    # print(masked_f, masked_f.shape)
    # print(masked_h, masked_h.shape)
    return_pos = np.argmin(masked_h)
    return tuple(np.unravel_index(return_pos, H_GRID.shape))

    
    
def step(end_pos):

    print('Stepping...')
    # Implement A* here
    if not any(FRONTIER.flatten() == 1):
        print('No more positions to check')
        return
    
    p = select_next_pos()
    print(p)
    add_neighbors_to_frontier(p, end_pos)
    FRONTIER[p] = -1
    # k_index = np.argmin(POS_QUEUE.values())
    # next_pos = list(POS_QUEUE.keys())[k_index]
    # print(next_pos)
    # travel_value = POS_QUEUE[next_pos] + COST_GRID[next_pos[0], next_pos[1]] + distance_heuristic(next_pos, end_pos)
    # TRAVEL_GRID[next_pos[0], next_pos[1]] = travel_value
    
    
    
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

def draw_path(screen):
    pass

def get_tile(pos):
    pos = np.array(pos)
    np.clip(pos[:1], 0, SCREEN_W-1, out=pos[:1])
    np.clip(pos[0:], 0, SCREEN_H-1, out=pos[0:])
    return (int(pos[0] / CELL_W), int(pos[1] / CELL_H))

if __name__ == '__main__':
    main()
