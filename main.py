import numpy as np
import pygame as pg
from a_star_class import A_Star, A_Star_Portals
import display_vars as dv
# Add game of life

# CONTROL VARS
MANUAL_CONTROL = False
AUTO_STEPS_PER_SECOND = 50

# PATHFINDING VARS
GRID_W, GRID_H = 32, 24
DEFAULT_COST = 1
WALL_COST = -1

# DISPLAY CONSTANTS
# TODO: Force a square aspect ratio.
SQUARE_CELLS = True
CELL_W, CELL_H = dv.SCREEN_W / GRID_W, dv.SCREEN_H / GRID_H
if SQUARE_CELLS: CELL_W = CELL_H = min(CELL_W, CELL_H)
ORIGIN_X = (dv.SCREEN_W - CELL_W * GRID_W) / 2
ORIGIN_Y = (dv.SCREEN_H - CELL_H * GRID_H) / 2

def main():
    sim = A_Star_Portals(w=GRID_W, h=GRID_H, default_cost=DEFAULT_COST)

    pg.init()
    screen = pg.display.set_mode((dv.SCREEN_W, dv.SCREEN_H))

    running = True # Main loop control
    searching = False # Pathfinding loop control

    # Temp var to store portal start position during portal creation
    temp_portal_entrance = None
    
    # Timer to auto-step the simulation
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
                    
                # R key resets the simulation
                elif event.key == pg.K_r:
                    print('Resetting...')
                    return main()
                
                # Spacebar steps the simulation if manual control is enabled
                elif not sim.finished and event.key == pg.K_SPACE:
                    if sim.start_pos is None or sim.end_pos is None:
                        print('Please select a start and end position.')
                        continue
                    
                    searching = True
                    # If manual control is enabled, step the simulation
                    if MANUAL_CONTROL and searching:
                        _ = sim.step()
                        if sim.finished: print(f'Finished in: {sim.step_count} steps. Path had length: {sim.path_length}.')
                    
                # 0 Key places portal start and end points
                elif not sim.finished and event.key == pg.K_0:
                    if temp_portal_entrance is None:
                        temp_portal_entrance = get_tile(pg.mouse.get_pos())
                    else:
                        portal_exit = get_tile(pg.mouse.get_pos())
                        sim.portals[temp_portal_entrance] = portal_exit
                        print('Portal created from', temp_portal_entrance, 'to', portal_exit)
    
                        temp_portal_entrance = None
                
            
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
                            sim.cost_grid[clicked_tile[0], clicked_tile[1]] = WALL_COST
                        elif clicks[2]:
                            sim.cost_grid[clicked_tile[0], clicked_tile[1]] = DEFAULT_COST

                except AttributeError:
                    pass
            
            # If auto-stepping is enabled, step the simulation
            if not sim.finished and not MANUAL_CONTROL and searching and event.type == pg.USEREVENT+1:
                _ = sim.step()
                if sim.finished: print(f'Finished in: {sim.step_count} steps. Path had length: {sim.path_length}.')
                
        pg.display.flip()


def draw_state(screen, sim):
    screen.fill(dv.BG_COLOR) # Seen in grid lines between cells and empty border space.
    
    # This loop is optimized to reduce the number of draw calls to 1 per cell.
    # This is at the expense of checks for each cell, and readability overall.
    
    for w in range(GRID_W):
        for h in range(GRID_H):
            x, y = ORIGIN_X + CELL_W * w + dv.BORDER_PX, ORIGIN_Y + CELL_H * h + dv.BORDER_PX
            width, height = CELL_W - dv.BORDER_PX*2, CELL_H - dv.BORDER_PX*2
            rect_vars = (x, y, width, height)
            
            if (w, h) == sim.start_pos:                 # Draw the start position.
                pg.draw.rect(screen, dv.START_COLOR, rect_vars)
            
            elif (w, h) == sim.end_pos:                 # Draw the end position.
                pg.draw.rect(screen, dv.END_COLOR, rect_vars)
            
            elif (w, h) in sim.last_path:               # Draw the last traversed path.
                i = int(sim.last_path.index((w, h)) in (0, len(sim.last_path)-1))
                pg.draw.rect(screen, dv.PATH_COLORS[i], rect_vars)

             # TODO: Draw impassable tiles as black, shade others as a gradient by cost.
            elif sim.cost_grid[w, h] == WALL_COST:      # Draw walls.
                pg.draw.rect(screen, dv.WALL_COLOR, rect_vars)
           
            elif (w, h) in sim.portals.keys():     # Draw portal entrances.
                pg.draw.rect(screen, dv.PORTAL_COLORS[0], rect_vars)
            elif (w, h) in sim.portals.values():     # Draw portal exits.
                pg.draw.rect(screen, dv.PORTAL_COLORS[1], rect_vars)         
                       
            elif sim.state_grid[w, h] == 1:             # Draw searched cells.
                pg.draw.rect(screen, dv.SEARCHED_COLORS[(h + w) % 2], rect_vars)
            
            elif sim.state_grid[w, h] == -1:            # Draw traversed cells.
                pg.draw.rect(screen, dv.TRAVERSED_COLORS[(h + w) % 2], rect_vars)
            
            else:                                       # Draw empty/unsearched cells.
                pg.draw.rect(screen, dv.CELL_COLORS[(h + w) % 2], rect_vars)


def get_tile(pos):
    """ Convert pixel coordinates into cell coordinates.
            Always returns a valid cell coordinate, even if the pixel position is outside the grid.

    Args:
        pos (int, int): Pixel position, presumably from mouse.get_pos()

    Returns:
        (int, int): Cell coordinates, clamped to grid size.
    """
    pos = np.array(pos)
    pos[0] = (pos[0] - ORIGIN_X) / CELL_W
    pos[1] = (pos[1] - ORIGIN_Y) / CELL_H
    np.clip(pos[:1], 0, GRID_W-1, out=pos[:1])
    np.clip(pos[1:], 0, GRID_H-1, out=pos[1:])
    return tuple(pos.astype(int))

if __name__ == '__main__':
    main()
