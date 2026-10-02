import cv2
import mediapipe as mp
import pygame
import pygame.gfxdraw
import math
import random

# ==========================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN
# ==========================================
pygame.init()
WIDTH, HEIGHT = 900, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gestos Holográficos HUD Pro")
clock = pygame.time.Clock()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.75, min_tracking_confidence=0.75)
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

NUM_PARTICLES = 1600

# ==========================================
# 2. GENERADORES DE FIGURAS 2D (DEDO 0, 1 y 4)
# ==========================================

# --- DEDO 0: CORAZÓN ---
def get_heart_offsets(num_points, scale=12):
    offsets = []
    for _ in range(num_points):
        t = random.uniform(0, math.pi * 2)
        x = 16 * (math.sin(t) ** 3)
        y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
        espesor = random.uniform(0.7, 1.1)
        offsets.append((int(x * scale * espesor), -int(y * scale * espesor)))
    return offsets

# --- DEDO 1: TEXTO "I LOVE YOU" ---
def get_text_offsets(text, num_points):
    try:
        font = pygame.font.SysFont("Arial Black", 75)
    except:
        font = pygame.font.SysFont("Arial", 75, bold=True)
    text_surface = font.render(text, True, (255, 255, 255), (0, 0, 0))
    tw, th = text_surface.get_size()
    valid_pixels = [(x - tw // 2, y - th // 2) for x in range(0, tw, 2) for y in range(0, th, 2) if text_surface.get_at((x, y))[0] > 120]
    return [random.choice(valid_pixels) for _ in range(num_points)] if valid_pixels else [(0,0)]*num_points

# --- DEDO 4: DINOSAURIO (T-REX) ---
def get_dino_offsets(num_points, scale=9):
    dino_ascii = [
        "                 XXXXXXX",
        "                XXXXXXXX",
        "                XX XXXXX",
        "                XXXXXXXX",
        "                XXXXX   ",
        "       X        XXXXX   ",
        "      XX       XXXXXX XX",
        "     XXX      XXXXXXXXXX",
        "    XXXX     XXXXXXXXXXX",
        "    XXXXX   XXXXXXXXXXXX",
        "     XXXXXXXXXXXXXXXXXX ",
        "      XXXXXXXXXXXXXXXX  ",
        "        XXXXXXXXXXXX    ",
        "         XXXXXXXXX      ",
        "          XXXXXX        ",
        "          XX  XX        ",
        "          XX  XX        ",
        "          X    X        ",
        "         XX    XX       "
    ]
    valid_pixels = []
    for y, row in enumerate(dino_ascii):
        for x, char in enumerate(row):
            if char == 'X':
                valid_pixels.append(((x - 12) * scale, (y - 10) * scale))
    return [random.choice(valid_pixels) for _ in range(num_points)] if valid_pixels else [(0,0)]*num_points

heart_offsets = get_heart_offsets(NUM_PARTICLES)
text_offsets = get_text_offsets("I LOVE YOU", NUM_PARTICLES)
dino_offsets = get_dino_offsets(NUM_PARTICLES)

# ==========================================
# 3. CLASE DE PARTÍCULAS
# ==========================================
class Particle:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)
        self.vx = 0
        self.vy = 0
        
        # Geometría 3D Esférica
        self.sphere_theta = random.uniform(0, 2 * math.pi)
        self.sphere_phi = math.acos(random.uniform(-1, 1))
        
        # Júpiter
        self.jupiter_radius = random.uniform(45, 75)
        self.is_ring = random.random() < 0.38
        self.ring_angle = random.uniform(0, 2 * math.pi)
        self.ring_radius = random.uniform(95, 145)
        
        # Tierra
        self.earth_radius = random.uniform(50, 80)

    def move_to(self, tx, ty, speed=0.09, friction=0.84):
        self.vx += (tx - self.x) * speed
        self.vy += (ty - self.y) * speed
        self.vx *= friction
        self.vy *= friction
        self.x += self.vx
        self.y += self.vy

particles = [Particle() for _ in range(NUM_PARTICLES)]

# ==========================================
# 4. DETECTOR DE DEDOS
# ==========================================
def count_fingers(hand_landmarks):
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    count = 0
    
    thumb_tip = hand_landmarks.landmark[4]
    pinky_base = hand_landmarks.landmark[17]
    if math.hypot(thumb_tip.x - pinky_base.x, thumb_tip.y - pinky_base.y) > 0.28:
        count += 1
        
    for tip, pip in zip(tips, pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            count += 1
    return count

# ==========================================
# 5. DIBUJADO DE HUD MODERNO (DEDOS: X)
# ==========================================
font_hud_num = pygame.font.SysFont("Impact", 36)
font_hud_lbl = pygame.font.SysFont("Arial Black", 14)

def draw_cool_hud(surface, finger_count):
    # Crear tarjeta con transparencia
    hud_bg = pygame.Surface((150, 60), pygame.SRCALPHA)
    pygame.draw.rect(hud_bg, (15, 20, 35, 210), (0, 0, 150, 60), border_radius=12)
    pygame.draw.rect(hud_bg, (0, 220, 255, 180), (0, 0, 150, 60), width=2, border_radius=12)
    pygame.draw.rect(hud_bg, (0, 220, 255, 255), (0, 0, 6, 60), border_top_left_radius=12, border_bottom_left_radius=12)
    
    # Texto
    lbl = font_hud_lbl.render("DEDOS", True, (160, 200, 230))
    num = font_hud_num.render(f"{finger_count}", True, (255, 255, 255))
    
    hud_bg.blit(lbl, (20, 10))
    hud_bg.blit(num, (85, 12))
    
    surface.blit(hud_bg, (25, 25))

# ==========================================
# 6. BUCLE PRINCIPAL
# ==========================================
running = True
time_step = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    finger_count = 5
    hand_x, hand_y = WIDTH // 2, HEIGHT // 2

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            finger_count = count_fingers(hand_landmarks)
            hand_x = int(hand_landmarks.landmark[8].x * WIDTH)
            hand_y = int(hand_landmarks.landmark[8].y * HEIGHT)

    cv2.imshow("Camara", frame)
    screen.fill((8, 10, 16)) # Fondo espacio profundo
    time_step += 0.025

    # --- PROCESAMIENTO DE PARTÍCULAS ---
    for i, p in enumerate(particles):
        size = 2
        
        # DEDO 0 (PUÑO): CORAZÓN
        if finger_count == 0:
            ox, oy = heart_offsets[i]
            tx, ty = hand_x + ox, hand_y + oy
            color = (255, 50, 110)
            p.move_to(tx, ty, speed=0.08)

        # DEDO 1: I LOVE YOU
        elif finger_count == 1:
            ox, oy = text_offsets[i]
            tx, ty = hand_x + ox, hand_y + oy
            color = (0, 230, 255)
            p.move_to(tx, ty, speed=0.14, friction=0.80)

        # DEDO 2: JÚPITER 3D PREMIUM
        elif finger_count == 2:
            rotation = time_step * 1.4
            tilt = 0.35 # Inclinación orbital
            
            if p.is_ring:
                raw_x = p.ring_radius * math.cos(p.ring_angle + rotation)
                raw_z = p.ring_radius * math.sin(p.ring_angle + rotation)
                tx = hand_x + raw_x
                ty = hand_y + (raw_z * tilt)
                
                # Brillo de los anillos
                brightness = int(180 + (raw_z / p.ring_radius) * 75)
                color = (min(255, brightness + 40), min(255, brightness + 10), max(0, brightness - 80))
            else:
                x3d = p.jupiter_radius * math.sin(p.sphere_phi) * math.cos(p.sphere_theta + rotation)
                y3d = p.jupiter_radius * math.cos(p.sphere_phi)
                z3d = p.jupiter_radius * math.sin(p.sphere_phi) * math.sin(p.sphere_theta + rotation)
                
                tx = hand_x + x3d
                ty = hand_y + y3d
                
                # Sombra 3D y capas de la atmósfera
                z_factor = max(0.2, (z3d + p.jupiter_radius) / (2 * p.jupiter_radius))
                band = math.sin(p.sphere_phi * 10)
                
                # Gran Mancha Roja
                is_spot = (abs(p.sphere_phi - 2.1) < 0.25 and abs((p.sphere_theta + rotation) % (2*math.pi) - 3.14) < 0.4)
                
                if is_spot:
                    base_c = (240, 60, 40)
                elif band > 0.3:
                    base_c = (245, 210, 165) # Crema
                elif band > -0.2:
                    base_c = (210, 110, 50)  # Terracota
                else:
                    base_c = (150, 75, 25)   # Ámbar oscuro
                    
                color = (int(base_c[0] * z_factor), int(base_c[1] * z_factor), int(base_c[2] * z_factor))
                if z3d > 10: size = 3
                
            p.move_to(tx, ty, speed=0.1)

        # DEDO 3: TIERRA 3D CON LUCES NOCTURNAS
        elif finger_count == 3:
            rotation = time_step * 1.1
            
            x3d = p.earth_radius * math.sin(p.sphere_phi) * math.cos(p.sphere_theta + rotation)
            y3d = p.earth_radius * math.cos(p.sphere_phi)
            z3d = p.earth_radius * math.sin(p.sphere_phi) * math.sin(p.sphere_theta + rotation)
            
            tx = hand_x + x3d
            ty = hand_y + y3d
            
            lat = p.sphere_phi
            lon = p.sphere_theta + rotation
            is_land = math.sin(lat * 5) * math.cos(lon * 5) + math.sin(lat * 8 - lon * 3) * 0.5 > 0.15
            
            if z3d > -5: # Lado de Día
                z_factor = max(0.3, z3d / p.earth_radius)
                if is_land:
                    base_c = (50, 215, 120) if abs(lat - math.pi/2) > 0.35 else (235, 195, 110)
                else:
                    base_c = (20, 140, 240) # Océanos turquesa
                color = (int(base_c[0] * z_factor), int(base_c[1] * z_factor), int(base_c[2] * z_factor))
                if z3d > 15: size = 3
            else: # Lado de Noche (Ciudades / Sombra)
                if is_land:
                    color = (255, 190, 60) # Ciudades doradas desde el espacio
                else:
                    color = (10, 30, 70)   # Océano nocturno profundo
                    
            p.move_to(tx, ty, speed=0.1)

        # DEDO 4: DINOSAURIO (T-REX ÁMBAR)
        elif finger_count == 4:
            ox, oy = dino_offsets[i]
            tx, ty = hand_x + ox, hand_y + oy
            var = math.sin(time_step * 4 + i)
            color = (255, 190, 40) if var > 0.3 else (255, 90, 20)
            p.move_to(tx, ty, speed=0.1, friction=0.85)

        # DEDO 5: POLVO ESTELAR
        else:
            tx = p.x + math.cos(time_step + i) * 6
            ty = p.y + math.sin(time_step + i) * 6
            color = (130, 170, 255)
            p.move_to(tx, ty, speed=0.02, friction=0.92)
            if p.x < 0 or p.x > WIDTH or p.y < 0 or p.y > HEIGHT:
                p.x, p.y = random.uniform(0, WIDTH), random.uniform(0, HEIGHT)

        # DIBUJADO DE ALTA DEFINICIÓN
        ix, iy = int(p.x), int(p.y)
        if 0 <= ix < WIDTH and 0 <= iy < HEIGHT:
            pygame.gfxdraw.aacircle(screen, ix, iy, size, color)
            pygame.gfxdraw.filled_circle(screen, ix, iy, size, color)

    # DIBUJAR TARJETA HUD
    draw_cool_hud(screen, finger_count)

    pygame.display.flip()
    clock.tick(60)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
pygame.quit()