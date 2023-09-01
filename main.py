import numpy as np
import pygame as pg
from a_star_class import A_Star

MANUAL_CONTROL = False
AUTO_STEPS_PER_SECOND = 1000

SCREEN_W, SCREEN_H = 800, 800

BORDER_PX = 1

BG_COLOR = (0, 0, 0) # Black, seen in grid lines between cells
CELL_COLORS = (255, 255, 255), (255, 255, 255) 
TRAVERSED_COLORS = (200, 255, 200), (200, 255, 200)
SEARCHED_COLORS = (100, 255, 100), (100, 255, 100) # Green tinted red, green tinted blue
WALL_COLOR = (15, 15, 15) # Dark gray
PATH_COLORS = (240, 50, 50), (200, 0, 0) # Red, darker red

START_COLOR = (100, 180, 100) # Dark green
END_COLOR = (180, 80, 180) # Dark purple


GRID_W, GRID_H = 20, 20
DEFAULT_COST = 1
WALL_COST = -1

astar = A_Star(w=GRID_W, h=GRID_H, default_cost=DEFAULT_COST, wall_cost=WALL_COST)

# TODO: Force a square aspect ratio.
CELL_W, CELL_H = SCREEN_W / GRID_W, SCREEN_H / GRID_H
STORED_PATH = []

def main():
    sim = A_Star(w=GRID_W, h=GRID_H)

    pg.init()
    screen = pg.display.set_mode((SCREEN_W, SCREEN_H))
    
    running = True
    searching = False

    
    # Timer to step the simulation
    pg.time.set_timer(pg.USEREVENT+1, 1000//AUTO_STEPS_PER_SECOND)

    # Main loop
    while running:
        pg.display.set_caption(f'A* Pathfinding: steps: {sim.step_count} ~ length: {sim.path_length}')
        
        # Draw current state of pathfinding sim
        draw_state(screen, sim)
        
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
                elif not sim.finished and event.key == pg.K_SPACE:
                    if sim.start_pos is None or sim.end_pos is None:
                        print('Please select a start and end position.')
                        continue
                    
                    if searching and MANUAL_CONTROL:
                        pos = sim.step()
                        if sim.finished: print(f'Finished in: {sim.step_count} steps. Path had length: {sim.path_length}.')
                    
                    searching = True
                    
                # R key resets the simulation
                elif event.key == pg.K_r:
                    print('Resetting...')
                    return main()
            
            # On left click, set start/end if they are not yet set
            elif event.type == pg.MOUSEBUTTONDOWN:
                clicked_tile = get_tile(event.pos)
                if sim.start_pos is None:
                    sim.start_pos = clicked_tile
                    
                elif sim.end_pos is None:
                    sim.end_pos = clicked_tile
                    sim.search_cell(sim.start_pos) # Start searching from start_pos


            # TODO: Add realtime wall drawing, allow paths to be cut and altered?
            if not searching and sim.start_pos is not None and sim.end_pos is not None: # Before searching, allow user to place walls
                try:
                    clicks = pg.mouse.get_pressed()
                    if any(clicks):
                        clicked_tile = get_tile(pg.mouse.get_pos())

                        if clicked_tile == sim.start_pos or clicked_tile == sim.end_pos:
                            continue
                        
                        if clicks[0]:
                            sim.cost_grid[clicked_tile[0], clicked_tile[1]] = sim.wall_cost
                        elif clicks[2]:
                            sim.cost_grid[clicked_tile[0], clicked_tile[1]] = sim.default_cost

                except AttributeError:
                    pass
                
            if not sim.finished and not MANUAL_CONTROL and searching and event.type == pg.USEREVENT+1:
                pos = sim.step()
                if sim.finished: print(f'Finished in: {sim.step_count} steps. Path had length: {sim.path_length}.')
                
        pg.display.flip()


# TODO: Consolidate all the draw functions into one
def draw_state(screen, sim):
    screen.fill(BG_COLOR) # Seen in grid lines between cells.
    
    for w in range(GRID_W):
        for h in range(GRID_H):
             # TODO: Draw impassable tiles as black, shade others as a gradient by cost.
             
            if sim.cost_grid[w, h] == sim.wall_cost: # Draw walls.
                pg.draw.rect(screen, WALL_COLOR, (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
           
            elif sim.state_grid[w, h] == 1:          # Draw searched cells.
                pg.draw.rect(screen, SEARCHED_COLORS[(h + w) % 2], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
            
            elif sim.state_grid[w, h] == -1:         # Draw traversed cells.
                pg.draw.rect(screen, TRAVERSED_COLORS[(h + w) % 2], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
            
            else:                                    # Draw empty/unsearched cells.
                pg.draw.rect(screen, CELL_COLORS[(h + w) % 2], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))

    # Draw the last traversed path.
    for i, (w, h) in enumerate(sim.last_path):
        if i == 0 or i == len(sim.last_path)-1:
            # First and last cells are drawn slightly darker (usually covered by start/end cells, so this could be skipped)
            pg.draw.rect(screen, PATH_COLORS[1], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
        else:
            pg.draw.rect(screen, PATH_COLORS[0], (w*CELL_W+BORDER_PX, h*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
    
    # Draw start cell.
    if sim.start_pos is not None:
        pg.draw.rect(screen, START_COLOR, (sim.start_pos[0]*CELL_W+BORDER_PX, sim.start_pos[1]*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))
    
    # Draw end cell.
    if sim.end_pos is not None:
        pg.draw.rect(screen, END_COLOR, (sim.end_pos[0]*CELL_W+BORDER_PX, sim.end_pos[1]*CELL_H+BORDER_PX, CELL_W-BORDER_PX*2, CELL_H-BORDER_PX*2))


# TODO: Update to account for possible screen bordering around simulation area.
def get_tile(pos):
    pos = np.array(pos)
    np.clip(pos[:1], 0, SCREEN_W-1, out=pos[:1])
    np.clip(pos[0:], 0, SCREEN_H-1, out=pos[0:])
    return (int(pos[0] / CELL_W), int(pos[1] / CELL_H))

if __name__ == '__main__':
    main()
