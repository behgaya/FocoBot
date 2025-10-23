import pygame
import random
import time
from PIL import Image, ImageOps
import cv2
import math

# ------------------------
# Bubble (visual feedback)
# ------------------------
class Bubble:
    def __init__(self, x, y, radius=5, vx=0, vy=-1, color=(200, 200, 255), life=60):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.color = color
        self.life = life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, tela):
        alpha = max(0, int(255 * (self.life / 60)))
        surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (self.radius, self.radius), self.radius)
        tela.blit(surf, (self.x - self.radius, self.y - self.radius))


# ------------------------
# Food Object
# ------------------------
class Food:
    def __init__(self, x, y, img_path="Assets/SUSE/food.png"):
        self.x = x
        self.y = y
        self.collected = False
        self.image = pygame.image.load(img_path).convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (30, 30))
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self, tela):
        if not self.collected:
            tela.blit(self.image, self.rect)


# ------------------------
# Moving Fish Object
# ------------------------
class MovingObject:
    def __init__(self, path, size, x, y, speed):
        self.x = x
        self.y = y
        self.speed = speed
        self.vel_x = random.choice([-1, 1]) * speed
        self.vel_y = random.choice([-1, 1]) * speed
        self.raio = size // 2
        self.img_colorida, self.img_gray = self._load_images(path, (size, size))
        self.img = self.img_gray

    def _load_images(self, path, size):
        pil_img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
        colorida = pygame.image.fromstring(pil_img.tobytes(), pil_img.size, pil_img.mode)

        rgb = pil_img.convert("RGB")
        alpha = pil_img.getchannel("A")
        gray_rgb = ImageOps.grayscale(rgb).convert("RGB")
        gray_pil = Image.merge("RGBA", (*gray_rgb.split(), alpha))
        grayscale = pygame.image.fromstring(gray_pil.tobytes(), gray_pil.size, gray_pil.mode)
        return colorida, grayscale

    def move_toward(self, target_x, target_y, turn_rate=0.05):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        if dist != 0:
            target_vx = self.speed * dx / dist
            target_vy = self.speed * dy / dist
            # Smoothly turn toward target
            self.vel_x = (1 - turn_rate) * self.vel_x + turn_rate * target_vx
            self.vel_y = (1 - turn_rate) * self.vel_y + turn_rate * target_vy
        self.x += self.vel_x
        self.y += self.vel_y


    def draw(self, tela):
        tela.blit(self.img, (self.x - self.raio, self.y - self.raio))

    def set_highlight(self, active: bool):
        self.img = self.img_colorida if active else self.img_gray


    def move_random(self):
        # Slightly rotate current velocity
        angle_change = random.uniform(-0.2, 0.2)
        speed = math.hypot(self.vel_x, self.vel_y)
        current_angle = math.atan2(self.vel_y, self.vel_x) + angle_change
        self.vel_x = math.cos(current_angle) * speed
        self.vel_y = math.sin(current_angle) * speed

        # Move
        self.x += self.vel_x
        self.y += self.vel_y

        # Keep inside screen
        self.x = max(self.raio, min(self.x, 1920 - self.raio))
        self.y = max(self.raio, min(self.y, 1080 - self.raio))

# ------------------------
# Player (gaze or mouse)
# ------------------------
class Player:
    def __init__(self, gaze=None, smooth_alpha=0.2, snap_radius=200):
        self.gaze = gaze
        self.smooth_alpha = smooth_alpha
        self.snap_radius = snap_radius
        self.last_mx, self.last_my = None, None


    def get_position(self):
        if self.gaze:
            mx, my = self.gaze.get_gaze()
            if mx is None or my is None:
                return -1, -1
        else:
            mx, my = pygame.mouse.get_pos()
        return mx, my

    def smooth(self, mx, my):
        if mx < 0 or my < 0:
            return mx, my
        if self.last_mx is not None:
            mx = int(self.smooth_alpha * mx + (1 - self.smooth_alpha) * self.last_mx)
            my = int(self.smooth_alpha * my + (1 - self.smooth_alpha) * self.last_my)
        self.last_mx, self.last_my = mx, my
        return mx, my

    def draw_cursor(self, tela, mx, my):
        if mx >= 0 and my >= 0:
            pygame.draw.circle(tela, (255, 0, 0), (mx, my), 8)

    def snap_to_target(self, mx, my, target_x, target_y):
        if mx < 0 or my < 0:
            return mx, my
        distance = math.hypot(mx - target_x, my - target_y)
        if distance <= self.snap_radius:
            return target_x, target_y
        return mx, my



