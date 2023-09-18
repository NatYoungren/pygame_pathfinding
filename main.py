# Nathaniel Alden Homans Youngren
# September 13, 2023

import numpy as np
import pygame as pg
from a_star import A_Star_Portals
import display_vars as dv

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                   # INSTRUCTIONS: #                     #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# 1. Left click to set start position and end position.

# 2. Set cell costs with left click, reset costs with right click. (Select cost with 0-9 keys)

# 3. Place portal entrances and exits with 'p' key. (Must be paired)

# 4. Press spacebar to start the simulation.
#       (Continue to step with spacebar if manual control is enabled, toggle to manual with 'm' key)

# 5. Press 'r' to reset the pathfinding, or escape to quit. (Shift+'r' to reset fully)
#       (Additional controls are listed below)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                   # ALL CONTROLS: #                     #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# m1 -> Set start position, then end position, then change cell cost
# m2 -> Reset cells to default cost

# 'p' -> Place portal entrance and exit

# '1' ... '9' -> Change cost of placed cells to 1 - 9
# '0' -> Change cost of placed cells to -1 (walls)

# 'f' -> Toggle search display
# 'g' -> Toggle path display

# 't' -> Toggle text display
# 'y' -> Toggle text content (coords, cost/portal, heuristics)

# 'm' -> Toggle manual control
# 't' -> Toggle heuristic testing
# 'h' -> Toggle heuristic mode manually

# ' ' -> Start simulation, or step if manual control is enabled
# 'r' -> Reset pathfinding
# 'R' -> Reset completely
# ESC -> Quit


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                        # SETUP: #                       #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# PATHFINDING VARS
GRID_W, GRID_H = 25, 25     # Grid size
DEFAULT_COST = 1            # Default cost of cells
COST_DICT = {pg.K_0: -1,    # Dict mapping keypress to cell cost
             pg.K_1: 1,
             pg.K_2: 2,
             pg.K_3: 3,
             pg.K_4: 4,
             pg.K_5: 5,
             pg.K_6: 6,
             pg.K_7: 7,
             pg.K_8: 8,
             pg.K_9: 9}

# STEP SPEED VARS
STEPS_PER_SECOND = 200       # Number of steps per second (if manual control is disabled)
STEPS_PER_FRAME = 0         # Maximum steps per frame update (if < 1, no limit)

# Dict to track state information, avoids individual global variables or passing/returning many arguments.
STATE_DICT =   {'manual_control': False,    # If true, manual control is enabled (If false, auto-step is enabled)
                
                'test_heuristics': False,    # If true, cycle through all heuristic modes and print results.
                'heuristic_test_index': 0,  # Index of current heuristic mode being tested
                
                'cell_cost': -1,            # Cost of cells placed with left click
                
                'show_text': True,          # If true, show text on mouseover
                'text_content': 0,          # 0 = coords, 1 = cost/portal, 2 = heuristics,
                
                'show_search': True,        # If true, show searched/traversed cells
                'show_path': True,          # If true, show path cells
                
                # Internal state vars
                'running': True,            # Main loop control
                'searching': False,         # Pathfinding loop control
                'resetting': 2,             # Reset pathfinding flag (1 = pathfinding reset, 2 = full reset)
                
                'temp_portal': None,        # Temp var to store portal start position during portal creation
                }


# TESTING VARS
HEURISTIC_MODE_TEST_ARGS = ['standard', 'store_all', 'store_none', 'naive']

# DISPLAY VARS
SQUARE_CELLS = True         # If true, cells will always be square

# DISPLAY CONSTANTS
CELL_W, CELL_H = dv.SCREEN_W / GRID_W, dv.SCREEN_H / GRID_H
if SQUARE_CELLS: CELL_W = CELL_H = min(CELL_W, CELL_H)
ORIGIN_X = (dv.SCREEN_W - CELL_W * GRID_W) / 2
ORIGIN_Y = (dv.SCREEN_H - CELL_H * GRID_H) / 2

PORTAL_COLORS = [] # Used to store randomly generated portal colors
def add_portal_color():
    PORTAL_COLORS.append(list(np.random.random(size=3) * 256)) # Randomly generate a color for the portal


