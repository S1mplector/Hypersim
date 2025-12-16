"""Example: Object morphing demonstration.

Shows smooth transitions between different 4D polytopes
using the morphing system.
"""
import pygame
import numpy as np

from hypersim.objects import (
    Hypercube, SixteenCell, TwentyFourCell, Pentachoron,
    SixHundredCell, Duoprism,
)
from hypersim.core.morphing import ShapeMorpher, MorphStrategy, EasingType


def main():
    pygame.init()
    screen = pygame.display.set_mode((1000, 700))
    pygame.display.set_caption("HyperSim - Object Morphing Demo")
    clock = pygame.time.Clock()
    
    # Create shapes to morph between
    shapes = [
        ("Pentachoron", Pentachoron(size=1.2), (255, 180, 100)),
        ("Tesseract", Hypercube(size=1.0), (100, 200, 255)),
        ("16-cell", SixteenCell(size=1.1), (150, 255, 150)),
        ("24-cell", TwentyFourCell(size=0.9), (200, 130, 255)),
        ("Duoprism 4×5", Duoprism(m=4, n=5, size=1.0), (255, 200, 100)),
    ]
    
    # Morphing system
    morpher = ShapeMorpher(
        strategy=MorphStrategy.DISTRIBUTE,
        easing=EasingType.EASE_IN_OUT,
    )
    
    current_idx = 0
    target_idx = 1
    
    # Start first morph
    morpher.start_morph(shapes[current_idx][1], shapes[target_idx][1], duration=2.0)
    
    # Current displayed vertices/edges
    current_vertices = None
    current_edges = []
    
    # Projection settings
    projection_scale = 150.0
    w_factor = 0.3
    auto_rotate = True
    rotation_time = 0.0
    
    def project(v, rotation_offset=0.0):
        """Project 4D to 2D with rotation."""
        x, y, z, w = v
        
        # Apply rotation
        angle = rotation_offset
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        x2 = x * cos_a - w * sin_a
        w2 = x * sin_a + w * cos_a
        
        angle2 = rotation_offset * 0.7
        cos_a2, sin_a2 = np.cos(angle2), np.sin(angle2)
        y2 = y * cos_a2 - z * sin_a2
        z2 = y * sin_a2 + z * cos_a2
        
        w_scale = 1.0 / (1.0 + abs(w2) * w_factor)
        px = x2 * w_scale * projection_scale + 500
        py = -y2 * w_scale * projection_scale + 350
        depth = z2 * w_scale
        
        return int(px), int(py), depth
    
    # UI fonts
    font = pygame.font.SysFont("Arial", 16)
    title_font = pygame.font.SysFont("Arial", 28)
    shape_font = pygame.font.SysFont("Arial", 20)
    
    # Easing options
    easing_types = [
        ("Linear", EasingType.LINEAR),
        ("Ease In/Out", EasingType.EASE_IN_OUT),
        ("Ease In", EasingType.EASE_IN),
        ("Ease Out", EasingType.EASE_OUT),
        ("Elastic", EasingType.ELASTIC),
        ("Bounce", EasingType.BOUNCE),
        ("Overshoot", EasingType.OVERSHOOT),
    ]
    current_easing_idx = 1
    
    # Strategy options
    strategies = [
        ("Distribute", MorphStrategy.DISTRIBUTE),
        ("Nearest", MorphStrategy.NEAREST),
        ("Centroid", MorphStrategy.CENTROID),
    ]
    current_strategy_idx = 0
    
    morph_duration = 2.0
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Start morph to next shape
                    if not morpher.is_morphing:
                        current_idx = target_idx
                        target_idx = (target_idx + 1) % len(shapes)
                        morpher.easing = easing_types[current_easing_idx][1]
                        morpher.strategy = strategies[current_strategy_idx][1]
                        morpher.start_morph(
                            shapes[current_idx][1],
                            shapes[target_idx][1],
                            duration=morph_duration,
                        )
                elif event.key == pygame.K_r:
                    auto_rotate = not auto_rotate
                elif event.key == pygame.K_e:
                    # Cycle easing
                    current_easing_idx = (current_easing_idx + 1) % len(easing_types)
                elif event.key == pygame.K_s:
                    # Cycle strategy
                    current_strategy_idx = (current_strategy_idx + 1) % len(strategies)
                elif event.key == pygame.K_UP:
                    morph_duration = min(5.0, morph_duration + 0.5)
                elif event.key == pygame.K_DOWN:
                    morph_duration = max(0.5, morph_duration - 0.5)
                elif event.key >= pygame.K_1 and event.key <= pygame.K_5:
                    # Quick jump to shape
                    new_target = event.key - pygame.K_1
                    if new_target < len(shapes) and not morpher.is_morphing:
                        current_idx = target_idx
                        target_idx = new_target
                        morpher.easing = easing_types[current_easing_idx][1]
                        morpher.strategy = strategies[current_strategy_idx][1]
                        morpher.start_morph(
                            shapes[current_idx][1],
                            shapes[target_idx][1],
                            duration=morph_duration,
                        )
        
        # Update morphing
        morpher.update(dt)
        
        # Get current vertices
        if morpher.is_morphing:
            current_vertices = morpher.vertices
            current_edges = morpher.edges
        else:
            # Use target shape
            current_vertices = np.array(shapes[target_idx][1].get_transformed_vertices())
            current_edges = list(shapes[target_idx][1].edges)
        
        # Update rotation
        if auto_rotate:
            rotation_time += dt * 0.5
        
        # Render
        screen.fill((8, 10, 18))
        
        # Interpolate color
        if morpher.is_morphing:
            t = morpher.progress
            c1 = shapes[current_idx][2]
            c2 = shapes[target_idx][2]
            color = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        else:
            color = shapes[target_idx][2]
        
        # Project and sort edges
        if current_vertices is not None:
            projected = [project(v, rotation_time) for v in current_vertices]
            
            edge_data = []
            for a, b in current_edges:
                if a < len(projected) and b < len(projected):
                    p1 = projected[a]
                    p2 = projected[b]
                    avg_depth = (p1[2] + p2[2]) / 2
                    edge_data.append((avg_depth, p1, p2))
            
            edge_data.sort(reverse=True)
            
            for depth, p1, p2 in edge_data:
                t = max(0, min(1, (depth + 2) / 4))
                edge_color = tuple(int(c * (0.3 + 0.7 * (1 - t))) for c in color)
                width = max(1, int(2 * (1 - t * 0.5)))
                pygame.draw.line(screen, edge_color, (p1[0], p1[1]), (p2[0], p2[1]), width)
        
        # Draw UI
        title = title_font.render("Object Morphing Demo", True, (220, 220, 240))
        screen.blit(title, (20, 20))
        
        # Current shape info
        from_name = shapes[current_idx][0]
        to_name = shapes[target_idx][0]
        
        if morpher.is_morphing:
            progress_pct = int(morpher.progress * 100)
            shape_text = f"{from_name}  →  {to_name}  ({progress_pct}%)"
        else:
            shape_text = to_name
        
        shape_surf = shape_font.render(shape_text, True, color)
        screen.blit(shape_surf, (20, 60))
        
        # Progress bar
        if morpher.is_morphing:
            bar_width = 300
            bar_height = 8
            bar_x, bar_y = 20, 95
            pygame.draw.rect(screen, (40, 45, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
            progress_width = int(bar_width * morpher.progress)
            pygame.draw.rect(screen, color, (bar_x, bar_y, progress_width, bar_height), border_radius=4)
        
        # Settings panel
        panel_x = 750
        pygame.draw.rect(screen, (20, 25, 35), (panel_x - 10, 10, 250, 200), border_radius=8)
        
        settings = [
            f"Easing: {easing_types[current_easing_idx][0]}",
            f"Strategy: {strategies[current_strategy_idx][0]}",
            f"Duration: {morph_duration:.1f}s",
            f"Vertices: {len(current_vertices) if current_vertices is not None else 0}",
            f"Edges: {len(current_edges)}",
            f"Auto-rotate: {'ON' if auto_rotate else 'OFF'}",
        ]
        
        for i, text in enumerate(settings):
            surf = font.render(text, True, (180, 185, 200))
            screen.blit(surf, (panel_x, 20 + i * 25))
        
        # Shape list
        list_y = 500
        list_title = font.render("Shapes (1-5 to select):", True, (150, 155, 170))
        screen.blit(list_title, (20, list_y))
        
        for i, (name, _, col) in enumerate(shapes):
            prefix = "→ " if i == target_idx else "  "
            text_col = col if i == target_idx else (120, 125, 140)
            surf = font.render(f"{prefix}{i+1}. {name}", True, text_col)
            screen.blit(surf, (20, list_y + 25 + i * 22))
        
        # Controls
        controls = [
            "Space: Morph to next",
            "1-5: Jump to shape",
            "E: Cycle easing",
            "S: Cycle strategy",
            "↑/↓: Adjust duration",
            "R: Toggle rotation",
            "Esc: Quit",
        ]
        for i, text in enumerate(controls):
            surf = font.render(text, True, (100, 105, 120))
            screen.blit(surf, (panel_x, 500 + i * 22))
        
        pygame.display.flip()
    
    pygame.quit()


if __name__ == "__main__":
    main()
