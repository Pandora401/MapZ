import os
import pygame
import numpy as np

TILE_DIR = "tiles"
TILE_SIZE = 256
START_ZOOM = 2
MIN_ZOOM = 4
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
# Window class for floating UI panels with a title bar
# ----------------------------------------------------------
class FloatingWindow:
    def __init__(self, rect: pygame.Rect, title: str, title_height=28, rounded=6):
        self.rect = rect
        self.title = title
        self.title_height = title_height
        self.dragging = False
        self.drag_offset = (0, 0)
        self.rounded = rounded
        self.visible = True

    @property
    def title_bar_rect(self):
        return pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.title_height)

    def handle_event_down(self, event_pos):
        """Return True if event consumed (clicked on titlebar)."""
        if self.title_bar_rect.collidepoint(event_pos):
            self.dragging = True
            self.drag_offset = (event_pos[0] - self.rect.x, event_pos[1] - self.rect.y)
            return True
        return False

    def handle_event_up(self, event_pos):
        self.dragging = False

    def handle_drag(self, event_pos, screen_w, screen_h):
        if self.dragging:
            nx = event_pos[0] - self.drag_offset[0]
            ny = event_pos[1] - self.drag_offset[1]
            # Keep window on-screen (simple clamp)
            nx = max(0, min(nx, screen_w - self.rect.width))
            ny = max(0, min(ny, screen_h - self.rect.height))
            self.rect.topleft = (nx, ny)

    def draw(self, surface, font):
        # Draw window background (under title + content). Content area may be semi-transparent drawn later.
        pygame.draw.rect(surface, (36, 36, 36), self.rect, border_radius=self.rounded)
        # Title bar (opaque)
        tb = self.title_bar_rect
        pygame.draw.rect(surface, (220, 220, 220), tb, border_radius=self.rounded)
        # mac-like circles on left
        circle_y = tb.y + tb.height // 2
        circle_x = tb.x + 12
        pygame.draw.circle(surface, (255, 96, 92), (circle_x, circle_y), 6)  # red
        pygame.draw.circle(surface, (255, 189, 46), (circle_x + 16, circle_y), 6)  # yellow
        pygame.draw.circle(surface, (39, 201, 63), (circle_x + 32, circle_y), 6)  # green
        # Title text centered vertically in title bar
        text = font.render(self.title, True, (10, 10, 10))
        surface.blit(text, (tb.x + 60, tb.y + (tb.height - text.get_height()) // 2))

# ----------------------------------------------------------
# Create a marker surface (Pygame-drawn "pin")
# ----------------------------------------------------------
def create_marker_surface(size=32):
    """Return a surface with a pin-like marker drawn (filled)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = size // 2
    # draw outer teardrop (triangle-like tail + circle top)
    # tail (triangle)
    tail_height = size // 3
    pygame.draw.polygon(surf, (200, 20, 20), [
        (cx, size - 1),
        (cx - size//6, size//2 + 4),
        (cx + size//6, size//2 + 4)
    ])
    # circle head
    pygame.draw.circle(surf, (220, 60, 60), (cx, size//3), size//4)
    # inner circle
    pygame.draw.circle(surf, (255, 190, 190), (cx, size//3), size//8)
    return surf

# ----------------------------------------------------------
# MAIN
# ----------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_w, screen_h = screen.get_size()
    pygame.display.set_caption("DayZ Tile Dashboard - Floating Windows with Markers")

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
    zoom_float = target_zoom = float(current_zoom)
    dragging_map = False
    drag_start = drag_offset_start = (0, 0)

    # Invert toggle
    invert_enabled = True
    invert_large = True  # Which map starts inverted

    # Log system
    # Now entries store: (x_tile_float, y_tile_float, zoom_at_save (float), comment)
    log_entries = []  # list of tuples described above
    markers = []      # list of dicts: {"x":..., "y":..., "zoom":..., "id":..., "comment":...}
    current_comment = ""
    typing_comment = False
    entry_rects = []

    # Log window transparency
    LOG_BG_ALPHA = 150  # semi-transparent alpha 0-255

    # Load centered logo for log panel (Option 1: do not scale)
    log_bg_img = None
    log_bg_path = "Assets/Icons/unit2800.png"
    if os.path.exists(log_bg_path):
        try:
            log_bg_img = pygame.image.load(log_bg_path).convert_alpha()
        except Exception as e:
            print(f"Failed to load log background image '{log_bg_path}': {e}")
            log_bg_img = None
    else:
        print(f"Log background image not found at '{log_bg_path}'. Continuing without image.")

    # Marker surface
    marker_surf = create_marker_surface(36)
    marker_anchor = (marker_surf.get_width() // 2, marker_surf.get_height() - 2)  # anchor so marker bottom sits on coordinate

    clock = pygame.time.Clock()
    running = True

    # Full-screen large map rect
    large_rect = pygame.Rect(0, 0, screen_w, screen_h)

    # Create floating windows (small map + log panel)
    small_w, small_h = int(screen_w * 0.28), int(screen_h * 0.28)
    small_window = FloatingWindow(pygame.Rect(screen_w - small_w - 40, 60, small_w, small_h), "FIR [IR] 1,000μm")

    # Smaller log panel (user requested smaller)
    log_w, log_h = int(screen_w * 0.22), int(screen_h * 0.20)  # smaller
    log_window = FloatingWindow(pygame.Rect(40, 60, log_w, log_h), "Log Panel")

    windows = [small_window, log_window]

    active_window = None  # the window currently being dragged (if any)

    while running:
        screen.fill((50, 50, 50))  # Background (behind the map if wanted)
        zoom_scale = zoom_float / current_zoom

        # -----------------------
        # Render large map (full screen)
        # -----------------------
        def render_map(surface_rect, show_hud=True, inverted=False):
            map_surface = pygame.Surface(surface_rect.size)
            map_surface.fill((70, 70, 70))
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
                        key = (x, y, int(zoom_float * 100))
                        if (x, y) in tiles:
                            if key not in scaled_tiles_cache:
                                scaled_tiles_cache[key] = pygame.transform.smoothscale(
                                    tiles[(x, y)],
                                    (int(TILE_SIZE * zoom_scale), int(TILE_SIZE * zoom_scale))
                                )
                            map_surface.blit(scaled_tiles_cache[key], (px, py))
                        else:
                            rect = pygame.Rect(px, py, int(TILE_SIZE * zoom_scale), int(TILE_SIZE * zoom_scale))
                            pygame.draw.rect(map_surface, (70, 70, 70), rect)
                if show_hud:
                    # Dotted grid
                    for x in range(start_x, end_x + 1):
                        px = int(x * TILE_SIZE * zoom_scale + target_offset_x)
                        draw_dotted_line(map_surface, (0, 0, 0), (px, 0), (px, surface_rect.height))
                    for y in range(start_y, end_y + 1):
                        py = int(y * TILE_SIZE * zoom_scale + target_offset_y)
                        draw_dotted_line(map_surface, (0, 0, 0), (0, py), (surface_rect.width, py))
            if inverted:
                arr = pygame.surfarray.pixels3d(map_surface)
                np.subtract(255, arr, out=arr)
                gray = arr.mean(axis=2, keepdims=True).astype(np.uint8)
                arr[:] = gray
                del arr
            return map_surface

        large_map = render_map(
            large_rect, show_hud=True, 
            # inverted=invert_enabled 
            #     if invert_large 
            #     else not invert_enabled
            )

        # Crosshair in center of large_map
        cross_x = large_rect.width // 2
        cross_y = large_rect.height // 2
        box_size = 50
        pygame.draw.line(large_map, (255, 0, 0), (cross_x - box_size, cross_y - box_size), (cross_x + box_size, cross_y - box_size), 2)
        pygame.draw.line(large_map, (255, 0, 0), (cross_x - box_size, cross_y + box_size), (cross_x + box_size, cross_y + box_size), 2)
        pygame.draw.line(large_map, (255, 0, 0), (cross_x - box_size, cross_y - box_size), (cross_x - box_size, cross_y + box_size), 2)
        pygame.draw.line(large_map, (255, 0, 0), (cross_x + box_size, cross_y - box_size), (cross_x + box_size, cross_y + box_size), 2)

        # Coordinate overlay on large_map
        map_x = (cross_x - target_offset_x) / (TILE_SIZE * zoom_scale)
        map_y = (cross_y - target_offset_y) / (TILE_SIZE * zoom_scale)
        arrow_text = small_font.render(">", True, (255, 255, 0))
        coord_text = small_font.render(f"X:{map_x:.2f}", True, (255, 0, 0))
        coord_text2 = small_font.render(f"Y:{map_y:.2f}", True, (255, 0, 0))
        large_map.blit(arrow_text, (cross_x + 2, cross_y - 15))
        large_map.blit(coord_text, (cross_x + 15, cross_y - 15))
        large_map.blit(coord_text2, (cross_x + 15, cross_y))

        # blit the full-screen large_map to screen at (0,0)
        screen.blit(large_map, large_rect.topleft)

        # -----------------------
        # Draw markers on the main map (use same math as render_map)
        # -----------------------
        # We draw markers after the map so they appear above tiles.
        for m in markers:
            # compute pixel position using current zoom_float/current_zoom and target_offset_x/y
            px = int(m["x"] * TILE_SIZE * (zoom_float / current_zoom) + target_offset_x)
            py = int(m["y"] * TILE_SIZE * (zoom_float / current_zoom) + target_offset_y)
            # anchor the marker so its bottom center sits at px,py
            blit_x = px - marker_anchor[0]
            blit_y = py - marker_anchor[1]
            screen.blit(marker_surf, (blit_x, blit_y))

        # -----------------------
        # Draw floating windows (small map + log)
        # -----------------------
        # Draw windows in z-order (log first, then small map so small map can overlap)
        for w in windows:
            # Background content surface for the window contents (below title bar)
            content_surface = pygame.Surface((w.rect.width, w.rect.height - w.title_height), pygame.SRCALPHA)
            # Fill content depending on window
            if w is small_window:
                # Render the mini-map into the content surface
                mini_rect = pygame.Rect(0, 0, content_surface.get_width(), content_surface.get_height())
                mini_map = render_map(
                    mini_rect, 
                    show_hud=False, 
                    inverted=invert_enabled 
                        # if not invert_large 
                        # else not invert_enabled
                    )
                # draw crosshair at center of mini_map
                cx = mini_rect.width // 2
                cy = mini_rect.height // 2
                pygame.draw.line(mini_map, (255, 0, 0), (cx - 10, cy), (cx + 10, cy), 2)
                pygame.draw.line(mini_map, (255, 0, 0), (cx, cy - 10), (cx, cy + 10), 2)
                pygame.draw.circle(mini_map, (255, 0, 0), (cx, cy), 12, 1)

                # draw markers onto the mini_map as well (same coordinate math)
                for m in markers:
                    px = int(m["x"] * TILE_SIZE * (zoom_float / current_zoom) + target_offset_x)
                    py = int(m["y"] * TILE_SIZE * (zoom_float / current_zoom) + target_offset_y)
                    # mini_map is rendered into content_surface coords, so px/py are directly usable here
                    # But only blit if inside mini_map bounds
                    if 0 <= px < mini_rect.width and 0 <= py < mini_rect.height:
                        blit_x = px - marker_anchor[0]
                        blit_y = py - marker_anchor[1]
                        mini_map.blit(marker_surf, (blit_x, blit_y))

                content_surface.blit(mini_map, (0, 0))
            elif w is log_window:
                # Render the log entries inside the content area
                # Semi-transparent background fill for content area (same alpha to be used also on image)
                content_surface.fill((0, 0, 0, LOG_BG_ALPHA))

                # Center the image (Option 1: no scaling)
                if log_bg_img:
                    try:
                        img_copy = log_bg_img.copy()
                        img_copy.set_alpha(LOG_BG_ALPHA)
                        img_x = (content_surface.get_width() // 2) - (img_copy.get_width() // 2)
                        img_y = (content_surface.get_height() // 2) - (img_copy.get_height() // 2)
                        content_surface.blit(img_copy, (img_x, img_y))
                    except Exception as e:
                        print(f"Error drawing log bg image: {e}")

                # Draw log text entries above background+image
                entry_y = 8
                entry_h = 18
                mx, my = pygame.mouse.get_pos()
                # Convert global mouse to window-local coords
                local_mx = mx - w.rect.x
                local_my = my - w.rect.y - w.title_height
                entry_rects.clear()
                # show last ~10 entries to keep it compact
                for idx, (x_val, y_val, z_val, comment) in enumerate(log_entries[-10:]):
                    text_surf = small_font.render(f"X:{x_val:.2f} Y:{y_val:.2f} Z:{z_val:.2f} {comment}", True, (230, 230, 230))
                    rect = pygame.Rect(8, entry_y, content_surface.get_width() - 16, entry_h)
                    content_surface.blit(text_surf, (rect.x, rect.y))
                    # store global rect for clicking (map to screen coords)
                    global_rect = pygame.Rect(rect.x + w.rect.x, rect.y + w.rect.y + w.title_height, rect.width, rect.height)
                    entry_rects.append((global_rect, x_val, y_val, z_val, comment))
                    entry_y += entry_h + 4

                # Typing area at bottom
                if typing_comment:
                    prompt = small_font.render("> " + (current_comment if current_comment else "Write comment"), True, (255, 255, 0))
                    content_surface.blit(prompt, (8, content_surface.get_height() - 24))

            # Blit window background + title bar onto screen
            w.draw(screen, font)
            # Blit the content surface (this will include semi-transparent fill)
            screen.blit(content_surface, (w.rect.x, w.rect.y + w.title_height))

        # Mouse pointer handling (change cursor when over titlebar or entries)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        cursor = pygame.SYSTEM_CURSOR_ARROW
        for w in windows:
            if w.title_bar_rect.collidepoint((mouse_x, mouse_y)):
                cursor = pygame.SYSTEM_CURSOR_HAND
                break
        # If hovering a log entry
        for rect, x_val, y_val, z_val, comment in entry_rects:
            if rect.collidepoint((mouse_x, mouse_y)):
                cursor = pygame.SYSTEM_CURSOR_HAND
                break
        pygame.mouse.set_system_cursor(cursor)

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
                        # Add log entry with map center coords AND save zoom
                        saved_x = map_x
                        saved_y = map_y
                        saved_zoom = zoom_float
                        log_entries.append((saved_x, saved_y, saved_zoom, current_comment))
                        # Create a marker for this entry
                        markers.append({
                            "x": saved_x,
                            "y": saved_y,
                            "zoom": saved_zoom,
                            "comment": current_comment
                        })
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
                # First: check windows title bars (topmost first)
                clicked_on_window = False
                # iterate windows from top to bottom (reverse list so last drawn is top)
                for w in reversed(windows):
                    if w.handle_event_down((mx, my)):
                        active_window = w
                        clicked_on_window = True
                        # bring this window to top of z-order
                        windows.remove(w)
                        windows.append(w)
                        break

                if clicked_on_window:
                    # clicked a title bar -> do not start map drag
                    dragging_map = False
                else:
                    # Next: check if clicked inside any window content (not titlebar)
                    clicked_in_content = False
                    for w in reversed(windows):
                        if w.rect.collidepoint((mx, my)):
                            # clicked inside content, but not titlebar
                            clicked_in_content = True
                            # If it's the log window, check for entry clicks
                            if w is log_window:
                                # check entry rects (global coords)
                                for rect, x_val, y_val, z_val, comment in entry_rects:
                                    if rect.collidepoint((mx, my)):
                                        # center large map on this entry using saved zoom
                                        saved_x = x_val
                                        saved_y = y_val
                                        saved_zoom = z_val
                                        # set the target zoom and compute offsets so saved point becomes center
                                        target_zoom = saved_zoom
                                        # compute offset that will put saved_x/saved_y at center
                                        # use current 'current_zoom' to compute clamp correctly (clamp expects zoom_scale = new_target_zoom/current_zoom)
                                        target_offset_x = large_rect.width / 2 - (saved_x * TILE_SIZE * (target_zoom / current_zoom))
                                        target_offset_y = large_rect.height / 2 - (saved_y * TILE_SIZE * (target_zoom / current_zoom))
                                        # clamp offsets for that zoom
                                        target_offset_x, target_offset_y = clamp_offset(target_offset_x, target_offset_y, tiles, large_rect.width, large_rect.height, target_zoom / current_zoom)
                                        break
                            break

                    if not clicked_in_content:
                        # Start dragging the main map
                        dragging_map = large_rect.collidepoint((mx, my))
                        if dragging_map:
                            drag_start = event.pos
                            drag_offset_start = (target_offset_x, target_offset_y)
                            active_window = None

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # release any window dragging
                for w in windows:
                    w.handle_event_up(event.pos)
                active_window = None
                dragging_map = False

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                # If a window is dragging, move it
                for w in windows:
                    w.handle_drag((mx, my), screen_w, screen_h)
                # If dragging the map, pan
                if dragging_map:
                    dx = event.pos[0] - drag_start[0]
                    dy = event.pos[1] - drag_start[1]
                    target_offset_x = drag_offset_start[0] + dx
                    target_offset_y = drag_offset_start[1] + dy
                    target_offset_x, target_offset_y = clamp_offset(target_offset_x, target_offset_y, tiles, large_rect.width, large_rect.height, zoom_float / current_zoom)

            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                zoom_change = 1 if event.y > 0 else -1
                new_target_zoom = max(MIN_ZOOM, min(MAX_ZOOM, target_zoom + zoom_change))
                # compute zoom ratio relative to current target_zoom
                zoom_ratio = 2 ** (new_target_zoom - target_zoom) if new_target_zoom != target_zoom else 1.0
                # adjust offsets so zoom is centered on mouse pos
                target_offset_x = mx - zoom_ratio * (mx - target_offset_x)
                target_offset_y = my - zoom_ratio * (my - target_offset_y)
                target_zoom = new_target_zoom
                target_offset_x, target_offset_y = clamp_offset(target_offset_x, target_offset_y, tiles, large_rect.width, large_rect.height, new_target_zoom / current_zoom)

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