def main():
    # Var to store the current pathfinding simulation
    sim = None
    
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
        
        # Reset the simulation if flagged
        if STATE_DICT['resetting']:
            sim = reset_sim(sim, STATE_DICT['resetting'])
            STATE_DICT['resetting'] = 0
        
        # Update window title
        pg.display.set_caption(f'A* Pathfinding [{sim.h_mode}]: steps: {sim.step_count} ~ heuristic count: {sim.heuristic_count} ~ length: {sim.path_length}')
        
        # Handle input events
        parse_events(sim)
        
        # Draw current state of pathfinding sim
        draw_state(screen, sim)

        # Draw text at mouse position
        if STATE_DICT['show_text']:
            draw_mouse_text(screen, font, sim)
        
        # Update display
        pg.display.flip()
        
        # If heuristic testing is enabled, cycle through heuristic modes when the simulation finishes
        if STATE_DICT['searching'] and \
            STATE_DICT['test_heuristics'] and \
                (sim.finished or sim.blocked) and \
                    STATE_DICT['heuristic_test_index'] < len(HEURISTIC_MODE_TEST_ARGS)-1:
            
            # Initialize a new sim using the next heuristic mode
            STATE_DICT['heuristic_test_index'] += 1
            sim = copy_sim(sim, search=True)
    
    
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
            if not 0 < STEPS_PER_FRAME <= step_count:
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
                
                STATE_DICT['resetting'] = 1
                
                if event.unicode == 'R': STATE_DICT['resetting'] = 2
            
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
            # Check dict of predefined keys to determine cost change (default: 0-9 Keys set cell cost, 0 sets to -1 [walls])
            elif event.key in COST_DICT:
                STATE_DICT['cell_cost'] = COST_DICT[event.key]
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
                    if not 0 < STEPS_PER_FRAME <= step_count:
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
        
        
    # Adjust any moused-over cell costs if holding left or right click
    #   Only allow cost changes before searching begins
    if not STATE_DICT['searching'] and sim.start_pos is not None and sim.end_pos is not None:
        try:
            clicks = pg.mouse.get_pressed()
            if any(clicks):
                clicked_cell = get_cell(pg.mouse.get_pos())

                if clicked_cell == sim.start_pos or clicked_cell == sim.end_pos:
                    pass
                
                elif clicks[0]: # Left click changes cell cost
                    sim.cost_grid[clicked_cell[0], clicked_cell[1]] = STATE_DICT['cell_cost']
                    
                elif clicks[2]: # Right click resets cell to default
                    sim.cost_grid[clicked_cell[0], clicked_cell[1]] = DEFAULT_COST

        except AttributeError:
            pass
    
    # Print results if the simulation is finished
    if step_count > 0 and sim.finished:
        print_results(sim)


def draw_state(surf, sim):
    """ Draw the current state of the pathfinding simulation to the given surface.
            Renders the contents of each cell, minimizing draw calls at the expense of readability and checks-per-cell.
            Portals are drawn as paired triangles, with direction indicating entrance/exit.

    Args:
        surf (pygame.Surface): Surface to draw to (presumably the screen).
        sim (A_Star_Portals): Simulation from which to get state information.
    """
    surf.fill(dv.BG_COLOR) # Used for grid lines between cells and empty border space.

    # # #
    # Draw cell grid
    
    # Width and height of each cell, minus the border width
    width  = CELL_W - dv.BORDER_PX*2    
    height = CELL_H - dv.BORDER_PX*2
    
    # Draw the highest priority cell feature at each cell coordinate.
    for w in range(GRID_W):
        for h in range(GRID_H):

            x = ORIGIN_X + CELL_W * w           # Top left corner of the cell
            y = ORIGIN_Y + CELL_H * h   
            _x = x + dv.BORDER_PX               # Offset corner by border width
            _y = y + dv.BORDER_PX       
            rect_vars = (_x, _y, width, height) # Rect vars for pg.draw.rect
            
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
                pg.draw.rect(surf, dv.SEARCHED_COLOR, rect_vars)
            
            # Draw traversed cells.
            elif STATE_DICT['show_search'] and sim.state_grid[w, h] == -1:
                pg.draw.rect(surf, dv.TRAVERSED_COLOR, rect_vars)
                
            # Draw empty/unsearched cells.
            else:
                c = dv.CELL_COLOR # Default color
                if sim.cost_grid[w, h] in list(COST_DICT.values()): # Override color based on cell cost.
                    c = dv.COST_COLORS[list(COST_DICT.values()).index(sim.cost_grid[w, h]) - 1]
                
                pg.draw.rect(surf, c, rect_vars)
    
    # # #
    # Draw portals
    
    # Width and height of the portal triangle inset
    triangle_inset_w, triangle_inset_h = CELL_W / 4, CELL_H / 4
    
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
        
        # Draw stored portal entrance.
        x, y = ORIGIN_X + CELL_W * STATE_DICT['temp_portal'][0], ORIGIN_Y + CELL_H * STATE_DICT['temp_portal'][1]
        pg.draw.polygon(surf, PORTAL_COLORS[i], ((x+triangle_inset_w, y+CELL_H-triangle_inset_h), (x+CELL_W-triangle_inset_w, y+CELL_H-triangle_inset_h), (x+int(CELL_W/2), y+triangle_inset_h)))
        
        # Draw line from entrance to mouse position.
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

    if STATE_DICT['text_content'] == 0: # Show cell coordinates
        text = f'{clicked_cell}'
        
    elif STATE_DICT['text_content'] == 1: # Show cell cost/portal
        text = f'C({sim.cost_grid[clicked_cell]})  '
        if clicked_cell in sim.portals:
            text += f'P{sim.portals[clicked_cell]}'
        
    elif STATE_DICT['text_content'] == 2: # Show cell G/H/F if they are not max
        text = ''
        g_val = sim.g_grid[clicked_cell]
        h_val = sim.h_grid[clicked_cell]
        
        if g_val != np.iinfo(int).max:
            text += f'G({g_val})  '
        if h_val != np.iinfo(int).max:
            text += f'H({h_val})  '
        if g_val != np.iinfo(int).max and h_val != np.iinfo(int).max:
            text += f'F({g_val + h_val})'
            
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


