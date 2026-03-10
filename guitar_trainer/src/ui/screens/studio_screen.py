import pygame
from .base import Screen
from ..widgets.knob import Knob
import numpy as np
import wave

class StudioScreen(Screen):
    def __init__(self, cfg, state, controller):
        super().__init__(cfg, state, controller)
        W, H = cfg.window_size
        self.W, self.H = W, H

        self.font_main = pygame.font.SysFont("monospace", int(H * 0.06), bold=True)
        self.font_info = pygame.font.SysFont("monospace", int(H * 0.035))
        self.font_small = pygame.font.SysFont("monospace", int(H * 0.025))
        self.font_hint = pygame.font.SysFont("monospace", int(H * 0.02))
        self.font_grid = pygame.font.SysFont("monospace", int(H * 0.018), bold=True)
        knob_y = int(H * 0.88)
        knob_radius = int(H * 0.035)
        knob_start = int(W * 0.15)
        knob_step = int(W * 0.14)
        self.knob_gate = Knob(knob_start, knob_y, knob_radius, "GATE", cfg.rms_threshold, 0.0, 0.15)
        self.knob_pure = Knob(knob_start + knob_step, knob_y, knob_radius, "PURE", cfg.flatness_threshold, 0.0, 1.0)
        self.knob_drive = Knob(knob_start + knob_step * 2, knob_y, knob_radius, "DRIVE", 0.0, 0.0, 1.0)
        self.knob_tone = Knob(knob_start + knob_step * 3, knob_y, knob_radius, "TONE", cfg.tone, 0.0, 1.0)
        self.knob_vol = Knob(knob_start + knob_step * 4, knob_y, knob_radius, "VOL", 0.8, 0.0, 1.0)

    def on_enter(self):
        self.controller.set_active_mode("studio")
        self.controller.studio_engine.reset_recording()

    def on_exit(self):
        self.controller.set_active_mode("game")

    def handle_event(self, event):
        engine = self.controller.studio_engine
        if self.knob_gate.handle_event(event):
            self.cfg.rms_threshold = self.knob_gate.val
            self.controller.set_audio_gate(self.knob_gate.val)
        if self.knob_pure.handle_event(event):
            self.cfg.flatness_threshold = self.knob_pure.val
        if self.knob_drive.handle_event(event):
            self.controller.set_audio_drive(self.knob_drive.val)
        if self.knob_tone.handle_event(event):
            self.controller.set_audio_tone(self.knob_tone.val)
        if self.knob_vol.handle_event(event):
            self.controller.set_audio_volume(self.knob_vol.val)
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.change_screen("menu")
            elif event.key == pygame.K_RIGHT:
                engine.next_target()
            elif event.key == pygame.K_LEFT:
                engine.prev_target()
            elif event.key == pygame.K_SPACE:
                self._play_current_sample()
            elif event.key == pygame.K_r:
                engine.reset_recording()
            elif event.key == pygame.K_n:
                self._skip_to_next_undone()


    def _play_current_sample(self):
        path = self.controller.studio_engine.get_last_saved_path()
        if not path:
            return
        try:
            with wave.open(path, 'rb') as wf:
                n_frames = wf.getnframes()
                raw = wf.readframes(n_frames)
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32767.0
            self.controller.play_sample(audio)
        except Exception as e:
            print(f"[STUDIO] Playback error: {e}")

    def _skip_to_next_undone(self):
        engine = self.controller.studio_engine
        start = engine.current_idx
        for i in range(len(engine.targets)):
            idx = (start + 1 + i) % len(engine.targets)
            if not engine.targets[idx]["done"]:
                engine.current_idx = idx
                engine.reset_recording()
                return

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill((15, 18, 25))
        engine = self.controller.studio_engine
        target = engine.get_current_target()
        done_count, total_count = engine.get_progress()

        self._draw_title(surface, done_count, total_count)
        self._draw_grid(surface, engine)

        if not target:
            txt = self.font_main.render("Tous les samples sont enregistrés !", True, (100, 255, 100))
            surface.blit(txt, (self.W // 2 - txt.get_width() // 2, int(self.H * 0.5)))
            return

        self._draw_target(surface, target, engine)
        self._draw_status(surface, engine)
        self._draw_progress_bar(surface, engine)
        self._draw_diagnostics(surface)
        self._draw_hints(surface)
        
        self.knob_gate.draw(surface)
        self.knob_pure.draw(surface)
        self.knob_drive.draw(surface)
        self.knob_tone.draw(surface)
        self.knob_vol.draw(surface)

    def _draw_title(self, surface, done, total):
        txt = self.font_main.render("MODE STUDIO", True, (200, 150, 255))
        surface.blit(txt, (int(self.W * 0.05), int(self.H * 0.03)))

        counter = self.font_info.render(f"{done} / {total} enregistrés", True, (150, 150, 150))
        surface.blit(counter, (self.W - counter.get_width() - int(self.W * 0.05), int(self.H * 0.04)))

    def _draw_grid(self, surface, engine):
        grid_x = int(self.W * 0.05)
        grid_y = int(self.H * 0.12)
        cell_w = int(self.W * 0.035)
        cell_h = int(self.H * 0.035)
        padding = 3

        strings_in_grid = [6, 5, 4, 3, 2, 1]
        max_fret = 0
        for t in engine.targets:
            if t["fret"] > max_fret:
                max_fret = t["fret"]

        target = engine.get_current_target()
        target_key = (target["string"], target["fret"]) if target else None

        lookup = {}
        for t in engine.targets:
            lookup[(t["string"], t["fret"])] = t

        string_labels = ["E2", "A2", "D3", "G3", "B3", "E4"]
        for row, s in enumerate(strings_in_grid):
            lbl = self.font_grid.render(string_labels[row], True, (120, 120, 120))
            surface.blit(lbl, (grid_x - lbl.get_width() - 8, grid_y + row * (cell_h + padding) + 2))

            for col in range(max_fret + 1):
                x = grid_x + col * (cell_w + padding)
                y = grid_y + row * (cell_h + padding)
                rect = pygame.Rect(x, y, cell_w, cell_h)

                key = (s, col)
                t = lookup.get(key)

                if t is None:
                    bg = (25, 25, 30)
                    border = (40, 40, 50)
                elif key == target_key:
                    bg = (0, 80, 120)
                    border = (0, 255, 255)
                elif t["done"]:
                    bg = (20, 80, 30)
                    border = (0, 200, 50)
                else:
                    bg = (40, 40, 50)
                    border = (80, 80, 90)

                pygame.draw.rect(surface, bg, rect, border_radius=3)
                pygame.draw.rect(surface, border, rect, 1, border_radius=3)

                if t:
                    fret_txt = self.font_grid.render(str(col), True, (180, 180, 180))
                    surface.blit(fret_txt, (rect.centerx - fret_txt.get_width() // 2, rect.centery - fret_txt.get_height() // 2))

    def _draw_target(self, surface, target, engine):
        y = int(self.H * 0.45)
        txt = self.font_main.render(
            f"Corde {target['string']}  |  Case {target['fret']}  |  {target['note']}",
            True, (255, 200, 0)
        )
        surface.blit(txt, (self.W // 2 - txt.get_width() // 2, y))

        if target["done"] and engine.state != "RECORDING":
            done_txt = self.font_info.render("(déjà enregistré — R pour refaire)", True, (100, 200, 100))
            surface.blit(done_txt, (self.W // 2 - done_txt.get_width() // 2, y + int(self.H * 0.07)))

    def _draw_status(self, surface, engine):
        y = int(self.H * 0.58)

        if engine.state == "WAITING":
            if engine.confirm_timer > 0:
                txt = "Confirmation..."
                color = (255, 200, 50)
            else:
                txt = "Joue la note juste et tiens-la"
                color = (120, 120, 120)
        elif engine.state == "RECORDING":
            txt = "ENREGISTREMENT"
            color = (255, 50, 50)
        else:
            txt = "SAUVEGARDÉ"
            color = (50, 255, 50)

        rendered = self.font_info.render(txt, True, color)
        surface.blit(rendered, (self.W // 2 - rendered.get_width() // 2, y))

    def _draw_progress_bar(self, surface, engine):
        bar_x = int(self.W * 0.2)
        bar_y = int(self.H * 0.66)
        bar_w = int(self.W * 0.6)
        bar_h = int(self.H * 0.03)
        bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)

        if engine.state == "WAITING" and engine.confirm_timer > 0:
            progress = min(1.0, engine.confirm_timer / engine.confirm_duration)
            pygame.draw.rect(surface, (40, 40, 50), bar_rect, border_radius=4)
            fill = pygame.Rect(bar_x, bar_y, int(bar_w * progress), bar_h)
            pygame.draw.rect(surface, (255, 200, 50), fill, border_radius=4)
            pygame.draw.rect(surface, (100, 100, 100), bar_rect, 1, border_radius=4)

        elif engine.state == "RECORDING":
            progress = min(1.0, engine.record_timer / engine.record_duration)
            pygame.draw.rect(surface, (40, 40, 50), bar_rect, border_radius=4)
            fill = pygame.Rect(bar_x, bar_y, int(bar_w * progress), bar_h)
            pygame.draw.rect(surface, (255, 50, 50), fill, border_radius=4)
            pygame.draw.rect(surface, (100, 100, 100), bar_rect, 1, border_radius=4)

    def _draw_diagnostics(self, surface):
        features = self.state.get_features_snapshot()
        if not features or not features.is_voiced:
            return

        y = int(self.H * 0.74)
        purity_str = "Pur" if features.is_pure else "Bruit"
        txt = self.font_small.render(
            f"Entendu: {features.note_name}  |  {features.cents:+.1f} cts  |  {purity_str}",
            True, (130, 130, 200)
        )
        surface.blit(txt, (self.W // 2 - txt.get_width() // 2, y))

    def _draw_hints(self, surface):
        hints = "G/D : naviguer  |  N : prochain vide  |  R : refaire  |  ESPACE : écouter  |  Echap : quitter  |  GATE/PURE : souris"
        txt = self.font_hint.render(hints, True, (70, 70, 70))
        surface.blit(txt, (self.W // 2 - txt.get_width() // 2, int(self.H * 0.95)))
