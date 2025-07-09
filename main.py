import pygame as pg
import math
from enum import Enum

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
GRID_WIDTH, GRID_HEIGHT = 30, 30

# Calculate initial offset to center the grid
TOTAL_GRID_WIDTH = GRID_WIDTH * GRID_SQUARE_SIZE
TOTAL_GRID_HEIGHT = GRID_HEIGHT * GRID_SQUARE_SIZE

# Visual settings
BACKGROUND_COLOR = (25, 25, 25)
SQUARE_COLOR = (200, 200, 200)

# Load and scale sprites
cave_tile_sprite = pg.image.load("assets/cave_tile.png").convert()
cave_tile_sprite = pg.transform.scale(cave_tile_sprite, (80, 80))
stone_block_sprite = pg.image.load("assets/stone_block.png").convert()
stone_block_sprite = pg.transform.scale(stone_block_sprite, (80, 80))

start_offset_x = (TOTAL_GRID_WIDTH - SCREEN_WIDTH) // 2
start_offset_y = (TOTAL_GRID_HEIGHT - SCREEN_HEIGHT) // 2
offset_x = start_offset_x
offset_y = start_offset_y

# Game loop settings
clock = pg.time.Clock()
running = True

class Terrain(Enum):
    Empty = 0,
    Stone = 1,


def create_terrain():
    terrain = [[Terrain.Stone for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)]

    # Hub creation, or the area where NPCs will spawn
    hub_area = 4 # 4 x 4

    start = (GRID_WIDTH // 2) - 2
    for i in range(start, start + hub_area):
        for j in range(start, start + hub_area):
            terrain[i][j] = Terrain.Empty

    return terrain


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

def draw_terrain(screen, terrain):
    center_x = len(terrain[0]) // 2
    center_y = len(terrain) // 2
    empty_terrain = []
    for i in range(len(terrain)):
        for j in range(len(terrain[i])):
            screen_x = j * GRID_SQUARE_SIZE - offset_x
            screen_y = i * GRID_SQUARE_SIZE - offset_y

            # Only draw if the tile is actually visible on screen
            if (-GRID_SQUARE_SIZE < screen_x < SCREEN_WIDTH and 
                -GRID_SQUARE_SIZE < screen_y < SCREEN_HEIGHT):
                if terrain[i][j] == Terrain.Stone:
                    screen.blit(stone_block_sprite, (int(screen_x), int(screen_y)))
                elif terrain[i][j] == Terrain.Empty:
                    empty_terrain.append((i, j, screen_x, screen_y))
        draw_outlines(screen, terrain, empty_terrain)

def draw_outlines(screen, terrain, marked_terrain):
    outln_col = (0, 0, 0)
    # only to be called when on the outskirts of the map or on an empty terrain slot
    for slot in marked_terrain:
        i, j, screen_x, screen_y = slot
        if i + 1 < len(terrain):
            if terrain[i + 1][j] != Terrain.Empty: # checks downward
                start_x, end_x = screen_x, screen_x + GRID_SQUARE_SIZE
                y = screen_y + GRID_SQUARE_SIZE
                pg.draw.line(screen, outln_col, (start_x, y), (end_x, y), 2)

                glow_x = screen_x
                glow_y = screen_y + GRID_SQUARE_SIZE - 50
                screen.blit(Glows.Glow_Up, (glow_x, glow_y))

        if i - 1 < len(terrain):
            if terrain[i - 1][j] != Terrain.Empty: # checks upwards
                start_x, end_x = screen_x, screen_x + GRID_SQUARE_SIZE
                y = screen_y
                pg.draw.line(screen, outln_col, (start_x, y), (end_x, y), 2)

                glow_x = screen_x
                glow_y = screen_y
                screen.blit(Glows.Glow_Down, (glow_x, glow_y))

        if j + 1 < len(terrain[0]):
            if terrain[i][j + 1] != Terrain.Empty:  # checks right
                x = screen_x + GRID_SQUARE_SIZE
                start_y, end_y = screen_y, screen_y + GRID_SQUARE_SIZE
                pg.draw.line(screen, outln_col, (x, start_y), (x, end_y), 2)

                # Glow should fade leftward from the right edge
                glow_x = screen_x + GRID_SQUARE_SIZE - 50 # start at right edge
                glow_y = screen_y
                screen.blit(Glows.Glow_Left, (glow_x, glow_y))

        if j - 1 >= 0:
            if terrain[i][j - 1] != Terrain.Empty:  # checks left
                x = screen_x
                start_y, end_y = screen_y, screen_y + GRID_SQUARE_SIZE
                pg.draw.line(screen, outln_col, (x, start_y), (x, end_y), 2)

                # Glow should fade rightward from the left edge)
                glow_x = screen_x  # start 50px to the left of the tile
                glow_y = screen_y
                screen.blit(Glows.Glow_Right, (glow_x, glow_y))

def create_vert_glow(width, height, color, direction):
    glow = pg.Surface((width, height), pg.SRCALPHA)

    for y in range(height):
        fade_ratio = y / height
        if direction == "down":
            alpha = int(25 * (1 - fade_ratio)**4)  # quadratic fade from edge outward
        elif direction == "up":
            alpha = int(25 * fade_ratio**4)
        pg.draw.rect(glow, (*color, alpha), (0, y, width, 1))
    return glow

def create_horiz_glow(width, height, color, direction):
    glow = pg.Surface((width, height), pg.SRCALPHA)

    for x in range(width):
        fade_ratio = x / width
        if direction == "right":
            alpha = int(25 * (1 - fade_ratio)**4)  # fade from left edge outward
        elif direction == "left":
            alpha = int(25 * fade_ratio**4)        # fade from right edge outward
        pg.draw.rect(glow, (*color, alpha), (x, 0, 1, height))
    return glow


class Glows:
    Glow_Up = None
    Glow_Down = None
    Glow_Left = None
    Glow_Right = None

    @staticmethod
    def init():
        Glows.Glow_Up = create_vert_glow(GRID_SQUARE_SIZE, 50, (100, 100, 100), "up")
        Glows.Glow_Down = create_vert_glow(GRID_SQUARE_SIZE, 50, (100, 100, 100), "down")
        Glows.Glow_Left = create_horiz_glow(50, GRID_SQUARE_SIZE, (100, 100, 100), "left")
        Glows.Glow_Right = create_horiz_glow(50, GRID_SQUARE_SIZE, (100, 100, 100), "right")

def main():

    Glows.init()
    global offset_x, offset_y
    clock = pg.time.Clock()
    running = True
    terrain = create_terrain()
# Main game loop
    while running:
        # Handle input
        mouse_x, mouse_y = pg.mouse.get_pos()
        offset_x, offset_y = check_scroll(mouse_x, mouse_y, offset_x, offset_y)

        # Handle events-
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:  # Left click
                mouse_x, mouse_y = pg.mouse.get_pos()

                grid_x = (mouse_x + offset_x) // GRID_SQUARE_SIZE
                grid_y = (mouse_y + offset_y) // GRID_SQUARE_SIZE

                if 0 <= grid_y < len(terrain) and 0 <= grid_x < len(terrain[0]):
                    if terrain[grid_y][grid_x] == Terrain.Stone:
                        terrain[grid_y][grid_x] = Terrain.Empty

        # Render
        screen.fill(BACKGROUND_COLOR)
        draw_floor(screen)
        draw_terrain(screen, terrain)
        pg.display.flip()

        # Control frame rate
        clock.tick(60) 

    pg.quit()

main()