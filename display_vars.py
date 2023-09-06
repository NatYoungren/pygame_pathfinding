# Display vars
SCREEN_W, SCREEN_H = 800, 800

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

START_COLOR = (100, 180, 100) # Dark green
END_COLOR = (180, 80, 180) # Dark purple

# Text vars
TEXT_FONT = 'freesansbold.ttf'
TEXT_COLOR = (100, 100, 100) # Gray
TEXT_ALPHA = 180
TEXT_OFFSET = (40, -20)
TEXT_SIZE = 24