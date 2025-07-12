import pygame as pg
import math
from enum import Enum
from collections import defaultdict
import random


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
BACKGROUND_COLOR = (20, 20, 20)

# Load and scale sprites


start_offset_x = (TOTAL_GRID_WIDTH - SCREEN_WIDTH) // 2
start_offset_y = (TOTAL_GRID_HEIGHT - SCREEN_HEIGHT) // 2
offset_x = start_offset_x
offset_y = start_offset_y

glow_length = 80
grid_glow_length = 100

class Terrain:
    Empty = 0
    Stone = 1
    Coal = 2
    Emberrock = 3
    Iron_ore = 4
    Zone1_terrain_list = None
    Zone1_terrain_chances = None

    def init():
        Terrain.Zone1_terrain_list = [Terrain.Stone, Terrain.Coal, Terrain.Emberrock, Terrain.Iron_ore]
        Terrain.Zone1_terrain_chances = [76.5, 13.5, 6.5, 3.5]

class TerrainSprites:
    floor_sprite = None
    stone_sprite = None
    coal_ore_sprite = None
    emberrock_sprite = None
    iron_ore_sprite = None
    hidden_block_sprite = None

    @staticmethod
    def init():
        TerrainSprites.floor_sprite = TerrainSprites.preload_terrain(location="assets/cave_tile.png")
        TerrainSprites.stone_sprite = TerrainSprites.preload_terrain(location="assets/stone_block.png")
        TerrainSprites.coal_ore_sprite = TerrainSprites.preload_terrain(location="assets/coal_ore_sprite.png")
        TerrainSprites.emberrock_sprite = TerrainSprites.preload_terrain(location="assets/emberrock_sprite.png")
        TerrainSprites.iron_ore_sprite = TerrainSprites.preload_terrain(location="assets/iron_ore.png")
        TerrainSprites.hidden_block_sprite = TerrainSprites.preload_terrain(sprite="n", color=(0, 0, 0))

    def preload_terrain(sprite: str = "y", location: str = None, color: tuple[int, int, int] = None):
        if sprite == "y":
            terrain = pg.image.load(location).convert()
            terrain = pg.transform.scale(terrain, (GRID_SQUARE_SIZE, GRID_SQUARE_SIZE))
        elif sprite == "n":
            terrain = pg.Surface((GRID_SQUARE_SIZE, GRID_SQUARE_SIZE))
            terrain.fill(color)

        return terrain
    
