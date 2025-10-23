import pygame
import random
import math
import cv2

# ----------------------------
# GameObject (rocket, planet, asteroids)
# ----------------------------
class GameObject:
    def __init__(self, x, y, vx, vy, raio, imagem=None, alvo=False, border_margin=200):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.raio = raio
        self.alvo = alvo
        self.border_margin = border_margin
        self.focus_time = 0
        self.time = 0
        self.angle = 0
        self.scale_phase = random.random() * 2 * math.pi
        if imagem:
            self.original_img = self.scale_image_keep_aspect(imagem, raio*2)
            self.imagem = self.original_img
        else:
            self.imagem = None

    @staticmethod
    def scale_image_keep_aspect(img, max_size):
        w, h = img.get_size()
        scale = min(max_size / w, max_size / h)
        new_w, new_h = int(w*scale), int(h*scale)
        return pygame.transform.smoothscale(img, (new_w, new_h))

    def update(self, largura, altura):
        self.x += self.vx
        self.y += self.vy

        # Mantém dentro da tela com margem
        min_x = self.raio + self.border_margin
        max_x = largura - self.raio - self.border_margin
        min_y = self.raio + self.border_margin
        max_y = altura - self.raio - self.border_margin

        # Verifica bordas e ajusta suavemente
        if self.x <= min_x:
            self.x = min_x
            if self.vx < 0:
                self.vx = abs(self.vx)  # garante movimento para dentro
        elif self.x >= max_x:
            self.x = max_x
            if self.vx > 0:
                self.vx = -abs(self.vx)

        if self.y <= min_y:
            self.y = min_y
            if self.vy < 0:
                self.vy = abs(self.vy)
        elif self.y >= max_y:
            self.y = max_y
            if self.vy > 0:
                self.vy = -abs(self.vy)

        # Animação
        self.time += 0.05
        self.angle = (self.angle + 1) % 360
        scale = 1.0 + 0.05 * math.sin(self.time + self.scale_phase)
        if self.imagem:
            self.imagem = pygame.transform.rotozoom(self.original_img, self.angle, scale)


    def draw(self, tela):
        if self.imagem:
            rect = self.imagem.get_rect(center=(int(self.x), int(self.y)))
            tela.blit(self.imagem, rect)


class Star(GameObject):
    def __init__(self, largura, altura, imagem=None):
        x = -50
        y = random.randint(100, altura - 100)
        vx = random.uniform(2, 4)
        vy = 0
        raio = 40
        super().__init__(x, y, vx, vy, raio, imagem)
        self.blink_phase = random.random() * 2 * math.pi

    def update(self, largura, altura):
        # Move horizontally
        self.x += self.vx

        # Small blinking / pulsing
        self.blink_phase += 0.1
        scale = 1.0 + 0.1 * math.sin(self.blink_phase)
        if self.original_img:
            self.imagem = pygame.transform.rotozoom(self.original_img, 0, scale)



# ----------------------------
# Player (gaze/mouse)
# ----------------------------
class Player:
    def __init__(self, gaze=None, snap_radius=160, release_mult=1.5):
        self.gaze = gaze
        self.snap_radius = snap_radius
        self.release_radius = snap_radius * release_mult
        self.snapped_obj = None

    def get_input(self):
        if self.gaze:
            mx, my = self.gaze.get_gaze()
            if mx is None or my is None: return -1, -1
            return mx, my
        else:
            return pygame.mouse.get_pos()

    def apply_snapping(self, raw_mx, raw_my, objetos):
        mx, my = raw_mx, raw_my
        if raw_mx < 0 or raw_my < 0: return mx, my

        if self.snapped_obj:
            dist = ((raw_mx - self.snapped_obj.x)**2 + (raw_my - self.snapped_obj.y)**2)**0.5
            if dist > self.release_radius:
                self.snapped_obj = None
            else:
                return self.snapped_obj.x, self.snapped_obj.y

        if not self.snapped_obj:
            for obj in objetos:
                dist = ((raw_mx - obj.x)**2 + (raw_my - obj.y)**2)**0.5
                if dist < self.snap_radius:
                    self.snapped_obj = obj
                    return obj.x, obj.y

        return mx, my

    def draw_cursor(self, tela, mx, my, rocket=None):
        if mx >= 0 and my >= 0:
            pygame.draw.circle(tela, (255,0,0), (int(mx), int(my)), 8)
            pygame.draw.circle(tela, (0,0,0), (int(mx), int(my)), 12, 2)
        if rocket:
            pygame.draw.circle(tela, (0,255,0), (int(rocket.x), int(rocket.y)), rocket.raio+20, 2)