# ------------------------
# Main Game Class
# ------------------------
class SUSEGame:
    def __init__(self, tela, largura, altura, clock, gaze=None, nivel="facil", num_foods=5, fish_speed=2):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        self.clock = clock
        self.gaze = gaze
        self.fonte = pygame.font.SysFont(None, 36)
        self.num_foods = num_foods
        self.last_watching = False  
        self.velocidade = fish_speed
        
        # Background
        bg_path = "Assets/SUSE/Background/background.png"
        self.background = pygame.image.load(bg_path).convert_alpha()
        self.background = pygame.transform.smoothscale(self.background, (largura, altura))
        self.bg_video = cv2.VideoCapture("Assets/SUSE/Background/background2.mp4")

        self.pontuacao = 0
        self.logo = pygame.image.load("Assets/MainMenu/Logo/logo_suse.png").convert_alpha()
        self.logo = pygame.transform.smoothscale(self.logo, (40, 40))

        # Fish
        imagens_possiveis = [
            "Assets/SUSE/obj1.png",
            "Assets/SUSE/obj2.png",
            "Assets/SUSE/obj3.png"
        ]
        imagem_escolhida = random.choice(imagens_possiveis)
        self.target = MovingObject(imagem_escolhida, 250, largura // 2, altura // 2, self.velocidade)
        self.player = Player(gaze)
        self.bubbles = []
        self.HIT_RADIUS = self.target.raio + 30

        # Foods
        self.foods = []
        min_distance = 150  # minimum distance between foods
        attempts = 0
        for _ in range(num_foods):
            while True:
                fx = random.randint(100, largura - 100)
                fy = random.randint(100, altura - 100)
                too_close = False
                for food in self.foods:
                    if math.hypot(fx - food.x, fy - food.y) < min_distance:
                        too_close = True
                        break
                if not too_close:
                    self.foods.append(Food(fx, fy))
                    break
                attempts += 1
                if attempts > 100:  # fail-safe to avoid infinite loop
                    self.foods.append(Food(fx, fy))
                    break


    # -------------------- Barra de informação --------------------
    def criar_barra_info(self, largura=600, altura=120, y=20, corner_radius=40):
        bar_surface = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.rect(
            bar_surface,
            (0, 0, 0, 120),
            (0, 0, largura, altura),
            border_top_left_radius=0,
            border_bottom_left_radius=0,
            border_top_right_radius=corner_radius,
            border_bottom_right_radius=corner_radius,
        )
        return bar_surface, (0, y)

    def desenhar_barra_info_com_logo(self, texto, bar_surface, bar_pos, bar_height):
        x_inicial = 15
        if self.logo:
            target_height = int(bar_height * 0.95)
            logo_ratio = self.logo.get_width() / self.logo.get_height()
            logo_width = int(target_height * logo_ratio)
            logo_scaled = pygame.transform.smoothscale(self.logo, (logo_width, target_height))
            logo_y = bar_pos[1] + (bar_height - target_height) // 2
            self.tela.blit(logo_scaled, (x_inicial, logo_y))
            x_inicial += logo_width + 15
        texto_surface = self.fonte.render(texto, True, (255, 255, 255))
        texto_rect = texto_surface.get_rect()
        texto_rect.centery = bar_pos[1] + bar_height // 2
        texto_rect.x = x_inicial
        self.tela.blit(texto_surface, texto_rect)

    def get_video_frame(self):
        ret, frame = self.bg_video.read()
        if not ret:
            self.bg_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.bg_video.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (self.largura, self.altura))
        frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        return frame

    # -------------------- Run --------------------
    def run(self):
        rodando = True
        
        while rodando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    rodando = False

        
            # Background frame
            bg_frame = self.get_video_frame()
            self.tela.blit(bg_frame, (0, 0))

            # Entrada: gaze ou mouse
            if self.gaze:
                mx, my = self.gaze.get_gaze()
                if mx is None or my is None:
                    mx, my = -1, -1
            else:
                mx, my = pygame.mouse.get_pos()

            # Snap cursor to fish if close
            mx, my = self.player.snap_to_target(mx, my, self.target.x, self.target.y)

            # --- desenhar cursor do olhar ---
            if mx >= 0 and my >= 0:
                pygame.draw.circle(self.tela, (255, 0, 0), (int(mx), int(my)), 10)   # ponto vermelho
                pygame.draw.circle(self.tela, (0, 0, 0), (int(mx), int(my)), 12, 2) # borda preta

            # Nearest food
            target_food = None
            min_dist = float("inf")
            for food in self.foods:
                if not food.collected:
                    d = math.hypot(self.target.x - food.x, self.target.y - food.y)
                    if d < min_dist:
                        min_dist = d
                        target_food = food

            # inside run loop
            watching = False
            if mx >= 0 and my >= 0:
                dist_to_fish = math.hypot(mx - self.target.x, my - self.target.y)
                watching = dist_to_fish < self.HIT_RADIUS
                self.target.set_highlight(watching)

            # Move fish
            if watching and target_food:
                self.target.move_toward(target_food.x, target_food.y)
            else:
                self.target.move_random()

            # Food collection
            if target_food and watching:
                fish_rect = pygame.Rect(
                    self.target.x - self.target.raio,
                    self.target.y - self.target.raio,
                    self.target.raio * 2,
                    self.target.raio * 2,
                )
                if fish_rect.colliderect(target_food.rect):
                    target_food.collected = True
                    self.pontuacao += 1

            # Draw foods
            for food in self.foods:
                food.draw(self.tela)

            # Bubbles
            if random.random() < 0.3:
                self.bubbles.append(
                    Bubble(self.target.x, self.target.y, random.randint(3, 8),
                           random.uniform(-0.3, 0.3), -random.uniform(1, 3))
                )
            for bubble in self.bubbles[:]:
                bubble.update()
                bubble.draw(self.tela)
                if bubble.life <= 0:
                    self.bubbles.remove(bubble)

            # Draw fish & cursor
            self.target.draw(self.tela)
            #self.player.draw_cursor(self.tela, mx, my)

            # Info bar
            bar_surface, bar_pos = self.criar_barra_info(largura=300, altura=50, y=10)
            self.tela.blit(bar_surface, bar_pos)
            self.desenhar_barra_info_com_logo(
                f"Pontos: {self.pontuacao}/{self.num_foods}", bar_surface, bar_pos, 50
            )

            # Win condition
            if all(food.collected for food in self.foods):
                rodando = False

            pygame.display.flip()
            self.clock.tick(60)

        if self.gaze:
            self.gaze.release()
        print(f"Fim do jogo! Pontos: {self.pontuacao}/{self.num_foods}")
