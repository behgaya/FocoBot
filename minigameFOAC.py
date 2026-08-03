import pygame
import random
from PIL import Image, ImageFilter, ImageDraw
from metricas_tecnicas import MetricasTecnicas
import os
import glob
import math
import time



class FOACGame:
    def __init__(self, tela, largura=1280, altura=720, clock=None, gaze=None, snap_radius=250, objetivos=3):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        self.clock = clock or pygame.time.Clock()
        self.gaze = gaze
        self.gaze_points = []  # store all gaze points
        self.heatmap_alpha = 100
        self.blinks_totais = 0
        self.blinks_corretos = 0
        self.tempo_ultima_fixacao_para_blink = [None] * 7  # para medir tempo de fixação até a piscada
        self.metricas = MetricasTecnicas("FOACGame")


        # --- game state ---
        self.acertos = 0
        self.objetivo = objetivos  # number of toys to find
        self.fonte = pygame.font.SysFont(None, 48)
        self.snap_radius = snap_radius  # distance in pixels for snapping range

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


        # -------------------- MÉTRICAS --------------------
        self.tempo_inicio = None
        self.tempo_fim = None

        # Para cada objeto: armazenar tempos de fixação
        self.fixacoes = {i: [] for i in range(7)}  # [(inicio, fim), ...]
        self.tempo_primeira_fixacao = {i: None for i in range(7)}
        self.num_fixacoes = {i: 0 for i in range(7)}
        self.duracao_total_fixacao = {i: 0.0 for i in range(7)}

        # --- load toys ---
        self.carregar_objetos_pasta("Assets/FOAC_Minigame/Objects")

        # --- main position + box area ---
        self.pos_principal = (self.largura // 2, int(self.altura * 0.1))
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
        box_path = "Assets/FOAC_Minigame/Objects/caixa.png"
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
        margin = 50
        y_max = self.box_pos[1] - self.box_img.get_height() // 2 - margin
        y_min = int(self.altura * 0.55)

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
            max_blur = 12
            extra_blur = int(depth * max_blur)
            img_blur = self.carregar_img(path, (120, 120), extra_blur)
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


    def show_end_screen(self, total_time, first_fixation, total_fixation_time,
                        fixation_frequency, avg_fixation):

        # --- Calcula média de fixações antes do blink ---
        tempos_fixacao_para_blink = [t for t in self.tempo_ultima_fixacao_para_blink if t is not None]
        avg_fixacao_blink = sum(tempos_fixacao_para_blink) / len(tempos_fixacao_para_blink) if tempos_fixacao_para_blink else 0

        # --- Carrega background e fontes ---
        bg_image = pygame.image.load("Assets/MainMenu/Background/bg_settings.png").convert_alpha()
        img_w, img_h = bg_image.get_size()
        scale_w = self.largura / img_w
        scale_h = self.altura / img_h
        scale_factor = max(scale_w, scale_h)
        new_w, new_h = int(img_w * scale_factor), int(img_h * scale_factor)
        bg_image = pygame.transform.smoothscale(bg_image, (new_w, new_h))
        bg_rect = bg_image.get_rect(center=(self.largura // 2, self.altura // 2))

        font_path = "Assets/Fonts/Fredoka-Regular.ttf"
        title_font = pygame.font.Font(font_path, 48)
        info_font = pygame.font.Font(font_path, 32)
        footer_font = pygame.font.Font(font_path, 28)

        # --- Dados das métricas (label, valor, cor) ---
        metrics_data = [
            ("Tempo total", f"{total_time:.1f} s", (255, 255, 255)),  # branco
            ("Tempo até a primeira fixação", f"{first_fixation:.1f} s", (255, 255, 255)),
            None,  # separador visual
            ("Número de fixações", f"{fixation_frequency}", (255, 255, 255)),
            ("Duração média de fixações", f"{avg_fixation:.1f} s", (255, 255, 255)),
            None,  # separador visual
            ("Taxa de acerto da piscada", 
            f"{self.blinks_corretos}/{self.blinks_totais} ({(self.blinks_corretos/self.blinks_totais*100 if self.blinks_totais>0 else 0):.1f}%)",
            (100, 255, 100)),  # verde
            ("Tempo médio de fixação antes da piscada", f"{avg_fixacao_blink:.2f} s", (255, 255, 255)),
        ]

        rodando = True
        while rodando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "menu"

            # --- Desenha background ---
            self.tela.blit(bg_image, bg_rect)

            # --- Overlay semitransparente atrás do texto ---
            overlay_width, overlay_height = self.largura - 100, self.altura - 100
            overlay = pygame.Surface((overlay_width, overlay_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            overlay_rect = overlay.get_rect(center=(self.largura // 2, self.altura // 2))
            self.tela.blit(overlay, overlay_rect)

            # --- Título com sombra ---
            title_text = "Fim do Minigame FOAC!"
            title_surf = title_font.render(title_text, True, (255, 255, 100))
            shadow_surf = title_font.render(title_text, True, (50, 50, 50))
            title_rect = title_surf.get_rect(center=(self.largura // 2, overlay_rect.top + 50))
            self.tela.blit(shadow_surf, (title_rect.x + 2, title_rect.y + 2))
            self.tela.blit(title_surf, title_rect)

            # --- Métricas ---
            y = title_rect.bottom + 30
            for item in metrics_data:
                if item is None:
                    # Linha separadora
                    pygame.draw.line(self.tela, (255, 255, 255, 100), (50, y), (self.largura - 50, y), 1)
                    y += 80  # espaço depois da linha
                    continue

                label, value, color = item

                # Label (amarelo com sombra)
                label_surf = info_font.render(f"{label}:", True, (255, 255, 100))
                label_shadow = info_font.render(f"{label}:", True, (50, 50, 50))
                label_rect = label_surf.get_rect(right=self.largura // 2 - 10, centery=y)
                self.tela.blit(label_shadow, (label_rect.x + 2, label_rect.y + 2))
                self.tela.blit(label_surf, label_rect)

                # Valor (cor destaque com sombra)
                value_surf = info_font.render(value, True, color)
                value_shadow = info_font.render(value, True, (50, 50, 50))
                value_rect = value_surf.get_rect(left=self.largura // 2 + 10, centery=y)
                self.tela.blit(value_shadow, (value_rect.x + 2, value_rect.y + 2))
                self.tela.blit(value_surf, value_rect)

                y += 80

            # --- Footer ---
            footer_text = "Pressione ESC para sair"
            footer_surf = footer_font.render(footer_text, True, (180, 180, 180))
            footer_rect = footer_surf.get_rect(center=(self.largura // 2, self.altura - 60))
            self.tela.blit(footer_surf, footer_rect)

            pygame.display.flip()
            self.clock.tick(30)




    # -------------------- MAIN UPDATE --------------------
    def atualizar(self):
        current_time = time.time() 
        self.tela.blit(self.fundo, (0, 0))

        #inicio_captura = time.time() / 1000

        # pega posição do cursor ou gaze
        mx, my, blink = self.get_cursor()
        gaze_valido = (mx is not None and my is not None)

        # --- draw all options ---
        for i, opc in enumerate(self.opcoes):
            if not opc["active"]:
                continue

            base_x, base_y, depth = self.posicoes[i]
            rect_center = (base_x + 30, base_y + 30)

            # --- hover considerando snap ---
            distance = math.hypot(mx - rect_center[0], my - rect_center[1])
            hover = distance < opc["scale"] / 2
            opc["hover"] = hover
            opc["target"] = 120 if hover else 100
            opc["scale"] += (opc["target"] - opc["scale"]) * 0.2

            # --- scale with depth + hover ---
            scale_factor = 0.7 + (1 - depth) * 0.4      # base depth scaling
            hover_scale = 1.0 + depth * 0.5 if hover else 1.0  # farther objects grow more when hovered
            final_scale = int(opc["scale"] * scale_factor * hover_scale)

            # choose image once
            img = opc["nitida"] if hover else opc["blur"]
            img_scaled = pygame.transform.smoothscale(img, (final_scale, final_scale))

            # --- dwell / fixação ---
            if hover:
                if self.gaze_start_times[i] is None:
                    self.gaze_start_times[i] = current_time
                    if self.tempo_primeira_fixacao[i] is None:
                        self.tempo_primeira_fixacao[i] = current_time - (self.tempo_inicio or current_time)
                    self.num_fixacoes[i] += 1
            else:
                if self.gaze_start_times[i] is not None:
                    duracao = current_time - self.gaze_start_times[i]
                    self.fixacoes[i].append((self.gaze_start_times[i], current_time))
                    self.duracao_total_fixacao[i] += duracao
                self.gaze_start_times[i] = None

            # --- blink selection ---
            if hover and blink and not self.jumping_objects[i]:
                self.blinks_totais += 1
                if opc["path"] == self.objeto_principal_path:
                    self.blinks_corretos += 1
                self.tempo_ultima_fixacao_para_blink[i] = current_time - (self.gaze_start_times[i] or current_time)
                self.handle_selection(i)
                self.jumping_objects[i] = True
                self.jump_start_times[i] = current_time


            # --- jump animation ---
            jump_offset = 0
            if self.jumping_objects[i]:
                elapsed = current_time - self.jump_start_times[i]
                jump_offset = math.sin(elapsed * math.pi) * 25
                if elapsed >= self.JUMP_DURATION:
                    self.jumping_objects[i] = False
                    self.handle_selection(i)

            # --- draw shadow and object ---
            img_rect = img_scaled.get_rect(center=(base_x + 30, base_y + 30 - jump_offset))
            shadow_surf = self.criar_sombra(int(final_scale * 0.3), 8)
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

        # --- 3️⃣ REGISTRO DE MÉTRICAS TÉCNICAS ---
        fim_frame = time.time()
        self.metricas.registrar_gaze(gaze_valido, current_time, fim_frame)
        self.metricas.registrar_fps(self.clock.get_fps())

        # --- check completion ---
        if len(self.coletados) >= self.objetivo:
            self.acertos += 1
            pygame.time.delay(800)
            total_time = (self.tempo_fim or time.time()) - self.tempo_inicio
            first_fixation = min([t for t in self.tempo_primeira_fixacao.values() if t is not None], default=0)
            total_fixation_time = sum(self.duracao_total_fixacao.values())
            fixation_frequency = sum(self.num_fixacoes.values())
            avg_fixation = total_fixation_time / fixation_frequency if fixation_frequency > 0 else 0
            self.tempo_fim = time.time()

            result = self.show_end_screen(
                total_time=total_time,
                first_fixation=first_fixation,
                total_fixation_time=total_fixation_time,
                fixation_frequency=fixation_frequency,
                avg_fixation=avg_fixation
            )

            dados_jogo = {
                "tempo_total_s": total_time,
                "tempo_primeira_fixacao_s": first_fixation,
                "tempo_total_fixacao_s": total_fixation_time,
                "frequencia_fixacoes": fixation_frequency,
                "duracao_media_fixacao_s": avg_fixation,
                "taxa_acerto_piscada_%": (self.blinks_corretos / self.blinks_totais * 100) if self.blinks_totais > 0 else 0,
                "brinquedos_coletados": len(self.coletados),
                "total_brinquedos": self.objetivo
            }

            self.metricas.salvar_csv(dados_jogo,"metricas_FOAC.csv")

            #self.resetar_jogo()
            return result

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

        # draw gaze cursor
        hovering = any(opc["hover"] and opc["active"] for opc in self.opcoes)
        if mx > 0 and my > 0 and not hovering:
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

        self.logo_change_time = time.time() 
    def get_cursor(self):
        if self.gaze:
            mx, my, blink = self.gaze.get_gaze_blink()
            if mx is None or my is None or mx <= 0 or my <= 0:
                mx, my = self.largura // 2, self.altura // 2
                blink = False
            else:
                self.gaze_points.append((mx, my))
        else:
            mx, my = pygame.mouse.get_pos()
            blink = False

        # --- SNAP mechanic ---
        closest_target = None
        closest_dist = float("inf")
        for i, opc in enumerate(self.opcoes):
            if not opc["active"]:
                continue

            base_x, base_y, depth = self.posicoes[i]

            # Calculate current object center (including scale and optional jump)
            # scale_factor = 0.7 + (1 - depth) * 0.4
            # current_scale = opc["scale"] * scale_factor
            jump_offset = 0
            if self.jumping_objects[i]:
                elapsed = time.time() - (self.jump_start_times[i] or 0)
                jump_offset = math.sin(elapsed * math.pi) * 25

            obj_center_x = base_x + 30  # your original center offset
            obj_center_y = base_y + 30 - jump_offset

            # Distance from cursor to object center
            dist = math.hypot(mx - obj_center_x, my - obj_center_y)
            if dist < closest_dist:
                closest_dist = dist
                closest_target = (obj_center_x, obj_center_y)

        # Snap cursor if target is close enough
        if closest_target:
            mx, my = self.snap_to_target(mx, my, closest_target[0], closest_target[1])

        return mx, my, blink


    def snap_to_target(self, mx, my, target_x, target_y):
        if mx < 0 or my < 0:
            return mx, my
        
        distance = math.hypot(mx - target_x, my - target_y)
        if distance <= self.snap_radius:
            # Make snap stronger
            factor = 0.7 + 0.3 * (1 - distance / self.snap_radius)  # stronger near center
            factor = min(factor, 1.0)

            new_x = mx + (target_x - mx) * factor
            new_y = my + (target_y - my) * factor
            return new_x, new_y

        return mx, my


    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                return False
        return True

    # -------------------- MAIN LOOP --------------------
    def run(self):
        self.tempo_inicio = time.time()
        self.tempo_fim = None
        rodando = True
        while rodando:
            rodando = self.processar_eventos()
            if not rodando:
                return "menu"  # ESC during gameplay → back to menu

            result = self.atualizar()
            if result in ("menu", "quit"):
                return result  # end screen returned a signal

            rodando = self.processar_eventos()
            # --- MÉTRICAS TÉCNICAS ---
            inicio_captura = time.time()
            fps_atual = self.clock.get_fps()

            # Simulate gaze capture timing if you don’t have it embedded yet
            fim_frame = time.time()

            # gaze_valido = self.gaze is not None and self.gaze.get_gaze_blink()[0] is not None
            # self.metricas.registrar_gaze(gaze_valido, inicio_captura, fim_frame)
            # self.metricas.registrar_fps(fps_atual)

            pygame.display.flip()
            self.clock.tick(60)
