import numpy as np
import pygame as pg
from a_star import A_Star_Portals
import display_vars as dv

# INSTRUCTIONS:
# 1. Left click to set start position and end position.

# 2. Set cell costs with left click, reset costs with right click. (Select cost with 0-9 keys)

# 3. Place portal entrances and exits with 'p' key. (Must be paired)

# 4. Press spacebar to start the simulation.
#       (Continue to step with spacebar if manual control is enabled)

# 5. Press 'r' to reset the simulation, or escape to quit.


# ALL CONTROLS:
# m1 -> Set start position, then end position, then change cell cost
# m2 -> Reset cells to default cost

# 'p' -> Place portal entrance and exit

# '1' ... '9' -> Change cost of placed cells to 1 - 9
# '0' -> Change cost of placed cells to -1 (walls)

# 'f' -> Toggle search display
# 'g' -> Toggle path display

# 't' -> Toggle text display
# 'y' -> Toggle text content (coords, cost, heuristics)

# 'm' -> Toggle manual control
# 't' -> Toggle heuristic testing
# 'h' -> Toggle heuristic mode manually

# ' ' -> Start simulation, or step if manual control is enabled
# 'r' -> Reset simulation
# ESC -> Quit

# TODO: Add controls and color gradients for difficult terrain.

# CONTROL VARS
STEPS_PER_SECOND = 1000

# PATHFINDING VARS
GRID_W, GRID_H = 25, 25
DEFAULT_COST = 1

# TESTING VARS
HEURISTIC_MODE_TEST_ARGS = ['standard', 'store_all', 'store_none', 'naive']