class Miner():
    miner_count = 0
    def __init__(self, id):
        Miner.miner_count += 1
        self.id = id
        self.sprite = pg.Surface((GRID_SQUARE_SIZE, GRID_SQUARE_SIZE), pg.SRCALPHA)
        pg.draw.circle(self.sprite, (100, 100, 10), (GRID_SQUARE_SIZE // 2, GRID_SQUARE_SIZE // 2), GRID_SQUARE_SIZE // 2)
        self.grid_pos = self.set_position()
        self.pos = self.grid_pos
        self.state = "searching"
        self.moving_to = self.grid_pos
        self.movement_speed = 2
        self.direction = "down"

    def set_position(self):
        spawn_positions = {
            1: (((GRID_WIDTH // 2) + 1), ((GRID_WIDTH // 2) - 2)),
            2: (((GRID_WIDTH // 2) - 2), ((GRID_WIDTH // 2) - 2)),  # Your OG spot
            3: (((GRID_WIDTH // 2) - 2), ((GRID_WIDTH // 2) + 1)),
            4: (((GRID_WIDTH // 2) - 2), ((GRID_WIDTH // 2) + 1)),
            # Add more as needed
        }

        return spawn_positions[self.id]

    def draw(self, screen, offset_x, offset_y):
        map_x, map_y = self.pos[0] * GRID_SQUARE_SIZE - offset_x, self.pos[1] * GRID_SQUARE_SIZE - offset_y
        screen.blit(self.sprite, (map_x, map_y))

    def check_surroundings(self, terrain) -> list[tuple[int, str]]:
        x, y = self.grid_pos
        values = []
        max_y = len(terrain)
        max_x = len(terrain[0]) if max_y > 0 else 0

        if x + 1 < max_x:
            values.append((terrain[y][x + 1], "right"))
        if x - 1 >= 0:
            values.append((terrain[y][x - 1], "left"))
        if y + 1 < max_y:
            values.append((terrain[y + 1][x], "down"))
        if y - 1 >= 0:
            values.append((terrain[y - 1][x], "up"))

        return values

    
    def find_best_direction(self, values):
        # Extract just the ore values (first item in each tuple)
        ore_values = [ore_value[0] for ore_value in values]
        highest = max(ore_values)

        # Collect all directions where that value is found
        best_directions = [direction for value, direction in values if value == highest]

        chosen_direction = random.choice(best_directions)

        return chosen_direction
    
    def ai_action(self, terrain, floor_edge_map, terrain_edge_map):
        if self.state == "searching":
            self.mine(terrain, floor_edge_map, terrain_edge_map)
        elif self.state == "moving":
            self.move()

    def mine(self, terrain, floor_edge_map, terrain_edge_map):
        values = self.check_surroundings(terrain)
        direction = self.find_best_direction(values)
        x, y = self.grid_pos
        if direction == "right":
            if terrain[y][x + 1] != Terrain.Empty:
                update_after_broken(terrain, x + 1, y, floor_edge_map, terrain_edge_map)
            self.moving_to = (x + 1, y)
        elif direction == "up":
            if terrain[y - 1][x] != Terrain.Empty:
                update_after_broken(terrain, x, y - 1, floor_edge_map, terrain_edge_map)
            self.moving_to = (x, y - 1)
        elif direction == "down":
            if terrain[y + 1][x] != Terrain.Empty:
                update_after_broken(terrain, x, y + 1, floor_edge_map, terrain_edge_map)
            self.moving_to = (x, y + 1)
        elif direction == "left":
            if terrain[y][x - 1] != Terrain.Empty:
                update_after_broken(terrain, x - 1, y, floor_edge_map, terrain_edge_map)
            self.moving_to = (x - 1, y)

        self.direction = direction
        self.state = "moving"

    def move(self):
        movement_amnt = self.movement_speed / 100
        x, y = self.pos[0], self.pos[1]
        if self.direction == "up":
            new_pos = (x, y - movement_amnt)
        elif self.direction == "down":
            new_pos = (x, y + movement_amnt)
        elif self.direction == "left":
            new_pos = (x - movement_amnt, y)
        elif self.direction == "right":
            new_pos = (x + movement_amnt, y)
        
        dx = abs(x - self.moving_to[0])
        dy = abs(y - self.moving_to[1])
        if dx > movement_amnt or dy > movement_amnt:
            self.pos = new_pos
            
        else:
            self.pos = self.moving_to
            self.grid_pos = self.pos
            self.state = "searching"

    



def create_miners(amount):
    miners = []
    for i in range(amount):
        miners.append(Miner(i + 1))

    return miners

def miners_ai_action(miners, terrain, floor_edge_map, terrain_edge_map):
    for miner in miners:
        miner.ai_action(terrain, floor_edge_map, terrain_edge_map)


def draw_miners(screen, offset_x, offset_y, miners):
    for miner in miners:
        miner.draw(screen, offset_x, offset_y)


def create_terrain(floor_edge_map, terrain_edge_map):
    terrain = [[Terrain.Stone for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)]

    # Hub creation, or the area where NPCs will spawn
    hub_area = 4 # 4 x 4

    start = (GRID_WIDTH // 2) - 2
    dirty_rects = []
    for i in range(start, start + hub_area):
        for j in range(start, start + hub_area):
            terrain[i][j] = Terrain.Empty
            surrounding_terrain = check_outlines(i, j, terrain, floor_edge_map, terrain_edge_map)
            dirty_rects.append((j, i))
            dirty_rects += surrounding_terrain # to add to visible map

    create_minerals(terrain)
    RenderGroups.draw_to_visible(terrain, dirty_rects)
    return terrain

def create_minerals(terrain):
    for i in range(len(terrain)):
        for j in range(len(terrain[0])):
            if terrain[i][j] != Terrain.Empty:
                terrain[i][j] = random.choices(Terrain.Zone1_terrain_list, Terrain.Zone1_terrain_chances, k=1)[0]


def draw_floor_shadow(screen, offset_x, offset_y):
    screen.blit(Glows.Grid_Top_Glow, (-offset_x, -offset_y - grid_glow_length))
    screen.blit(Glows.Grid_Bottom_Glow, (-offset_x, TOTAL_GRID_HEIGHT - offset_y))
    screen.blit(Glows.Grid_Left_Glow, (-offset_x - grid_glow_length, -offset_y))
    screen.blit(Glows.Grid_Right_Glow, (TOTAL_GRID_WIDTH - offset_x, -offset_y))

    screen.blit(Glows.Grid_Glow_TL, (-offset_x - grid_glow_length, -offset_y - grid_glow_length))
    screen.blit(Glows.Grid_Glow_TR, (TOTAL_GRID_WIDTH - offset_x, -offset_y - grid_glow_length))
    screen.blit(Glows.Grid_Glow_BL, (-offset_x - grid_glow_length, TOTAL_GRID_HEIGHT - offset_y))
    screen.blit(Glows.Grid_Glow_BR, (TOTAL_GRID_WIDTH - offset_x, TOTAL_GRID_HEIGHT - offset_y))


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

def draw_terrain(screen, offset_x, offset_y):
    screen.blit(RenderGroups.visibleMap, (-offset_x, -offset_y))

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
    dirty_rects = []
    if i + 1 < len(terrain):
        if terrain[i + 1][j] != Terrain.Empty: # down
            edge_map.append(((i, j), "down"))
            terrain_edge_map[(i + 1, j)].add("up")

            dirty_rects.append((j, i + 1))
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

            dirty_rects.append((j, i - 1))
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

            dirty_rects.append((j + 1, i))
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

            dirty_rects.append((j - 1, i))
        else:
            terrain_edge_map[(i, j - 1)].discard("right")
            try:
                edge_map.remove(((i, j - 1), "right"))
            except ValueError:
                pass

    return dirty_rects



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

def update_after_broken(terrain, grid_x, grid_y, floor_edge_map, terrain_edge_map):
    terrain[grid_y][grid_x] = Terrain.Empty
    surrounding_terrain = check_outlines(grid_y, grid_x, terrain, floor_edge_map, terrain_edge_map)
    dirty_rects = [(grid_x, grid_y)] + surrounding_terrain
    RenderGroups.draw_to_visible(terrain, dirty_rects)

class RenderGroups:
    visibleMap = None
    hiddenMap = None
    glowMap = None

    @staticmethod
    def init():
        RenderGroups.visibleMap = pg.Surface((TOTAL_GRID_WIDTH, TOTAL_GRID_HEIGHT), pg.SRCALPHA)
        RenderGroups.visibleMap.fill((5, 5, 5))
        #RenderGroups.hiddenMap = pg.Surface((TOTAL_GRID_WIDTH, TOTAL_GRID_HEIGHT), pg.SRCALPHA) # to be added in the future potentially

    def draw_to_visible(terrain, positions: list[tuple[int, int]]):
        for tile in positions:
            x, y = tile[0], tile[1]
            map_x, map_y = x * GRID_SQUARE_SIZE, y * GRID_SQUARE_SIZE

            terrain_type = terrain[y][x]
            if terrain_type == Terrain.Stone:
                RenderGroups.visibleMap.blit(TerrainSprites.stone_sprite, (map_x, map_y))
            elif terrain_type == Terrain.Coal:
                RenderGroups.visibleMap.blit(TerrainSprites.coal_ore_sprite, (map_x, map_y))
            elif terrain_type == Terrain.Emberrock:
                RenderGroups.visibleMap.blit(TerrainSprites.emberrock_sprite, (map_x, map_y))
            elif terrain_type == Terrain.Iron_ore:
                RenderGroups.visibleMap.blit(TerrainSprites.iron_ore_sprite, (map_x, map_y))
            elif terrain_type == Terrain.Empty:
                RenderGroups.visibleMap.blit(TerrainSprites.floor_sprite, (map_x, map_y))

    #def draw_to_hidden(terrain: list[(int, int)]):
        #for tile in terrain:
            #x, y = tile
            #RenderGroups.hiddenMap.blit(TerrainSprites.hidden_block_sprite, (x, y)) # to be added in the future


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
    Terrain.init()
    TerrainSprites.init()
    RenderGroups.init()
    global offset_x, offset_y
    clock = pg.time.Clock()
    running = True
    floor_edge_map, terrain_edge_map = [], defaultdict(set)
    terrain = create_terrain(floor_edge_map, terrain_edge_map)
    miners = create_miners(4)
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
                    if terrain[grid_y][grid_x] != Terrain.Empty:
                        update_after_broken(terrain, grid_x, grid_y, floor_edge_map, terrain_edge_map)

        miners_ai_action(miners, terrain, floor_edge_map, terrain_edge_map)

        # Render
        screen.fill(BACKGROUND_COLOR)
        draw_floor_shadow(screen, offset_x, offset_y)
        draw_terrain(screen, offset_x, offset_y)
        draw_outlines(screen, floor_edge_map, terrain_edge_map, offset_x, offset_y)
        draw_miners(screen, offset_x, offset_y, miners)
        pg.display.flip()

        # Control frame rate
        clock.tick(60) 

    pg.quit()

main()