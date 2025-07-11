import pygame as pg
import math
from enum import Enum
from collections import defaultdict


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
GRID_WIDTH, GRID_HEIGHT = 20, 20

# Calculate initial offset to center the grid
TOTAL_GRID_WIDTH = GRID_WIDTH * GRID_SQUARE_SIZE
TOTAL_GRID_HEIGHT = GRID_HEIGHT * GRID_SQUARE_SIZE

# Visual settings
BACKGROUND_COLOR = (15, 15, 15)
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

glow_length = 80
grid_glow_length = 100

class Terrain(Enum):
    Empty = 0,
    Stone = 1,


def create_terrain(floor_edge_map, terrain_edge_map):
    terrain = [[Terrain.Stone for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)]

    # Hub creation, or the area where NPCs will spawn
    hub_area = 4 # 4 x 4

    start = (GRID_WIDTH // 2) - 2
    for i in range(start, start + hub_area):
        for j in range(start, start + hub_area):
            terrain[i][j] = Terrain.Empty
            check_outlines(i, j, terrain, floor_edge_map, terrain_edge_map)
    return terrain

def draw_floor_shadow(screen, offset_x, offset_y):
    screen.blit(Glows.Grid_Top_Glow, (-offset_x, -offset_y - grid_glow_length))
    screen.blit(Glows.Grid_Bottom_Glow, (-offset_x, TOTAL_GRID_HEIGHT - offset_y))
    screen.blit(Glows.Grid_Left_Glow, (-offset_x - grid_glow_length, -offset_y))
    screen.blit(Glows.Grid_Right_Glow, (TOTAL_GRID_WIDTH - offset_x, -offset_y))

    screen.blit(Glows.Grid_Glow_TL, (-offset_x - grid_glow_length, -offset_y - grid_glow_length))
    screen.blit(Glows.Grid_Glow_TR, (TOTAL_GRID_WIDTH - offset_x, -offset_y - grid_glow_length))
    screen.blit(Glows.Grid_Glow_BL, (-offset_x - grid_glow_length, TOTAL_GRID_HEIGHT - offset_y))
    screen.blit(Glows.Grid_Glow_BR, (TOTAL_GRID_WIDTH - offset_x, TOTAL_GRID_HEIGHT - offset_y))




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
                

def draw_outlines(screen, edge_map, terrain_edge_map, offset_x, offset_y):
    outln_col = (0, 0, 0)
    # only to be called when on the outskirts of the map or on an empty terrain slot
    for edge in edge_map:

        i, j = edge[0]
        screen_x = j * GRID_SQUARE_SIZE - offset_x
        screen_y = i * GRID_SQUARE_SIZE - offset_y
        if edge[1] == "down":
                start_x, end_x = screen_x, screen_x + GRID_SQUARE_SIZE
                y = screen_y + GRID_SQUARE_SIZE
                pg.draw.line(screen, outln_col, (start_x, y), (end_x, y), 2)

                glow_x = screen_x
                glow_y = screen_y + GRID_SQUARE_SIZE - glow_length
                screen.blit(Glows.Glow_Up, (glow_x, glow_y))

        if edge[1] == "up":
            start_x, end_x = screen_x, screen_x + GRID_SQUARE_SIZE
            y = screen_y
            pg.draw.line(screen, outln_col, (start_x, y), (end_x, y), 2)

            glow_x = screen_x
            glow_y = screen_y + 1
            screen.blit(Glows.Glow_Down, (glow_x, glow_y))

        if edge[1] == "right":
            x = screen_x + GRID_SQUARE_SIZE
            start_y, end_y = screen_y, screen_y + GRID_SQUARE_SIZE
            pg.draw.line(screen, outln_col, (x, start_y), (x, end_y), 2)

            # Glow should fade leftward from the right edge
            glow_x = screen_x + GRID_SQUARE_SIZE - glow_length # start at right edge
            glow_y = screen_y
            screen.blit(Glows.Glow_Left, (glow_x, glow_y))

        if edge[1] == "left":
            x = screen_x
            start_y, end_y = screen_y, screen_y + GRID_SQUARE_SIZE
            pg.draw.line(screen, outln_col, (x, start_y), (x, end_y), 2)

            # Glow should fade rightward from the left edge)
            glow_x = screen_x + 1  # start 50px to the left of the tile
            glow_y = screen_y
            screen.blit(Glows.Glow_Right, (glow_x, glow_y))

    for (i, j), directions in terrain_edge_map.items():
        screen_x = j * GRID_SQUARE_SIZE - offset_x
        screen_y = i * GRID_SQUARE_SIZE - offset_y

        if "up" in directions and "left" in directions:
            screen.blit(Glows.Glow_Corner_TL, (screen_x - GRID_SQUARE_SIZE, screen_y - GRID_SQUARE_SIZE))

        if "up" in directions and "right" in directions:
            screen.blit(Glows.Glow_Corner_TR, (screen_x + GRID_SQUARE_SIZE, screen_y - GRID_SQUARE_SIZE))

        if "down" in directions and "left" in directions:
            screen.blit(Glows.Glow_Corner_BL, (screen_x - GRID_SQUARE_SIZE, screen_y + GRID_SQUARE_SIZE))

        if "down" in directions and "right" in directions:
            screen.blit(Glows.Glow_Corner_BR, (screen_x + GRID_SQUARE_SIZE, screen_y + GRID_SQUARE_SIZE))


def check_outlines(i, j, terrain, edge_map, terrain_edge_map):
    terrain_edge_map.pop((i, j), None)
    if i + 1 < len(terrain):
        if terrain[i + 1][j] != Terrain.Empty: # down
            edge_map.append(((i, j), "down"))
            terrain_edge_map[(i + 1, j)].add("up")
        else:
            terrain_edge_map[(i + 1, j)].discard("up")
            try:
                edge_map.remove(((i + 1, j), "up"))
            except ValueError:
                pass

    if i - 1 < len(terrain):
        if terrain[i - 1][j] != Terrain.Empty: # up
            edge_map.append(((i, j), "up"))
            terrain_edge_map[(i - 1, j)].add("down")
        else:
            terrain_edge_map[(i - 1, j)].discard("down")
            try:
                edge_map.remove(((i - 1, j), "down"))
            except ValueError:
                pass

    if j + 1 < len(terrain[0]):
        if terrain[i][j + 1] != Terrain.Empty: # right
            edge_map.append(((i, j), "right"))
            terrain_edge_map[(i, j + 1)].add("left")
        else:
            terrain_edge_map[(i, j + 1)].discard("left")
            try:
                edge_map.remove(((i, j + 1), "left"))
            except ValueError:
                pass

    if j - 1 >= 0:
        if terrain[i][j - 1] != Terrain.Empty: # left
            edge_map.append(((i, j), "left"))
            terrain_edge_map[(i, j - 1)].add("right")
        else:
            terrain_edge_map[(i, j - 1)].discard("right")
            try:
                edge_map.remove(((i, j - 1), "right"))
            except ValueError:
                pass



def create_vert_glow(width, height, color, direction):
    glow = pg.Surface((width, height), pg.SRCALPHA)

    for y in range(height):
        fade_ratio = y / height
        if direction == "down":
            alpha = int(255 * (1 - fade_ratio)**2)  # quadratic fade from edge outward
        elif direction == "up":
            alpha = int(255 * fade_ratio**2)
        pg.draw.rect(glow, (*color, alpha), (0, y, width, 1))
    return glow

def create_horiz_glow(width, height, color, direction):
    glow = pg.Surface((width, height), pg.SRCALPHA)

    for x in range(width):
        fade_ratio = x / width
        if direction == "right":
            alpha = int(255 * (1 - fade_ratio)**2)  # fade from left edge outward
        elif direction == "left":
            alpha = int(255 * fade_ratio**2)        # fade from right edge outward
        pg.draw.rect(glow, (*color, alpha), (x, 0, 1, height))
    return glow

def create_corner_glow(size, color, corner, glow_intensity=220):
    glow = pg.Surface((size, size), pg.SRCALPHA)
    center = (size - 1, size - 1)
    if corner == "TR":
        center = (0, size - 1)
    elif corner == "BL":
        center = (size - 1, 0)
    elif corner == "BR":
        center = (0, 0)

    for y in range(size):
        for x in range(size):
            dx = x - center[0]
            dy = y - center[1]
            dist = (dx**2 + dy**2)**0.5
            fade = max(0, 1 - dist / size)
            alpha = int(glow_intensity * fade**2)
            glow.set_at((x, y), (*color, alpha))

    return glow


class Glows:
    Glow_Up = None
    Glow_Down = None
    Glow_Left = None
    Glow_Right = None
    Glow_Corner_TL = None
    Glow_Corner_TR = None
    Glow_Corner_BL = None
    Glow_Corner_BR = None
    edge_glow_color = (10, 10, 10)
    corner_glow_color = (10, 10, 10)

    grid_glow_color = (5, 5, 5)
    Grid_Top_Glow = None
    Grid_Bottom_Glow = None
    Grid_Right_Glow = None
    Grid_Left_Glow = None
    Grid_Glow_TL = None
    Grid_Glow_BL = None
    Grid_Glow_TR = None
    Grid_Glow_BR = None

    @staticmethod
    def init():
        Glows.Glow_Up = create_vert_glow(GRID_SQUARE_SIZE, glow_length, Glows.edge_glow_color, "up").convert_alpha()
        Glows.Glow_Down = create_vert_glow(GRID_SQUARE_SIZE, glow_length, Glows.edge_glow_color, "down").convert_alpha()
        Glows.Glow_Left = create_horiz_glow(glow_length, GRID_SQUARE_SIZE, Glows.edge_glow_color, "left").convert_alpha()
        Glows.Glow_Right = create_horiz_glow(glow_length, GRID_SQUARE_SIZE, Glows.edge_glow_color, "right").convert_alpha()
        Glows.Glow_Corner_TL = create_corner_glow(GRID_SQUARE_SIZE, Glows.corner_glow_color, "TL").convert_alpha()
        Glows.Glow_Corner_TR = create_corner_glow(GRID_SQUARE_SIZE, Glows.corner_glow_color, "TR").convert_alpha()
        Glows.Glow_Corner_BL = create_corner_glow(GRID_SQUARE_SIZE, Glows.corner_glow_color, "BL").convert_alpha()
        Glows.Glow_Corner_BR = create_corner_glow(GRID_SQUARE_SIZE, Glows.corner_glow_color, "BR").convert_alpha()
        Glows.Grid_Top_Glow = create_vert_glow(TOTAL_GRID_WIDTH, grid_glow_length, Glows.grid_glow_color, "up").convert_alpha()
        Glows.Grid_Bottom_Glow = create_vert_glow(TOTAL_GRID_WIDTH, grid_glow_length, Glows.grid_glow_color, "down").convert_alpha()
        Glows.Grid_Right_Glow = create_horiz_glow(grid_glow_length, TOTAL_GRID_HEIGHT, Glows.grid_glow_color, "right").convert_alpha()
        Glows.Grid_Left_Glow = create_horiz_glow(grid_glow_length, TOTAL_GRID_HEIGHT, Glows.grid_glow_color, "left").convert_alpha()
        Glows.Grid_Glow_TL = create_corner_glow(grid_glow_length, Glows.grid_glow_color, "TL", 255).convert_alpha()
        Glows.Grid_Glow_TR = create_corner_glow(grid_glow_length, Glows.grid_glow_color, "TR").convert_alpha()
        Glows.Grid_Glow_BL = create_corner_glow(grid_glow_length, Glows.grid_glow_color, "BL").convert_alpha()
        Glows.Grid_Glow_BR = create_corner_glow(grid_glow_length, Glows.grid_glow_color, "BR").convert_alpha()



def main():

    Glows.init()
    global offset_x, offset_y
    clock = pg.time.Clock()
    running = True
    floor_edge_map, terrain_edge_map = [], defaultdict(set)
    terrain = create_terrain(floor_edge_map, terrain_edge_map)
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
                        check_outlines(grid_y, grid_x, terrain, floor_edge_map, terrain_edge_map)
 
        # Render
        screen.fill(BACKGROUND_COLOR)
        draw_floor(screen)
        draw_floor_shadow(screen, offset_x, offset_y)
        draw_terrain(screen, terrain)
        draw_outlines(screen, floor_edge_map, terrain_edge_map, offset_x, offset_y)
        pg.display.flip()

        # Control frame rate
        clock.tick(60) 

    pg.quit()

main()