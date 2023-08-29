import numpy as np
import pygame as pg

MANUAL_CONTROL = True

SCREEN_W, SCREEN_H = 500, 500


BORDER_PX = 1
GRID_W, GRID_H = 25, 25

BG_COLOR = (0, 0, 0) # Black
CELL_COLORS = (255, 240, 240), (240, 240, 255) # Light red, light blue
SEARCHED_COLORS = (240, 200, 200), (200, 200, 240) # Less light red, less light blue
FRONTIER_COLORS = (220, 255, 180), (180, 255, 220) # Green tinted red, green tinted blue
WALL_COLOR = (15, 15, 15) # Dark gray

DEFAULT_COST = 1
WALL_COST = 255

CELL_W, CELL_H = SCREEN_W / GRID_W, SCREEN_H / GRID_H


COST_GRID = np.ones((GRID_W, GRID_H), dtype=np.uint8)
TRAVEL_GRID = np.full((GRID_W, GRID_H), fill_value=np.inf, dtype=np.float32)
# POS_QUEUE = {}


# Heuristic distance from each tile to the end, (can be precomputed, but not necessary)
H_GRID = np.full((GRID_W, GRID_H), fill_value=np.inf, dtype=np.float32)

# Distance from start to each tile, based on shortest path found so far
G_GRID = np.full((GRID_W, GRID_H), fill_value=np.inf, dtype=np.float32)

# Sum of G and H
F_GRID = np.full((GRID_W, GRID_H), fill_value=np.inf, dtype=np.float32)

# Parent of each tile, used to reconstruct path, 1D array
P_GRID = np.full((GRID_W * GRID_H), fill_value=np.nan, dtype=np.uint)

FRONTIER = np.zeros((GRID_W, GRID_H), dtype=np.uint)


# START_POS = (0, 0)
# START_POS = None
START_COLOR = (100, 150, 100)

# END_POS = (GRID_W-1, GRID_H-1)
# END_POS = None
END_COLOR = (150, 100, 100)



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
                    # pg.draw.rect(screen, START_COLOR, (start_pos[0]*CELL_W, start_pos[1]*CELL_H, CELL_W, CELL_H))
                    # POS_QUEUE[start_pos] = 0
                    FRONTIER[start_pos] = 1
                    
                elif end_pos is None:
                    end_pos = clicked_tile
                    # pg.draw.rect(screen, END_COLOR, (end_pos[0]*CELL_W, end_pos[1]*CELL_H, CELL_W, CELL_H))
                    
                elif not searching:
                    print(distance_heuristic(clicked_tile, end_pos))
                    if COST_GRID[clicked_tile[0], clicked_tile[1]] == WALL_COST:
                        COST_GRID[clicked_tile[0], clicked_tile[1]] = 1
                    else:
                        COST_GRID[clicked_tile[0], clicked_tile[1]] = WALL_COST
                    # pg.draw.rect(screen, WALL_COLOR, (clicked_tile[0]*CELL_W, clicked_tile[1]*CELL_H, CELL_W, CELL_H))
                
        pg.display.flip()

def distance_heuristic(pos, end_pos):
    return np.sqrt((pos[0] - end_pos[0])**2 + (pos[1] - end_pos[1])**2)

def select_next_pos():
    min_f_indexes = np.argwhere(F_GRID == np.min(F_GRID))
    print(min_f_indexes)
    min_f_h_index = np.argmin(H_GRID[min_f_indexes[:, 0], min_f_indexes[:, 1]])
    print(min_f_h_index)
    
    
def step(end_pos):
    print('Stepping...')
    # Implement A* here
    if not any(FRONTIER.flatten() == 1):
        print('No more positions to check')
        return
    
    # k_index = np.argmin(POS_QUEUE.values())
    # next_pos = list(POS_QUEUE.keys())[k_index]
    # print(next_pos)
    # travel_value = POS_QUEUE[next_pos] + COST_GRID[next_pos[0], next_pos[1]] + distance_heuristic(next_pos, end_pos)
    # TRAVEL_GRID[next_pos[0], next_pos[1]] = travel_value
    
    
    

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

def draw_path(screen):
    pass

def draw_search(screen):
    for w in range(GRID_W):
        for h in range(GRID_H):
            if FRONTIER[w, h] == 1:
                pg.draw.rect(screen, FRONTIER_COLORS[(h + w) % 2], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
            elif FRONTIER[w, h] == -1:
                pg.draw.rect(screen, SEARCHED_COLORS[(h + w) % 2], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
            # if TRAVEL_GRID[w, h] != np.inf:
            #     pg.draw.rect(screen, SEARCHED_COLORS[(h + w) % 2], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
                
def draw_frontier(screen):
    for w in range(GRID_W):
        for h in range(GRID_H):
            if (w, h) in FRONTIER:
                pg.draw.rect(screen, FRONTIER_COLORS[(h + w) % 2], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))

def get_tile(pos):
    return (int(pos[0] / CELL_W), int(pos[1] / CELL_H))

if __name__ == '__main__':
    main()
