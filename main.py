import pygame
from os.path import join
from random import randint, uniform

# General setup
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Space Shooter')
clock = pygame.time.Clock()
FPS = 60

# Load assets
try:
    star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
    meteor_surf = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
    laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
    font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
    explosion_frames = [pygame.image.load(join('images', 'explosion', f'{i}.png')).convert_alpha() for i in range(21)]
    laser_sound = pygame.mixer.Sound(join('audio', 'laser.wav'))
    explosion_sound = pygame.mixer.Sound(join('audio', 'explosion.wav'))
    game_music = pygame.mixer.Sound(join('audio', 'game_music.wav'))
except Exception as e:
    print(f"Error loading assets: {e}")
    pygame.quit()
    exit()

# Colors and constants
BACKGROUND_COLOR = '#3a2e3f'
TEXT_COLOR = (240, 240, 240)
SECRET_CODE_COLOR = (255, 200, 200)

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, groups, all_sprites, laser_sprites):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player.png')).convert_alpha()
        self.rect = self.image.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.direction = pygame.Vector2()
        self.speed = 300  # Base speed
        self.cheat_speed = 600  # Speed when cheat is active
        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = 400
        self.mask = pygame.mask.from_surface(self.image)
        self.all_sprites = all_sprites
        self.laser_sprites = laser_sprites
        self.cheat_active = False  # Cheat flag

    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        self.direction = self.direction.normalize() if self.direction else self.direction

        # Use cheat speed if cheat is active
        current_speed = self.cheat_speed if self.cheat_active else self.speed
        self.rect.center += self.direction * current_speed * dt

        if keys[pygame.K_SPACE] and self.can_shoot:
            Laser(laser_surf, self.rect.midtop, (self.all_sprites, self.laser_sprites))
            self.can_shoot = False
            self.laser_shoot_time = pygame.time.get_ticks()
            laser_sound.play()

        self.laser_timer()

# Star class
class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(center=(randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)))

# Laser class
class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(midbottom=pos)

    def update(self, dt):
        self.rect.centery -= 400 * dt
        if self.rect.bottom < 0:
            self.kill()

# Meteor class
class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_surf = surf
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 3000
        self.direction = pygame.Vector2(uniform(-0.5, 0.5), 1)
        self.speed = randint(400, 500)
        self.rotation_speed = randint(40, 80)
        self.rotation = 0

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()
        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)
        self.rect = self.image.get_rect(center=self.rect.center)

# AnimatedExplosion class
class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        explosion_sound.play()

    def update(self, dt):
        self.frame_index += 20 * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.kill()

# Collisions function
def collisions(player, meteor_sprites, laser_sprites, all_sprites):
    # Skip collision check if cheat is active (player is immortal)
    if not player.cheat_active:
        collision_sprites = pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask)
        if collision_sprites:
            return False  # Return False to indicate the game should end

    for laser in laser_sprites:
        collided_sprites = pygame.sprite.spritecollide(laser, meteor_sprites, True)
        if collided_sprites:
            laser.kill()
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)

    return True  # Return True to indicate the game should continue

# Display score function
def display_score():
    current_time = pygame.time.get_ticks() // 100
    text_surf = font.render(str(current_time), True, (240, 240, 240))
    text_rect = text_surf.get_rect(midbottom=(WINDOW_WIDTH / 2, WINDOW_HEIGHT - 50))
    display_surface.blit(text_surf, text_rect)
    pygame.draw.rect(display_surface, (240, 240, 240), text_rect.inflate(20, 10).move(0, -8), 5, 10)

# Start Menu
def start_menu(player):
    running = True
    secret_code = ""
    message = ""
    while running:
        display_surface.fill(BACKGROUND_COLOR)
        title_text = font.render("Space Shooter", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 4))
        display_surface.blit(title_text, title_rect)

        start_text = font.render("Press S to Start", True, TEXT_COLOR)
        start_rect = start_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        display_surface.blit(start_text, start_rect)

        instructions_text = font.render("Press I for Instructions", True, TEXT_COLOR)
        instructions_rect = instructions_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 1.5))
        display_surface.blit(instructions_text, instructions_rect)

        quit_text = font.render("Press Q to Quit", True, TEXT_COLOR)
        quit_rect = quit_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 1.2))
        display_surface.blit(quit_text, quit_rect)

        # Secret code input box
        code_text = font.render("Enter Secret Code: " + secret_code, True, SECRET_CODE_COLOR)
        code_rect = code_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 1.1))
        display_surface.blit(code_text, code_rect)

        # Display message if a code is entered
        if message:
            message_text = font.render(message, True, SECRET_CODE_COLOR)
            message_rect = message_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 1.05))
            display_surface.blit(message_text, message_rect)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    return 'start'
                if event.key == pygame.K_i:
                    instructions_screen()
                if event.key == pygame.K_q:
                    pygame.quit()
                    exit()
                # Handle secret code input
                if event.key == pygame.K_BACKSPACE:
                    secret_code = secret_code[:-1]
                elif event.key == pygame.K_RETURN:
                    if secret_code == "cheat":
                        message = "Cheat activated! Unlimited power!"
                        player.cheat_active = True  # Activate cheat
                    elif secret_code == "hehe":
                        message = "Will you be my Valentine? ❤️"
                    else:
                        message = "Invalid code!"
                    secret_code = ""
                else:
                    # Append the pressed key to the secret code
                    if event.unicode.isalpha():
                        secret_code += event.unicode

# Instructions Screen
def instructions_screen():
    running = True
    while running:
        display_surface.fill(BACKGROUND_COLOR)
        instructions_title = font.render("Instructions", True, TEXT_COLOR)
        instructions_title_rect = instructions_title.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 4))
        display_surface.blit(instructions_title, instructions_title_rect)

        instructions_text = font.render("Use Arrow keys to Move", True, TEXT_COLOR)
        instructions_rect = instructions_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2.5))
        display_surface.blit(instructions_text, instructions_rect)

        shoot_text = font.render("Press SPACE to Shoot", True, TEXT_COLOR)
        shoot_rect = shoot_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        display_surface.blit(shoot_text, shoot_rect)

        back_text = font.render("Press B to Back", True, TEXT_COLOR)
        back_rect = back_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 1.5))
        display_surface.blit(back_text, back_rect)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    return

# Game loop
def game_loop():
    global running
    running = True
    all_sprites = pygame.sprite.Group()
    meteor_sprites = pygame.sprite.Group()
    laser_sprites = pygame.sprite.Group()
    player = Player(all_sprites, all_sprites, laser_sprites)  # Pass the groups here

    # Custom events
    meteor_event = pygame.event.custom_type()
    pygame.time.set_timer(meteor_event, 1000)  # Spawn meteors every 1 second

    # Start game music
    game_music.play(-1)

    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == meteor_event:
                x, y = randint(0, WINDOW_WIDTH), randint(-200, -100)
                Meteor(meteor_surf, (x, y), (all_sprites, meteor_sprites))

        all_sprites.update(dt)
        running = collisions(player, meteor_sprites, laser_sprites, all_sprites)

        # Draw everything
        display_surface.fill(BACKGROUND_COLOR)
        display_score()
        all_sprites.draw(display_surface)

        pygame.display.update()

# Main game entry point
def main():
    all_sprites = pygame.sprite.Group()
    meteor_sprites = pygame.sprite.Group()
    laser_sprites = pygame.sprite.Group()
    player = Player(all_sprites, all_sprites, laser_sprites)  # Create the player object here

    while True:
        option = start_menu(player)  # Pass the player object to the start_menu function
        if option == 'start':
            game_loop()

# Run the game
if __name__ == "__main__":
    main()