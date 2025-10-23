import pygame
import random
from PIL import Image, ImageFilter, ImageDraw
import os
import glob
import math

class FOACGame:
    def __init__(self, tela, largura=1280, altura=720, clock=None, gaze=None, nivel="facil"):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        self.clock = clock or pygame.time.Clock()
        self.gaze = gaze
        self.nivel_atual = nivel

        # --- game state ---
        self.acertos = 0
        self.objetivo = 3  # number of toys to find
        self.mensagem = ""
        self.fonte = pygame.font.SysFont(None, 48)
        self.snap_dist = 200
        self.snap_radius = 200  # distance in pixels for snapping range

        self.DWELL_TIME = 2.5
        self.JUMP_DURATION = 1.2

        # --- gaze tracking memory ---
        self.gaze_start_times = [None] * 7
        self.jumping_objects = [False] * 7
        self.jump_start_times = [None] * 7

        # --- logos ---
        self.logo_default = self.load_logo("Assets/MainMenu/Logo/logo_waiting.png")
        self.logo_correct = self.load_logo("Assets/MainMenu/Logo/logo_correct.png")
        self.logo_wrong = self.load_logo("Assets/MainMenu/Logo/logo_wrong.png")
        self.logo_img = self.logo_default
        self.logo_change_time = 0
        self.logo_duration = 0.6

        # --- background ---
        bg_options = [
            "Assets/FOAC_Minigame/Background/background_day.png",
            "Assets/FOAC_Minigame/Background/background_night.png"
        ]
        self.fundo = pygame.image.load(random.choice(bg_options)).convert()
        self.fundo = pygame.transform.scale(self.fundo, (self.largura, self.altura))

        # --- load toys ---
        self.carregar_objetos_pasta("Assets/FOAC_Minigame/Objects")

        # --- config difficulty ---
        # self.config = {
        #     "facil": {"objetos": self.objetos_facil, "blur": 6, "dist": 200},
        #     "medio": {"objetos": self.objetos_medio, "blur": 4, "dist": 150},
        #     "dificil": {"objetos": self.objetos_dificil, "blur": 2, "dist": 120}
        # }

        # --- main position + box area ---
        self.pos_principal = (self.largura // 2, int(self.altura * 0.8))
        self.box_pos = (int(self.largura * 0.9), int(self.altura * 0.85))
        self.box_img = self.load_box_image()

        # --- lists for objects and animations ---
        self.opcoes = []
        self.posicoes = []
        self.animacoes = []  # flying objects
        self.coletados = []  # collected toys

        self.resetar_jogo()

    # -------------------- ASSETS --------------------
    def load_logo(self, path):
        if os.path.exists(path):
            logo = pygame.image.load(path).convert_alpha()
            size = int(120 * 0.95)
            return pygame.transform.smoothscale(logo, (size, size))
        return None

    def load_box_image(self):
        box_path = "Assets/FOAC_Minigame/box.png"
        if os.path.exists(box_path):
            box = pygame.image.load(box_path).convert_alpha()
            return pygame.transform.scale(box, (180, 180))
        else:
            # fallback: simple rectangle
            surf = pygame.Surface((180, 180), pygame.SRCALPHA)
            pygame.draw.rect(surf, (80, 50, 0, 180), (0, 0, 180, 180), border_radius=25)
            return surf

    def criar_sombra(self, radius, blur_strength=8, color=(0, 0, 0, 150)):
        size = radius * 4
        pil_surf = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(pil_surf)
        draw.ellipse(
            (size//2 - radius, size//2 - radius, size//2 + radius, size//2 + radius),
            fill=color
        )
        pil_surf = pil_surf.filter(ImageFilter.GaussianBlur(blur_strength))
        return pygame.image.fromstring(pil_surf.tobytes(), pil_surf.size, pil_surf.mode)

    def carregar_objetos_pasta(self, base_path):
        pastas = [f.path for f in os.scandir(base_path) if f.is_dir()]
        if not pastas:
            raise ValueError(f"Nenhuma pasta encontrada em {base_path}")

        pasta_escolhida = random.choice(pastas)
        imagens = glob.glob(os.path.join(pasta_escolhida, "*.png"))
        if len(imagens) < 7:
            raise ValueError(f"A pasta {pasta_escolhida} deve ter pelo menos 7 imagens")

        self.all_images = imagens  # keep all images for variety


    def carregar_img(self, path, size, blur_radius=0):
        pil_img = Image.open(path).convert("RGBA")
        target_w, target_h = size
        if blur_radius > 0:
            pil_up = pil_img.resize((target_w * 3, target_h * 3), Image.LANCZOS)
            pil_up = pil_up.filter(ImageFilter.GaussianBlur(blur_radius))
            pil_final = pil_up.resize((target_w, target_h), Image.LANCZOS)
        else:
            pil_final = pil_img.resize((target_w, target_h), Image.LANCZOS)
        return pygame.image.fromstring(pil_final.tobytes(), pil_final.size, pil_final.mode)

    # -------------------- RESET --------------------
    def resetar_jogo(self):
        # --- pick objects for this round ---
        random.shuffle(self.all_images)
        objs = self.all_images[:7]
        blur_radius = 4      # default blur
        dist_min = 150       # default spacing

        self.objeto_principal_path = random.choice(objs)
        self.objeto_principal = self.carregar_img(self.objeto_principal_path, (200, 200), 0)

        # --- first, generate positions and depths ---
        self.posicoes = []
        y_min = int(self.altura * 0.55)
        y_max = int(self.altura * 0.85)
        for _ in range(len(objs)):
            while True:
                x = random.randint(100, self.largura - 200)
                y = random.randint(y_min, y_max)
                if all(((x - px)**2 + (y - py)**2)**0.5 > dist_min for (px, py, _) in self.posicoes):
                    depth = 1 - ((y - y_min) / (y_max - y_min))  # 0 = bottom, 1 = top
                    self.posicoes.append((x, y, depth))
                    break

        # --- now create images, using depth info ---
        self.opcoes = []
        for i, path in enumerate(objs):
            _, _, depth = self.posicoes[i]
            extra_blur = int(blur_radius * (1 + depth * 0.6))
            img_blur = self.carregar_img(path, (100, 100), extra_blur)
            img_nitida = self.carregar_img(path, (120, 120), 0)
            self.opcoes.append({
                "path": path,
                "blur": img_blur,
                "nitida": img_nitida,
                "hover": False,
                "scale": 100,
                "target": 100,
                "active": True
            })

        # reset states
        self.gaze_start_times = [None] * len(objs)
        self.jumping_objects = [False] * len(objs)
        self.jump_start_times = [None] * len(objs)
        self.animacoes.clear()
        self.coletados.clear()


    # -------------------- DRAW HELPERS --------------------
    def criar_barra_info(self, largura=600, altura=120, y=20, corner_radius=40):
        surf = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.rect(
            surf, (0, 0, 0, 120),
            (0, 0, largura, altura),
            border_top_right_radius=corner_radius,
            border_bottom_right_radius=corner_radius
        )
        return surf, (0, y)

    def desenhar_logo(self, logo_img, bar_y, bar_height, x_offset=10):
        if logo_img:
            y = bar_y + (bar_height - logo_img.get_height()) // 2
            self.tela.blit(logo_img, (x_offset, y))
            return x_offset + logo_img.get_width() + 30
        return x_offset

    # -------------------- MAIN UPDATE --------------------
    def atualizar(self):
        current_time = pygame.time.get_ticks() / 1000
        self.tela.blit(self.fundo, (0, 0))

        # gaze or mouse
        mx, my, blink = self.get_cursor()


        # --- draw all options ---
        for i, opc in enumerate(self.opcoes):
            if not opc["active"]:
                continue

            base_x, base_y, depth = self.posicoes[i]
            rect_center = (base_x + 30, base_y + 30)
            rect = pygame.Rect(0, 0, opc["scale"], opc["scale"])
            rect.center = rect_center

            # dwell detection
            if rect.collidepoint(mx, my):
                if self.gaze_start_times[i] is None:
                    self.gaze_start_times[i] = current_time
            else:
                self.gaze_start_times[i] = None
                self.jumping_objects[i] = False

            # blink detection
            if rect.collidepoint(mx, my) and blink and not self.jumping_objects[i]:
                self.handle_selection(i)
                self.jumping_objects[i] = True
                self.jump_start_times[i] = current_time


            # jump animation
            jump_offset = 0
            if self.jumping_objects[i]:
                elapsed = current_time - self.jump_start_times[i]
                jump_offset = math.sin(elapsed * math.pi) * 25
                if elapsed >= self.JUMP_DURATION:
                    self.jumping_objects[i] = False
                    self.handle_selection(i)

            # scale + hover
            opc["hover"] = rect.collidepoint(mx, my)
            opc["target"] = 120 if opc["hover"] else 100
            opc["scale"] += (opc["target"] - opc["scale"]) * 0.2
            # Apply depth-based scaling: higher (depth=1) → smaller
            scale_factor = 0.9 + (1 - depth) * 0.1  # range ~0.9–1.0
            opc["scale"] *= scale_factor


            img = opc["nitida"] if opc["hover"] else opc["blur"]
            img_scaled = pygame.transform.smoothscale(img, (int(opc["scale"]), int(opc["scale"])))
            img_rect = img_scaled.get_rect(center=(base_x + 30, base_y + 30 - jump_offset))

            # shadow
            shadow_surf = self.criar_sombra(int(opc["scale"] * 0.3), 8)
            shadow_rect = shadow_surf.get_rect(center=(img_rect.centerx, img_rect.centery + 10))
            self.tela.blit(shadow_surf, shadow_rect.topleft)
            self.tela.blit(img_scaled, img_rect.topleft)

        # --- animate flying toys ---
        completed = []
        for anim in self.animacoes:
            anim["progress"] += 0.03
            if anim["progress"] >= 1.0:
                completed.append(anim)
                self.coletados.append(anim["path"])
            else:
                t = anim["progress"]
                x = anim["start"][0] + (anim["end"][0] - anim["start"][0]) * t
                y = anim["start"][1] + (anim["end"][1] - anim["start"][1]) * t - 80 * math.sin(t * math.pi)
                scale = int(100 * (1 - t * 0.5))
                toy_img = pygame.transform.smoothscale(anim["img"], (scale, scale))
                rect = toy_img.get_rect(center=(x, y))
                self.tela.blit(toy_img, rect.topleft)
        for anim in completed:
            self.animacoes.remove(anim)

        # --- check completion ---
        if len(self.coletados) >= self.objetivo:
            self.acertos += 1
            pygame.time.delay(800)
            self.resetar_jogo()
            return

        # --- draw main + box + info ---
        self.tela.blit(self.objeto_principal, self.pos_principal)
        self.tela.blit(self.box_img, self.box_img.get_rect(center=self.box_pos))

        # info bar
        bar_surf, bar_pos = self.criar_barra_info()
        self.tela.blit(bar_surf, bar_pos)
        start_x = self.desenhar_logo(self.logo_img, bar_pos[1], bar_surf.get_height())
        texto = f"Acertos: {self.acertos}  Brinquedos: {len(self.coletados)}/{self.objetivo}"
        txt_surf = self.fonte.render(texto, True, (255, 255, 255))
        self.tela.blit(txt_surf, (start_x, bar_pos[1] + bar_surf.get_height() // 3))

        # draw gaze
        if mx > 0 and my > 0:
            pygame.draw.circle(self.tela, (255, 0, 0), (int(mx), int(my)), 10)
            pygame.draw.circle(self.tela, (0, 0, 0), (int(mx), int(my)), 12, 2)



    def atualizar_objeto_principal(self):
        # choose a new target among remaining active options
        remaining_options = [opc["path"] for opc in self.opcoes if opc["active"]]
        if remaining_options:
            self.objeto_principal_path = random.choice(remaining_options)
            self.objeto_principal = self.carregar_img(self.objeto_principal_path, (200, 200), 0)


    # -------------------- EVENT HANDLING --------------------
    def handle_selection(self, i):
        opc = self.opcoes[i]
        if opc["path"] == self.objeto_principal_path:
            self.logo_img = self.logo_correct
            start_pos = (self.posicoes[i][0] + 30, self.posicoes[i][1] + 30)
            self.animacoes.append({
                "path": opc["path"],
                "img": opc["nitida"],
                "start": start_pos,
                "end": self.box_pos,
                "progress": 0.0
            })
            opc["active"] = False

            # --- update main target to a new active option ---
            self.atualizar_objeto_principal()
            
        else:
            self.logo_img = self.logo_wrong

        self.logo_change_time = pygame.time.get_ticks() / 1000



    def snap_to_target(self, mx, my, target_x, target_y):
        if mx < 0 or my < 0:
            return mx, my
        distance = math.hypot(mx - target_x, my - target_y)
        if distance <= self.snap_radius:
            # You can either fully snap or interpolate smoothly:
            snap_strength = 0.7  # 1.0 = instant, 0.5 = gentle pull
            new_x = mx + (target_x - mx) * snap_strength
            new_y = my + (target_y - my) * snap_strength
            return new_x, new_y
        return mx, my

    def get_cursor(self):
        if self.gaze:
            mx, my, blink = self.gaze.get_gaze_blink()
            if mx is None or my is None:
                return -1, -1, False
        else:
            mx, my = pygame.mouse.get_pos()
            blink = False

        # SNAP mechanic (unchanged)
        closest_target = None
        closest_dist = float("inf")
        for i, opc in enumerate(self.opcoes):
            if not opc["active"]:
                continue
            tx, ty, _ = self.posicoes[i]
            dist = math.hypot(mx - tx, my - ty)
            if dist < closest_dist:
                closest_dist = dist
                closest_target = (tx, ty)

        if closest_target:
            mx, my = self.snap_to_target(mx, my, closest_target[0], closest_target[1])

        return mx, my, blink


    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                return False
        return True

    # -------------------- MAIN LOOP --------------------
    def run(self):
        rodando = True
        while rodando:
            rodando = self.processar_eventos()
            self.atualizar()
            pygame.display.flip()
            self.clock.tick(60)
