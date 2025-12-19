"""Codex/Lore viewer UI for reading discovered lore entries."""
from __future__ import annotations

from typing import Dict, List, Optional, Callable

import pygame

from hypersim.game.story.lore import LoreEntry, LoreCategory, Codex, CAMPAIGN_LORE


class CodexViewer:
    """UI for viewing discovered lore entries."""
    
    CATEGORY_COLORS = {
        LoreCategory.DIMENSIONS: (100, 180, 255),
        LoreCategory.BEINGS: (255, 150, 100),
        LoreCategory.HISTORY: (200, 180, 100),
        LoreCategory.LOCATIONS: (100, 200, 150),
        LoreCategory.SCIENCE: (180, 150, 255),
        LoreCategory.PHILOSOPHY: (255, 200, 150),
        LoreCategory.ARTIFACTS: (255, 220, 100),
    }
    
    def __init__(self, screen: pygame.Surface, codex: Codex):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.codex = codex
        
        # State
        self.visible = False
        self.selected_category: Optional[LoreCategory] = None
        self.selected_entry: Optional[str] = None
        self.category_index = 0
        self.entry_index = 0
        self.scroll_offset = 0
        
        # Fonts
        self._font_title = pygame.font.Font(None, 48)
        self._font_heading = pygame.font.Font(None, 32)
        self._font_text = pygame.font.Font(None, 22)
        self._font_small = pygame.font.Font(None, 18)
        
        # Layout
        self.sidebar_width = 250
        self.content_padding = 20
        
        # Callbacks
        self.on_close: Optional[Callable] = None
    
    def show(self) -> None:
        self.visible = True
        self.scroll_offset = 0
        # Select first category with entries
        for cat in LoreCategory:
            entries = self.codex.get_by_category(cat)
            if entries:
                self.selected_category = cat
                self.selected_entry = entries[0].id if entries else None
                break
    
    def hide(self) -> None:
        self.visible = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input. Returns True if consumed."""
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                if self.on_close:
                    self.on_close()
                return True
            elif event.key == pygame.K_UP:
                self._move_selection(-1)
                return True
            elif event.key == pygame.K_DOWN:
                self._move_selection(1)
                return True
            elif event.key == pygame.K_LEFT:
                self._move_category(-1)
                return True
            elif event.key == pygame.K_RIGHT:
                self._move_category(1)
                return True
            elif event.key == pygame.K_PAGEUP:
                self.scroll_offset = max(0, self.scroll_offset - 200)
                return True
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll_offset += 200
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 40)
                return True
            elif event.button == 5:  # Scroll down
                self.scroll_offset += 40
                return True
            elif event.button == 1:
                # Check for entry click
                self._handle_click(event.pos)
                return True
        
        return False
    
    def _handle_click(self, pos: tuple) -> None:
        """Handle mouse click."""
        x, y = pos
        
        # Check sidebar clicks
        if x < self.sidebar_width:
            # Category or entry click
            entries = self._get_current_entries()
            entry_y = 120
            
            for entry in entries:
                if entry_y <= y < entry_y + 28:
                    self.selected_entry = entry.id
                    self.scroll_offset = 0
                    return
                entry_y += 28
    
    def _move_selection(self, delta: int) -> None:
        """Move entry selection."""
        entries = self._get_current_entries()
        if not entries:
            return
        
        current_idx = 0
        for i, e in enumerate(entries):
            if e.id == self.selected_entry:
                current_idx = i
                break
        
        new_idx = (current_idx + delta) % len(entries)
        self.selected_entry = entries[new_idx].id
        self.scroll_offset = 0
    
    def _move_category(self, delta: int) -> None:
        """Move to next/previous category."""
        categories = [cat for cat in LoreCategory if self.codex.get_by_category(cat)]
        if not categories:
            return
        
        current_idx = 0
        for i, cat in enumerate(categories):
            if cat == self.selected_category:
                current_idx = i
                break
        
        new_idx = (current_idx + delta) % len(categories)
        self.selected_category = categories[new_idx]
        
        entries = self._get_current_entries()
        self.selected_entry = entries[0].id if entries else None
        self.scroll_offset = 0
    
    def _get_current_entries(self) -> List[LoreEntry]:
        """Get entries for current category."""
        if not self.selected_category:
            return []
        return self.codex.get_by_category(self.selected_category)
    
    def draw(self) -> None:
        """Draw the codex viewer."""
        if not self.visible:
            return
        
        # Dark overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 240))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self._font_title.render("CODEX", True, (200, 180, 255))
        title_rect = title.get_rect(center=(self.width // 2, 35))
        self.screen.blit(title, title_rect)
        
        # Completion
        discovered, total = self.codex.get_discovery_count()
        completion = self._font_small.render(
            f"Discovered: {discovered}/{total} ({self.codex.get_completion_percentage():.0f}%)",
            True, (150, 150, 170)
        )
        self.screen.blit(completion, (self.width - 180, 20))
        
        # Draw sidebar
        self._draw_sidebar()
        
        # Draw content
        self._draw_content()
        
        # Controls hint
        hint = self._font_small.render(
            "↑↓: Select Entry | ←→: Category | Scroll: Read | ESC: Close",
            True, (100, 100, 120)
        )
        hint_rect = hint.get_rect(center=(self.width // 2, self.height - 15))
        self.screen.blit(hint, hint_rect)
    
    def _draw_sidebar(self) -> None:
        """Draw the category/entry sidebar."""
        # Sidebar background
        sidebar_rect = pygame.Rect(0, 70, self.sidebar_width, self.height - 100)
        pygame.draw.rect(self.screen, (15, 15, 25), sidebar_rect)
        pygame.draw.line(self.screen, (50, 50, 70), 
                        (self.sidebar_width, 70), (self.sidebar_width, self.height - 30), 2)
        
        y = 80
        
        # Category tabs
        for cat in LoreCategory:
            entries = self.codex.get_by_category(cat)
            if not entries:
                continue
            
            is_selected = cat == self.selected_category
            color = self.CATEGORY_COLORS.get(cat, (150, 150, 150))
            
            if is_selected:
                # Highlight bar
                pygame.draw.rect(self.screen, (30, 30, 50), 
                               (0, y - 2, self.sidebar_width - 5, 24))
                pygame.draw.rect(self.screen, color, 
                               (0, y - 2, 4, 24))
            
            cat_text = self._font_small.render(
                f"{cat.value.title()} ({len(entries)})",
                True, color if is_selected else (100, 100, 120)
            )
            self.screen.blit(cat_text, (10, y))
            y += 26
        
        y += 10
        pygame.draw.line(self.screen, (40, 40, 60), (10, y), (self.sidebar_width - 10, y), 1)
        y += 10
        
        # Entries in selected category
        entries = self._get_current_entries()
        for entry in entries:
            is_selected = entry.id == self.selected_entry
            
            if is_selected:
                pygame.draw.rect(self.screen, (40, 40, 60), 
                               (5, y - 2, self.sidebar_width - 15, 24))
            
            # Icon
            icon_text = self._font_small.render(entry.icon, True, (180, 180, 200))
            self.screen.blit(icon_text, (10, y))
            
            # Title (truncated)
            title = entry.title[:22] + "..." if len(entry.title) > 25 else entry.title
            title_color = (220, 220, 240) if is_selected else (150, 150, 170)
            title_text = self._font_small.render(title, True, title_color)
            self.screen.blit(title_text, (30, y))
            
            y += 28
            
            if y > self.height - 60:
                break
    
    def _draw_content(self) -> None:
        """Draw the selected entry content."""
        if not self.selected_entry:
            # No entry selected
            no_entry = self._font_text.render(
                "Select an entry to read",
                True, (100, 100, 120)
            )
            self.screen.blit(no_entry, (self.sidebar_width + 50, 150))
            return
        
        entry = self.codex.entries.get(self.selected_entry)
        if not entry:
            return
        
        # Content area
        content_x = self.sidebar_width + self.content_padding
        content_width = self.width - self.sidebar_width - self.content_padding * 2
        content_y = 80 - self.scroll_offset
        
        # Create clipping rect
        clip_rect = pygame.Rect(self.sidebar_width, 70, 
                               self.width - self.sidebar_width, self.height - 100)
        
        # Entry title
        cat_color = self.CATEGORY_COLORS.get(entry.category, (150, 150, 150))
        
        if content_y > 40:
            title = self._font_heading.render(entry.title, True, cat_color)
            self.screen.blit(title, (content_x, content_y))
        content_y += 40
        
        # Category and discovery info
        if content_y > 40:
            meta = f"{entry.category.value.title()}"
            if entry.discovery_source:
                meta += f" • Found: {entry.discovery_source}"
            meta_text = self._font_small.render(meta, True, (120, 120, 140))
            self.screen.blit(meta_text, (content_x, content_y))
        content_y += 25
        
        # Separator
        if 40 < content_y < self.height - 50:
            pygame.draw.line(self.screen, (50, 50, 70),
                           (content_x, content_y), (content_x + content_width, content_y), 1)
        content_y += 15
        
        # Short description
        if entry.short_description and content_y > 40:
            desc = self._font_text.render(entry.short_description, True, (180, 180, 200))
            self.screen.blit(desc, (content_x, content_y))
            content_y += 30
        
        # Main content (wrapped)
        lines = self._wrap_text(entry.content, self._font_text, content_width)
        for line in lines:
            if 40 < content_y < self.height - 50:
                line_text = self._font_text.render(line, True, (160, 160, 180))
                self.screen.blit(line_text, (content_x, content_y))
            content_y += 22
        
        content_y += 20
        
        # Related entries
        if entry.related_entries:
            if 40 < content_y < self.height - 50:
                related_title = self._font_small.render("Related:", True, (120, 120, 150))
                self.screen.blit(related_title, (content_x, content_y))
            content_y += 20
            
            for related_id in entry.related_entries:
                related = self.codex.entries.get(related_id)
                if related and 40 < content_y < self.height - 50:
                    status = "✓" if related.discovered else "?"
                    color = (100, 180, 100) if related.discovered else (100, 100, 120)
                    related_text = self._font_small.render(
                        f"  {status} {related.title}", True, color
                    )
                    self.screen.blit(related_text, (content_x, content_y))
                content_y += 18
        
        # Scroll indicator
        if self.scroll_offset > 0:
            up_arrow = self._font_text.render("▲ Scroll up", True, (100, 100, 120))
            self.screen.blit(up_arrow, (content_x + content_width - 80, 75))
        
        total_height = content_y + self.scroll_offset
        if total_height > self.height - 50:
            down_arrow = self._font_text.render("▼ Scroll down", True, (100, 100, 120))
            self.screen.blit(down_arrow, (content_x + content_width - 100, self.height - 45))
    
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """Wrap text to fit width, preserving paragraphs."""
        paragraphs = text.split('\n')
        lines = []
        
        for para in paragraphs:
            if not para.strip():
                lines.append("")
                continue
            
            words = para.split()
            current = ""
            
            for word in words:
                test = current + (" " if current else "") + word
                if font.size(test)[0] <= max_width:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = word
            
            if current:
                lines.append(current)
        
        return lines
