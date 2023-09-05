import numpy as np
import pygame as pg
from a_star_class import A_Star
import display_vars as dv
# Add game of life

# CONTROL VARS
MANUAL_CONTROL = False
AUTO_STEPS_PER_SECOND = 1000

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
    sim = A_Star(w=GRID_W, h=GRID_H, default_cost=DEFAULT_COST, wall_cost=WALL_COST)

    pg.init()
    screen = pg.display.set_mode((dv.SCREEN_W, dv.SCREEN_H))
    
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
    screen.fill(dv.BG_COLOR) # Seen in grid lines between cells and empty border space.
    
    # This loop is optimized to reduce the number of draw calls to 1 per cell.
    # This is at the expense of checks for each cell, and readability overall.
    
    for w in range(GRID_W):
        for h in range(GRID_H):
             # TODO: Draw impassable tiles as black, shade others as a gradient by cost.
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

            elif sim.cost_grid[w, h] == sim.wall_cost:  # Draw walls.
                pg.draw.rect(screen, dv.WALL_COLOR, rect_vars)
           
            elif sim.state_grid[w, h] == 1:             # Draw searched cells.
                pg.draw.rect(screen, dv.SEARCHED_COLORS[(h + w) % 2], rect_vars)
            
            elif sim.state_grid[w, h] == -1:            # Draw traversed cells.
                pg.draw.rect(screen, dv.TRAVERSED_COLORS[(h + w) % 2], rect_vars)
            
            else:                                       # Draw empty/unsearched cells.
                pg.draw.rect(screen, dv.CELL_COLORS[(h + w) % 2], rect_vars)

    # # Draw the last traversed path.
    # for i, (w, h) in enumerate(sim.last_path):
    #     if i == 0 or i == len(sim.last_path)-1:
    #         # First and last cells are drawn slightly darker (usually covered by start/end cells, so this could be skipped)
    #         pg.draw.rect(screen, dv.PATH_COLORS[1], (w*CELL_W+dv.BORDER_PX, h*CELL_H+dv.BORDER_PX, CELL_W-dv.BORDER_PX*2, CELL_H-dv.BORDER_PX*2))
    #     else:
    #         pg.draw.rect(screen, dv.PATH_COLORS[0], (w*CELL_W+dv.BORDER_PX, h*CELL_H+dv.BORDER_PX, CELL_W-dv.BORDER_PX*2, CELL_H-dv.BORDER_PX*2))
    
    # # Draw start cell.
    # if sim.start_pos is not None:
    #     pg.draw.rect(screen, dv.START_COLOR, (sim.start_pos[0]*CELL_W+dv.BORDER_PX, sim.start_pos[1]*CELL_H+dv.BORDER_PX, CELL_W-dv.BORDER_PX*2, CELL_H-dv.BORDER_PX*2))
    # # Draw end cell.
    # if sim.end_pos is not None:
    #     pg.draw.rect(screen, dv.END_COLOR, (sim.end_pos[0]*CELL_W+dv.BORDER_PX, sim.end_pos[1]*CELL_H+dv.BORDER_PX, CELL_W-dv.BORDER_PX*2, CELL_H-dv.BORDER_PX*2))


def get_tile(pos):
    """ Convert pixel coordinates into cell coordinates.
            Always returns a valid cell coordinate, even if the pixel position is outside the grid.
            This is done by clamping the pixel position to the grid size.

    Args:
        pos (int, int): Pixel position, presumably from mouse.get_pos()

    Returns:
        (int, int): Cell coordinates, limited to grid size.
    """
    pos = np.array(pos)
    pos[0] -= ORIGIN_X
    pos[1] -= ORIGIN_Y
    pos[0] /= CELL_W
    pos[1] /= CELL_H
    np.clip(pos[:1], 0, GRID_W-1, out=pos[:1])
    np.clip(pos[0:], 0, GRID_H-1, out=pos[0:])
    return tuple(pos.astype(int))

if __name__ == '__main__':
    main()
