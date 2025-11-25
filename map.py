import os
import pygame
import numpy as np
import pygame.surfarray

TILE_DIR = "tiles"
TILE_SIZE = 256
START_ZOOM = 2
MIN_ZOOM = 2
MAX_ZOOM = 5
SMOOTH_SPEED = 0.2  # smooth pan & zoom speed


# ----------------------------------------------------------
# LOAD TILES
# ----------------------------------------------------------
def load_tiles(zoom):
    tiles = {}
    zoom_dir = os.path.join(TILE_DIR, str(zoom))
    if not os.path.exists(zoom_dir):
        return tiles
    for x_name in os.listdir(zoom_dir):
        x_path = os.path.join(zoom_dir, x_name)
        if not os.path.isdir(x_path):
            continue
        for y_name in os.listdir(x_path):
            if not y_name.endswith(".webp"):
                continue
            y_path = os.path.join(x_path, y_name)
            try:
                x_index = int(x_name)
                y_index = int(y_name.replace(".webp", ""))
            except ValueError:
                continue
            try:
                tiles[(x_index, y_index)] = pygame.image.load(y_path).convert_alpha()
            except Exception as e:
                print(f"Failed to load {y_path}: {e}")
    return tiles


# ----------------------------------------------------------
# DOTTED LINE DRAWER
# ----------------------------------------------------------
def draw_dotted_line(surface, color, start, end, dash_length=10):
    x1, y1 = start
    x2, y2 = end
    length = max(abs(x2 - x1), abs(y2 - y1))
    if length == 0:
        return
    dx = (x2 - x1) / length
    dy = (y2 - y1) / length
    for i in range(0, length, dash_length * 2):
        sx = int(x1 + dx * i)
        sy = int(y1 + dy * i)
        ex = int(x1 + dx * (i + dash_length))
        ey = int(y1 + dy * (i + dash_length))
        pygame.draw.line(surface, color, (sx, sy), (ex, ey))


def lerp(a, b, t):
    return a + (b - a) * t


