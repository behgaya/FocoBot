import pygame
import pygame.gfxdraw

# ------------------------
# HELPERS DE INTERFACE (compartilhados entre menu, configurações e tutorial)
# ------------------------
FONT_PATH = "Assets/Fonts/Fredoka-Regular.ttf"

BRANCO = (255, 255, 255)
ROSA = (255, 100, 150)          # contorno do título do menu
ROSA_ESCURO = (225, 70, 125)


def font(size):
    return pygame.font.Font(FONT_PATH, int(size))


def load_cover(path, largura, altura):
    """Carrega uma imagem escalada para cobrir a tela inteira (centralizada)."""
    img = pygame.image.load(path).convert_alpha()
    w, h = img.get_size()
    scale = max(largura / w, altura / h)
    img = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
    return img, img.get_rect(center=(largura // 2, altura // 2))


def load_scaled(path, width):
    """Carrega uma imagem com a largura dada, mantendo a proporção."""
    img = pygame.image.load(path).convert_alpha()
    w, h = img.get_size()
    return pygame.transform.smoothscale(img, (int(width), int(width * h / w)))


def render_outlined(fonte, text, color=BRANCO, outline_color=ROSA, outline=4):
    """Texto com contorno (8 cópias deslocadas por baixo do texto principal)."""
    main = fonte.render(text, True, color)
    back = fonte.render(text, True, outline_color)
    w, h = main.get_size()
    surf = pygame.Surface((w + outline * 2, h + outline * 2), pygame.SRCALPHA)
    for dx in (-outline, 0, outline):
        for dy in (-outline, 0, outline):
            if dx or dy:
                surf.blit(back, (dx + outline, dy + outline))
    surf.blit(main, (outline, outline))
    return surf


def draw_round_rect(surface, rect, color, radius, width=0):
    """Retângulo arredondado com suporte a transparência (RGBA)."""
    rect = pygame.Rect(rect)
    shape = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shape, color, shape.get_rect(), width, border_radius=int(radius))
    surface.blit(shape, rect.topleft)


def draw_circle(surface, center, radius, color):
    """Círculo preenchido com borda suavizada."""
    x, y, r = int(center[0]), int(center[1]), int(radius)
    pygame.gfxdraw.filled_circle(surface, x, y, r, color)
    pygame.gfxdraw.aacircle(surface, x, y, r, color)


def set_hand_cursor(active):
    try:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if active else pygame.SYSTEM_CURSOR_ARROW)
    except pygame.error:
        pass  # alguns drivers de vídeo não suportam cursores do sistema


def mix(c1, c2, t):
    """Interpola duas cores RGB (t=0 -> c1, t=1 -> c2)."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


class PillButton:
    """Botão arredondado com texto, no estilo das telas do menu."""

    def __init__(self, text, rect, callback, fonte, color=ROSA, filled=True):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.callback = callback
        self.font = fonte
        self.color = color
        self.filled = filled

    def is_hover(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, surface):
        hover = self.is_hover()
        radius = self.rect.height // 2
        # sombra
        draw_round_rect(surface, self.rect.move(0, 4), (0, 0, 0, 70), radius)
        if self.filled:
            fill = mix(self.color, BRANCO, 0.15) if hover else self.color
            draw_round_rect(surface, self.rect, fill, radius)
            text_color = BRANCO
        else:
            draw_round_rect(surface, self.rect, (255, 255, 255, 60 if hover else 30), radius)
            draw_round_rect(surface, self.rect, (255, 255, 255, 200), radius, width=2)
            text_color = BRANCO
        txt = self.font.render(self.text, True, text_color)
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.callback()
