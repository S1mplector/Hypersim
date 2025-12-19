"""Save/Load UI for Tessera campaign."""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple

import pygame

from hypersim.game.save_system import (
    SaveManager, SaveSlot, SaveType, GameSaveData,
    get_save_manager
)


class SaveLoadMode(Enum):
    """Mode of the save/load menu."""
    SAVE = auto()
    LOAD = auto()


@dataclass
class SlotButton:
    """A save slot button."""
    slot: SaveSlot
    rect: pygame.Rect
    hover: bool = False
    selected: bool = False
    hover_progress: float = 0.0
    delete_hover: bool = False


class SaveLoadMenu:
    """Save/Load menu UI."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.visible = False
        self.mode = SaveLoadMode.LOAD
        self.save_manager = get_save_manager()
        
        # Slots
        self.slot_buttons: List[SlotButton] = []
        self.selected_slot: Optional[int] = None
        
        # UI state
        self.scroll_offset = 0
        self.max_scroll = 0
        self.animation_time = 0.0
        self.fade_alpha = 0.0
        
        # Confirmation dialog
        self.confirm_action: Optional[str] = None
        self.confirm_slot: Optional[int] = None
        
        # Input for save name
        self.editing_name = False
        self.save_name_input = ""
        
        # Fonts
        self._font_title = pygame.font.Font(None, 48)
        self._font_slot = pygame.font.Font(None, 28)
        self._font_detail = pygame.font.Font(None, 22)
        self._font_small = pygame.font.Font(None, 18)
        
        # Callbacks
        self.on_load: Optional[Callable[[GameSaveData], None]] = None
        self.on_save: Optional[Callable[[int, str], None]] = None
        self.on_close: Optional[Callable] = None
        
        # Current game data (for saving)
        self._current_data: Optional[GameSaveData] = None
    
    def show(self, mode: SaveLoadMode, current_data: Optional[GameSaveData] = None) -> None:
        """Show the menu."""
        self.visible = True
        self.mode = mode
        self._current_data = current_data
        self.fade_alpha = 0.0
        self.selected_slot = None
        self.confirm_action = None
        self.editing_name = False
        self.save_name_input = ""
        self._refresh_slots()
    
    def hide(self) -> None:
        """Hide the menu."""
        self.visible = False
        if self.on_close:
            self.on_close()
    
    def _refresh_slots(self) -> None:
        """Refresh slot list from save manager."""
        self.slot_buttons.clear()
        
        # Layout
        slot_height = 80
        slot_width = 500
        start_x = (self.width - slot_width) // 2
        start_y = 150
        
        # Manual slots
        manual_slots = self.save_manager.get_manual_slots()
        for i, slot in enumerate(manual_slots):
            rect = pygame.Rect(start_x, start_y + i * (slot_height + 10), slot_width, slot_height)
            self.slot_buttons.append(SlotButton(slot=slot, rect=rect))
        
        # Calculate max scroll
        total_height = len(manual_slots) * (slot_height + 10)
        visible_height = self.height - 250
        self.max_scroll = max(0, total_height - visible_height)
    
    def update(self, dt: float) -> None:
        """Update animations."""
        if not self.visible:
            return
        
        self.animation_time += dt
        
        # Fade in
        if self.fade_alpha < 1.0:
            self.fade_alpha = min(1.0, self.fade_alpha + dt * 4)
        
        # Update hover progress
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.slot_buttons:
            adjusted_rect = btn.rect.copy()
            adjusted_rect.y -= self.scroll_offset
            
            is_hover = adjusted_rect.collidepoint(mouse_pos) and 150 <= adjusted_rect.y <= self.height - 100
            target = 1.0 if is_hover else 0.0
            btn.hover_progress += (target - btn.hover_progress) * dt * 10
            btn.hover = is_hover
            
            # Check delete button hover
            if is_hover and not btn.slot.is_empty:
                delete_rect = pygame.Rect(adjusted_rect.right - 40, adjusted_rect.y + 25, 30, 30)
                btn.delete_hover = delete_rect.collidepoint(mouse_pos)
            else:
                btn.delete_hover = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input. Returns True if consumed."""
        if not self.visible:
            return False
        
        # Confirmation dialog takes priority
        if self.confirm_action:
            return self._handle_confirm_event(event)
        
        # Name input mode
        if self.editing_name:
            return self._handle_name_input(event)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                return self._handle_click(event.pos)
            elif event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 30)
                return True
            elif event.button == 5:  # Scroll down
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 30)
                return True
        
        return False
    
    def _handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click."""
        # Check slot buttons
        for i, btn in enumerate(self.slot_buttons):
            adjusted_rect = btn.rect.copy()
            adjusted_rect.y -= self.scroll_offset
            
            if adjusted_rect.collidepoint(pos) and 150 <= adjusted_rect.y <= self.height - 100:
                # Check delete button
                if btn.delete_hover and not btn.slot.is_empty:
                    self.confirm_action = "delete"
                    self.confirm_slot = i
                    return True
                
                # Select/action
                self.selected_slot = i
                
                if self.mode == SaveLoadMode.LOAD:
                    if not btn.slot.is_empty:
                        self._do_load(i)
                else:  # SAVE
                    if btn.slot.is_empty:
                        self.editing_name = True
                        self.save_name_input = f"Save {btn.slot.slot_id}"
                    else:
                        self.confirm_action = "overwrite"
                        self.confirm_slot = i
                
                return True
        
        # Check back button
        back_rect = pygame.Rect(20, self.height - 60, 100, 40)
        if back_rect.collidepoint(pos):
            self.hide()
            return True
        
        # Check tab buttons
        save_tab = pygame.Rect(self.width // 2 - 110, 90, 100, 35)
        load_tab = pygame.Rect(self.width // 2 + 10, 90, 100, 35)
        
        if save_tab.collidepoint(pos):
            self.mode = SaveLoadMode.SAVE
            self._refresh_slots()
            return True
        if load_tab.collidepoint(pos):
            self.mode = SaveLoadMode.LOAD
            self._refresh_slots()
            return True
        
        return False
    
    def _handle_confirm_event(self, event: pygame.event.Event) -> bool:
        """Handle events in confirmation dialog."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_n:
                self.confirm_action = None
                self.confirm_slot = None
                return True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_y:
                self._execute_confirm()
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check confirm/cancel buttons
            dialog_rect = pygame.Rect(self.width // 2 - 150, self.height // 2 - 60, 300, 120)
            yes_rect = pygame.Rect(dialog_rect.x + 30, dialog_rect.bottom - 50, 100, 35)
            no_rect = pygame.Rect(dialog_rect.right - 130, dialog_rect.bottom - 50, 100, 35)
            
            if yes_rect.collidepoint(event.pos):
                self._execute_confirm()
                return True
            elif no_rect.collidepoint(event.pos):
                self.confirm_action = None
                self.confirm_slot = None
                return True
        
        return True  # Consume all events while dialog is open
    
    def _execute_confirm(self) -> None:
        """Execute the confirmed action."""
        if self.confirm_action == "delete" and self.confirm_slot is not None:
            slot = self.slot_buttons[self.confirm_slot].slot
            self.save_manager.delete_slot(slot.slot_id, slot.slot_type)
            self._refresh_slots()
        
        elif self.confirm_action == "overwrite" and self.confirm_slot is not None:
            slot = self.slot_buttons[self.confirm_slot].slot
            self.editing_name = True
            self.save_name_input = slot.metadata.save_name if slot.metadata else f"Save {slot.slot_id}"
        
        self.confirm_action = None
        self.confirm_slot = None
    
    def _handle_name_input(self, event: pygame.event.Event) -> bool:
        """Handle text input for save name."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.editing_name = False
                self.save_name_input = ""
                return True
            elif event.key == pygame.K_RETURN:
                if self.selected_slot is not None:
                    self._do_save(self.selected_slot, self.save_name_input)
                self.editing_name = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.save_name_input = self.save_name_input[:-1]
                return True
            elif event.unicode and len(self.save_name_input) < 30:
                self.save_name_input += event.unicode
                return True
        
        return True
    
    def _do_load(self, slot_index: int) -> None:
        """Load from a slot."""
        slot = self.slot_buttons[slot_index].slot
        save_data = self.save_manager.load_from_slot(slot.slot_id, slot.slot_type)
        
        if save_data and self.on_load:
            self.on_load(save_data)
            self.hide()
    
    def _do_save(self, slot_index: int, name: str) -> None:
        """Save to a slot."""
        if not self._current_data:
            return
        
        slot = self.slot_buttons[slot_index].slot
        success = self.save_manager.save_to_slot(
            self._current_data,
            slot.slot_id,
            slot.slot_type,
            name
        )
        
        if success:
            if self.on_save:
                self.on_save(slot.slot_id, name)
            self._refresh_slots()
    
    def draw(self) -> None:
        """Draw the menu."""
        if not self.visible:
            return
        
        # Darken background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        alpha = int(200 * self.fade_alpha)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = "LOAD GAME" if self.mode == SaveLoadMode.LOAD else "SAVE GAME"
        title_surf = self._font_title.render(title, True, (220, 230, 255))
        title_rect = title_surf.get_rect(center=(self.width // 2, 50))
        self.screen.blit(title_surf, title_rect)
        
        # Tabs
        self._draw_tabs()
        
        # Create clip rect for slots
        clip_rect = pygame.Rect(0, 150, self.width, self.height - 250)
        
        # Draw slots
        for i, btn in enumerate(self.slot_buttons):
            adjusted_rect = btn.rect.copy()
            adjusted_rect.y -= self.scroll_offset
            
            # Skip if outside clip area
            if adjusted_rect.bottom < 150 or adjusted_rect.top > self.height - 100:
                continue
            
            self._draw_slot(btn, adjusted_rect, i == self.selected_slot)
        
        # Scroll indicators
        if self.scroll_offset > 0:
            pygame.draw.polygon(self.screen, (150, 150, 180),
                              [(self.width // 2 - 10, 155), (self.width // 2 + 10, 155), (self.width // 2, 145)])
        if self.scroll_offset < self.max_scroll:
            y = self.height - 105
            pygame.draw.polygon(self.screen, (150, 150, 180),
                              [(self.width // 2 - 10, y), (self.width // 2 + 10, y), (self.width // 2, y + 10)])
        
        # Back button
        self._draw_back_button()
        
        # Controls hint
        hint = "Click slot to select • Scroll to see more • ESC to close"
        hint_surf = self._font_small.render(hint, True, (100, 100, 120))
        hint_rect = hint_surf.get_rect(center=(self.width // 2, self.height - 20))
        self.screen.blit(hint_surf, hint_rect)
        
        # Confirmation dialog
        if self.confirm_action:
            self._draw_confirm_dialog()
        
        # Name input dialog
        if self.editing_name:
            self._draw_name_input()
    
    def _draw_tabs(self) -> None:
        """Draw mode tabs."""
        save_tab = pygame.Rect(self.width // 2 - 110, 90, 100, 35)
        load_tab = pygame.Rect(self.width // 2 + 10, 90, 100, 35)
        
        # Save tab
        save_color = (60, 80, 120) if self.mode == SaveLoadMode.SAVE else (30, 40, 60)
        pygame.draw.rect(self.screen, save_color, save_tab, border_radius=5)
        if self.mode == SaveLoadMode.SAVE:
            pygame.draw.rect(self.screen, (100, 150, 255), save_tab, 2, border_radius=5)
        save_text = self._font_detail.render("SAVE", True, (200, 210, 230))
        self.screen.blit(save_text, save_text.get_rect(center=save_tab.center))
        
        # Load tab
        load_color = (60, 80, 120) if self.mode == SaveLoadMode.LOAD else (30, 40, 60)
        pygame.draw.rect(self.screen, load_color, load_tab, border_radius=5)
        if self.mode == SaveLoadMode.LOAD:
            pygame.draw.rect(self.screen, (100, 150, 255), load_tab, 2, border_radius=5)
        load_text = self._font_detail.render("LOAD", True, (200, 210, 230))
        self.screen.blit(load_text, load_text.get_rect(center=load_tab.center))
    
    def _draw_slot(self, btn: SlotButton, rect: pygame.Rect, selected: bool) -> None:
        """Draw a save slot."""
        slot = btn.slot
        
        # Background with hover effect
        bg_color = (40, 50, 70) if btn.hover_progress > 0.5 else (25, 30, 45)
        if selected:
            bg_color = (50, 70, 100)
        
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
        
        # Border
        border_color = (100, 150, 255) if selected else (60, 70, 90)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=8)
        
        # Hover glow
        if btn.hover_progress > 0.1:
            glow_alpha = int(30 * btn.hover_progress)
            glow_surf = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (100, 150, 255, glow_alpha), 
                           (0, 0, rect.width + 10, rect.height + 10), border_radius=10)
            self.screen.blit(glow_surf, (rect.x - 5, rect.y - 5), special_flags=pygame.BLEND_ADD)
        
        if slot.is_empty:
            # Empty slot
            empty_text = self._font_slot.render("Empty Slot", True, (100, 100, 120))
            self.screen.blit(empty_text, (rect.x + 20, rect.y + 28))
        else:
            # Slot with save
            # Name
            name = slot.metadata.save_name if slot.metadata else "Unknown"
            name_surf = self._font_slot.render(name, True, (220, 230, 255))
            self.screen.blit(name_surf, (rect.x + 20, rect.y + 12))
            
            # Details
            if slot.metadata:
                detail_parts = [
                    f"Ch.{slot.metadata.current_chapter}",
                    f"Lv.{slot.metadata.player_level}",
                    f"{slot.metadata.current_dimension.upper()}",
                    f"{slot.metadata.completion_percent:.0f}%",
                ]
                detail_text = " • ".join(detail_parts)
                detail_surf = self._font_detail.render(detail_text, True, (150, 160, 180))
                self.screen.blit(detail_surf, (rect.x + 20, rect.y + 40))
                
                # Time info
                time_text = f"{slot.last_played} • {slot.playtime_display}"
                time_surf = self._font_small.render(time_text, True, (100, 110, 130))
                self.screen.blit(time_surf, (rect.x + 20, rect.y + 60))
            
            # Delete button
            delete_rect = pygame.Rect(rect.right - 40, rect.y + 25, 30, 30)
            delete_color = (200, 80, 80) if btn.delete_hover else (100, 60, 60)
            pygame.draw.rect(self.screen, delete_color, delete_rect, border_radius=5)
            x_surf = self._font_detail.render("×", True, (255, 200, 200))
            self.screen.blit(x_surf, x_surf.get_rect(center=delete_rect.center))
    
    def _draw_back_button(self) -> None:
        """Draw back button."""
        rect = pygame.Rect(20, self.height - 60, 100, 40)
        pygame.draw.rect(self.screen, (40, 50, 70), rect, border_radius=6)
        pygame.draw.rect(self.screen, (80, 90, 110), rect, 2, border_radius=6)
        
        text = self._font_detail.render("← Back", True, (180, 190, 210))
        self.screen.blit(text, text.get_rect(center=rect.center))
    
    def _draw_confirm_dialog(self) -> None:
        """Draw confirmation dialog."""
        # Background overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Dialog box
        dialog_rect = pygame.Rect(self.width // 2 - 150, self.height // 2 - 60, 300, 120)
        pygame.draw.rect(self.screen, (30, 35, 50), dialog_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 120, 160), dialog_rect, 2, border_radius=10)
        
        # Message
        if self.confirm_action == "delete":
            msg = "Delete this save?"
        elif self.confirm_action == "overwrite":
            msg = "Overwrite this save?"
        else:
            msg = "Are you sure?"
        
        msg_surf = self._font_slot.render(msg, True, (220, 230, 255))
        self.screen.blit(msg_surf, msg_surf.get_rect(center=(self.width // 2, dialog_rect.y + 35)))
        
        # Buttons
        yes_rect = pygame.Rect(dialog_rect.x + 30, dialog_rect.bottom - 50, 100, 35)
        no_rect = pygame.Rect(dialog_rect.right - 130, dialog_rect.bottom - 50, 100, 35)
        
        pygame.draw.rect(self.screen, (80, 120, 80), yes_rect, border_radius=5)
        pygame.draw.rect(self.screen, (120, 80, 80), no_rect, border_radius=5)
        
        yes_text = self._font_detail.render("Yes", True, (220, 255, 220))
        no_text = self._font_detail.render("No", True, (255, 220, 220))
        self.screen.blit(yes_text, yes_text.get_rect(center=yes_rect.center))
        self.screen.blit(no_text, no_text.get_rect(center=no_rect.center))
    
    def _draw_name_input(self) -> None:
        """Draw save name input dialog."""
        # Background overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Dialog box
        dialog_rect = pygame.Rect(self.width // 2 - 200, self.height // 2 - 70, 400, 140)
        pygame.draw.rect(self.screen, (30, 35, 50), dialog_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 120, 160), dialog_rect, 2, border_radius=10)
        
        # Title
        title_surf = self._font_slot.render("Enter Save Name", True, (220, 230, 255))
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.width // 2, dialog_rect.y + 30)))
        
        # Input field
        input_rect = pygame.Rect(dialog_rect.x + 20, dialog_rect.y + 55, 360, 35)
        pygame.draw.rect(self.screen, (20, 25, 35), input_rect, border_radius=5)
        pygame.draw.rect(self.screen, (100, 150, 255), input_rect, 2, border_radius=5)
        
        # Text with cursor
        cursor = "|" if int(self.animation_time * 2) % 2 == 0 else ""
        input_text = self.save_name_input + cursor
        text_surf = self._font_detail.render(input_text, True, (220, 230, 255))
        self.screen.blit(text_surf, (input_rect.x + 10, input_rect.y + 8))
        
        # Hint
        hint_surf = self._font_small.render("Press ENTER to save, ESC to cancel", True, (100, 110, 130))
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(self.width // 2, dialog_rect.bottom - 20)))
