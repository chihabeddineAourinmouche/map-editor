#!/usr/bin/python3

import pygame
import random
import os
import sys

def generate_random_png_pygame(width=64, height=64, output_path_prefix="random_image", nb_images=1):
    # 1. Initialize Pygame
    pygame.init()
    
    colors = [
        (255, 114, 86),
        (13, 152, 186),
        (127, 255, 0),
        (249, 103, 20),
        (216, 222, 233)
    ]

    # 2. Create a surface with a color key for transparency
    screen = pygame.Surface((width, height), pygame.SRCALPHA)
    
    for image_index in range(nb_images):

        # 3. Fill the background with a transparent color
        screen.fill((0, 0, 0, 0))  # Fully transparent background (RGBA)

        # 4. Define the number of polygons
        num_shapes = random.randint(3, len(colors) - 1)

        # 5. Generate and draw random polygons
        for shape_index in range(num_shapes):
            # Generate random color for the polygon (with alpha)
            color = colors[shape_index]
            # Generate random points for the polygon.  Let's use between 3 and 6 points.

            shape = random.randint(0, 2)
            if shape == 0:
                # Draw polygon
                num_points = 3
                points = []
                for _ in range(num_points):
                    x = random.randint(0, width)
                    y = random.randint(0, height)
                    points.append((x, y))
                pygame.draw.polygon(screen, color, points)
            if shape == 1:
                # Draw Rect
                x = random.randint(0, width)
                y = random.randint(0, height)
                w = random.randint(width // 3, width // 2)
                h = random.randint(height // 3, height // 2)
                pygame.draw.rect(screen, color, (x, y, w, h))
            if shape == 2:
                # Draw Circle
                x = random.randint(0, width)
                y = random.randint(0, height)
                d = random.randint(width // 3, width // 2)
                pygame.draw.circle(screen, color, (x, y), d / 2)

        # 6. Save the surface as a PNG file
        try:
            pygame.image.save(screen, f"{output_path_prefix}_{image_index}.png")
            print(f"Successfully generated image: {output_path_prefix}_{image_index}.png")
        except Exception as e:
            print(f"Error saving image: {e}")

    # 7. Quit Pygame
    pygame.quit()

if __name__ == "__main__":
    generate_random_png_pygame(nb_images=int(sys.argv[1]) if len(sys.argv) == 2 and sys.argv[1].isnumeric() else 1)
