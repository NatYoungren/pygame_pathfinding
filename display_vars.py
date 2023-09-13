# Nathaniel Alden Homans Youngren
# September 13, 2023

import numpy as np

# Display vars
SCREEN_W, SCREEN_H = 800, 600

# Grid vars
BORDER_PX = 1
BG_COLOR = (0, 0, 0) # Black, seen in grid lines between cells
CELL_COLORS = (255, 255, 255), (255, 255, 255)

# Pathfinding vars
TRAVERSED_COLORS = (200, 255, 200), (200, 255, 200)
SEARCHED_COLORS = (100, 255, 100), (100, 255, 100) # Green tinted red, green tinted blue
PATH_COLORS = (240, 50, 50), (200, 0, 0) # Red, darker red

# Feature vars
PORTAL_COLORS = (160, 0, 250), (0, 240, 250) # Purple entrance, cyan exit
WALL_COLOR = (15, 15, 15) # Dark gray

COST_EXTREMES = (255, 255, 255), (80, 80, 80) # White, gray (for cost display)
COST_COUNT = 9
COST_COLORS = np.array([np.linspace(COST_EXTREMES[0][0], COST_EXTREMES[1][0], COST_COUNT),
                        np.linspace(COST_EXTREMES[0][1], COST_EXTREMES[1][1], COST_COUNT),
                        np.linspace(COST_EXTREMES[0][2], COST_EXTREMES[1][2], COST_COUNT)]).T.astype(int)

START_COLOR = (100, 180, 100) # Dark green
END_COLOR = (180, 80, 180) # Dark purple

# Text vars
TEXT_FONT = 'freesansbold.ttf'
TEXT_COLOR = (100, 100, 200) # Blue
TEXT_ALPHA = 230
TEXT_OFFSET = (40, -20)
TEXT_SIZE = 24