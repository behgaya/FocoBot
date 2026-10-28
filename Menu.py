import pygame
import sys
import os
from focobot import ui
from focobot.gaze_controller import GazeController
from focobot.alignment import face_alignment_screen
from focobot.minigames.minigameSESE import SESEGame
from focobot.minigames.minigameSUSE import SUSEGame
from focobot.minigames.minigameFOAC import FOACGame
from focobot.settings import SettingsScreen, Button, GameConfig


# ------------------------
# MINIGAMES
# ------------------------
# Cada minigame: classe, imagens do menu, tutorial e quais configurações recebe.
GAMES = [
    {
        "cls": SESEGame,
        "button": "Assets/MainMenu/SESE/Button.png",
        "button_hover": "Assets/MainMenu/SESE/button_hover.png",
        "bg": "Assets/MainMenu/Background/bg_neutral.png",
        "logo": "Assets/MainMenu/Logo/logo_sese.png",
        "tutorial": "Assets/Tutorial/tutorial_sese.png",
        "kwargs": lambda c: dict(asteroid_count=c.sese_asteroid_count, rocket_speed=c.sese_speed,
                                 snap_radius=c.sese_snap_radius, required_look_time=c.sese_required_look_time),
    },
    {
        "cls": SUSEGame,
        "button": "Assets/MainMenu/SUSE/button.png",
        "button_hover": "Assets/MainMenu/SUSE/button_hover.png",
        "bg": "Assets/MainMenu/Background/bg_neutral.png",
        "logo": "Assets/MainMenu/Logo/logo_suse.png",
        "tutorial": "Assets/Tutorial/tutorial_suse.png",
        "kwargs": lambda c: dict(num_foods=c.suse_num_foods, fish_speed=c.suse_fish_speed,
                                 hit_radius=c.suse_hit_radius, food_spacing=c.suse_food_spacing,
                                 object_size=c.suse_object_size),
    },
    {
        "cls": FOACGame,
        "button": "Assets/MainMenu/FOAC/button.png",
        "button_hover": "Assets/MainMenu/FOAC/button_hover.png",
        "bg": "Assets/MainMenu/Background/bg_neutral.png",
        "logo": "Assets/MainMenu/Logo/logo_foac.png",
        "tutorial": "Assets/Tutorial/tutorial_foac.png",
        "kwargs": lambda c: dict(snap_radius=c.foac_snap_radius, objetivos=c.foac_objetivos,
                                 max_blur=c.foac_max_blur, object_count=c.foac_object_count),
    },
]


# ------------------------
# TUTORIAL SCREEN
# ------------------------
class TutorialScreen:
    def __init__(self, tela, largura, altura, clock, image_path, next_callback):
        self.tela = tela
        self.clock = clock
        self.running = True
        self.next_callback = next_callback

        self.bg_image, self.bg_rect = ui.load_cover(image_path, largura, altura)

        s = min(largura / 1920, altura / 1080)
        fonte = ui.font(30 * s)
        w, h, margem = int(220 * s), int(64 * s), int(50 * s)
        y = altura - margem - h
        self.back_btn = ui.PillButton("Voltar", (margem, y, w, h), self.back, fonte, filled=False)
        self.next_btn = ui.PillButton("Começar", (largura - margem - w, y, w, h), self.next, fonte)

    def back(self):
        self.running = False

    def next(self):
        self.running = False
        self.next_callback()

    def run(self):
        self.running = True
        while self.running:
            self.tela.blit(self.bg_image, self.bg_rect)
            self.back_btn.draw(self.tela)
            self.next_btn.draw(self.tela)
            ui.set_hand_cursor(self.back_btn.is_hover() or self.next_btn.is_hover())
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.back()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.next()
                else:
                    self.back_btn.check_click(event)
                    self.next_btn.check_click(event)
                if not self.running:
                    break
            self.clock.tick(30)
        ui.set_hand_cursor(False)


