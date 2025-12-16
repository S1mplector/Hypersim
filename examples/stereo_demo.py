"""Example: Stereoscopic 3D rendering demo.

Demonstrates different stereoscopic rendering modes for enhanced
depth perception of 4D objects.
"""
import pygame
from hypersim.objects import Hypercube, TwentyFourCell
from hypersim.visualization.renderers.pygame.stereo import StereoRenderer, StereoMode


def main():
    pygame.init()
    screen = pygame.display.set_mode((1200, 600))
    pygame.display.set_caption("HyperSim - Stereoscopic Demo")
    
    # Create stereo renderer
    stereo = StereoRenderer(
        screen,
        mode=StereoMode.ANAGLYPH_RED_CYAN,
        eye_separation=0.15,
        projection_distance=5.0,
    )
    
    # Create object
    cube = Hypercube(size=1.3)
    cube.rotate(xy=0.3, xw=0.2, yw=0.15)
    
    modes = [
        StereoMode.ANAGLYPH_RED_CYAN,
        StereoMode.ANAGLYPH_GREEN_MAGENTA,
        StereoMode.SIDE_BY_SIDE,
        StereoMode.CROSS_EYE,
    ]
    mode_names = [
        "Anaglyph Red-Cyan (use 3D glasses)",
        "Anaglyph Green-Magenta",
        "Side-by-Side (parallel viewing)",
        "Cross-Eye (cross your eyes)",
    ]
    current_mode = 0
    
    font = pygame.font.SysFont("Arial", 20)
    small_font = pygame.font.SysFont("Arial", 16)
    
    running = True
    clock = pygame.time.Clock()
    last_time = pygame.time.get_ticks() / 1000.0
    
    while running:
        now = pygame.time.get_ticks() / 1000.0
        dt = now - last_time
        last_time = now
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    current_mode = (current_mode + 1) % len(modes)
                    stereo.set_mode(modes[current_mode])
                elif event.key == pygame.K_UP:
                    stereo.set_eye_separation(stereo.eye_separation + 0.02)
                elif event.key == pygame.K_DOWN:
                    stereo.set_eye_separation(stereo.eye_separation - 0.02)
        
        # Rotate object
        cube.rotate(xy=dt * 0.4, xw=dt * 0.3, yw=dt * 0.25)
        
        # Render in stereo
        stereo.render(cube, line_width=2, background=(5, 5, 15))
        
        # UI overlay
        mode_text = font.render(f"Mode: {mode_names[current_mode]}", True, (220, 220, 240))
        sep_text = small_font.render(f"Eye separation: {stereo.eye_separation:.2f}", True, (180, 180, 200))
        controls = small_font.render("Space: cycle modes | Up/Down: adjust separation | ESC: quit", True, (140, 140, 160))
        
        screen.blit(mode_text, (20, 20))
        screen.blit(sep_text, (20, 50))
        screen.blit(controls, (20, 570))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    main()
