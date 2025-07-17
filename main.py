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
FPS = 60

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
    Zone1_terrain_max_healths = None

    def init():
        Terrain.Zone1_terrain_list = [Terrain.Stone, Terrain.Coal, Terrain.Emberrock, Terrain.Iron_ore]
        Terrain.Zone1_terrain_chances = [76.5, 13.5, 6.5, 3.5]
        Terrain.Zone1_terrain_max_healths = [6, 15, 25, 40]

class TerrainSprites:
    floor_sprite = None
    stone_sprite = None
    coal_ore_sprite = None
    emberrock_sprite = None
    iron_ore_sprite = None
    darkness_block_sprite = None

    @staticmethod
    def init():
        TerrainSprites.floor_sprite = TerrainSprites.preload_terrain(location="assets/cave_tile.png")
        TerrainSprites.stone_sprite = TerrainSprites.preload_terrain(location="assets/stone_block.png")
        TerrainSprites.coal_ore_sprite = TerrainSprites.preload_terrain(location="assets/coal_ore_sprite.png")
        TerrainSprites.emberrock_sprite = TerrainSprites.preload_terrain(location="assets/emberrock_sprite.png")
        TerrainSprites.iron_ore_sprite = TerrainSprites.preload_terrain(location="assets/iron_ore.png")

        TerrainSprites.floor_sprite = TerrainSprites.glow_surface(TerrainSprites.floor_sprite, "dark", 50)
        TerrainSprites.stone_sprite = TerrainSprites.glow_surface(TerrainSprites.stone_sprite, "dark", 10)
        TerrainSprites.coal_ore_sprite = TerrainSprites.glow_surface(TerrainSprites.coal_ore_sprite, "dark", 10)
        TerrainSprites.emberrock_sprite = TerrainSprites.glow_surface(TerrainSprites.emberrock_sprite, "dark", 10)
        TerrainSprites.iron_ore_sprite = TerrainSprites.glow_surface(TerrainSprites.iron_ore_sprite, "dark", 10)
        TerrainSprites.darkness_block_sprite = TerrainSprites.preload_terrain(location="assets/darkness_tile_sprite.png")
        TerrainSprites.darkness_block_sprite = TerrainSprites.glow_surface(TerrainSprites.darkness_block_sprite, "dark", 25)

    def preload_terrain(sprite: str = "y", location: str = None, color: tuple[int, int, int] = None):
        if sprite == "y":
            terrain = pg.image.load(location).convert()
            terrain = pg.transform.scale(terrain, (GRID_SQUARE_SIZE, GRID_SQUARE_SIZE))
        elif sprite == "n":
            terrain = pg.Surface((GRID_SQUARE_SIZE, GRID_SQUARE_SIZE))
            terrain.fill(color)

        return terrain
    
    def glow_surface(surface, type, amount):
        temp = surface
        overlay = pg.Surface(temp.get_size(), pg.SRCALPHA)
        color = (0, 0, 0) if type == "dark" else (255, 255, 255)
        overlay.fill((*color, amount))
        temp.blit(overlay, (0, 0))
        return temp

    
