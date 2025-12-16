"""Example: 4D Physics simulation demonstration.

Showcases the physics system including:
- Rigid body dynamics
- Collision detection
- Particle effects
- Gravity and forces
"""
import pygame
import numpy as np

from hypersim.objects import Hypercube, SixteenCell, Pentachoron
from hypersim.physics import (
    PhysicsWorld, RigidBody4D, Gravity4D,
    ParticleSystem, ParticleConfig, EmitterShape,
)
from hypersim.visualization.materials import Materials, Gradient, GradientType


def main():
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("HyperSim - 4D Physics Demo")
    clock = pygame.time.Clock()
    
    # Create physics world
    world = PhysicsWorld()
    world.gravity = Gravity4D(
        direction=np.array([0, -1, 0, 0], dtype=np.float32),
        strength=5.0,
    )
    
    # Create objects and add to physics world
    objects = []
    
    # Bouncing hypercube
    cube = Hypercube(size=0.5)
    cube.set_position(np.array([0, 2, 0, 0]))
    cube_body = RigidBody4D(
        shape=cube,
        mass=1.0,
        restitution=0.8,
        velocity=np.array([1, 0, 0.5, 0], dtype=np.float32),
    )
    world.add_body(cube_body)
    objects.append((cube, (100, 200, 255)))
    
    # Falling 16-cell
    cell16 = SixteenCell(size=0.4)
    cell16.set_position(np.array([-1.5, 3, 0, 0]))
    cell16_body = RigidBody4D(
        shape=cell16,
        mass=0.5,
        restitution=0.6,
        angular_velocity={'xy': 1.0, 'zw': 0.5},
    )
    world.add_body(cell16_body)
    objects.append((cell16, (255, 150, 100)))
    
    # Pentachoron
    penta = Pentachoron(size=0.6)
    penta.set_position(np.array([1.5, 2.5, 0, 0]))
    penta_body = RigidBody4D(
        shape=penta,
        mass=0.8,
        restitution=0.7,
        velocity=np.array([-0.5, 0, 0, 0.2], dtype=np.float32),
    )
    world.add_body(penta_body)
    objects.append((penta, (150, 255, 150)))
    
    # Static floor (invisible, just for collision)
    floor = Hypercube(size=5.0)
    floor.set_position(np.array([0, -3, 0, 0]))
    floor_body = RigidBody4D(
        shape=floor,
        is_static=True,
    )
    world.add_body(floor_body)
    
    # Create particle system for collision effects
    particle_system = ParticleSystem()
    
    # Projection settings
    projection_scale = 120.0
    w_factor = 0.3
    
    def project(v):
        """Project 4D to 2D screen coordinates."""
        x, y, z, w = v
        w_scale = 1.0 / (1.0 + abs(w) * w_factor)
        px = x * w_scale * projection_scale + 600
        py = -y * w_scale * projection_scale + 400
        depth = z * w_scale
        return int(px), int(py), depth
    
    # Fonts
    font = pygame.font.SysFont("Arial", 16)
    title_font = pygame.font.SysFont("Arial", 24)
    
    running = True
    paused = False
    show_particles = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    # Reset positions
                    cube.set_position(np.array([0, 2, 0, 0]))
                    cube_body.velocity = np.array([1, 0, 0.5, 0], dtype=np.float32)
                    cell16.set_position(np.array([-1.5, 3, 0, 0]))
                    cell16_body.velocity = np.zeros(4, dtype=np.float32)
                    penta.set_position(np.array([1.5, 2.5, 0, 0]))
                    penta_body.velocity = np.array([-0.5, 0, 0, 0.2], dtype=np.float32)
                elif event.key == pygame.K_p:
                    show_particles = not show_particles
                elif event.key == pygame.K_UP:
                    # Add upward impulse to all objects
                    for body in world.bodies:
                        if not body.is_static:
                            body.apply_impulse(np.array([0, 5, 0, 0], dtype=np.float32))
        
        # Physics update
        if not paused:
            collisions = world.step(dt)
            
            # Create particles at collision points
            if show_particles:
                for collision in collisions:
                    if collision.point is not None:
                        # Create small burst
                        config = ParticleConfig(
                            lifetime_min=0.3,
                            lifetime_max=0.6,
                            speed_min=1.0,
                            speed_max=3.0,
                            size_start=4,
                            size_end=1,
                            color_start=(255, 255, 200),
                            color_end=(255, 100, 50),
                            gravity_scale=0.5,
                        )
                        emitter = particle_system.create_emitter(
                            collision.point,
                            config,
                            shape=EmitterShape.SPHERE,
                            shape_size=0.1,
                            emission_rate=0,
                        )
                        emitter.emit(10)
                        emitter.enabled = False
            
            particle_system.update(dt)
        
        # Render
        screen.fill((10, 12, 20))
        
        # Draw floor grid
        grid_color = (30, 35, 50)
        floor_y = project(np.array([0, -3, 0, 0]))[1]
        for i in range(-10, 11):
            x1 = 600 + i * 50
            pygame.draw.line(screen, grid_color, (x1, floor_y - 100), (x1, floor_y + 100), 1)
        for i in range(-2, 3):
            y1 = floor_y + i * 50
            pygame.draw.line(screen, grid_color, (100, y1), (1100, y1), 1)
        
        # Draw objects with depth sorting
        all_edges = []
        for obj, color in objects:
            vertices = obj.get_transformed_vertices()
            projected = [project(np.array(v)) for v in vertices]
            
            for a, b in obj.edges:
                if a < len(projected) and b < len(projected):
                    p1 = projected[a]
                    p2 = projected[b]
                    avg_depth = (p1[2] + p2[2]) / 2
                    all_edges.append((avg_depth, (p1[0], p1[1]), (p2[0], p2[1]), color))
        
        # Sort and draw
        all_edges.sort(reverse=True)
        for depth, p1, p2, color in all_edges:
            t = max(0, min(1, (depth + 2) / 4))
            edge_color = tuple(int(c * (0.4 + 0.6 * (1 - t))) for c in color)
            width = max(1, int(2 * (1 - t * 0.5)))
            pygame.draw.line(screen, edge_color, p1, p2, width)
        
        # Draw particles
        if show_particles:
            for particle in particle_system.get_all_particles():
                px, py, _ = project(particle.position)
                size = int(particle.current_size)
                color = (*particle.current_color, particle.current_alpha)
                
                if 0 < px < 1200 and 0 < py < 800:
                    surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, color, (size, size), size)
                    screen.blit(surf, (px - size, py - size))
        
        # Draw UI
        title = title_font.render("4D Physics Demo", True, (200, 200, 220))
        screen.blit(title, (20, 20))
        
        status = "PAUSED" if paused else "RUNNING"
        status_color = (255, 200, 100) if paused else (100, 255, 150)
        status_surf = font.render(f"Status: {status}", True, status_color)
        screen.blit(status_surf, (20, 55))
        
        energy = world.get_total_energy()
        energy_surf = font.render(f"Total Energy: {energy:.2f}", True, (180, 180, 200))
        screen.blit(energy_surf, (20, 80))
        
        particles_surf = font.render(f"Particles: {particle_system.total_particles}", True, (180, 180, 200))
        screen.blit(particles_surf, (20, 105))
        
        # Controls
        controls = [
            "Space: Pause/Resume",
            "R: Reset",
            "Up: Apply impulse",
            "P: Toggle particles",
            "Esc: Quit",
        ]
        for i, text in enumerate(controls):
            surf = font.render(text, True, (120, 130, 150))
            screen.blit(surf, (1050, 20 + i * 22))
        
        pygame.display.flip()
    
    pygame.quit()


if __name__ == "__main__":
    main()