def clamp_offset(offset_x, offset_y, tiles, screen_w, screen_h, zoom_scale=1.0):
    if not tiles:
        return offset_x, offset_y
    xs = [x for x, y in tiles.keys()]
    ys = [y for x, y in tiles.keys()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    map_w = (max_x - min_x + 1) * TILE_SIZE * zoom_scale
    map_h = (max_y - min_y + 1) * TILE_SIZE * zoom_scale
    max_x_off = -min_x * TILE_SIZE * zoom_scale
    min_x_off = screen_w - ((max_x + 1) * TILE_SIZE * zoom_scale)
    max_y_off = -min_y * TILE_SIZE * zoom_scale
    min_y_off = screen_h - ((max_y + 1) * TILE_SIZE * zoom_scale)
    return max(min_x_off, min(max_x_off, offset_x)), max(min_y_off, min(max_y_off, offset_y))


# ----------------------------------------------------------
# MAIN
# ----------------------------------------------------------
def main():
    invert_enabled = False  # start with invert off
    pygame.init()
    screen_w, screen_h = 1024, 768
    screen = pygame.display.set_mode((screen_w, screen_h), pygame.RESIZABLE)
    pygame.display.set_caption("DayZ Tile Map Viewer")

    # ----------------------------------------------------------
    # Military-style font
    # ----------------------------------------------------------
    try:
        font = pygame.font.SysFont("OCR A Extended", 18, bold=True)
    except:
        font = pygame.font.SysFont("Consolas", 18, bold=True)

    current_zoom = START_ZOOM
    tiles = load_tiles(current_zoom)
    scaled_tiles_cache = {}

    offset_x = offset_y = target_offset_x = target_offset_y = 0.0
    zoom_float = target_zoom = current_zoom
    dragging = False
    drag_start = drag_offset_start = (0, 0)

    clock = pygame.time.Clock()
    running = True

    while running:
        screen.fill((0, 0, 0))
        zoom_scale = zoom_float / current_zoom

        # ----------------------------------------------------------
        # DRAW TILES
        # ----------------------------------------------------------
        if tiles:
            xs = [x for x, y in tiles.keys()]
            ys = [y for x, y in tiles.keys()]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            start_x = max(min_x, int(-offset_x / (TILE_SIZE * zoom_scale)))
            end_x = min(max_x, int((screen_w - offset_x) / (TILE_SIZE * zoom_scale)) + 1)
            start_y = max(min_y, int(-offset_y / (TILE_SIZE * zoom_scale)))
            end_y = min(max_y, int((screen_h - offset_y) / (TILE_SIZE * zoom_scale)) + 1)

            for x in range(start_x, end_x + 1):
                for y in range(start_y, end_y + 1):
                    px = int(x * TILE_SIZE * zoom_scale + offset_x)
                    py = int(y * TILE_SIZE * zoom_scale + offset_y)
                    key = (x, y, int(zoom_float * 100))

                    if (x, y) in tiles:
                        if key not in scaled_tiles_cache:
                            scaled_tiles_cache[key] = pygame.transform.smoothscale(
                                tiles[(x, y)],
                                (int(TILE_SIZE * zoom_scale), int(TILE_SIZE * zoom_scale))
                            )
                        screen.blit(scaled_tiles_cache[key], (px, py))
                    else:
                        rect = pygame.Rect(px, py, int(TILE_SIZE * zoom_scale), int(TILE_SIZE * zoom_scale))
                        pygame.draw.rect(screen, (70, 70, 70), rect)
                        text = font.render(f"{x},{y}", True, (0, 0, 0))
                        screen.blit(text, text.get_rect(center=rect.center))

            # ----------------------------------------------------------
            # GRID (dotted)
            # ----------------------------------------------------------
            grid_color = (0, 0, 0)

            for x in range(start_x, end_x + 1):
                px = int(x * TILE_SIZE * zoom_scale + offset_x)
                draw_dotted_line(screen, grid_color, (px, 0), (px, screen_h))

            for y in range(start_y, end_y + 1):
                py = int(y * TILE_SIZE * zoom_scale + offset_y)
                draw_dotted_line(screen, grid_color, (0, py), (screen_w, py))

            # ----------------------------------------------------------
            # AXIS LABELS (mil green)
            # ----------------------------------------------------------
            axis_color = (60, 60, 60)

            for x in range(start_x, end_x + 1):
                px = int(x * TILE_SIZE * zoom_scale + offset_x)
                label = font.render(str(x), True, axis_color)
                screen.blit(label, (px + 5, 5))

            for y in range(start_y, end_y + 1):
                py = int(y * TILE_SIZE * zoom_scale + offset_y)
                label = font.render(str(y), True, axis_color)
                screen.blit(label, (5, py + 5))

            # ----------------------------------------------------------
            # INVERT FILTER (tiles + grid, before HUD)
            # ----------------------------------------------------------
            if invert_enabled:
                # Copy the current screen (tiles + grid)
                tile_surface = screen.copy()
                
                # Get pixel array
                arr = pygame.surfarray.pixels3d(tile_surface)
                
                # Invert colors
                np.subtract(255, arr, out=arr)
                
                # Convert to grayscale: average the RGB channels
                gray = arr.mean(axis=2, keepdims=True).astype(np.uint8)
                arr[:] = gray  # broadcast grayscale to all channels
                
                del arr  # unlock surface
                screen.blit(tile_surface, (0, 0))




        # ----------------------------------------------------------
        # HUD ALTITUDE (military style)
        # ----------------------------------------------------------
        altitude_km = 2 / zoom_float * 400
        hud_text = f"ALT {altitude_km:06.2f} KM"
        hud_surf = font.render(hud_text, True, (0, 255, 0))

        bg = pygame.Surface((hud_surf.get_width() + 16, hud_surf.get_height() + 12))
        bg.set_alpha(120)
        bg.fill((0, 40, 0))
        screen.blit(bg, (screen_w - bg.get_width() - 20, 20))
        screen.blit(hud_surf, (screen_w - hud_surf.get_width() - 12, 26))

        # ----------------------------------------------------------
        # SCALE BAR (bottom-left)
        # ----------------------------------------------------------
        tile_distance_km = 0.98 * (altitude_km / 50.0)
        tile_distance_m = max(tile_distance_km * 1000, 1)

        nice_units_m = [50, 100, 200, 500, 1000, 2000, 5000, 10000]
        best_unit_m = nice_units_m[-1]
        for u in nice_units_m:
            if u >= tile_distance_m * 0.3:
                best_unit_m = u
                break

        pixels_per_tile = TILE_SIZE * zoom_scale
        px_per_m = pixels_per_tile / tile_distance_m
        scale_bar_px = int(best_unit_m * px_per_m)
        scale_bar_px = max(40, min(scale_bar_px, int(screen_w * 0.4)))

        if best_unit_m < 1000:
            distance_text = f"{best_unit_m} M"
        else:
            distance_text = f"{best_unit_m/1000:.1f} KM"

        pad_x = 12
        pad_y = 8
        font_h = font.get_linesize()
        box_w = scale_bar_px + pad_x * 2
        box_h = font_h + pad_y * 2 + 6

        box_x = 20
        box_y = screen_h - box_h - 20

        bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_surf.fill((0, 40, 0, 150))
        screen.blit(bg_surf, (box_x, box_y))

        sx = box_x + pad_x
        sy = box_y + box_h - pad_y - 6
        ex = sx + scale_bar_px

        pygame.draw.line(screen, (0, 255, 0), (sx, sy), (ex, sy), 4)
        pygame.draw.line(screen, (0, 255, 0), (sx, sy - 8), (sx, sy + 8), 3)
        pygame.draw.line(screen, (0, 255, 0), (ex, sy - 8), (ex, sy + 8), 3)

        lbl = font.render(distance_text, True, (0, 255, 0))
        screen.blit(lbl, (sx, box_y + 5))

        pygame.display.flip()

        # ----------------------------------------------------------
        # EVENTS
        # ----------------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:  # press "I" to toggle invert
                    invert_enabled = not invert_enabled

            elif event.type == pygame.VIDEORESIZE:
                screen_w, screen_h = event.size
                screen = pygame.display.set_mode((screen_w, screen_h), pygame.RESIZABLE)

            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                zoom_change = 1 if event.y > 0 else -1
                new_target_zoom = max(MIN_ZOOM, min(MAX_ZOOM, target_zoom + zoom_change))
                zoom_ratio = 2 ** (new_target_zoom - target_zoom)

                target_offset_x = mx - zoom_ratio * (mx - target_offset_x)
                target_offset_y = my - zoom_ratio * (my - target_offset_y)

                target_zoom = new_target_zoom
                target_offset_x, target_offset_y = clamp_offset(
                    target_offset_x, target_offset_y, tiles, screen_w, screen_h,
                    zoom_scale=new_target_zoom / current_zoom
                )

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dragging = True
                drag_start = event.pos
                drag_offset_start = (target_offset_x, target_offset_y)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False

            elif event.type == pygame.MOUSEMOTION and dragging:
                dx = event.pos[0] - drag_start[0]
                dy = event.pos[1] - drag_start[1]

                target_offset_x = drag_offset_start[0] + dx
                target_offset_y = drag_offset_start[1] + dy

                target_offset_x, target_offset_y = clamp_offset(
                    target_offset_x, target_offset_y, tiles, screen_w, screen_h,
                    zoom_scale=zoom_float / current_zoom
                )

        # ----------------------------------------------------------
        # SMOOTH ZOOM & PAN
        # ----------------------------------------------------------
        offset_x = lerp(offset_x, target_offset_x, SMOOTH_SPEED)
        offset_y = lerp(offset_y, target_offset_y, SMOOTH_SPEED)

        zoom_float = lerp(zoom_float, target_zoom, SMOOTH_SPEED)
        zoom_float = max(MIN_ZOOM, min(MAX_ZOOM, zoom_float))

        new_zoom_int = int(round(zoom_float))
        if new_zoom_int != current_zoom:
            new_tiles = load_tiles(new_zoom_int)
            if new_tiles:
                tiles = new_tiles
                scaled_tiles_cache.clear()
                current_zoom = new_zoom_int

        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
