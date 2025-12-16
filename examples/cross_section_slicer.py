"""Example: Visualize cross-sections of 4D objects.

This example demonstrates the cross-section slicing feature, which
shows 3D "slices" through 4D objects at different W values.

Controls:
    - Up/Down: Move slice plane along W axis
    - Space: Toggle auto-animate slice
    - Left/Right: Change object
    - ESC: Quit
"""
import pygame
from hypersim.objects import Hypercube, Simplex4D, SixteenCell, TwentyFourCell
from hypersim.visualization.renderers.pygame import PygameRenderer, Color
from hypersim.core.slicer import compute_cross_section, compute_w_range


OBJECTS = [
    ("Hypercube", lambda: Hypercube(size=1.5)),
    ("Simplex", lambda: Simplex4D(size=1.5)),
    ("16-Cell", lambda: SixteenCell(size=1.5)),
    ("24-Cell", lambda: TwentyFourCell(size=1.2)),
]


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("HyperSim - Cross-Section Slicer")
    
    font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 18)
    
    current_idx = 0
    current_obj = OBJECTS[0][1]()
    w_min, w_max = compute_w_range(current_obj)
    current_w = (w_min + w_max) / 2
    w_step = (w_max - w_min) / 100
    
    auto_animate = False
    animate_direction = 1
    
    running = True
    clock = pygame.time.Clock()
    
    def load_object(idx):
        nonlocal current_obj, w_min, w_max, current_w, w_step
        current_obj = OBJECTS[idx][1]()
        current_obj.rotate(xy=0.3, xw=0.2, yw=0.15)
        w_min, w_max = compute_w_range(current_obj)
        current_w = (w_min + w_max) / 2
        w_step = (w_max - w_min) / 100
    
    load_object(0)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    current_w = min(w_max, current_w + w_step * 5)
                elif event.key == pygame.K_DOWN:
                    current_w = max(w_min, current_w - w_step * 5)
                elif event.key == pygame.K_SPACE:
                    auto_animate = not auto_animate
                elif event.key == pygame.K_RIGHT:
                    current_idx = (current_idx + 1) % len(OBJECTS)
                    load_object(current_idx)
                elif event.key == pygame.K_LEFT:
                    current_idx = (current_idx - 1) % len(OBJECTS)
                    load_object(current_idx)
        
        # Auto-animate slice
        if auto_animate:
            current_w += w_step * animate_direction
            if current_w >= w_max:
                current_w = w_max
                animate_direction = -1
            elif current_w <= w_min:
                current_w = w_min
                animate_direction = 1
        
        # Slowly rotate the object
        current_obj.rotate(xy=0.005, xw=0.003)
        w_min, w_max = compute_w_range(current_obj)
        current_w = max(w_min, min(w_max, current_w))
        
        # Compute cross-section
        cross_section = compute_cross_section(current_obj, current_w)
        
        # Clear screen
        screen.fill((10, 10, 25))
        
        # Draw the full 4D object (faded)
        center_x, center_y = 300, 400
        scale = 100
        vertices_4d = current_obj.get_transformed_vertices()
        for a, b in current_obj.edges:
            v1 = vertices_4d[a]
            v2 = vertices_4d[b]
            # Simple projection
            x1 = int(center_x + v1[0] * scale / (1 + abs(v1[3]) * 0.3))
            y1 = int(center_y - v1[1] * scale / (1 + abs(v1[3]) * 0.3))
            x2 = int(center_x + v2[0] * scale / (1 + abs(v2[3]) * 0.3))
            y2 = int(center_y - v2[1] * scale / (1 + abs(v2[3]) * 0.3))
            pygame.draw.line(screen, (40, 60, 80), (x1, y1), (x2, y2), 1)
        
        # Draw the cross-section (bright)
        center_x2, center_y2 = 724, 400
        if cross_section.vertices_3d:
            for a, b in cross_section.edges:
                if a < len(cross_section.vertices_3d) and b < len(cross_section.vertices_3d):
                    v1 = cross_section.vertices_3d[a]
                    v2 = cross_section.vertices_3d[b]
                    x1 = int(center_x2 + v1[0] * scale)
                    y1 = int(center_y2 - v1[1] * scale)
                    x2 = int(center_x2 + v2[0] * scale)
                    y2 = int(center_y2 - v2[1] * scale)
                    pygame.draw.line(screen, (100, 220, 255), (x1, y1), (x2, y2), 2)
            
            # Draw vertices
            for v in cross_section.vertices_3d:
                x = int(center_x2 + v[0] * scale)
                y = int(center_y2 - v[1] * scale)
                pygame.draw.circle(screen, (255, 200, 100), (x, y), 4)
        
        # Draw UI
        title = font.render(f"Cross-Section: {OBJECTS[current_idx][0]}", True, (220, 220, 240))
        screen.blit(title, (20, 20))
        
        w_text = small_font.render(f"W = {current_w:.3f} (range: {w_min:.2f} to {w_max:.2f})", True, (180, 180, 200))
        screen.blit(w_text, (20, 55))
        
        slice_info = small_font.render(f"Slice: {len(cross_section.vertices_3d)} vertices, {len(cross_section.edges)} edges", True, (180, 180, 200))
        screen.blit(slice_info, (20, 80))
        
        animate_text = small_font.render(f"Auto-animate: {'ON' if auto_animate else 'OFF'}", True, (160, 235, 160) if auto_animate else (200, 160, 140))
        screen.blit(animate_text, (20, 105))
        
        # Labels
        label_4d = small_font.render("4D Object", True, (150, 150, 170))
        screen.blit(label_4d, (center_x - 30, 150))
        
        label_3d = small_font.render("3D Cross-Section", True, (150, 150, 170))
        screen.blit(label_3d, (center_x2 - 60, 150))
        
        # Controls
        controls = small_font.render("Up/Down: Move W | Space: Auto-animate | Left/Right: Change object | ESC: Quit", True, (140, 140, 160))
        screen.blit(controls, (20, 740))
        
        # W slider
        slider_x = 50
        slider_width = 200
        slider_y = 700
        pygame.draw.rect(screen, (60, 60, 80), (slider_x, slider_y, slider_width, 10))
        t = (current_w - w_min) / (w_max - w_min) if w_max > w_min else 0.5
        handle_x = int(slider_x + t * slider_width)
        pygame.draw.circle(screen, (100, 180, 255), (handle_x, slider_y + 5), 8)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    main()
