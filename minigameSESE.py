import pygame
import random
import math
import cv2
import numpy as np
import time
from metricas_tecnicas import MetricasTecnicas


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
        self.grayscale = False
        self.gray_img = None



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

    def to_grayscale(self, img):
        arr = pygame.surfarray.pixels3d(img).copy()
        alpha = pygame.surfarray.pixels_alpha(img).copy()

        # Converte para grayscale
        gray = arr.mean(axis=2).astype('uint8')

        # Cria imagem cinza com 3 canais
        gray_rgb = np.stack((gray, gray, gray), axis=2)

        # Constrói surface final
        surf = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        pygame.surfarray.blit_array(surf, gray_rgb)

        # Adiciona alpha original
        pygame.surfarray.pixels_alpha(surf)[:] = alpha

        return surf


    def update(self, largura, altura):
        self.x += self.vx
        self.y += self.vy

        # ----------------------
        # ANIMAÇÃO (calcula scale antes de usar!)
        # ----------------------
        self.time += 0.05
        self.angle = (self.angle + 1) % 360
        scale = 1.0 + 0.05 * math.sin(self.time + self.scale_phase)

        # ----------------------
        # APLICA GRAYSCALE OU COLORIDO
        # ----------------------
        if self.grayscale:
            if self.gray_img is None:
                self.gray_img = self.to_grayscale(self.original_img)
            base = self.gray_img
        else:
            base = self.original_img

        self.imagem = pygame.transform.rotozoom(base, self.angle, scale)

        # ----------------------
        # LIMITES DA TELA
        # ----------------------
        min_x = self.raio + self.border_margin
        max_x = largura - self.raio - self.border_margin
        min_y = self.raio + self.border_margin
        max_y = altura - self.raio - self.border_margin

        if self.x <= min_x:
            self.x = min_x
            if self.vx < 0: self.vx = abs(self.vx)
        elif self.x >= max_x:
            self.x = max_x
            if self.vx > 0: self.vx = -abs(self.vx)

        if self.y <= min_y:
            self.y = min_y
            if self.vy < 0: self.vy = abs(self.vy)
        elif self.y >= max_y:
            self.y = max_y
            if self.vy > 0: self.vy = -abs(self.vy)


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
    def __init__(self, gaze=None, snap_radius=120, release_mult=1.5):
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

    def apply_snapping(self, mx, my, objetos):
        """
        Aplica snap do cursor a objetos da tela.
        mx, my: posição atual do cursor/gaze
        objetos: lista de objetos (GameObject, foguete, asteroides, etc.)
        """
        if mx < 0 or my < 0:
            return mx, my

        for obj in objetos:
            distance = math.hypot(mx - obj.x, my - obj.y)

            # Snap maior para asteroides
            if hasattr(obj, "raio") and obj.raio < 100:  # considera asteroides pelo tamanho
                snap_r = self.snap_radius
            else:  # foguete, estrela ou outros
                snap_r = self.snap_radius

            if distance <= snap_r:
                return obj.x, obj.y  # snap aplicado

        return mx, my  # nenhum snap


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
        self.first_fixation_time = None 
        self.focus_time_total = 0        
        self.focus_durations = []         
        self.focus_events = 0             
        self.last_focus_start = None
        self.last_watching = False
        self.start_time = None  
        self.gaze_points = []  
        self.rocket_positions = []  
        self.heatmap_alpha = 100  
        self.asteroid_look_events = 0       
        self.asteroid_punishments = 0        
        self.asteroid_reaction_times = []    
        self.asteroid_look_start = None     

        # imagem colorida
        self.rocket_img = pygame.image.load("Assets/SESE_Minigame/foguete.png").convert_alpha()
        # # gerar versão grayscale
        # self.rocket_img_gray = pygame.transform.average_color(self.rocket_img)
        # w, h = self.rocket_img.get_size()
        # gray_surface = pygame.Surface((w, h)).convert_alpha()

        # for x in range(w):
        #     for y in range(h):
        #         r, g, b, a = self.rocket_img.get_at((x, y))
        #         gray = int((r + g + b) / 3)
        #         gray_surface.set_at((x, y), (gray, gray, gray, a))

        # self.rocket_img_gray = gray_surface
        self.planet_img = pygame.image.load("Assets/SESE_Minigame/planeta.png").convert_alpha()
        self.asteroid_img = pygame.image.load("Assets/SESE_Minigame/asteroide.png").convert_alpha()

        # Create objects
        self.rocket = GameObject(100, random.randint(100, altura-100), 0, 0, 120, self.rocket_img)
        self.planet = GameObject(largura-150, random.randint(100, altura-100), 0, 0, 80, self.planet_img)
        self.asteroids = []
        for _ in range(self.asteroid_count):
            ast = GameObject(
                random.randint(100, largura-100),
                random.randint(100, altura-100),
                random.choice([-2, -1, 1, 2]),
                random.choice([-2, -1, 1, 2]),
                80, self.asteroid_img
            )
            self.asteroids.append(ast)


        self.asteroid_counted = {id(a): False for a in self.asteroids}

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




    def generate_heatmap(self, max_points=5000):
        """
        Gera heatmap dos pontos de olhar (gaze) e retorna superfície Pygame + imagem BGR para salvar.
        """
        # Limita o número de pontos para evitar distorções
        points = self.gaze_points[-max_points:]

        heat = np.zeros((self.altura, self.largura), dtype=np.float32)
        for x, y in points:
            if 0 <= x < self.largura and 0 <= y < self.altura:
                heat[int(y), int(x)] += 1

        # Gaussian blur para suavizar
        heat = cv2.GaussianBlur(heat, (0, 0), sigmaX=50, sigmaY=50)

        # Normaliza com segurança
        max_val = heat.max()
        heat = np.clip((heat / (max_val + 1e-5)) * 255, 0, 255).astype(np.uint8)

        # Aplica colormap JET
        heat_color = cv2.applyColorMap(heat, cv2.COLORMAP_JET)
        heat_color = cv2.cvtColor(heat_color, cv2.COLOR_BGR2RGBA)

        # Cria superfície Pygame
        heat_surf = pygame.image.frombuffer(heat_color.tobytes(), (self.largura, self.altura), 'RGBA')
        #heat_surf = pygame.transform.flip(heat_surf, False, True)
        heat_surf.set_alpha(self.heatmap_alpha)

        # Imagem BGR para salvar
        heat_bgr = cv2.cvtColor(heat_color[..., :3], cv2.COLOR_RGB2BGR)

        return heat_surf, heat_bgr


    def generate_rocket_heatmap(self, alpha=150, max_points=5000):
        """
        Gera heatmap das posições do foguete.
        """
        points = self.rocket_positions[-max_points:]

        heat = np.zeros((self.altura, self.largura), dtype=np.float32)
        for x, y in points:
            ix, iy = int(x), int(y)
            if 0 <= ix < self.largura and 0 <= iy < self.altura:
                heat[iy, ix] += 1

        heat = cv2.GaussianBlur(heat, (0, 0), sigmaX=50, sigmaY=50)
        heat = np.clip((heat / (heat.max() + 1e-5)) * 255, 0, 255).astype(np.uint8)

        heat_color = cv2.applyColorMap(heat, cv2.COLORMAP_HOT)
        heat_color = cv2.cvtColor(heat_color, cv2.COLOR_BGR2RGBA)

        heat_surf = pygame.image.frombuffer(heat_color.tobytes(), (self.largura, self.altura), 'RGBA')
        #heat_surf = pygame.transform.flip(heat_surf, False, True)
        heat_surf.set_alpha(alpha)

        heat_bgr = cv2.cvtColor(heat_color[..., :3], cv2.COLOR_RGB2BGR)
        return heat_surf, heat_bgr


    def show_end_screen(self, total_time, first_fixation, total_fixation_time, fixation_frequency, avg_fixation, taxa_desvio_medio,
                        taxa_acerto_asteroide=0, tempo_medio_reacao=0):

        # --- Carrega background e fontes ---
        bg_image = pygame.image.load("Assets/MainMenu/Background/bg_settings.png").convert_alpha()
        img_w, img_h = bg_image.get_size()
        scale_w = self.largura / img_w
        scale_h = self.altura / img_h
        scale_factor = max(scale_w, scale_h)
        new_w = int(img_w * scale_factor)
        new_h = int(img_h * scale_factor)
        bg_image = pygame.transform.smoothscale(bg_image, (new_w, new_h))
        bg_rect = bg_image.get_rect(center=(self.largura // 2, self.altura // 2))

        font_path = "Assets/Fonts/Fredoka-Regular.ttf"
        title_font = pygame.font.Font(font_path, 48)
        info_font = pygame.font.Font(font_path, 32)

        rodando = True
        while rodando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    rodando = False

            # --- Desenha background ---
            self.tela.blit(bg_image, bg_rect)

            # --- Overlay semitransparente ---
            overlay_width, overlay_height = self.largura - 100, self.altura - 100
            overlay = pygame.Surface((overlay_width, overlay_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            overlay_rect = overlay.get_rect(center=(self.largura // 2, self.altura // 2))
            self.tela.blit(overlay, overlay_rect)

            # --- Dados das métricas (label, valor, cor) ---
            metrics_data = [
                ("Tempo total", f"{total_time:.1f} s", (255, 255, 255)),
                ("Tempo até a primeira fixação", f"{first_fixation:.1f} s", (255, 255, 255)),
                ("Duração total de fixações", f"{total_fixation_time:.1f} s", (255, 255, 255)),
                ("Número de fixações", f"{fixation_frequency}", (255, 255, 255)),
                ("Taxa de Desvio Médio", f"{taxa_desvio_medio:.2f} px", (255, 255, 255)),
                ("Duração média de fixações", f"{avg_fixation:.1f} s", (255, 255, 255)),
                ("Taxa de Acerto/Fuga do Asteroide", f"{taxa_acerto_asteroide:.1f} %", (100, 255, 100)),  # verde destaque
                ("Asteroides olhados", f"{self.asteroid_look_events}", (255, 255, 255)),
                ("Tempo médio de reação ao Asteroide", f"{tempo_medio_reacao:.2f} s", (255, 255, 255)),
            ]

            # --- Desenha título centralizado ---
            title_text = "Fim do Minigame SESE!"
            title_surf = title_font.render(title_text, True, (255, 255, 100))
            title_shadow = title_font.render(title_text, True, (50, 50, 50))
            title_rect = title_surf.get_rect(center=(self.largura // 2, overlay_rect.top + 50))
            self.tela.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
            self.tela.blit(title_surf, title_rect)

            # --- Desenha métricas com label à esquerda e valor à direita ---
            y = title_rect.bottom + 40
            for label, value, color in metrics_data:
                # Label amarelo com sombra
                label_surf = info_font.render(f"{label}:", True, (255, 255, 100))
                label_shadow = info_font.render(f"{label}:", True, (50, 50, 50))
                label_rect = label_surf.get_rect(right=self.largura // 2 - 10, centery=y)
                self.tela.blit(label_shadow, (label_rect.x + 2, label_rect.y + 2))
                self.tela.blit(label_surf, label_rect)

                # Valor colorido com sombra
                value_surf = info_font.render(value, True, color)
                value_shadow = info_font.render(value, True, (50, 50, 50))
                value_rect = value_surf.get_rect(left=self.largura // 2 + 10, centery=y)
                self.tela.blit(value_shadow, (value_rect.x + 2, value_rect.y + 2))
                self.tela.blit(value_surf, value_rect)

                y += 60  # espaçamento maior entre linhas

            y += 20  # espaço extra antes dos heatmaps

            # --- Gerar e posicionar heatmaps ---
            heatmap_surf, heatmap_img = self.generate_heatmap()
            rocket_heatmap_surf, rocket_heatmap_img = self.generate_rocket_heatmap(alpha=120)
            map_width, map_height = 300, 200
            heatmap_surf_small = pygame.transform.smoothscale(heatmap_surf, (map_width, map_height))
            rocket_heatmap_surf_small = pygame.transform.smoothscale(rocket_heatmap_surf, (map_width, map_height))

            spacing = 20
            total_width = map_width * 2 + spacing
            x_start = (self.largura - total_width) // 2
            y_start = y + 20

            # Contorno branco ao redor dos heatmaps
            pygame.draw.rect(self.tela, (255, 255, 255), (x_start-5, y_start-5, total_width+10, map_height+10), 2)
            self.tela.blit(heatmap_surf_small, (x_start, y_start))
            self.tela.blit(rocket_heatmap_surf_small, (x_start + map_width + spacing, y_start))

            # --- Salvar heatmaps ---
            cv2.imwrite("heatmap_astronaut.png", heatmap_img)
            cv2.imwrite("heatmap_rocket.png", rocket_heatmap_img)

            pygame.display.flip()
            self.clock.tick(30)

    def push_rocket_back(self):
        """Move o foguete para trás (oposto ao planeta)."""

        dx = self.rocket.x - self.planet.x
        dy = self.rocket.y - self.planet.y
        dist = math.hypot(dx, dy)

        if dist > 0:
            strength = 5  # velocidade do recuo
            self.rocket.x += (dx / dist) * strength
            self.rocket.y += (dy / dist) * strength



    def run(self):
        # Inicializa variáveis
        self.rocket.grayscale = True
        self.star = None
        self.star_timer = random.randint(600, 1200)
        self.speed_boost_time = 0
        if self.start_time is None:
            self.start_time = time.time()
            
        # --- MÉTRICAS TÉCNICAS ---
        self.metricas = MetricasTecnicas("SESEGame")

        # Variáveis de asteroides
        self.asteroid_look_start_dict = {id(a): None for a in self.asteroids}
        self.asteroid_looked_dict = {id(a): False for a in self.asteroids}
        self.asteroid_reaction_times = []
        self.asteroid_punishments = 0
        self.asteroid_look_events = 0

        while self.rodando:
            frame_inicio = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.rodando = False

            # --- 1️⃣ CAPTURA DO GAZE ---
            inicio_captura = time.time()
            mx, my = self.player.get_input()  # pode ser gaze ou mouse
            gaze_valido = (mx is not None and my is not None)
            fim_captura = time.time()

            # --- 2️⃣ LÓGICA DO JOGO ---
            bg_frame = self.get_video_frame()
            self.tela.blit(bg_frame, (0, 0))

            watching = False
            if mx >= 0 and my >= 0:
                self.gaze_points.append((mx, my))
                dist_to_rocket = math.hypot(mx - self.rocket.x, my - self.rocket.y)
                watching = dist_to_rocket < self.rocket.raio

            # --- Fixações ---
            if watching and self.first_fixation_time is None:
                self.first_fixation_time = time.time() - self.start_time

            if watching and not self.last_watching:
                self.last_focus_start = time.time()
                self.focus_events += 1
            elif not watching and self.last_watching and self.last_focus_start is not None:
                duration = time.time() - self.last_focus_start
                self.focus_durations.append(duration)
                self.focus_time_total += duration
                self.last_focus_start = None
            self.last_watching = watching

            snap_objects = [self.rocket] + self.asteroids
            if self.star:
                snap_objects.append(self.star)

            self.player.draw_cursor(self.tela, mx, my, rocket=self.rocket)
            mx, my = self.player.apply_snapping(mx, my, snap_objects)

            # --- ASTEROIDES ---
            REQUIRED_LOOK_TIME = 0.2  # player must look at the asteroid for 1 second

            now = time.time()
            current_looking = None

            # --- Loop dos asteroides ---
            for ast in self.asteroids:
                ast.update(self.largura, self.altura)
                ast.draw(self.tela)
                dist = math.hypot(mx - ast.x, my - ast.y)

                self.check_collision(ast, self.rocket)
                # --- Check collisions between asteroids ---
                for i, ast1 in enumerate(self.asteroids):
                    for j, ast2 in enumerate(self.asteroids):
                        if i >= j:
                            continue  # avoid double-check and self-collision
                        self.check_collision(ast1, ast2)

                if not hasattr(ast, "look_start_time"):
                    ast.look_start_time = None
                if not hasattr(ast, "counted"):
                    ast.counted = False
                if not hasattr(ast, "last_counted_time"):
                    ast.last_counted_time = 0
                if not hasattr(ast, "appeared_time"):
                    ast.appeared_time = time.time()  # when asteroid was created

                if dist < ast.raio:

                    self.push_rocket_back()

                    current_looking = ast

                    # start the timer when player first looks
                    if ast.look_start_time is None:
                        ast.look_start_time = now

                    # check if the player has looked long enough
                    if not ast.counted and now - ast.look_start_time >= REQUIRED_LOOK_TIME:
                        reaction_time = now - ast.look_start_time
                        self.asteroid_reaction_times.append(reaction_time)
                        self.asteroid_look_events += 1
                        self.asteroid_punishments += 1
                        ast.counted = True
                        ast.last_counted_time = now

                else:
                    # reset the look timer if player looks away
                    ast.look_start_time = None


            # --- Após o loop: liberar asteroides que não estão sendo olhados atualmente ---
            for ast in self.asteroids:
                if ast.counted and current_looking != ast:
                    ast.counted = False



            # --- MOVIMENTO DO FOGUETE ---
            dist_to_rocket = math.hypot(mx - self.rocket.x, my - self.rocket.y)
            looking_at_any = any(math.hypot(mx - a.x, my - a.y) < a.raio for a in self.asteroids)


            if dist_to_rocket < self.rocket.raio and not looking_at_any:

             # Foguete deve ficar COLORIDO
                if self.rocket.grayscale:
                    self.rocket.grayscale = False
                dx = self.planet.x - self.rocket.x
                dy = self.planet.y - self.rocket.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    current_speed = self.rocket_speed
                    if self.speed_boost_time > 0:
                        current_speed *= 2
                        self.speed_boost_time -= 1
                    self.rocket.x += current_speed * dx / dist
                    self.rocket.y += current_speed * dy / dist
            else:
                # Foguete deve ficar GRAYSCALE
                if not self.rocket.grayscale:
                    self.rocket.grayscale = True
                    self.rocket.gray_img = None  # força regeneração da imagem cinza

            # --- ESTRELA (BOOST) ---
            self.star_timer -= 1
            if self.star_timer <= 0 and self.star is None:
                self.star = Star(self.largura, self.altura, self.star_img)
                self.star_timer = random.randint(600, 1200)
            if self.star:
                self.star.update(self.largura, self.altura)
                self.star.draw(self.tela)
                if mx >= 0 and my >= 0:
                    dist_to_star = math.hypot(mx - self.star.x, my - self.star.y)
                    if dist_to_star < self.star.raio:
                        self.speed_boost_time = 120
                        self.star = None
                if self.star and self.star.x - self.star.raio > self.largura:
                    self.star = None

            # --- RENDERIZAÇÃO DOS OBJETOS ---
            self.rocket.update(self.largura, self.altura)
            self.rocket.draw(self.tela)
            self.rocket_positions.append((self.rocket.x, self.rocket.y))
            self.planet.update(self.largura, self.altura)
            self.planet.draw(self.tela)
            self.asteroid_looked_dict[id(ast)] = False

            # --- MÉTRICAS DE FIXAÇÃO ---
            desvios = [
                math.hypot(gx - fx, gy - fy)
                for (gx, gy), (fx, fy) in zip(self.gaze_points, self.rocket_positions)
                if gx >= 0 and gy >= 0
            ]
            taxa_desvio_medio = sum(desvios) / len(desvios) if desvios else 0

            total_time = time.time() - self.start_time
            avg_fixation = sum(self.focus_durations) / len(self.focus_durations) if self.focus_durations else 0
            first_fixation = self.first_fixation_time if self.first_fixation_time else 0
            total_fixation_time = sum(self.focus_durations)
            fixation_frequency = self.focus_events
            # --- TEXTO INFERIOR ESQUERDO: ASTEROIDES OLHADOS ---
            font = pygame.font.SysFont(None, 28)  # ou usar sua fonte personalizada
            text = f"Asteroides olhados: {self.asteroid_look_events}"
            text_surf = font.render(text, True, (255, 255, 255))  # cor branca
            tela_x, tela_y = 10, self.altura - 30  # posição inferior esquerda
            self.tela.blit(text_surf, (tela_x, tela_y))


            # --- CONDIÇÃO DE VITÓRIA ---
            if math.hypot(self.rocket.x - self.planet.x, self.rocket.y - self.planet.y) < self.rocket.raio:
                if self.last_focus_start:
                    duration = time.time() - self.last_focus_start
                    self.focus_durations.append(duration)
                    self.focus_time_total += duration
                    self.last_focus_start = None

                taxa_acerto_asteroide = (
                    (self.asteroid_punishments / self.asteroid_look_events) * 100
                    if self.asteroid_look_events > 0 else 0
                )
                tempo_medio_reacao = (
                    sum(self.asteroid_reaction_times) / len(self.asteroid_reaction_times)
                    if self.asteroid_reaction_times else 0
                )

                self.show_end_screen(
                    total_time, first_fixation, total_fixation_time,
                    fixation_frequency, avg_fixation, taxa_desvio_medio,
                    taxa_acerto_asteroide, tempo_medio_reacao
                )

                print(f"Asteroides olhados: {self.asteroid_look_events}")
                print(f"Tempo médio de reação: {tempo_medio_reacao:.2f} s")
                print(f"Taxa de acerto/fuga do asteroide: {taxa_acerto_asteroide:.1f}%")
                self.rodando = False


            # --- 3️⃣ REGISTRO DE MÉTRICAS TÉCNICAS ---
            fim_frame = time.time()
            self.metricas.registrar_gaze(gaze_valido, inicio_captura, fim_frame)
            self.metricas.registrar_fps(self.clock.get_fps())


            pygame.display.flip()
            self.clock.tick(60)

        # --- SALVAR MÉTRICAS COMPLETAS ---
        dados_jogo = {
            "tempo_total_s": round(total_time, 2),
            "tempo_primeira_fixacao_s": round(first_fixation, 2),
            "tempo_total_fixacao_s": round(total_fixation_time, 2),
            "frequencia_fixacoes": fixation_frequency,
            "duracao_media_fixacao_s": round(avg_fixation, 2),
            "taxa_desvio_px": round(taxa_desvio_medio, 2),
            "asteroides_olhados": self.asteroid_look_events,
            "taxa_acerto_asteroide_%": round(taxa_acerto_asteroide, 1),
            "tempo_medio_reacao_s": round(tempo_medio_reacao, 2)
        }
        self.metricas.salvar_csv(dados_jogo, "metricas_sese.csv")

        print(f"Fim do jogo SESE! Dados salvos.")
