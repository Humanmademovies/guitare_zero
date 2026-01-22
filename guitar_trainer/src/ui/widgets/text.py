import pygame

class TextLabel:
    def __init__(self, font: pygame.font.Font, pos: tuple[int, int], color=(255, 255, 255), align="topleft"):
        self.font = font
        self.pos = pos
        self.base_color = color
        self.align = align
        self.text = ""
        self.surface = None
        self.rect = None

    def set_text(self, text: str, color=None) -> None:
        if text != self.text or color:
            self.text = text
            draw_color = color if color else self.base_color
            self.surface = self.font.render(self.text, True, draw_color)
            self.rect = self.surface.get_rect()
            # Application de l'alignement (center, topleft, etc.)
            setattr(self.rect, self.align, self.pos)

    def draw(self, surface: pygame.Surface) -> None:
        if self.surface and self.rect:
            surface.blit(self.surface, self.rect)