#COMPLETE RTS GAME CODE

import math
import random
import sys
import pygame

# --- Configuration & Constants ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# Colors
COLOR_BG = (34, 139, 34)       # Grass Green
COLOR_GRID = (30, 120, 30)
COLOR_RESOURCE = (255, 215, 0) # Gold
COLOR_UNIT = (30, 144, 255)   # Blue
COLOR_SELECTED = (255, 255, 255)
COLOR_BUILDING = (70, 130, 180)
COLOR_GHOST_VALID = (0, 255, 0, 128)
COLOR_GHOST_INVALID = (255, 0, 0, 128)
COLOR_UI = (50, 50, 50)
COLOR_TEXT = (255, 255, 255)

# Game Settings
UNIT_SPEED = 2.0
UNIT_RADIUS = 12
HARVEST_SPEED = 1      # Resources per tick
HARVEST_CAPACITY = 10  # Max carried gold per worker
BUILDING_COST = 50     # Gold required to build

# --- Entity Classes ---

class ResourceNode:
    def __init__(self, x, y, amount=500):
        self.x = x
        self.y = y
        self.radius = 20
        self.amount = amount

    def draw(self, surface):
        if self.amount > 0:
            pygame.draw.circle(surface, COLOR_RESOURCE, (int(self.x), int(self.y)), self.radius)
            # Inner circle scaling with remaining resources
            inner_r = max(2, int(self.radius * (self.amount / 500.0)))
            pygame.draw.circle(surface, (200, 160, 0), (int(self.x), int(self.y)), inner_r)

class Building:
    def __init__(self, x, y, width=60, height=60):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = COLOR_BUILDING

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, (30, 30, 30), self.rect, 2)

class Unit:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.selected = False
        
        # Gathering State Machine
        self.target_resource = None
        self.target_base = None
        self.carried_gold = 0
        self.state = "IDLE"  # IDLE, MOVING, HARVESTING, RETURNING

    def update(self, bases):
        # 1. State logic for harvesting
        if self.state == "HARVESTING" and self.target_resource:
            dist = math.hypot(self.target_resource.x - self.x, self.target_resource.y - self.y)
            if dist <= self.target_resource.radius + UNIT_RADIUS + 5:
                # Harvest resource
                if self.target_resource.amount > 0 and self.carried_gold < HARVEST_CAPACITY:
                    self.target_resource.amount -= HARVEST_SPEED
                    self.carried_gold += HARVEST_SPEED
                else:
                    # Full or node depleted -> find nearest base to drop off
                    nearest_base = self._find_nearest_base(bases)
                    if nearest_base:
                        self.target_base = nearest_base
                        self.target_x = nearest_base.rect.centerx
                        self.target_y = nearest_base.rect.centery
                        self.state = "RETURNING"
            else:
                # Move closer to resource
                self.target_x = self.target_resource.x
                self.target_y = self.target_resource.y

        elif self.state == "RETURNING" and self.target_base:
            dist = math.hypot(self.target_base.rect.centerx - self.x, self.target_base.rect.centery - self.y)
            if dist <= self.target_base.rect.width // 2 + UNIT_RADIUS:
                # Deposit resources
                deposited = self.carried_gold
                self.carried_gold = 0
                
                # Resume harvesting if resource still exists
                if self.target_resource and self.target_resource.amount > 0:
                    self.target_x = self.target_resource.x
                    self.target_y = self.target_resource.y
                    self.state = "HARVESTING"
                else:
                    self.state = "IDLE"
                return deposited

        # 2. Smooth Movement Towards Target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)

        if dist > UNIT_SPEED:
            self.x += (dx / dist) * UNIT_SPEED
            self.y += (dy / dist) * UNIT_SPEED
        else:
            self.x = self.target_x
            self.y = self.target_y
            if self.state == "MOVING":
                self.state = "IDLE"

        return 0

    def _find_nearest_base(self, bases):
        if not bases:
            return None
        return min(bases, key=lambda b: math.hypot(b.rect.centerx - self.x, b.rect.centery - self.y))

    def draw(self, surface):
        # Selection highlight
        if self.selected:
            pygame.draw.circle(surface, COLOR_SELECTED, (int(self.x), int(self.y)), UNIT_RADIUS + 3, 2)
        
        # Unit body
        pygame.draw.circle(surface, COLOR_UNIT, (int(self.x), int(self.y)), UNIT_RADIUS)
        
        # Indicate carrying resource
        if self.carried_gold > 0:
            pygame.draw.circle(surface, COLOR_RESOURCE, (int(self.x), int(self.y)), 4)

# --- Main Game Engine Class ---

class RTSGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Python RTS Engine")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)

        # Game State
        self.resources = 100
        self.units = [Unit(150 + i * 25, 200) for i in range(4)]
        self.bases = [Building(100, 100)]
        self.resource_nodes = [
            ResourceNode(500, 150, 600),
            ResourceNode(700, 400, 800),
            ResourceNode(300, 500, 500)
        ]

        # Interaction & Controls State
        self.drag_start = None
        self.drag_rect = None
        self.build_mode = False
        self.building_size = (60, 60)

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    # Toggle build mode
                    self.build_mode = not self.build_mode
                elif event.key == pygame.K_ESCAPE:
                    self.build_mode = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left Mouse Button
                    if self.build_mode:
                        self.try_place_building(mouse_pos)
                    else:
                        # Begin drag selection
                        self.drag_start = mouse_pos
                        self.drag_rect = pygame.Rect(mouse_pos[0], mouse_pos[1], 0, 0)

                elif event.button == 3:  # Right Mouse Button
                    # Cancel build mode on right-click
                    if self.build_mode:
                        self.build_mode = False
                    else:
                        self.issue_command(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.drag_start and not self.build_mode:
                    self.finish_box_selection(mouse_pos)
                    self.drag_start = None
                    self.drag_rect = None

            elif event.type == pygame.MOUSEMOTION:
                if self.drag_start and not self.build_mode:
                    # Update box selection dimensions
                    x = min(self.drag_start[0], mouse_pos[0])
                    y = min(self.drag_start[1], mouse_pos[1])
                    w = abs(self.drag_start[0] - mouse_pos[0])
                    h = abs(self.drag_start[1] - mouse_pos[1])
                    self.drag_rect = pygame.Rect(x, y, w, h)

        return True

    def finish_box_selection(self, mouse_pos):
        # Deselect all first
        for u in self.units:
            u.selected = False

        # If drag was tiny, treat as a single point click
        if self.drag_rect and (self.drag_rect.width > 5 or self.drag_rect.height > 5):
            for u in self.units:
                if self.drag_rect.collidepoint(u.x, u.y):
                    u.selected = True
        else:
            # Single click unit selection
            for u in self.units:
                if math.hypot(u.x - mouse_pos[0], u.y - mouse_pos[1]) <= UNIT_RADIUS + 3:
                    u.selected = True
                    break

    def issue_command(self, pos):
        # Find selected units
        selected_units = [u for u in self.units if u.selected]
        if not selected_units:
            return

        # Check if clicked on a resource node
        target_node = None
        for node in self.resource_nodes:
            if math.hypot(node.x - pos[0], node.y - pos[1]) <= node.radius and node.amount > 0:
                target_node = node
                break

        # Command units
        for u in selected_units:
            if target_node:
                u.target_resource = target_node
                u.state = "HARVESTING"
            else:
                u.target_x = pos[0]
                u.target_y = pos[1]
                u.target_resource = None
                u.state = "MOVING"

    def try_place_building(self, pos):
        if self.resources >= BUILDING_COST:
            new_building = Building(pos[0] - self.building_size[0] // 2, 
                                    pos[1] - self.building_size[1] // 2, 
                                    self.building_size[0], self.building_size[1])
            self.bases.append(new_building)
            self.resources -= BUILDING_COST
            self.build_mode = False

    def update(self):
        # Cleanup depleted resources
        self.resource_nodes = [node for node in self.resource_nodes if node.amount > 0]

        # Update units & gather resources
        for unit in self.units:
            gathered = unit.update(self.bases)
            self.resources += gathered

    def render(self):
        self.screen.fill(COLOR_BG)

        # Draw Entities
        for node in self.resource_nodes:
            node.draw(self.screen)

        for base in self.bases:
            base.draw(self.screen)

        for unit in self.units:
            unit.draw(self.screen)

        # Draw Box Selection Drag Rect
        if self.drag_rect:
            pygame.draw.rect(self.screen, COLOR_SELECTED, self.drag_rect, 1)

        # Draw Building Preview Ghost
        if self.build_mode:
            mx, my = pygame.mouse.get_pos()
            ghost_rect = pygame.Rect(mx - self.building_size[0] // 2, 
                                     my - self.building_size[1] // 2, 
                                     self.building_size[0], self.building_size[1])
            ghost_color = COLOR_GHOST_VALID if self.resources >= BUILDING_COST else COLOR_GHOST_INVALID
            
            s = pygame.Surface((self.building_size[0], self.building_size[1]), pygame.SRCALPHA)
            s.fill(ghost_color)
            self.screen.blit(s, ghost_rect.topleft)

        # Render HUD / UI
        self.render_ui()

        pygame.display.flip()

    def render_ui(self):
        # UI Top Bar
        pygame.draw.rect(self.screen, COLOR_UI, (0, 0, SCREEN_WIDTH, 40))
        
        res_text = self.font.render(f"Gold: {self.resources}", True, COLOR_RESOURCE)
        units_text = self.font.render(f"Selected Units: {sum(1 for u in self.units if u.selected)}", True, COLOR_TEXT)
        instructions = self.font.render("L-Drag: Select | R-Click: Move/Gather | 'B': Build Base (Cost: 50)", True, COLOR_TEXT)

        self.screen.blit(res_text, (20, 10))
        self.screen.blit(units_text, (150, 10))
        self.screen.blit(instructions, (350, 10))


if __name__ == "__main__":
    game = RTSGame()
    game.run()
