import pygame as pg
import math

# Initialize Pygame
pg.init()
info = pg.display.Info()

# Screen and display settings
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w - 80, info.current_h - 120
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pg.display.set_caption("Mining game")

# Scrolling settings
SCROLL_MARGIN = 50
SCROLL_SPEED = 10

# Grid settings
GRID_SQUARE_SIZE = 80
GRID_WIDTH, GRID_HEIGHT = 10, 10
GRID = [["_" for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)]

# Calculate initial offset to center the grid
TOTAL_GRID_WIDTH = GRID_WIDTH * GRID_SQUARE_SIZE
TOTAL_GRID_HEIGHT = GRID_HEIGHT * GRID_SQUARE_SIZE
start_offset_x = (TOTAL_GRID_WIDTH - SCREEN_WIDTH) // 2
start_offset_y = (TOTAL_GRID_HEIGHT - SCREEN_HEIGHT) // 2
offset_x = start_offset_x
offset_y = start_offset_y

# Visual settings
BACKGROUND_COLOR = (25, 25, 25)
SQUARE_COLOR = (200, 200, 200)

# Load and scale sprites
cave_tile_sprite = pg.image.load("assets/cave_tile.png").convert()
cave_tile_sprite = pg.transform.scale(cave_tile_sprite, (85, 85))

# Game loop settings
clock = pg.time.Clock()
running = True


def draw_floor(screen):
    # Calculate how many tiles we need to draw on screen
    tiles_x = SCREEN_WIDTH // GRID_SQUARE_SIZE + 2
    tiles_y = SCREEN_HEIGHT // GRID_SQUARE_SIZE + 2

    # Calculate starting tile positions based on camera offset
    start_tile_x = math.floor(offset_x / GRID_SQUARE_SIZE)
    start_tile_y = math.floor(offset_y / GRID_SQUARE_SIZE)

    # Draw tiles in the visible area
    for tile_x in range(start_tile_x, start_tile_x + tiles_x):
        for tile_y in range(start_tile_y, start_tile_y + tiles_y):
            # Check if tile is within grid boundaries
            if 0 <= tile_x < GRID_WIDTH and 0 <= tile_y < GRID_HEIGHT:
                screen_x = tile_x * GRID_SQUARE_SIZE - offset_x
                screen_y = tile_y * GRID_SQUARE_SIZE - offset_y
                
                # Only draw if the tile is actually visible on screen
                if (-GRID_SQUARE_SIZE < screen_x < SCREEN_WIDTH and 
                    -GRID_SQUARE_SIZE < screen_y < SCREEN_HEIGHT):
                    screen.blit(cave_tile_sprite, (screen_x, screen_y))


def check_scroll(mouse_x, mouse_y, offset_x, offset_y):
    # Horizontal scrolling
    if mouse_x < SCROLL_MARGIN and offset_x > (start_offset_x - (TOTAL_GRID_WIDTH // 2)):
        offset_x -= SCROLL_SPEED
    elif mouse_x > SCREEN_WIDTH - SCROLL_MARGIN and offset_x < (start_offset_x + (TOTAL_GRID_WIDTH // 2)):
        offset_x += SCROLL_SPEED

    # Vertical scrolling
    if mouse_y < SCROLL_MARGIN and offset_y > (start_offset_y - (TOTAL_GRID_HEIGHT // 2)):
        offset_y -= SCROLL_SPEED 
    elif mouse_y > SCREEN_HEIGHT - SCROLL_MARGIN and offset_y < (start_offset_y + (TOTAL_GRID_HEIGHT // 2)):
        offset_y += SCROLL_SPEED

    return offset_x, offset_y


# Main game loop
while running:
    # Handle input
    mouse_x, mouse_y = pg.mouse.get_pos()
    offset_x, offset_y = check_scroll(mouse_x, mouse_y, offset_x, offset_y)

    # Handle events
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

    # Render
    screen.fill(BACKGROUND_COLOR)
    draw_floor(screen)
    pg.display.flip()

    # Control frame rate
    clock.tick(60) 

pg.quit()