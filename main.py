import numpy as np
import pygame as pg
from a_star import A_Star, A_Star_Portals
import display_vars as dv
# Add game of life

# INSTRUCTIONS:
# 1. Left click to set start position then end position.
# 2a. Place walls with left click, remove walls with right click.
# 2b. Place portal entrances and exits with 'p' key. (Must be paired)
# 3. Press spacebar to start the simulation.
#       (Continue to step with spacebar if manual control is enabled)
# 4. Press 'r' to reset the simulation, or escape to quit.


# TODO: Generate a related color pair for each portal pair.
# TODO: Add controls and color gradients to difficult terrain.

# CONTROL VARS
MANUAL_CONTROL = False
AUTO_STEPS_PER_SECOND = 100

# PATHFINDING VARS
GRID_W, GRID_H = 14, 14
DEFAULT_COST = 1
WALL_COST = -1

# DISPLAY VARS
SQUARE_CELLS = True

# DISPLAY CONSTANTS
CELL_W, CELL_H = dv.SCREEN_W / GRID_W, dv.SCREEN_H / GRID_H
if SQUARE_CELLS: CELL_W = CELL_H = min(CELL_W, CELL_H)
ORIGIN_X = (dv.SCREEN_W - CELL_W * GRID_W) / 2
ORIGIN_Y = (dv.SCREEN_H - CELL_H * GRID_H) / 2

PORTAL_COLORS = []

def add_portal_color():
    PORTAL_COLORS.append(list(np.random.random(size=3) * 256)) # Randomly generate a color for the portal


