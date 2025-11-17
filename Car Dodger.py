import pygame
import random
import sys

# --- Configuration ---
WIDTH, HEIGHT = 480, 700
FPS = 60
LANE_COUNT = 3
LANE_PADDING = 40
CAR_WIDTH, CAR_HEIGHT = 50, 90
OBSTACLE_WIDTH, OBSTACLE_HEIGHT = 50, 90
SPAWN_EVENT = pygame.USEREVENT + 1

# Game parameters (scales with score)
BASE_SPAWN_MS = 1000
MIN_SPAWN_MS = 350
BASE_SPEED = 4
MAX_SPEED = 18

# Colors
WHITE = (255, 255, 255)
GRAY = (30, 30, 30)
ROAD = (50, 50, 50)
YELLOW = (240, 220, 80)
RED = (200, 30, 30)
GREEN = (30, 180, 30)
BLUE = (30, 140, 220)
BLACK = (0, 0, 0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Car Dodger")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
big_font = pygame.font.SysFont(None, 64)

# Calculate lane centers
lane_width = (WIDTH - 2 * LANE_PADDING) / LANE_COUNT
lane_centers = [int(LANE_PADDING + lane_width * i + lane_width / 2) for i in range(LANE_COUNT)]

# Helper functions
def draw_text(surf, text, pos, color=WHITE, fontobj=None):
    f = fontobj if fontobj else font
    img = f.render(text, True, color)
    surf.blit(img, pos)

class Player:
    def __init__(self):
        self.lane = LANE_COUNT // 2
        self.rect = pygame.Rect(0, 0, CAR_WIDTH, CAR_HEIGHT)
        self.update_pos()
        self.color = BLUE
        self.alive = True

    def update_pos(self):
        cx = lane_centers[self.lane]
        self.rect.centerx = cx
        self.rect.bottom = HEIGHT - 20

    def move_left(self):
        if self.lane > 0:
            self.lane -= 1
            self.update_pos()

    def move_right(self):
        if self.lane < LANE_COUNT - 1:
            self.lane += 1
            self.update_pos()

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect, border_radius=8)
        # windshield / decoration
        windshield = pygame.Rect(self.rect.centerx - 12, self.rect.top + 12, 24, 18)
        pygame.draw.rect(surf, (200, 230, 255), windshield, border_radius=4)

class Obstacle:
    def __init__(self, lane, speed):
        self.lane = lane
        self.rect = pygame.Rect(0, 0, OBSTACLE_WIDTH, OBSTACLE_HEIGHT)
        self.rect.centerx = lane_centers[lane]
        self.rect.top = -OBSTACLE_HEIGHT - random.randint(0, 100)
        self.speed = speed
        self.color = RED if random.random() < 0.5 else GREEN

    def update(self):
        self.rect.y += self.speed

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect, border_radius=8)
        # small headlight shapes
        hl_w = 8
        pygame.draw.rect(surf, YELLOW, (self.rect.left+8, self.rect.bottom-18, hl_w, 6), border_radius=2)
        pygame.draw.rect(surf, YELLOW, (self.rect.right-8-hl_w, self.rect.bottom-18, hl_w, 6), border_radius=2)

def draw_road(surf):
    surf.fill(GRAY)
    road_rect = pygame.Rect(LANE_PADDING - 10, 0, WIDTH - 2*(LANE_PADDING - 10), HEIGHT)
    pygame.draw.rect(surf, ROAD, road_rect)
    # draw lane separators
    for i in range(1, LANE_COUNT):
        x = int(LANE_PADDING + i * lane_width)
        # dashed line
        dash_h = 30
        gap = 20
        y = -((pygame.time.get_ticks() // 6) % (dash_h + gap))
        while y < HEIGHT:
            pygame.draw.line(surf, WHITE, (x, y), (x, y + dash_h), 4)
            y += dash_h + gap

def spawn_obstacle_for_score(score):
    # speed scales with score
    speed = min(BASE_SPEED + score // 5, MAX_SPEED)
    # bias spawn lanes (less likely to spawn in same lane twice consecutively)
    lane = random.randrange(0, LANE_COUNT)
    return Obstacle(lane, speed)

def game_loop():
    player = Player()
    obstacles = []
    score = 0
    running = True
    paused = False

    # spawn timing: reduce interval as score increases
    def set_spawn_timer():
        interval = max(MIN_SPAWN_MS, BASE_SPAWN_MS - (score * 8))
        pygame.time.set_timer(SPAWN_EVENT, interval)
    set_spawn_timer()

    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # quit whole program
            if event.type == SPAWN_EVENT and not paused and player.alive:
                obstacles.append(spawn_obstacle_for_score(score))
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key in (pygame.K_p, pygame.K_SPACE):
                    paused = not paused
                if event.key == pygame.K_r and not player.alive:
                    # restart
                    return True  # signal restart
                if not paused and player.alive:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        player.move_left()
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        player.move_right()

        if not paused and player.alive:
            # update obstacles
            for ob in obstacles:
                ob.update()

            # remove off-screen obstacles and increase score when they pass
            new_obstacles = []
            for ob in obstacles:
                if ob.rect.top > HEIGHT:
                    score += 1
                    set_spawn_timer()
                else:
                    new_obstacles.append(ob)
            obstacles = new_obstacles

            # collision check (rect collision)
            for ob in obstacles:
                if player.rect.colliderect(ob.rect):
                    player.alive = False
                    # stop spawn timer
                    pygame.time.set_timer(SPAWN_EVENT, 0)

        # draw everything
        draw_road(screen)
        # draw side borders
        pygame.draw.rect(screen, BLACK, (0, 0, LANE_PADDING - 10, HEIGHT))
        pygame.draw.rect(screen, BLACK, (WIDTH - (LANE_PADDING - 10), 0, LANE_PADDING - 10, HEIGHT))

        # draw obstacles and player
        for ob in obstacles:
            ob.draw(screen)
        player.draw(screen)

        # HUD
        draw_text(screen, f"Score: {score}", (10, 10))
        draw_text(screen, "P/SPACE to pause, ←/→ or A/D to move, R to restart", (10, 40), color=(200,200,200), fontobj=pygame.font.SysFont(None, 20))

        if paused:
            draw_text(screen, "PAUSED", (WIDTH//2 - 60, HEIGHT//2 - 20), color=YELLOW, fontobj=big_font)

        if not player.alive:
            draw_text(screen, "GAME OVER", (WIDTH//2 - 140, HEIGHT//2 - 40), color=RED, fontobj=big_font)
            draw_text(screen, f"Final Score: {score}", (WIDTH//2 - 80, HEIGHT//2 + 20), color=WHITE, fontobj=font)
            draw_text(screen, "Press R to play again or ESC to quit", (WIDTH//2 - 160, HEIGHT//2 + 60), color=(200,200,200), fontobj=pygame.font.SysFont(None, 20))

        pygame.display.flip()

    return False

def main():
    playing = True
    while playing:
        should_restart = game_loop()
        if should_restart:
            continue
        else:
            break
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