class Miner():
    miner_count = 0
    all_mining_positions = []
    glow_radius = 4
    tiles_seen = {}
    def __init__(self, id):
        Miner.miner_count += 1
        self.id = id
        self.sprite = pg.Surface((GRID_SQUARE_SIZE, GRID_SQUARE_SIZE), pg.SRCALPHA)
        pg.draw.circle(self.sprite, (200, 200, 25), (GRID_SQUARE_SIZE // 2, GRID_SQUARE_SIZE // 2), GRID_SQUARE_SIZE // 2)
        self.grid_pos = self.set_position()
        self.pos = self.grid_pos
        self.state = "searching"
        self.moving_to = self.grid_pos
        self.mining_pos = (0, 0)
        Miner.all_mining_positions.append(self.mining_pos)

        self.movement_speed = 2
        self.direction = "down"
        self.pickaxe = Pickaxe("wooden pickaxe", 1)

        self.cd = 0.50 # cool down
        self.dt = self.cd # down time

        self.visibile_tiles = []

    def set_position(self):
        spawn_positions = {
            1: (((GRID_WIDTH // 2) + 1), ((GRID_WIDTH // 2) - 2)),
            2: (((GRID_WIDTH // 2) - 2), ((GRID_WIDTH // 2) - 2)),  # Your OG spot
            3: (((GRID_WIDTH // 2) - 2), ((GRID_WIDTH // 2) + 1)),
            4: (((GRID_WIDTH // 2) + 1), ((GRID_WIDTH // 2) + 1)),
            # Add more as needed
        }

        return spawn_positions[self.id]

    def draw(self, screen):
        map_x, map_y = self.pos[0] * GRID_SQUARE_SIZE, self.pos[1] * GRID_SQUARE_SIZE
        screen.blit(self.sprite, (map_x, map_y))
        return (self.pos[0], self.pos[1])

    def radial_visibility(self, terrain, radius=4):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                tile_x = self.grid_pos[0] + dx
                tile_y = self.grid_pos[1] + dy

                if 0 <= tile_y < len(terrain) and 0 <= tile_x < len(terrain[0]):
                    distance = math.hypot(dx, dy)
                    if distance <= radius:
                        if terrain[tile_y][tile_x] == Terrain.Empty:
                            Miner.tiles_seen[(tile_x, tile_y)] = distance

            # Make sure the miner’s own tile is included!
            Miner.tiles_seen[self.grid_pos] = 0

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

        ore_values = [ore_value[0] for ore_value in values if not self.check_for_occupied(ore_value[1])]
        highest = max(ore_values)

        # Collect all directions where that value is found
        best_directions = [direction for value, direction in values if value == highest]

        chosen_direction = random.choice(best_directions)

        return chosen_direction
    
    @staticmethod
    def clear_tiles_seen_map():
        Miner.tiles_seen = {}
    
    def check_for_occupied(self, direction):
        x, y = self.grid_pos
        if direction == "right":
            if (x + 1, y) in Miner.all_mining_positions:
                return True
        elif direction == "left":
            if (x - 1, y) in Miner.all_mining_positions:
                return True
        elif direction == "down":
            if (x, y + 1) in Miner.all_mining_positions:
                return True
        elif direction == "up":
            if (x, y - 1) in Miner.all_mining_positions:
                return True
        return False
    
    def ai_action(self, terrain, floor_edge_map, terrain_edge_map, terrain_health_map, terrain_to_be_faded, delta_time):
        if self.state == "searching":
            self.search(terrain)
        elif self.state == "moving":
            self.move(terrain)
        elif self.state == "mining":
            self.mine_process(terrain, [floor_edge_map, terrain_edge_map, terrain_health_map, terrain_to_be_faded], delta_time)

    def search(self, terrain):
        values = self.check_surroundings(terrain)
        direction = self.find_best_direction(values)
        x, y = self.grid_pos

        if direction == "right":
            selected_loc = (x + 1, y)
            if terrain[y][x + 1] != Terrain.Empty:
                self.state = "mining"
                self.mining_pos = selected_loc
                Miner.all_mining_positions[self.id - 1] = self.mining_pos
            else:
                self.state = "moving"

        elif direction == "up":
            selected_loc = (x, y - 1)
            if terrain[y - 1][x] != Terrain.Empty:
                self.state = "mining"
                self.mining_pos = selected_loc
                Miner.all_mining_positions[self.id - 1] = self.mining_pos
            else:
                self.state = "moving"

        elif direction == "down":
            selected_loc = (x, y + 1)
            if terrain[y + 1][x] != Terrain.Empty:
                self.state = "mining"
                self.mining_pos = selected_loc
                Miner.all_mining_positions[self.id - 1] = self.mining_pos
            else:
                self.state = "moving"

        elif direction == "left":
            selected_loc = (x - 1, y)
            if terrain[y][x - 1] != Terrain.Empty:
                self.state = "mining"
                self.mining_pos = selected_loc
                Miner.all_mining_positions[self.id - 1] = self.mining_pos
            else:
                self.state = "moving"

        self.moving_to = selected_loc
        self.direction = direction

    def mine_process(self, terrain, maps: list,  delta_time):
        floor_edge_map, terrain_edge_map, terrain_health_map, terrain_to_be_faded = maps
        x, y = self.mining_pos
        if self.dt <= 0:
            terrain_health_map[self.mining_pos] -= self.pickaxe.damage

            selected_ore_max_hp = Terrain.Zone1_terrain_max_healths[terrain[y][x] - 1]
            if terrain_health_map[self.mining_pos] <= 0:
                update_after_broken(terrain, x, y, floor_edge_map, terrain_edge_map, terrain_health_map, terrain_to_be_faded)
                self.state = "moving"
            else:
                current_health_percent = (terrain_health_map[self.mining_pos] / selected_ore_max_hp) * 100
                RenderGroups.draw_health_bar(x, y, current_health_percent)
            self.dt = self.cd

        else:
            self.dt -= delta_time

    def move(self, terrain):
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

class Pickaxe():
    def __init__(self, name, power):
        self.name = name
        self.power = power
        self.damage = self.set_damage()

    def set_damage(self):
        return self.power * 2

def create_miners(terrain, amount):
    miners = []
    for i in range(amount):
        new_miner = Miner(i + 1)
        new_miner.radial_visibility(terrain)
        miners.append(new_miner)
    RenderGroups.draw_miners(miners)

    return miners

def miners_ai_action(miners: list[Miner], terrain, floor_edge_map, terrain_edge_map, terrain_health_map, terrain_to_be_faded, dt):
    Miner.clear_tiles_seen_map()
    for miner in miners:
        miner.radial_visibility(terrain)
        miner.ai_action(terrain, floor_edge_map, terrain_edge_map, terrain_health_map, terrain_to_be_faded, dt)
    RenderGroups.draw_miners(miners)


def create_terrain(floor_edge_map, terrain_edge_map, terrain_health_map, terrain_to_be_faded):
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

    corners = [(start - 1, start - 1), (start + 4, start - 1), (start - 1, start + 4), (start + 4, start + 4)]
    dirty_rects += corners

    create_minerals(terrain)
    RenderGroups.draw_to_visible(terrain, dirty_rects)
    create_terrain_health(terrain, dirty_rects, terrain_health_map)
    terrain_to_be_faded.append((start - 1, start - 1, start + 5, start + 5, 1.0))
    return terrain

def create_minerals(terrain):
    for i in range(len(terrain)):
        for j in range(len(terrain[0])):
            if terrain[i][j] != Terrain.Empty:
                terrain[i][j] = random.choices(Terrain.Zone1_terrain_list, Terrain.Zone1_terrain_chances, k=1)[0]

def create_terrain_health(terrain, visible_blocks, terrain_health_map):
    for x, y in visible_blocks:
        current = terrain[y][x]
        if current != Terrain.Empty:
            terrain_health_map[(x, y)] = Terrain.Zone1_terrain_max_healths[current - 1]

def draw_floor_shadow(screen, offset_x, offset_y):
    screen.blit(Glows.Grid_Top_Glow, (-offset_x, -offset_y - grid_glow_length))
    screen.blit(Glows.Grid_Bottom_Glow, (-offset_x, TOTAL_GRID_HEIGHT - offset_y))
    screen.blit(Glows.Grid_Left_Glow, (-offset_x - grid_glow_length, -offset_y))
    screen.blit(Glows.Grid_Right_Glow, (TOTAL_GRID_WIDTH - offset_x, -offset_y))

    screen.blit(Glows.Grid_Glow_TL, (-offset_x - grid_glow_length, -offset_y - grid_glow_length))
    screen.blit(Glows.Grid_Glow_TR, (TOTAL_GRID_WIDTH - offset_x, -offset_y - grid_glow_length))
    screen.blit(Glows.Grid_Glow_BL, (-offset_x - grid_glow_length, TOTAL_GRID_HEIGHT - offset_y))
    screen.blit(Glows.Grid_Glow_BR, (TOTAL_GRID_WIDTH - offset_x, TOTAL_GRID_HEIGHT - offset_y))


def check_camera(keys, offset_x, offset_y):
    if keys[pg.K_a] and offset_x > (start_offset_x - (TOTAL_GRID_WIDTH // 2)):
        offset_x -= SCROLL_SPEED
    elif keys[pg.K_d] and offset_x < (start_offset_x + (TOTAL_GRID_WIDTH // 2)):
        offset_x += SCROLL_SPEED

    # Vertical movement
    if keys[pg.K_w] and offset_y > (start_offset_y - (TOTAL_GRID_HEIGHT // 2)):
        offset_y -= SCROLL_SPEED
    elif keys[pg.K_s] and offset_y < (start_offset_y + (TOTAL_GRID_HEIGHT // 2)):
        offset_y += SCROLL_SPEED

    return offset_x, offset_y

def draw_floor(screen, offset_x, offset_y):
    screen.blit(RenderGroups.floorMap, (-offset_x, -offset_y))

def draw_miner_lights(screen, offset_x, offset_y):
    RenderGroups.cap_alpha(RenderGroups.minerGlowMap)
    screen.blit(RenderGroups.minerGlowMap, (-offset_x, -offset_y))

def draw_terrain(screen, offset_x, offset_y):
    screen.blit(RenderGroups.terrainShadowMap, (-offset_x, -offset_y))
    screen.blit(RenderGroups.wallMap, (-offset_x, -offset_y))

def draw_miners(screen, offset_x, offset_y):
    screen.blit(RenderGroups.minerMap, (-offset_x, -offset_y))

def draw_healthbars(screen, offset_x, offset_y):
    screen.blit(RenderGroups.HealthBarMap, (-offset_x, -offset_y))

def draw_darkness(screen, offset_x, offset_y):
    screen.blit(RenderGroups.terrainGlowBalanceMap, (-offset_x, -offset_y))
    screen.blit(RenderGroups.darknessMap, (-offset_x, -offset_y))

def draw_outlines(screen, edge_map, terrain_edge_map, offset_x, offset_y):
    # only to be called when on the outskirts of the map or on an empty terrain slot
    for edge in edge_map:

        x, y = edge[0]

        outln_col = (230, 230, 230)

        screen_x = y * GRID_SQUARE_SIZE - offset_x
        screen_y = x * GRID_SQUARE_SIZE - offset_y
        if edge[1] == "down":
            start_x, end_x = screen_x, screen_x + GRID_SQUARE_SIZE
            y = screen_y + GRID_SQUARE_SIZE
            draw_alpha_line(screen, outln_col, (start_x, y), (end_x, y), 2, 15)

            glow_x = screen_x
            glow_y = screen_y + GRID_SQUARE_SIZE - glow_length - 2
            screen.blit(Glows.Glow_Up, (glow_x, glow_y))

        if edge[1] == "up":
            start_x, end_x = screen_x, screen_x + GRID_SQUARE_SIZE
            y = screen_y - 2
            draw_alpha_line(screen, outln_col, (start_x, y), (end_x, y), 2, 15)

            glow_x = screen_x
            glow_y = screen_y + 2
            screen.blit(Glows.Glow_Down, (glow_x, glow_y))

        if edge[1] == "right":
            x = screen_x + GRID_SQUARE_SIZE
            start_y, end_y = screen_y, screen_y + GRID_SQUARE_SIZE
            draw_alpha_line(screen, outln_col, (x, start_y), (x, end_y), 2, 15)

            # Glow should fade leftward from the right edge
            glow_x = screen_x + GRID_SQUARE_SIZE - glow_length - 2 # start at right edge
            glow_y = screen_y
            screen.blit(Glows.Glow_Left, (glow_x, glow_y))

        if edge[1] == "left":
            x = screen_x
            start_y, end_y = screen_y, screen_y + GRID_SQUARE_SIZE
            draw_alpha_line(screen, outln_col, (x, start_y), (x, end_y), 2, 15)

            # Glow should fade rightward from the left edge)
            glow_x = screen_x + 2
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

def draw_alpha_line(target_surface, color, start_pos, end_pos, width, alpha):

    # Calculate the line’s bounding box
    min_x = min(start_pos[0], end_pos[0])
    min_y = min(start_pos[1], end_pos[1])
    max_x = max(start_pos[0], end_pos[0])
    max_y = max(start_pos[1], end_pos[1])
    w = max_x - min_x + width
    h = max_y - min_y + width

    # Create a temporary surface large enough to hold the line
    line_surface = pg.Surface((w, h), pg.SRCALPHA)

    # Offset positions relative to the temporary surface
    start = (start_pos[0] - min_x, start_pos[1] - min_y)
    end = (end_pos[0] - min_x, end_pos[1] - min_y)

    # Draw the line with alpha
    color_with_alpha = (*color[:3], alpha)
    pg.draw.line(line_surface, color_with_alpha, start, end, width)

    # Blit onto target surface at the correct spot
    target_surface.blit(line_surface, (min_x, min_y))




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

def create_corner_glow(size, color, corner, glow_intensity=240):
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
            alpha = int(glow_intensity * fade**1.85)
            glow.set_at((x, y), (*color, alpha))

    return glow

def create_miner_glow(radius, color, glow_intensity=200):
    radius *= GRID_SQUARE_SIZE
    glow_surface = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)

    for x in range(radius * 2):
        for y in range(radius * 2):
            dx = x - radius
            dy = y - radius
            dist = math.hypot(dx, dy)

            if dist <= radius:
                normalized = dist / radius

                # Strong center glow + steep outer fade
                if normalized < 0.1:
                    alpha = glow_intensity
                else:
                    alpha = int((1.0 - normalized) ** 3.5 * glow_intensity)

                glow_surface.set_at((x, y), (*color, max(0, min(alpha, 255))))

    return glow_surface




def update_after_broken(terrain, grid_x, grid_y, floor_edge_map, terrain_edge_map, terrain_health_map, terrain_to_be_faded):
    terrain[grid_y][grid_x] = Terrain.Empty
    surrounding_terrain = check_outlines(grid_y, grid_x, terrain, floor_edge_map, terrain_edge_map)
    dirty_rects = [(grid_x, grid_y)] + surrounding_terrain
    create_terrain_health(terrain, dirty_rects, terrain_health_map)
    RenderGroups.draw_to_visible(terrain, dirty_rects)
    RenderGroups.erase_health_bar(grid_x, grid_y)
    terrain_to_be_faded += [(
        x,
        y,
        x,
        y,
        1.0  # start fully opaque
    )
    for x, y in surrounding_terrain]


class RenderGroups:
    floorMap = None
    wallMap = None
    darknessMap = None
    HealthBarMap = None
    minerMap = None
    minerGlowMap = None
    terrainGlowBalanceMap = None
    terrainShadowMap = None

    @staticmethod
    def init():
        RenderGroups.floorMap = pg.Surface((TOTAL_GRID_WIDTH, TOTAL_GRID_HEIGHT), pg.SRCALPHA)
        RenderGroups.floorMap.fill((5, 5, 5))
        RenderGroups.wallMap = pg.Surface((TOTAL_GRID_WIDTH, TOTAL_GRID_HEIGHT), pg.SRCALPHA)
        RenderGroups.minerMap = pg.Surface((TOTAL_GRID_WIDTH, TOTAL_GRID_HEIGHT), pg.SRCALPHA)
        RenderGroups.HealthBarMap = pg.Surface((TOTAL_GRID_WIDTH, TOTAL_GRID_HEIGHT), pg.SRCALPHA)
        RenderGroups.darknessMap = pg.Surface((TOTAL_GRID_WIDTH, TOTAL_GRID_HEIGHT), pg.SRCALPHA)
        RenderGroups.fill_darkness()
        RenderGroups.terrainGlowBalanceMap = pg.Surface((TOTAL_GRID_WIDTH, TOTAL_GRID_HEIGHT), pg.SRCALPHA)
        RenderGroups.terrainShadowMap = pg.Surface((TOTAL_GRID_WIDTH, TOTAL_GRID_HEIGHT), pg.SRCALPHA)
        RenderGroups.minerGlowMap = pg.Surface((TOTAL_GRID_WIDTH, TOTAL_GRID_HEIGHT), pg.SRCALPHA)

    def draw_to_visible(terrain, positions: list[tuple[int, int]]):
        for tile in positions:
            x, y = tile[0], tile[1]
            map_x, map_y = x * GRID_SQUARE_SIZE, y * GRID_SQUARE_SIZE

            terrain_type = terrain[y][x]
            if terrain_type == Terrain.Stone:
                RenderGroups.wallMap.blit(TerrainSprites.stone_sprite, (map_x, map_y))
            elif terrain_type == Terrain.Coal:
                RenderGroups.wallMap.blit(TerrainSprites.coal_ore_sprite, (map_x, map_y))
            elif terrain_type == Terrain.Emberrock:
                RenderGroups.wallMap.blit(TerrainSprites.emberrock_sprite, (map_x, map_y))
            elif terrain_type == Terrain.Iron_ore:
                RenderGroups.wallMap.blit(TerrainSprites.iron_ore_sprite, (map_x, map_y))
            elif terrain_type == Terrain.Empty:
                RenderGroups.wallMap.fill((0, 0, 0, 0), rect=(map_x, map_y, GRID_SQUARE_SIZE, GRID_SQUARE_SIZE))
                RenderGroups.terrainGlowBalanceMap.fill((0, 0, 0, 0), rect=(map_x, map_y, GRID_SQUARE_SIZE, GRID_SQUARE_SIZE))
                RenderGroups.terrainShadowMap.fill((0, 0, 0, 0), rect=(map_x + 20, map_y + 20, GRID_SQUARE_SIZE, GRID_SQUARE_SIZE))
                RenderGroups.floorMap.blit(TerrainSprites.floor_sprite, (map_x, map_y))

            if terrain_type != Terrain.Empty:
                RenderGroups.terrainShadowMap.fill((10, 10, 10, 230), rect=(map_x + 20, map_y + 20, GRID_SQUARE_SIZE, GRID_SQUARE_SIZE))
                RenderGroups.terrainGlowBalanceMap.fill((0, 0, 0, 100), rect=(map_x, map_y, GRID_SQUARE_SIZE, GRID_SQUARE_SIZE))

    def fill_darkness():
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                map_x, map_y = x * GRID_SQUARE_SIZE, y * GRID_SQUARE_SIZE
                RenderGroups.darknessMap.blit(TerrainSprites.darkness_block_sprite, (map_x, map_y))


    def draw_miners(miners):
        RenderGroups.minerMap.fill((0, 0, 0, 0))
        miner_info = []
        for miner in miners:
            miner_info.append(miner.draw(RenderGroups.minerMap))
        RenderGroups.draw_miner_glow(miner_info)


    def draw_health_bar(x, y, health_percent):
        map_x, map_y = x * GRID_SQUARE_SIZE, y * GRID_SQUARE_SIZE
        # Background (e.g., dark gray)
        pg.draw.rect(RenderGroups.HealthBarMap, (40, 40, 40), (map_x, map_y, GRID_SQUARE_SIZE, 10))

        # Fill (e.g., green) — scaled to health percentage
        fill_width = int(GRID_SQUARE_SIZE * (health_percent / 100))
        pg.draw.rect(RenderGroups.HealthBarMap, (0, 255, 0), (map_x, map_y, fill_width, 10))

    def erase_health_bar(x, y):
        map_x, map_y = x * GRID_SQUARE_SIZE, y * GRID_SQUARE_SIZE
        RenderGroups.HealthBarMap.fill((0, 0, 0, 0), rect=(map_x, map_y, GRID_SQUARE_SIZE, 10))


    def reveal_darkness(terrain: list[(int, int, int, int, int)], fade_speed=0.05):
        # reveal phase can between 0 and 1: 1 - 0.01 means in the process of revealing, 0 means done
        updated_terrain = []

        for x1, y1, x2, y2, reveal_phase in terrain:

            # Clamp phase between 0 and 1 just in case
            reveal_phase = max(0.0, reveal_phase)

            # Calculate current alpha (0 fully transparent → 255 fully opaque)
            fade_strength = reveal_phase ** 1.5  # optional easing for smoother start
            alpha = int(25 + (230 * fade_strength))  # 150 + remainder of 255 - 150



            # Create the fading rect
            rect_x = x1 * GRID_SQUARE_SIZE
            rect_y = y1 * GRID_SQUARE_SIZE
            width = max(1.0, (x2 - x1)) * GRID_SQUARE_SIZE
            height = max(1.0, (y2 - y1)) * GRID_SQUARE_SIZE

            # Draw it on the darkness surface at the proper location
            RenderGroups.darknessMap.fill((5, 5, 5, alpha), rect=(rect_x, rect_y, width, height))

            # Update the phase for next frame
            new_phase = reveal_phase - fade_speed

            if new_phase > 0:
                updated_terrain.append((x1, y1, x2, y2, new_phase))
            # If new_phase <= 0, the block is fully revealed — skip re-adding

        return updated_terrain
    
    def draw_miner_glow(miner_info):
        RenderGroups.minerGlowMap.fill((0, 0, 0, 0))
        for x, y in miner_info:
            map_x, map_y = x * GRID_SQUARE_SIZE, y * GRID_SQUARE_SIZE
            #special_flags = pg.BLEND_RGBA_MULT
            RenderGroups.minerGlowMap.blit(Glows.Glow_Miner, 
                                           (map_x - (Miner.glow_radius * GRID_SQUARE_SIZE) + (GRID_SQUARE_SIZE // 2),
                                             map_y - (Miner.glow_radius * GRID_SQUARE_SIZE) + (GRID_SQUARE_SIZE // 2)))


    def cap_alpha(map):
        import pygame.surfarray
        import numpy as np

        arr = pygame.surfarray.pixels_alpha(map)
        np.clip(arr, 0, 175, out=arr)  # clamp alpha to 0–120 range
        del arr  # release surface lock


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
    Glow_Miner = None
    miner_glow_color = (220, 240, 255)

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
        Glows.Grid_Glow_TL = create_corner_glow(grid_glow_length, Glows.grid_glow_color, "TL").convert_alpha()
        Glows.Grid_Glow_TR = create_corner_glow(grid_glow_length, Glows.grid_glow_color, "TR").convert_alpha()
        Glows.Grid_Glow_BL = create_corner_glow(grid_glow_length, Glows.grid_glow_color, "BL").convert_alpha()
        Glows.Grid_Glow_BR = create_corner_glow(grid_glow_length, Glows.grid_glow_color, "BR").convert_alpha()
        Glows.Glow_Miner = create_miner_glow(Miner.glow_radius, Glows.miner_glow_color).convert_alpha()





def main():

    Glows.init()
    Terrain.init()
    TerrainSprites.init()
    RenderGroups.init()
    global offset_x, offset_y
    clock = pg.time.Clock()
    running = True
    floor_edge_map, terrain_edge_map = [], defaultdict(set)
    terrain_health_map = {}
    terrain_to_be_faded = []
    terrain = create_terrain(floor_edge_map, terrain_edge_map, terrain_health_map, terrain_to_be_faded)
    miners = create_miners(terrain, 4)
    dt = 0.0
# Main game loop
    while running:
        # Handle input
        keys = pg.key.get_pressed()
        offset_x, offset_y = check_camera(keys, offset_x, offset_y)
        

        # Handle events-
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        miners_ai_action(miners, terrain, floor_edge_map, terrain_edge_map, terrain_health_map, terrain_to_be_faded, dt)
        if len(terrain_to_be_faded) >= 1:
            terrain_to_be_faded = RenderGroups.reveal_darkness(terrain_to_be_faded)

        # Render
        screen.fill(BACKGROUND_COLOR)
        draw_floor_shadow(screen, offset_x, offset_y)
        draw_floor(screen, offset_x, offset_y)
        draw_terrain(screen, offset_x, offset_y)
        draw_miner_lights(screen, offset_x, offset_y)
        draw_outlines(screen, floor_edge_map, terrain_edge_map, offset_x, offset_y)
        draw_miners(screen, offset_x, offset_y)
        draw_healthbars(screen, offset_x, offset_y)
        draw_darkness(screen, offset_x, offset_y)
        pg.display.flip()

        # Control frame rate
        dt = clock.tick(FPS) / 1000

    pg.quit()

main()