def print_results(sim: A_Star_Portals):
    """ Summarize the results of pathfinding.

    Args:
        sim (A_Star_Portals): Pathfinding simulation to summarize.
    """
    print(f'\n\tHeuristic mode: {HEURISTIC_MODE_TEST_ARGS[STATE_DICT["heuristic_test_index"]]}')
    print(f' > Step Count: {sim.step_count}')
    print(f' > Path Length: {sim.path_length}')
    print(f' > Heuristic count: {sim.heuristic_count}')
    print(f' > Traversed cells: {np.count_nonzero(sim.state_grid == -1)}')
    print(f' > Searched cells: {np.count_nonzero(sim.state_grid != 0)}')
    print(f' > Step time: {sim.step_time:.4f}')
    print(f' > Average time per step: {(sim.step_time) / sim.step_count:.4f}\n')


def copy_sim(sim: A_Star_Portals, search=False):
    """ Duplicates simulation setup into a new simulation.
            Retain start/end positions, cost grid, and portals.

    Args:
        sim (A_Star_Portals): Pathfinding simulation to duplicate.
        
    Returns:
        A_Star_Portals: New simulation with the same setup as the given simulation.
    """
    newsim = A_Star_Portals(w=GRID_W, h=GRID_H, default_cost=DEFAULT_COST, h_mode=HEURISTIC_MODE_TEST_ARGS[STATE_DICT['heuristic_test_index']])
    newsim.start_pos = sim.start_pos
    newsim.end_pos = sim.end_pos
    newsim.cost_grid = sim.cost_grid
    newsim.portals = sim.portals
    
    if search and newsim.start_pos is not None and newsim.end_pos is not None:
        newsim.search_cell(sim.start_pos)
    return newsim


def reset_sim(sim: A_Star_Portals, reset_type=2):
    """ Return a new simulation, reset either partially or fully.

    Args:
        sim (A_Star_Portals): Simulation to copy setup from (if reset_type is 1).
        reset_type (int, optional): If 1, retain start/end/cost_grid/portals from sim.
                                    If 2, return a fresh sim.
                                    Defaults to 2.

    Returns:
        A_Star_Portals: The new simulation.
    """
    if reset_type not in [1, 2]:
        print(f'\nInvalid reset type: {reset_type}. Skipping reset.\n')
        return sim
    
    print('\nResetting...\n')
    STATE_DICT['heuristic_test_index'] = 0
    STATE_DICT['searching'] = False
    STATE_DICT['temp_portal'] = None
    
    if STATE_DICT['resetting'] == 1: # Retain start/end/cost_grid/portals from the previous sim
        return copy_sim(sim, search=False)
        
    elif STATE_DICT['resetting'] == 2: # Retain nothing from the previous sim
        return A_Star_Portals(w=GRID_W, h=GRID_H, default_cost=DEFAULT_COST, h_mode=HEURISTIC_MODE_TEST_ARGS[STATE_DICT['heuristic_test_index']])
    
    
if __name__ == '__main__':
    main()
