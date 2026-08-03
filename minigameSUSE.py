import pygame
import random
import time
from PIL import Image, ImageOps
import cv2
import math
import numpy as np
import csv
import os
from metricas_tecnicas import MetricasTecnicas

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
            self.vel_x = (1 - turn_rate) * self.vel_x + turn_rate * target_vx
            self.vel_y = (1 - turn_rate) * self.vel_y + turn_rate * target_vy
        self.x += self.vel_x
        self.y += self.vel_y

    def draw(self, tela):
        tela.blit(self.img, (self.x - self.raio, self.y - self.raio))

    def set_highlight(self, active: bool):
        self.img = self.img_colorida if active else self.img_gray

    def move_random(self):
        angle_change = random.uniform(-0.2, 0.2)
        speed = math.hypot(self.vel_x, self.vel_y)
        current_angle = math.atan2(self.vel_y, self.vel_x) + angle_change
        self.vel_x = math.cos(current_angle) * speed
        self.vel_y = math.sin(current_angle) * speed
        self.x += self.vel_x
        self.y += self.vel_y
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
        self.start_time = None
        self.focus_time = 0
        self.first_fixation_time = None    
        self.last_focus_start = None   
        self.focus_durations = []           
        self.focus_time_total = 0         
        self.focus_events = 0                
        self.gaze_positions = []  # lista de tuplas (x, y)
        self.heatmap_alpha = 100  # opacidade do heatmap
        self.fish_positions = []  # lista de tuplas (x, y) do peixe

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
        min_distance = 150
        attempts = 0
        for _ in range(num_foods):
            while True:
                fx = random.randint(100, largura - 100)
                fy = random.randint(100, altura - 100)
                too_close = any(math.hypot(fx - f.x, fy - f.y) < min_distance for f in self.foods)
                if not too_close or attempts > 100:
                    self.foods.append(Food(fx, fy))
                    break
                attempts += 1

    def is_gaze_on_fish(self, gaze_x, gaze_y):
        if gaze_x < 0 or gaze_y < 0:
            return False
        dist = math.hypot(gaze_x - self.target.x, gaze_y - self.target.y)
        return dist < self.HIT_RADIUS

    # -------------------- Info bar --------------------
    def criar_barra_info(self, largura=600, altura=120, y=20, corner_radius=40):
        bar_surface = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.rect(bar_surface, (0, 0, 0, 120),
                         (0, 0, largura, altura),
                         border_top_right_radius=corner_radius,
                         border_bottom_right_radius=corner_radius)
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

    # -------------------- Tela Final --------------------
    def show_end_screen(self, total_time, first_fixation, total_fixation_time, fixation_frequency, avg_fixation, taxa_desvio_medio):

        # --- Background ---
        bg_image = pygame.image.load("Assets/MainMenu/Background/bg_settings.png").convert_alpha()
        img_w, img_h = bg_image.get_size()
        scale_factor = max(self.largura / img_w, self.altura / img_h)
        bg_image = pygame.transform.smoothscale(bg_image, (int(img_w * scale_factor), int(img_h * scale_factor)))
        bg_rect = bg_image.get_rect(center=(self.largura // 2, self.altura // 2))

        font_path = "Assets/Fonts/Fredoka-Regular.ttf"
        title_font = pygame.font.Font(font_path, 60)
        info_font = pygame.font.Font(font_path, 36)

        rodando = True
        while rodando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

            # --- Desenha background ---
            self.tela.blit(bg_image, bg_rect)

            # --- Overlay semitransparente ---
            overlay = pygame.Surface((self.largura - 100, self.altura - 100), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            overlay_rect = overlay.get_rect(center=(self.largura // 2, self.altura // 2))
            self.tela.blit(overlay, overlay_rect)

            # --- Título com sombra ---
            title_text = "🎉 Bom trabalho!"
            title_surf = title_font.render(title_text, True, (255, 255, 0))
            shadow_surf = title_font.render(title_text, True, (50, 50, 50))
            title_rect = title_surf.get_rect(center=(self.largura // 2, overlay_rect.top + 60))
            self.tela.blit(shadow_surf, (title_rect.x + 2, title_rect.y + 2))
            self.tela.blit(title_surf, title_rect)

            # --- Métricas como (label, valor, cor) ---
            metrics = [
                ("Tempo total", f"{total_time:.1f} s", (255, 255, 255)),
                ("Tempo até 1ª fixação", f"{first_fixation:.1f} s", (255, 255, 255)),
                ("Tempo focado (total)", f"{total_fixation_time:.1f} s", (255, 255, 255)),
                ("Frequência de fixações", f"{fixation_frequency}", (255, 255, 255)),
                ("Duração média das fixações", f"{avg_fixation:.2f} s", (255, 255, 255)),
                ("Taxa de Desvio Médio", f"{taxa_desvio_medio:.2f} px", (255, 255, 255)),
                ("Comidas coletadas", f"{self.pontuacao}/{self.num_foods}", (255, 255, 255)),
            ]

            # --- Desenha métricas alinhadas label à esquerda e valor à direita ---
            y = title_rect.bottom + 40
            for label, value, color in metrics:
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

            # --- Heatmaps ---
            heatmap_surf, heatmap_img = self.generate_heatmap()
            fish_heatmap_surf, fish_heatmap_img = self.generate_fish_heatmap(alpha=120)

            map_width, map_height = 300, 200
            heatmap_surf_small = pygame.transform.smoothscale(heatmap_surf, (map_width, map_height))
            fish_heatmap_surf_small = pygame.transform.smoothscale(fish_heatmap_surf, (map_width, map_height))

            spacing = 20
            total_width = map_width * 2 + spacing
            x_start = (self.largura - total_width) // 2
            y_start = y + 20

            # Desenha borda branca em volta dos heatmaps
            pygame.draw.rect(self.tela, (255, 255, 255), (x_start-5, y_start-5, total_width+10, map_height+10), 2)
            self.tela.blit(heatmap_surf_small, (x_start, y_start))
            self.tela.blit(fish_heatmap_surf_small, (x_start + map_width + spacing, y_start))

            # --- Salvar arquivos ---
            cv2.imwrite("heatmap_gaze.png", heatmap_img)
            cv2.imwrite("heatmap_fish.png", fish_heatmap_img)

            pygame.display.flip()
            self.clock.tick(30)



    def generate_fish_heatmap(self, alpha=150):
        heat = np.zeros((self.altura, self.largura), dtype=np.float32)
        for x, y in self.fish_positions:
            if 0 <= x < self.largura and 0 <= y < self.altura:
                heat[y, x] += 1

        heat = cv2.GaussianBlur(heat, (0, 0), sigmaX=50, sigmaY=50)
        heat = np.clip((heat / heat.max()) * 255, 0, 255).astype(np.uint8)

        # Colormap diferente, por exemplo COLORMAP_HOT
        heat_color = cv2.applyColorMap(heat, cv2.COLORMAP_HOT)
        heat_color = cv2.cvtColor(heat_color, cv2.COLOR_BGR2RGBA)
        heat_color = np.ascontiguousarray(heat_color.swapaxes(0, 1))
        heat_surf = pygame.image.frombuffer(heat_color.tobytes(), heat_color.shape[:2][::-1], 'RGBA')
        heat_surf.set_alpha(alpha)

        # também retorna a imagem para salvar
        heat_bgr = cv2.cvtColor(heat_color.swapaxes(0, 1)[..., :3], cv2.COLOR_RGB2BGR)

        return heat_surf, heat_bgr


    def generate_heatmap(self):
        # cria matriz de calor
        heat = np.zeros((self.altura, self.largura), dtype=np.float32)

        for x, y in self.gaze_positions:
            if 0 <= x < self.largura and 0 <= y < self.altura:
                heat[y, x] += 1

        heat = cv2.GaussianBlur(heat, (0, 0), sigmaX=50, sigmaY=50)
        heat = np.clip((heat / heat.max()) * 255, 0, 255).astype(np.uint8)

        # Colormap JET
        heat_color = cv2.applyColorMap(heat, cv2.COLORMAP_JET)
        heat_color = cv2.cvtColor(heat_color, cv2.COLOR_BGR2RGBA)
        heat_color = np.ascontiguousarray(heat_color.swapaxes(0, 1))
        heat_surf = pygame.image.frombuffer(heat_color.tobytes(), heat_color.shape[:2][::-1], 'RGBA')
        heat_surf.set_alpha(self.heatmap_alpha)

        # Se quisermos salvar, converte novamente para BGR
        heat_bgr = cv2.cvtColor(heat_color.swapaxes(0,1)[..., :3], cv2.COLOR_RGB2BGR)

        return heat_surf, heat_bgr


    # -------------------- Run --------------------
    def run(self):
        rodando = True
        self.start_time = time.time()

        self.metricas = MetricasTecnicas("SUSEGame")

        while rodando:
            frame_inicio = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    rodando = False

            # ----------------------------
            # 1️⃣ CAPTURA DO GAZE / MOUSE
            # ----------------------------
            inicio_captura = time.time()

            if self.gaze:
                mx, my = self.gaze.get_gaze()
                gaze_valido = (mx is not None and my is not None)
                if not gaze_valido:
                    mx, my = -1, -1
            else:
                mx, my = pygame.mouse.get_pos()
                gaze_valido = True  # mouse sempre válido (modo de teste)

            fim_captura = time.time()

            # ----------------------------
            # 2️⃣ LÓGICA DO JOGO
            # ----------------------------
            bg_frame = self.get_video_frame()
            self.tela.blit(bg_frame, (0, 0))

            self.gaze_positions.append((int(mx), int(my)))
            self.fish_positions.append((int(self.target.x), int(self.target.y)))

            # --- Calcular taxa de desvio médio frame a frame ---
            desvios = []
            for (gx, gy), (fx, fy) in zip(self.gaze_positions, self.fish_positions):
                if gx >= 0 and gy >= 0:
                    d = math.hypot(gx - fx, gy - fy)
                    desvios.append(d)
            taxa_desvio_medio = sum(desvios) / len(desvios) if desvios else 0

            # --- Snap / cursor ---
            mx, my = self.player.snap_to_target(mx, my, self.target.x, self.target.y)
            if mx >= 0 and my >= 0:
                pygame.draw.circle(self.tela, (255, 0, 0), (int(mx), int(my)), 10)
                pygame.draw.circle(self.tela, (0, 0, 0), (int(mx), int(my)), 12, 2)

            # --- Checagem de fixação ---
            watching = False
            if mx >= 0 and my >= 0:
                dist_to_fish = math.hypot(mx - self.target.x, my - self.target.y)
                watching = dist_to_fish < self.HIT_RADIUS
                self.target.set_highlight(watching)

            # --- Primeira fixação ---
            if watching and self.first_fixation_time is None:
                self.first_fixation_time = time.time() - self.start_time

            # --- Controle de fixações ---
            if watching and not self.last_watching:
                self.last_focus_start = time.time()
                self.focus_events += 1
            elif not watching and self.last_watching and self.last_focus_start:
                duration = time.time() - self.last_focus_start
                self.focus_durations.append(duration)
                self.focus_time_total += duration
                self.last_focus_start = None

            self.last_watching = watching

            # --- Movimento do peixe e comidas ---
            target_food = None
            min_dist = float("inf")
            for food in self.foods:
                if not food.collected:
                    d = math.hypot(self.target.x - food.x, self.target.y - food.y)
                    if d < min_dist:
                        min_dist = d
                        target_food = food

            if watching and target_food:
                self.target.move_toward(target_food.x, target_food.y)
            else:
                self.target.move_random()

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

            # --- Desenho dos elementos ---
            for food in self.foods:
                food.draw(self.tela)

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

            self.target.draw(self.tela)

            # --- Barra de info ---
            bar_surface, bar_pos = self.criar_barra_info(largura=300, altura=50, y=10)
            self.tela.blit(bar_surface, bar_pos)
            self.desenhar_barra_info_com_logo(
                f"Pontos: {self.pontuacao}/{self.num_foods}", bar_surface, bar_pos, 50
            )

            if all(food.collected for food in self.foods):
                rodando = False

            pygame.display.flip()

            # ----------------------------
            # 3️⃣ REGISTRO DE MÉTRICAS
            # ----------------------------
            render_time = time.time()
            self.metricas.registrar_gaze(gaze_valido, inicio_captura, render_time)
            self.metricas.registrar_fps(self.clock.get_fps())

            self.clock.tick(60)

        # --- Estatísticas finais ---
        total_time = time.time() - self.start_time
        avg_fixation = sum(self.focus_durations) / len(self.focus_durations) if self.focus_durations else 0
        first_fixation = self.first_fixation_time if self.first_fixation_time else 0
        total_fixation_time = sum(self.focus_durations)  # ou self.focus_time_total
        fixation_frequency = self.focus_events


        if self.last_focus_start:
            duration = time.time() - self.last_focus_start
            self.focus_durations.append(duration)
            self.focus_time_total += duration
            self.last_focus_start = None

        # --- Tela final ---
        self.show_end_screen(
            total_time, first_fixation, total_fixation_time, fixation_frequency, avg_fixation, taxa_desvio_medio
        )
        
        # Salvar métricas completas (técnicas + do jogo)
        dados_jogo = {
            "tempo_total_s": round(total_time, 2),
            "tempo_primeira_fixacao_s": round(first_fixation, 2),
            "tempo_total_fixacao_s": round(total_fixation_time, 2),
            "frequencia_fixacoes": fixation_frequency,
            "duracao_media_fixacao_s": round(avg_fixation, 2),
            "taxa_desvio_px": round(taxa_desvio_medio, 2),
            "comidas_coletadas": self.pontuacao,
            "total_comidas": self.num_foods
        }
        self.metricas.salvar_csv(dados_jogo, "metricas_suse.csv")

        if self.gaze:
            self.gaze.release()
        print(f"Fim do jogo! Pontos: {self.pontuacao}/{self.num_foods}")
