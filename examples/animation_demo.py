"""Example: Keyframe animation system demo.

Demonstrates the animation and keyframe system with easing functions.
"""
import pygame
from hypersim.objects import Hypercube
from hypersim.engine import (
    Animation,
    EasingFunction,
    create_rotation_animation,
    create_scale_pulse,
)
from hypersim.visualization.renderers.pygame import PygameRenderer, Color


def main():
    renderer = PygameRenderer(
        width=1024,
        height=768,
        title="HyperSim - Animation Demo",
        background_color=Color(10, 10, 25),
        auto_spin=False,
    )

    cube = Hypercube(size=1.2)
    
    # Create a complex animation
    anim = Animation(name="Demo")
    
    # Position keyframes - move in a square pattern
    anim.keyframe(0.0, "position", [0, 0, 0, 0], EasingFunction.LINEAR)
    anim.keyframe(1.0, "position", [1, 0, 0, 0], EasingFunction.EASE_OUT)
    anim.keyframe(2.0, "position", [1, 1, 0, 0], EasingFunction.EASE_IN_OUT)
    anim.keyframe(3.0, "position", [0, 1, 0, 0], EasingFunction.EASE_OUT)
    anim.keyframe(4.0, "position", [0, 0, 0, 0], EasingFunction.EASE_IN)
    
    # Rotation keyframes
    anim.keyframe(0.0, "rotation.xy", 0.0)
    anim.keyframe(2.0, "rotation.xy", 3.14, EasingFunction.EASE_IN_OUT)
    anim.keyframe(4.0, "rotation.xy", 6.28, EasingFunction.EASE_IN_OUT)
    
    anim.keyframe(0.0, "rotation.xw", 0.0)
    anim.keyframe(4.0, "rotation.xw", 3.14, EasingFunction.LINEAR)
    
    # Scale pulse
    anim.keyframe(0.0, "scale", 1.0)
    anim.keyframe(1.0, "scale", 1.3, EasingFunction.EASE_OUT_ELASTIC)
    anim.keyframe(2.0, "scale", 1.0, EasingFunction.EASE_IN)
    anim.keyframe(3.0, "scale", 0.8, EasingFunction.EASE_OUT)
    anim.keyframe(4.0, "scale", 1.0, EasingFunction.EASE_OUT_BOUNCE)
    
    anim.play(loop=True)
    
    font = pygame.font.SysFont("Arial", 20)
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
                    if anim._playing:
                        anim.pause()
                    else:
                        anim.play(loop=True)
                elif event.key == pygame.K_r:
                    anim.stop()
                    anim.play(loop=True)
        
        # Update animation
        anim.update(dt)
        anim.apply_to(cube)
        
        # Render
        renderer.clear()
        renderer.render_4d_object(cube, Color(100, 200, 255), 2)
        
        # UI
        screen = renderer.screen
        time_text = font.render(f"Time: {anim.current_time:.2f}s / {anim.duration:.2f}s", True, (200, 200, 220))
        status = "Playing" if anim._playing else "Paused"
        status_text = font.render(f"Status: {status} (Space: play/pause, R: reset)", True, (180, 180, 200))
        screen.blit(time_text, (20, 20))
        screen.blit(status_text, (20, 50))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    main()