def main():
    sim = A_Star_Portals(w=GRID_W, h=GRID_H, default_cost=DEFAULT_COST)
    # Portal runtime testing:
    # sim.start_pos = (0, 0)
    # sim.end_pos = (GRID_W-1, GRID_H-1)
    # for i in range(1, GRID_W-2):
    #     sim.portals[(i, i)] = (i+1, i+1)

    pg.init()
    pg.font.init()
    
    font = pg.font.Font(dv.TEXT_FONT, dv.TEXT_SIZE)
    show_text = True
    text_coords = True
    
    screen = pg.display.set_mode((dv.SCREEN_W, dv.SCREEN_H))

    running = True # Main loop control
    searching = False # Pathfinding loop control

    # Temp var to store portal start position during portal creation
    temp_portal_entrance = None
    
    # Timer to auto-step the simulation
    pg.time.set_timer(pg.USEREVENT+1, 1000//AUTO_STEPS_PER_SECOND)

    # Main loop
    while running:
        pg.display.set_caption(f'A* Pathfinding: steps: {sim.step_count} ~ heuristic count: {sim.heuristic_count} ~ length: {sim.path_length}')
        
        # Draw current state of pathfinding sim
        draw_state(screen, sim)
        
        # TODO: Make input handling into a function
        
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
                    sim = A_Star_Portals(w=GRID_W, h=GRID_H, default_cost=DEFAULT_COST)
                    searching = False
                    # return main()
                
                # Spacebar steps the simulation if manual control is enabled
                elif event.key == pg.K_SPACE and not sim.finished:
                    if sim.start_pos is None or sim.end_pos is None:
                        print('Please select a start and end position.')
                        continue
                    
                    elif not searching and not sim.finished:
                        sim.search_cell(sim.start_pos) # Seed search with start_pos
                        searching = True # If start and end are set, begin searching
                    
                    # If manual control is enabled, step the simulation
                    if MANUAL_CONTROL and searching:
                        _ = sim.step()
                        if sim.finished: print(f'Finished in: {sim.step_count} steps. Path had length: {sim.path_length}.')
                    
                # 'p' Key places portal entrance and exits
                elif event.key == pg.K_p and not searching and not sim.finished and sim.end_pos is not None:
                    
                     # If no portal entrance is set, set one
                    if temp_portal_entrance is None:
                        temp_portal_entrance = get_tile(pg.mouse.get_pos())
                        
                    # If a portal entrance is set, set the exit and add the portal to the sim
                    else:
                        portal_exit = get_tile(pg.mouse.get_pos())
                        sim.portals[temp_portal_entrance] = portal_exit
                        print('Portal created from', temp_portal_entrance, 'to', portal_exit)
                        
                        temp_portal_entrance = None # Reset the temp portal entrance
                        
                # TODO: Document
                elif event.key == pg.K_t:
                    show_text = not show_text
                elif event.key == pg.K_y:
                    text_coords = not text_coords

            
            # On left click, set start/end if they are not yet set
            elif event.type == pg.MOUSEBUTTONDOWN:
                clicked_tile = get_tile(event.pos)
                if sim.start_pos is None:
                    sim.start_pos = clicked_tile
                    
                elif sim.end_pos is None:
                    sim.end_pos = clicked_tile


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

        # TODO: Move into method
        if show_text:
            mouse_pos = pg.mouse.get_pos()
            clicked_tile = get_tile(mouse_pos)
            if text_coords:
                text = f'({clicked_tile[0]}, {clicked_tile[1]})'
            else:
                text = ''
                g_val = sim.g_grid[clicked_tile]
                h_val = sim.h_grid[clicked_tile]

                if g_val != np.iinfo(int).max:
                    text += f'   G({g_val})'
                if h_val != np.iinfo(int).max:
                    text += f'   H({h_val})'
                if g_val != np.iinfo(int).max and h_val != np.iinfo(int).max:
                    text += f'   F({g_val + h_val})'

            text_surface = font.render(text, True, dv.TEXT_COLOR)
            text_surface.set_alpha(dv.TEXT_ALPHA)
            rect = text_surface.get_rect()
            rect.center = np.add(mouse_pos, dv.TEXT_OFFSET)
            screen.blit(text_surface, rect)

        pg.display.flip()


def draw_state(screen, sim):
    screen.fill(dv.BG_COLOR) # Seen in grid lines between cells and empty border space.
    
    # This loop is optimized to reduce the number of draw calls to 1 per cell. (Excepting portals)
    # This is at the expense of checks for each cell, and readability overall.
    
    triangle_inset_w, triangle_inset_h = CELL_W / 4, CELL_H / 4

    for w in range(GRID_W):
        for h in range(GRID_H):
            x, y = ORIGIN_X + CELL_W * w, ORIGIN_Y + CELL_H * h
            _x, _y = x + dv.BORDER_PX, y + dv.BORDER_PX
            width, height = CELL_W - dv.BORDER_PX*2, CELL_H - dv.BORDER_PX*2
            rect_vars = (_x, _y, width, height)
            
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
           
            elif sim.state_grid[w, h] == 1:             # Draw searched cells.
                pg.draw.rect(screen, dv.SEARCHED_COLORS[(h + w) % 2], rect_vars)
            
            elif sim.state_grid[w, h] == -1:            # Draw traversed cells.
                pg.draw.rect(screen, dv.TRAVERSED_COLORS[(h + w) % 2], rect_vars)
            
            else:                                       # Draw empty/unsearched cells.
                pg.draw.rect(screen, dv.CELL_COLORS[(h + w) % 2], rect_vars)
    
    # Draw portals as triangles, with direction indicating entrance/exit
    for i, (p_entrance, p_exit) in enumerate(sim.portals.items()):
        if i > len(PORTAL_COLORS)-1: add_portal_color() # If a portal has no color, add one.
        # Draw portal entrances.
        x, y = ORIGIN_X + CELL_W * p_entrance[0], ORIGIN_Y + CELL_H * p_entrance[1]
        pg.draw.polygon(screen, PORTAL_COLORS[i], ((x+triangle_inset_w, y+CELL_H-triangle_inset_h), (x+CELL_W-triangle_inset_w, y+CELL_H-triangle_inset_h), (x+int(CELL_W/2), y+triangle_inset_h)))
        
        # Draw portal exits.
        x, y = ORIGIN_X + CELL_W * p_exit[0], ORIGIN_Y + CELL_H * p_exit[1]
        pg.draw.polygon(screen, PORTAL_COLORS[i], ((x+triangle_inset_w, y+triangle_inset_h), (x+CELL_W-triangle_inset_w, y+triangle_inset_h), (x+int(CELL_W/2), y+CELL_H-triangle_inset_h)))
                       

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
