import os
import pygame
import numpy as np

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

# ----------------------------------------------------------
# HELPERS
# ----------------------------------------------------------
def lerp(a, b, t):
    return a + (b - a) * t

def clamp_offset(offset_x, offset_y, tiles, viewport_w, viewport_h, zoom_scale=1.0):
    if not tiles:
        return offset_x, offset_y
    xs = [x for x, y in tiles.keys()]
    ys = [y for x, y in tiles.keys()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    map_w = (max_x - min_x + 1) * TILE_SIZE * zoom_scale
    map_h = (max_y - min_y + 1) * TILE_SIZE * zoom_scale
    max_x_off = -min_x * TILE_SIZE * zoom_scale
    min_x_off = viewport_w - ((max_x + 1) * TILE_SIZE * zoom_scale)
    max_y_off = -min_y * TILE_SIZE * zoom_scale
    min_y_off = viewport_h - ((max_y + 1) * TILE_SIZE * zoom_scale)
    return max(min_x_off, min(max_x_off, offset_x)), max(min_y_off, min(max_y_off, offset_y))

# ----------------------------------------------------------
# MAIN
# ----------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    screen_w, screen_h = screen.get_size()
    pygame.display.set_caption("DayZ Tile Dashboard")

    # Fonts
    try:
        font = pygame.font.SysFont("OCR A Extended", 18, bold=True)
    except:
        font = pygame.font.SysFont("Consolas", 18, bold=True)
    small_font = pygame.font.SysFont("Consolas", 14, bold=True)

    current_zoom = START_ZOOM
    tiles = load_tiles(current_zoom)
    scaled_tiles_cache = {}

    # Offsets and zoom
    offset_x = offset_y = target_offset_x = target_offset_y = 0.0
    zoom_float = target_zoom = current_zoom
    dragging = False
    drag_start = drag_offset_start = (0, 0)

    # Invert toggle
    invert_enabled = False
    invert_large = True  # Which map starts inverted

    # Log system
    log_entries = []  # list of (x, y, comment)
    current_comment = ""
    typing_comment = False
    entry_rects = []

    clock = pygame.time.Clock()
    running = True

    # Define map viewports
    large_rect = pygame.Rect(0, 0, int(screen_w*0.7), int(screen_h*0.7))
    small_w, small_h = int(screen_w*0.28), int(screen_h*0.28)
    small_rect = pygame.Rect(screen_w-small_w, screen_h-small_h, small_w, small_h)
    log_rect = pygame.Rect(screen_w*0.7, 0, screen_w*0.3, screen_h*0.7)
    bottom_left_rect = pygame.Rect(0, screen_h*0.7, screen_w*0.7, screen_h*0.3)  # blank for now

    while running:
        screen.fill((50,50,50))  # Dashboard background

        zoom_scale = zoom_float / current_zoom

        # -----------------------
        # Render maps
        # -----------------------
        def render_map(surface_rect, show_hud=True, inverted=False):
            map_surface = pygame.Surface(surface_rect.size)
            map_surface.fill((70,70,70))
            if tiles:
                xs = [x for x, y in tiles.keys()]
                ys = [y for x, y in tiles.keys()]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                start_x = max(min_x, int(-target_offset_x / (TILE_SIZE * zoom_scale)))
                end_x = min(max_x, int((surface_rect.width - target_offset_x) / (TILE_SIZE * zoom_scale)) + 1)
                start_y = max(min_y, int(-target_offset_y / (TILE_SIZE * zoom_scale)))
                end_y = min(max_y, int((surface_rect.height - target_offset_y) / (TILE_SIZE * zoom_scale)) + 1)
                for x in range(start_x, end_x + 1):
                    for y in range(start_y, end_y + 1):
                        px = int(x * TILE_SIZE * zoom_scale + target_offset_x)
                        py = int(y * TILE_SIZE * zoom_scale + target_offset_y)
                        key = (x, y, int(zoom_float*100))
                        if (x, y) in tiles:
                            if key not in scaled_tiles_cache:
                                scaled_tiles_cache[key] = pygame.transform.smoothscale(
                                    tiles[(x,y)],
                                    (int(TILE_SIZE*zoom_scale), int(TILE_SIZE*zoom_scale))
                                )
                            map_surface.blit(scaled_tiles_cache[key], (px, py))
                        else:
                            rect = pygame.Rect(px, py, int(TILE_SIZE*zoom_scale), int(TILE_SIZE*zoom_scale))
                            pygame.draw.rect(map_surface, (70,70,70), rect)
                if show_hud:
                    # Dotted grid
                    for x in range(start_x, end_x+1):
                        px = int(x * TILE_SIZE * zoom_scale + target_offset_x)
                        draw_dotted_line(map_surface, (0,0,0), (px,0), (px,surface_rect.height))
                    for y in range(start_y, end_y+1):
                        py = int(y * TILE_SIZE * zoom_scale + target_offset_y)
                        draw_dotted_line(map_surface, (0,0,0), (0,py), (surface_rect.width,py))
            if inverted:
                arr = pygame.surfarray.pixels3d(map_surface)
                np.subtract(255, arr, out=arr)
                gray = arr.mean(axis=2, keepdims=True).astype(np.uint8)
                arr[:] = gray
                del arr
            return map_surface

        # Large map
        large_map = render_map(large_rect, show_hud=True, inverted=invert_enabled if invert_large else not invert_enabled)
        cross_x = large_rect.width // 2
        cross_y = large_rect.height // 2
        box_size = 50  # half-width/height of the box
        gap = 10       # gap at corners

        # Top horizontal line
        pygame.draw.line(large_map, (255,0,0,20), (cross_x - box_size, cross_y - box_size), (cross_x + box_size, cross_y - box_size), 2)
        # Bottom horizontal line
        pygame.draw.line(large_map, (255,0,0,20), (cross_x - box_size, cross_y + box_size), (cross_x + box_size, cross_y + box_size), 2)
        # Left vertical line
        pygame.draw.line(large_map, (255,0,0,20), (cross_x - box_size, cross_y - box_size), (cross_x - box_size, cross_y + box_size), 2)
        # Right vertical line
        pygame.draw.line(large_map, (255,0,0,20), (cross_x + box_size, cross_y - box_size), (cross_x + box_size, cross_y + box_size), 2)
        # Coordinates
        map_x = (cross_x - target_offset_x) / (TILE_SIZE * zoom_scale)
        map_y = (cross_y - target_offset_y) / (TILE_SIZE * zoom_scale)
        # Render
        arrow_text = small_font.render(">", True, (255, 255, 0))
        coord_text = small_font.render(f"X:{map_x:.2f}", True, (255,0,0))
        coord_text2 = small_font.render(f"Y:{map_y:.2f}", True, (255,0,0))
        large_map.blit(arrow_text, (cross_x + 2, cross_y - 15))
        large_map.blit(coord_text, (cross_x + 15, cross_y - 15))
        large_map.blit(coord_text2, (cross_x + 15, cross_y))
        screen.blit(large_map, large_rect.topleft)

                
        # Small map
        small_map = render_map(small_rect, show_hud=False, inverted=invert_enabled if not invert_large else not invert_enabled)
        # Red crosshair
        cross_x = small_rect.width // 2
        cross_y = small_rect.height // 2
        pygame.draw.line(small_map, (255,0,0), (cross_x - 10, cross_y), (cross_x + 10, cross_y), 2)
        pygame.draw.line(small_map, (255,0,0), (cross_x, cross_y - 10), (cross_x, cross_y + 10), 2)
        pygame.draw.circle(small_map, (255,0,0), (cross_x, cross_y), 12, 1)
        # Coordinates
        map_x = (cross_x - target_offset_x) / (TILE_SIZE * zoom_scale)
        map_y = (cross_y - target_offset_y) / (TILE_SIZE * zoom_scale)
        # Render
        arrow_text = small_font.render(">", True, (255, 255, 0))
        coord_text = small_font.render(f"X:{map_x:.2f}", True, (255,0,0))
        coord_text2 = small_font.render(f"Y:{map_y:.2f}", True, (255,0,0))
        small_map.blit(arrow_text, (cross_x + 2, cross_y - 15))
        small_map.blit(coord_text, (cross_x + 15, cross_y - 15))
        small_map.blit(coord_text2, (cross_x + 15, cross_y))
        screen.blit(small_map, small_rect.topleft)

        # -----------------------
        # Render log (top right)
        # -----------------------
        entry_rects.clear()
        log_y = 5
        log_line_height = 20
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for x_val, y_val, comment in log_entries[-30:]:
            entry_text_color = (255,255,255)
            entry_font = font
            rect = font.render(f"X:{x_val:.2f} Y:{y_val:.2f} {comment}", True, entry_text_color).get_rect(topleft=(log_rect.x + 5, log_y))

            # Hover effect
            if rect.collidepoint(mouse_x, mouse_y):
                entry_font.set_underline(True)
                pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                entry_font.set_underline(False)
                pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_ARROW)

            # Render
            entry_text = entry_font.render(f"X:{x_val:.2f} Y:{y_val:.2f} {comment}", True, entry_text_color)
            screen.blit(entry_text, rect.topleft)
            entry_rects.append((rect, x_val, y_val))
            log_y += log_line_height


        # Typing
        if typing_comment:
            arrow_text = font.render(">", True, (255,255,0))
            if current_comment:
                display_text = current_comment
                text_color = (255,255,0)
            else:
                display_text = " Write comment"
                text_color = (100,100,100)
            comment_text = font.render(display_text, True, text_color)
            screen.blit(arrow_text, (log_rect.x + 5, log_y))
            screen.blit(comment_text, (log_rect.x + 20, log_y))

        pygame.display.flip()

        # -----------------------
        # EVENTS
        # -----------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:
                    invert_large = not invert_large
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN:
                    if typing_comment:
                        log_entries.append((map_x, map_y, current_comment))
                        current_comment = ""
                        typing_comment = False
                    else:
                        typing_comment = True
                elif typing_comment:
                    if event.key == pygame.K_BACKSPACE:
                        current_comment = current_comment[:-1]
                    else:
                        current_comment += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # Drag map
                dragging = large_rect.collidepoint(mx, my)
                drag_start = event.pos
                drag_offset_start = (target_offset_x, target_offset_y)
                # Check clicks on log
                for rect, x_val, y_val in entry_rects:
                    if rect.collidepoint(mx, my):
                        target_offset_x = large_rect.width/2 - x_val*TILE_SIZE*zoom_float/current_zoom
                        target_offset_y = large_rect.height/2 - y_val*TILE_SIZE*zoom_float/current_zoom
                        target_offset_x, target_offset_y = clamp_offset(target_offset_x, target_offset_y, tiles, large_rect.width, large_rect.height, zoom_float/current_zoom)
                        break

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False

            elif event.type == pygame.MOUSEMOTION and dragging:
                dx = event.pos[0] - drag_start[0]
                dy = event.pos[1] - drag_start[1]
                target_offset_x = drag_offset_start[0] + dx
                target_offset_y = drag_offset_start[1] + dy
                target_offset_x, target_offset_y = clamp_offset(target_offset_x, target_offset_y, tiles, large_rect.width, large_rect.height, zoom_float/current_zoom)

            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                zoom_change = 1 if event.y > 0 else -1
                new_target_zoom = max(MIN_ZOOM, min(MAX_ZOOM, target_zoom + zoom_change))
                zoom_ratio = 2 ** (new_target_zoom - target_zoom)
                target_offset_x = mx - zoom_ratio * (mx - target_offset_x)
                target_offset_y = my - zoom_ratio * (my - target_offset_y)
                target_zoom = new_target_zoom
                target_offset_x, target_offset_y = clamp_offset(target_offset_x, target_offset_y, tiles, large_rect.width, large_rect.height, new_target_zoom/current_zoom)

        # -----------------------
        # SMOOTH ZOOM & PAN
        # -----------------------
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