STATE_DICT =   {'manual_control': False,    # If true, manual control is enabled (If false, auto-step is enabled)
                
                'test_heuristics': False,    # If true, test all heuristic modes and print results.
                'heuristic_test_index': 0,  # Index of current heuristic mode being tested
                
                'cell_cost': -1,            # Cost of cells placed with left click
                
                'show_text': True,          # If true, show text on mouseover
                'text_content': 0,          # 0 = coords, 1 = cost/portal, 2 = heuristics,
                
                'show_search': True,        # If true, show searched/traversed cells
                'show_path': True,          # If true, show path cells
                
                # Internal state vars
                'running': True,            # Main loop control
                'searching': False,         # Pathfinding loop control
                'resetting': True,          # Reset pathfinding flag
                
                'temp_portal': None,        # Temp var to store portal start position during portal creation
                
                'steps_per_frame': 0        # Maximum steps per frame update (if < 1, no limit)
                }


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
    # Var to store the current pathfinding simulation
    sim = None
    
    # # Portal runtime testing:     # TODO: Clean up testing implementation, make random board generator (maze generator? game of life?)
    # sim.start_pos = (0, 0)
    # sim.end_pos = (GRID_W-1, GRID_H-1)
    # for i in range(1, GRID_W-2):
    #     sim.portals[(i, i)] = (i+1, i+1)

    # Initialize pygame window
    pg.init()
    screen = pg.display.set_mode((dv.SCREEN_W, dv.SCREEN_H))

    # Initialize font
    pg.font.init()
    font = pg.font.Font(dv.TEXT_FONT, dv.TEXT_SIZE)

    # Timer to auto-step the simulation
    pg.time.set_timer(pg.USEREVENT+1, 1000//STEPS_PER_SECOND)

    # Main loop
    while STATE_DICT['running']:
        # Reset the simulation if requested
        if STATE_DICT['resetting']:
            print('\nResetting...\n')
            STATE_DICT['heuristic_test_index'] = 0
            STATE_DICT['resetting'] = False
            STATE_DICT['searching'] = False
            STATE_DICT['temp_portal'] = None
            sim = A_Star_Portals(w=GRID_W, h=GRID_H, default_cost=DEFAULT_COST, h_mode=HEURISTIC_MODE_TEST_ARGS[STATE_DICT['heuristic_test_index']])
            
        # Update window title
        pg.display.set_caption(f'A* Pathfinding: steps: {sim.step_count} ~ heuristic count: {sim.heuristic_count} ~ length: {sim.path_length}')
        
        # Handle input events
        parse_events(sim)
        
        # Draw current state of pathfinding sim
        draw_state(screen, sim)

        # Draw text at mouse position
        if STATE_DICT['show_text']:
            draw_mouse_text(screen, font, sim)
        
        # Update display
        pg.display.flip()
        
        
        # TODO: Move into method/clean up
        if sim.finished and STATE_DICT['heuristic_test_index'] < len(HEURISTIC_MODE_TEST_ARGS):
            
            # Initialize a new sim using the next heuristic mode
            STATE_DICT['heuristic_test_index'] += 1
            if STATE_DICT['heuristic_test_index'] < len(HEURISTIC_MODE_TEST_ARGS):
                sim = copy_sim(sim)


def print_results(sim):
    print(f'\n\tHeuristic mode: {HEURISTIC_MODE_TEST_ARGS[STATE_DICT["heuristic_test_index"]]}')
    print(f' > Step Count: {sim.step_count}')
    print(f' > Path Length: {sim.path_length}')
    print(f' > Heuristic count: {sim.heuristic_count}')
    print(f' > Traversed cells: {np.count_nonzero(sim.state_grid == -1)}')
    print(f' > Searched cells: {np.count_nonzero(sim.state_grid != 0)}')
    print(f' > Step time: {sim.step_time:.4f}')
    print(f' > Average time per step: {(sim.step_time) / sim.step_count:.4f}\n')

def copy_sim(sim):
    newsim = A_Star_Portals(w=GRID_W, h=GRID_H, default_cost=DEFAULT_COST, h_mode=HEURISTIC_MODE_TEST_ARGS[STATE_DICT['heuristic_test_index']])
    newsim.start_pos = sim.start_pos
    newsim.end_pos = sim.end_pos
    newsim.cost_grid = sim.cost_grid
    newsim.portals = sim.portals
    newsim.search_cell(sim.start_pos)
    return newsim
    
    
def parse_events(sim: A_Star_Portals):
    """ Handle pygame events and update the simulation/visualization accordingly.
        Simulation is stepped inside this function, either manually or via timer.

    Args:
        sim (A_Star_Portals): Pathfinding simulation to update.
    """
    
    step_count = 0 # Used to track/limit the number of steps per frame
    
    # Handle input events
    for event in pg.event.get():
        
        # Handle quit event
        if event.type == pg.QUIT:
            STATE_DICT['running'] = False
        
        # If searching, and manual control is disabled, step the simulation on a timer
        elif event.type == pg.USEREVENT+1:
            if not 0 < STATE_DICT['steps_per_frame'] <= step_count:
                if not sim.finished and not STATE_DICT['manual_control'] and STATE_DICT['searching']:
                    _ = sim.step()
                    step_count += 1
                    
        # On left click, set start/end if they are not yet set
        elif event.type == pg.MOUSEBUTTONDOWN:
            clicked_cell = get_cell(event.pos)
            if sim.start_pos is None:
                sim.start_pos = clicked_cell
                
            elif sim.end_pos is None:
                sim.end_pos = clicked_cell
                
        # Handle keypresses
        elif event.type == pg.KEYDOWN:
            
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # Escape key quits
            if event.key == pg.K_ESCAPE:
                STATE_DICT['running'] = False
            
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # R key resets the simulation at the beginning of the next main loop
            elif event.key == pg.K_r:
                STATE_DICT['resetting'] = True
            
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # M key toggles manual control
            elif event.key == pg.K_m:
                STATE_DICT['manual_control'] = not STATE_DICT['manual_control']
                print('Manual control:', STATE_DICT['manual_control'])
            
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # T key toggles heuristic testing
            elif event.key == pg.K_t:
                STATE_DICT['test_heuristics'] = not STATE_DICT['test_heuristics']
                STATE_DICT['heuristic_text_index'] = 0
                print('Heuristic testing:', STATE_DICT['test_heuristics'])
            
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # H key toggles between heuristic modes manually
            elif event.key == pg.K_h and not STATE_DICT['test_heuristics']:
                STATE_DICT['heuristic_test_index'] = (STATE_DICT['heuristic_test_index'] + 1) % len(HEURISTIC_MODE_TEST_ARGS)
                sim.h_mode = HEURISTIC_MODE_TEST_ARGS[STATE_DICT['heuristic_test_index']]
                print('Heuristic mode:', sim.h_mode)
            
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # 't' Key toggles text display
            elif event.key == pg.K_t:
                STATE_DICT['show_text'] = not STATE_DICT['show_text']
                print('Show text:', STATE_DICT['show_text'])
            
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # 'y' Key toggles text content
            elif event.key == pg.K_y:
                STATE_DICT['text_content'] = (STATE_DICT['text_content'] + 1) % 3
            
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # 'g' Key toggles path display
            elif event.key == pg.K_g:
                STATE_DICT['show_path'] = not STATE_DICT['show_path']
                print('Show path:', STATE_DICT['show_path'])
                
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # 'f' Key toggles search display
            elif event.key == pg.K_f:
                STATE_DICT['show_search'] = not STATE_DICT['show_search']
                print('Show search:', STATE_DICT['show_search'])
                
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # 0-9 Keys set cell cost, 0 sets to -1 (walls)
            elif event.key in [pg.K_0, pg.K_1, pg.K_2, pg.K_3, pg.K_4, pg.K_5, pg.K_6, pg.K_7, pg.K_8, pg.K_9]:
                i = [pg.K_0, pg.K_1, pg.K_2, pg.K_3, pg.K_4, pg.K_5, pg.K_6, pg.K_7, pg.K_8, pg.K_9].index(event.key)
                if i == 0: i = -1
                STATE_DICT['cell_cost'] = i
                print('Cell cost:', STATE_DICT['cell_cost'])
            
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # Spacebar begins the simulation (also steps if manual control is enabled)
            elif event.key == pg.K_SPACE:
                if sim.start_pos is None or sim.end_pos is None:
                    print('Please select a start and end position.')
                    continue
                
                if not STATE_DICT['searching']: # If start and end are set, begin searching
                    sim.search_cell(sim.start_pos) # Seed search with start_pos
                    STATE_DICT['searching'] = True
                
                # If manual control is enabled, step the simulation
                if STATE_DICT['manual_control'] and not sim.finished:
                    if not 0 < STATE_DICT['steps_per_frame'] <= step_count:
                        _ = sim.step()
                        step_count += 1
                    
                    if sim.finished and not STATE_DICT['test_heuristics']:
                        print(f'Finished in: {sim.step_count} steps. Path had length: {sim.path_length}.')
            
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # 'p' Key places portal entrance and exits
            elif event.key == pg.K_p and not STATE_DICT['searching'] and not sim.finished and sim.end_pos is not None:
                
                # If no portal entrance is stored, set one
                if STATE_DICT['temp_portal'] is None:
                    portal_entrance = get_cell(pg.mouse.get_pos())
                    STATE_DICT['temp_portal'] = portal_entrance
                    
                    # Remove any existing portal at the new location (and its color)
                    if portal_entrance in sim.portals:
                        i = list(sim.portals.keys()).index(portal_entrance)
                        PORTAL_COLORS.pop(i)
                        sim.portals.pop(portal_entrance)
                    
                # If a portal entrance is stored, add the portal to the sim
                else:
                    portal_exit = get_cell(pg.mouse.get_pos())
                    
                    # Abort if the portal entrance and exit are the same
                    if portal_exit != STATE_DICT['temp_portal']:
                        sim.portals[STATE_DICT['temp_portal']] = portal_exit
                        print('Portal created from', STATE_DICT['temp_portal'], 'to', portal_exit)
                    
                    STATE_DICT['temp_portal'] = None # Reset the temp portal entrance
        
        
        # TODO: Add realtime wall drawing, allow paths to be cut and altered?
        if not STATE_DICT['searching'] and sim.start_pos is not None and sim.end_pos is not None: # Before searching, allow user to place walls
            try:
                clicks = pg.mouse.get_pressed()
                if any(clicks):
                    clicked_cell = get_cell(pg.mouse.get_pos())

                    if clicked_cell == sim.start_pos or clicked_cell == sim.end_pos:
                        continue
                    
                    if clicks[0]: # Left click changes cell cost
                        sim.cost_grid[clicked_cell[0], clicked_cell[1]] = STATE_DICT['cell_cost']
                        
                    elif clicks[2]: # Right click resets cell to default
                        sim.cost_grid[clicked_cell[0], clicked_cell[1]] = DEFAULT_COST

            except AttributeError:
                pass
    
    # Print results if the simulation is finished
    if step_count > 0 and sim.finished:
        print_results(sim)


def draw_state(surf, sim):
    surf.fill(dv.BG_COLOR) # Used for grid lines between cells and empty border space.
    
    # This loop is optimized to reduce the number of draw calls to 1 per cell. (Excepting portals)
    # This is at the expense of checks for each cell, and readability overall.
    
    triangle_inset_w, triangle_inset_h = CELL_W / 4, CELL_H / 4
    
    for w in range(GRID_W):
        for h in range(GRID_H):
            # Top left corner of the cell
            x, y = ORIGIN_X + CELL_W * w, ORIGIN_Y + CELL_H * h
            
            # Top left corner of the cell, offset by the border width
            _x, _y = x + dv.BORDER_PX, y + dv.BORDER_PX
            
            # Width and height of the cell, minus the border width
            width, height = CELL_W - dv.BORDER_PX*2, CELL_H - dv.BORDER_PX*2
            
            # Rect vars for drawing
            rect_vars = (_x, _y, width, height)
            
            # Draw the start position.
            if (w, h) == sim.start_pos:
                pg.draw.rect(surf, dv.START_COLOR, rect_vars)
            
            # Draw the end position.
            elif (w, h) == sim.end_pos:
                pg.draw.rect(surf, dv.END_COLOR, rect_vars)
                
            # Draw the last traversed path.
            elif STATE_DICT['show_path'] and (w, h) in sim.last_path:
                i = int(sim.last_path.index((w, h)) in (0, len(sim.last_path)-1))
                pg.draw.rect(surf, dv.PATH_COLORS[i], rect_vars)
                
            # Draw walls.
            elif sim.cost_grid[w, h] < 0:
                pg.draw.rect(surf, dv.WALL_COLOR, rect_vars)
           
           # Draw searched cells.
            elif STATE_DICT['show_search'] and sim.state_grid[w, h] == 1:
                pg.draw.rect(surf, dv.SEARCHED_COLORS[(h + w) % 2], rect_vars)
            
            # Draw traversed cells.
            elif STATE_DICT['show_search'] and sim.state_grid[w, h] == -1:
                pg.draw.rect(surf, dv.TRAVERSED_COLORS[(h + w) % 2], rect_vars)
                
            # Draw empty/unsearched cells.
            else:
                c = sim.cost_grid[w, h]
                pg.draw.rect(surf, dv.COST_COLORS[c-1], rect_vars)
    
    # Draw portals as triangles, with direction indicating entrance/exit.
    for i, (p_entrance, p_exit) in enumerate(sim.portals.items()):
        if i > len(PORTAL_COLORS)-1: add_portal_color() # If a portal has no color, add one.
        # Draw portal entrances.
        x, y = ORIGIN_X + CELL_W * p_entrance[0], ORIGIN_Y + CELL_H * p_entrance[1]
        pg.draw.polygon(surf, PORTAL_COLORS[i], ((x+triangle_inset_w, y+CELL_H-triangle_inset_h), (x+CELL_W-triangle_inset_w, y+CELL_H-triangle_inset_h), (x+int(CELL_W/2), y+triangle_inset_h)))
        
        # Draw portal exits.
        x, y = ORIGIN_X + CELL_W * p_exit[0], ORIGIN_Y + CELL_H * p_exit[1]
        pg.draw.polygon(surf, PORTAL_COLORS[i], ((x+triangle_inset_w, y+triangle_inset_h), (x+CELL_W-triangle_inset_w, y+triangle_inset_h), (x+int(CELL_W/2), y+CELL_H-triangle_inset_h)))

    # Draw the stored portal entrance if one is being placed.
    if STATE_DICT['temp_portal'] is not None:
        i = len(sim.portals)
        if i > len(PORTAL_COLORS)-1: add_portal_color() # If a portal has no color, add one.

        x, y = ORIGIN_X + CELL_W * STATE_DICT['temp_portal'][0], ORIGIN_Y + CELL_H * STATE_DICT['temp_portal'][1]
        pg.draw.polygon(surf, PORTAL_COLORS[i], ((x+triangle_inset_w, y+CELL_H-triangle_inset_h), (x+CELL_W-triangle_inset_w, y+CELL_H-triangle_inset_h), (x+int(CELL_W/2), y+triangle_inset_h)))
        
        mouse_pos = pg.mouse.get_pos()
        pg.draw.line(surf, PORTAL_COLORS[i], (x+int(CELL_W/2), y+int(CELL_H/2)), mouse_pos, 2)


def draw_mouse_text(surf, font, sim):
    """ Draw text at the mouse position, indicating the cell coordinates or heuristics.

    Args:
        surf (pygame.Surface): Surface to draw text to.
        font (pygame.font.Font): Font to use for text.
        sim (A_Star_Portals): Pathfinding simulation to get heuristics from.
    """
    mouse_pos = pg.mouse.get_pos()
    clicked_cell = get_cell(mouse_pos)
    text_pos = np.add(mouse_pos, dv.TEXT_OFFSET)

    if STATE_DICT['text_content'] == 0:
        text = f'{clicked_cell}'
        
    elif STATE_DICT['text_content'] == 1:
        text = f'C({sim.cost_grid[clicked_cell]})'
        if clicked_cell in sim.portals:
            text += f'  P{sim.portals[clicked_cell]}'
        
    elif STATE_DICT['text_content'] == 2:
        text = ''
        g_val = sim.g_grid[clicked_cell]
        h_val = sim.h_grid[clicked_cell]
        
        if g_val != np.iinfo(int).max:
            text += f'G({g_val})'
        if h_val != np.iinfo(int).max:
            text += f'  H({h_val})'
        if g_val != np.iinfo(int).max and h_val != np.iinfo(int).max:
            text += f'  F({g_val + h_val})'
            
    draw_text(surf, text, text_pos, font, dv.TEXT_COLOR, dv.TEXT_ALPHA)


def draw_text(surf, text, pos, font, color, alpha):
    """ Blit text onto the screen at the given position.

    Args:
        surf (pygame.Surface): Surface to draw text to.
        text (str): Text to draw.
        pos (int, int): Coords at which to center the text.
        font (pygame.font.Font): Font to use for text.
        color (int, int, int): RGB color of text.
        alpha (int): Alpha value of text from 0 to 255.
    """
    text_surface = font.render(text, True, color)
    text_surface.set_alpha(alpha)
    rect = text_surface.get_rect()
    rect.center = pos
    surf.blit(text_surface, rect)


def get_cell(pos):
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