# ----------------------------
# SESEGame
# ----------------------------
class SESEGame:
    def __init__(self, tela, largura, altura, clock, gaze=None, asteroid_count=5, rocket_speed=0.5):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        self.clock = clock
        self.gaze = gaze
        self.player = Player(gaze)
        self.font = pygame.font.SysFont(None, 36)
        self.star = None
        self.star_timer = random.randint(300, 600)  # frames until next star
        self.speed_boost_time = 0
        self.star_img = pygame.image.load("Assets/SESE_Minigame/estrela.png").convert_alpha()

        self.asteroid_count = asteroid_count
        self.rocket_speed = rocket_speed

        # Load images
        self.rocket_img = pygame.image.load("Assets/SESE_Minigame/foguete.png").convert_alpha()
        self.planet_img = pygame.image.load("Assets/SESE_Minigame/planeta.png").convert_alpha()
        self.asteroid_img = pygame.image.load("Assets/SESE_Minigame/asteroide.png").convert_alpha()

        # Create objects
        self.rocket = GameObject(100, random.randint(100, altura-100), 0, 0, 60, self.rocket_img)
        self.planet = GameObject(largura-150, random.randint(100, altura-100), 0, 0, 80, self.planet_img)
        self.asteroids = []
        for _ in range(self.asteroid_count):
            ast = GameObject(
                random.randint(100, largura-100),
                random.randint(100, altura-100),
                random.choice([-2, -1, 1, 2]),
                random.choice([-2, -1, 1, 2]),
                50, self.asteroid_img
            )
            self.asteroids.append(ast)

        # Background video
        self.bg_video_path = "Assets/SESE_Minigame/background/background2.mp4"
        self.bg_video = cv2.VideoCapture(self.bg_video_path)

        self.rodando = True

    def get_video_frame(self):
        ret, frame = self.bg_video.read()
        if not ret:
            self.bg_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.bg_video.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (self.largura, self.altura))
        return pygame.surfarray.make_surface(frame.swapaxes(0,1))
    

    def check_collision(self, obj1, obj2):
        dx = obj1.x - obj2.x
        dy = obj1.y - obj2.y
        dist = math.hypot(dx, dy)
        min_dist = obj1.raio + obj2.raio
        if dist < min_dist and dist != 0:
            overlap = min_dist - dist
            obj1.x += (dx / dist) * overlap
            obj1.y += (dy / dist) * overlap

            nx, ny = dx / dist, dy / dist
            dot = obj1.vx * nx + obj1.vy * ny
            obj1.vx -= 2 * dot * nx
            obj1.vy -= 2 * dot * ny


    def run(self):
        # Initialize star variables
        self.star = None
        self.star_timer = random.randint(600, 1200)  # frames until next star
        self.speed_boost_time = 0  # frames remaining for speed boost

        while self.rodando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.rodando = False

            # Background
            bg_frame = self.get_video_frame()
            self.tela.blit(bg_frame, (0, 0))

            # Input
            mx, my = self.player.get_input()
            snap_objects = [self.rocket] + self.asteroids
            if self.star:
                snap_objects.append(self.star)

            mx, my = self.player.apply_snapping(mx, my, snap_objects)

            self.player.draw_cursor(self.tela, mx, my, rocket=self.rocket)

            # Move asteroids
            for ast in self.asteroids:
                ast.update(self.largura, self.altura)

                # Collision with rocket
                self.check_collision(ast, self.rocket)

                # Collision with other asteroids
                for other in self.asteroids:
                    if other != ast:
                        self.check_collision(ast, other)

                ast.draw(self.tela)

            # Move rocket toward planet if looking at rocket and not asteroids
            dist_to_rocket = math.hypot(mx - self.rocket.x, my - self.rocket.y)
            looking_at_asteroid = any(math.hypot(mx - a.x, my - a.y) < a.raio for a in self.asteroids)

            if dist_to_rocket < self.rocket.raio and not looking_at_asteroid:
                dx = self.planet.x - self.rocket.x
                dy = self.planet.y - self.rocket.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    # Determine current rocket speed
                    current_speed = self.rocket_speed
                    if self.speed_boost_time > 0:
                        current_speed *= 2  # double speed
                        self.speed_boost_time -= 1

                    # Base movement vector
                    move_x = current_speed * dx / dist
                    move_y = current_speed * dy / dist

                    # Sinusoidal sway
                    sway_amplitude = 3
                    sway_speed = 0.15
                    move_x += sway_amplitude * math.sin(self.rocket.time * sway_speed)
                    move_y += sway_amplitude * math.cos(self.rocket.time * sway_speed)

                    # Random jitter
                    jitter = 1.0
                    move_x += random.uniform(-jitter, jitter)
                    move_y += random.uniform(-jitter, jitter)

                    # Apply movement
                    self.rocket.x += move_x
                    self.rocket.y += move_y

            elif looking_at_asteroid:
                self.rocket.x = max(100, self.rocket.x - self.rocket_speed // 1.5)

            # Handle star spawn
            self.star_timer -= 1
            if self.star_timer <= 0 and self.star is None:
                self.star = Star(self.largura, self.altura, self.star_img)
                self.star_timer = random.randint(600, 1200)

            # Update and draw star
            if self.star:
                self.star.update(self.largura, self.altura)
                self.star.draw(self.tela)

                # Check if player is looking at the star
                if mx >= 0 and my >= 0:
                    dist_to_star = math.hypot(mx - self.star.x, my - self.star.y)
                    if dist_to_star < self.star.raio:
                        self.speed_boost_time = 120  # 2 seconds boost at 60 FPS
                        self.star = None  # star disappears after being “looked at”

                # Remove star if it goes off screen
                if self.star and self.star.x - self.star.raio > self.largura:
                    self.star = None

            # Update and draw rocket & planet
            self.rocket.update(self.largura, self.altura)
            self.rocket.draw(self.tela)
            self.planet.update(self.largura, self.altura)
            self.planet.draw(self.tela)

            # Win condition
            if math.hypot(self.rocket.x - self.planet.x, self.rocket.y - self.planet.y) < self.rocket.raio:
                print("Você chegou no planeta!")
                self.rodando = False

            pygame.display.flip()
            self.clock.tick(60)