# ------------------------
# MAIN MENU
# ------------------------
class Menu:
    # layout da grade: logo em cima, os 3 minigames embaixo
    CELL_W, CELL_H = 350, 180
    COL_SPACING, ROW_SPACING = 380, 250

    def __init__(self, tela, largura, altura, clock, config):
        self.tela = tela
        self.largura = largura
        self.altura = altura
        self.clock = clock
        self.config = config
        font = pygame.font.SysFont(None, 40)

        # --- Tudo carregado uma vez (antes era recarregado do disco a cada frame) ---
        # fundo alinhado no canto superior esquerdo (mostra a parte de cima da imagem)
        self.bg = (ui.load_cover("Assets/MainMenu/Background/bg_neutral.png", largura, altura)[0], (0, 0))
        title = ui.render_outlined(ui.font(84), "Escolha um Minigame")
        self.title = (title, title.get_rect(center=(largura // 2, 120)))

        start_x = largura // 2 - (2 * self.COL_SPACING + self.CELL_W) // 2
        start_y = altura // 2 - (self.ROW_SPACING + self.CELL_H) // 2

        logo = ui.load_scaled("Assets/MainMenu/Logo/logo_neutral.png", self.CELL_W * 1.3)
        self.logo = (logo, logo.get_rect(center=(largura // 2, start_y + self.CELL_H // 2)))

        # --- Botões dos minigames + imagens mostradas ao passar o mouse ---
        self.buttons = []
        self.hover_images = []  # (botão, fundo, logo)
        bg_cache = {}
        for i, game in enumerate(GAMES):
            x = start_x + i * self.COL_SPACING
            y = start_y + self.ROW_SPACING
            button = Button("", (x, y, self.CELL_W, self.CELL_H), self.make_game_callback(game),
                            image_path=game["button"], hover_image_path=game["button_hover"],
                            font=font, show_text=False)
            self.buttons.append(button)

            if game["bg"] not in bg_cache:
                bg_cache[game["bg"]] = (ui.load_cover(game["bg"], largura, altura)[0], (0, 0))
            hover_logo = ui.load_scaled(game["logo"], 1.3 * 250)
            logo_rect = hover_logo.get_rect(center=(largura // 2, altura // 2 - hover_logo.get_height() // 2 - 37))
            self.hover_images.append((button, bg_cache[game["bg"]], (hover_logo, logo_rect)))

        # --- Configurações (canto inferior esquerdo) e Sair (canto inferior direito) ---
        margem, size = 50, 200
        corner_y = altura - size - margem
        self.buttons.append(Button("Settings", (margem, corner_y, size, size), self.open_settings,
                                   image_path="Assets/Settings/button.png",
                                   hover_image_path="Assets/Settings/button_hover.png",
                                   font=font, show_text=False))
        self.buttons.append(Button("Sair", (largura - size - margem, corner_y, size, size), self.quit_game,
                                   image_path="Assets/MainMenu/QUIT/button.png",
                                   hover_image_path="Assets/MainMenu/QUIT/button_hover.png",
                                   font=font, show_text=False))

    # -------------------- ações --------------------
    def make_game_callback(self, game):
        def go_to_calibration():
            if not face_alignment_screen():
                return
            gaze = GazeController()
            try:
                instance = game["cls"](self.tela, self.largura, self.altura, self.clock, gaze=gaze,
                                       **game["kwargs"](self.config))
                instance.run()
            finally:
                gaze.release()  # libera a webcam ao sair de qualquer minigame

        def start_game():
            TutorialScreen(self.tela, self.largura, self.altura, self.clock,
                           image_path=game["tutorial"], next_callback=go_to_calibration).run()

        return start_game

    def open_settings(self):
        SettingsScreen(self.tela, self.largura, self.altura, self.clock, self.config).run()

    def quit_game(self):
        pygame.quit()
        sys.exit()

    # -------------------- loop --------------------
    def run(self):
        while True:
            # fundo e logo mudam conforme o minigame sob o mouse
            bg, logo = self.bg, self.logo
            for button, hover_bg, hover_logo in self.hover_images:
                if button.is_hover():
                    bg, logo = hover_bg, hover_logo
                    break

            self.tela.blit(*bg)
            self.tela.blit(*self.title)
            for b in self.buttons:
                b.draw(self.tela)
            self.tela.blit(*logo)
            ui.set_hand_cursor(any(b.is_hover() for b in self.buttons))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                for b in self.buttons:
                    b.check_click(event)

            pygame.display.flip()
            self.clock.tick(30)


# ------------------------
# MAIN
# ------------------------
if __name__ == "__main__":
    # Assets/ and data/ paths are relative to the project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    pygame.init()
    info = pygame.display.Info()
    tela = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
    largura, altura = tela.get_size()
    pygame.display.set_caption("EyeTrax Minigames")
    clock = pygame.time.Clock()

    config = GameConfig()
    menu = Menu(tela, largura, altura, clock, config)
    menu.run()
