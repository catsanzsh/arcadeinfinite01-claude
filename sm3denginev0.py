from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

class Mario3DEngine(Ursina):
    def __init__(self):
        super().__init__()
        # Basic window setup
        window.title = 'Super Mario 3D'
        window.borderless = False
        window.fullscreen = False
        window.exit_button.visible = False
        window.fps_counter.enabled = True

        # Create player
        self.player = FirstPersonController(
            model='cube',
            color=color.red,
            scale=(1,2,1),
            position=(0,2,0),
            speed=10,
            jump_height=4
        )
        self.player.health = 3
        self.score = 0
        
        # UI Elements
        self.health_text = Text(text=f'Lives: {self.player.health}', position=(-0.85, 0.45))
        self.score_text = Text(text=f'Score: {self.score}', position=(-0.85, 0.4))
        self.status_message = Text(text='', position=(0, 0.3))
        self.status_message.visible = False
        
        # Create ground and environment
        self.current_level = 0
        self.levels = self.define_levels()
        self.load_level(self.current_level)
        
        # Visual effects
        self.flash_effect = Entity(model='quad', scale=(2, 1), color=color.rgba(1,1,1,0))
        self.flash_effect.z = -0.1
        
        # Sky and lighting
        self.sky = Sky()
        self.directional_light = DirectionalLight()
        self.directional_light.look_at(Vec3(1,-1,-1))

    def show_message(self, text, duration=1):
        self.status_message.text = text
        self.status_message.visible = True
        invoke(setattr, self.status_message, 'visible', False, delay=duration)

    def flash_screen(self, color_rgba):
        self.flash_effect.color = color_rgba
        self.flash_effect.animate_color(color.rgba(1,1,1,0), duration=0.5)

    def define_levels(self):
        return [
            {
                'theme': 'grass',
                'color': color.green,
                'enemies': 5,
                'coins': 10,
                'ground_scale': (100,1,100),
                'platforms': 8
            },
            {
                'theme': 'desert',
                'color': color.yellow,
                'enemies': 7,
                'coins': 15,
                'ground_scale': (120,1,120),
                'platforms': 10
            },
            {
                'theme': 'snow',
                'color': color.white,
                'enemies': 10,
                'coins': 20,
                'ground_scale': (150,1,150),
                'platforms': 12
            }
        ]

    def load_level(self, level_idx):
        # Clear previous level
        for entity in scene.entities:
            if entity not in [self.player, self.sky, self.directional_light, 
                            self.flash_effect, self.status_message]:
                destroy(entity)
                
        level = self.levels[level_idx]
        self.show_message(f'Level {level_idx + 1}: {level["theme"].title()}', 2)
        
        # Create ground
        self.ground = Entity(
            model='plane',
            scale=level['ground_scale'],
            color=level['color'],
            texture='grass' if level['theme'] == 'grass' else 'sand' if level['theme'] == 'desert' else 'snow',
            texture_scale=(50,50),
            collider='box'
        )
        
        # Create platforms
        self.platforms = []
        for _ in range(level['platforms']):
            plat = Entity(
                model='cube',
                color=color.light_gray,
                position=(
                    random.uniform(-40, 40),
                    random.uniform(3, 15),
                    random.uniform(-40, 40)
                ),
                scale=(4,0.5,4),
                texture='brick',
                collider='box'
            )
            self.platforms.append(plat)
            
        # Create coins
        self.coins = []
        for _ in range(level['coins']):
            coin = Entity(
                model='sphere',
                scale=0.5,
                color=color.gold,
                position=(
                    random.uniform(-45, 45),
                    random.uniform(1, 10),
                    random.uniform(-45, 45)
                ),
                collider='sphere'
            )
            coin.animate_rotation_y(360, duration=1, loop=True)
            self.coins.append(coin)
            
        # Create enemies
        self.enemies = []
        for _ in range(level['enemies']):
            enemy = Entity(
                model='cube',
                scale=(1,1,1),
                color=color.red,
                position=(
                    random.uniform(-45, 45),
                    1,
                    random.uniform(-45, 45)
                ),
                collider='box'
            )
            enemy.speed = random.uniform(2, 4)
            enemy.direction = Vec3(
                random.uniform(-1, 1),
                0,
                random.uniform(-1, 1)
            ).normalized()
            self.enemies.append(enemy)

    def update(self):
        # Update UI
        self.health_text.text = f'Lives: {self.player.health}'
        self.score_text.text = f'Score: {self.score}'
        
        # Check for coin collection
        for coin in self.coins[:]:
            if distance(coin.position, self.player.position) < 2:
                # Visual feedback for coin collection
                self.flash_screen(color.rgba(1,1,0,0.3))  # Gold flash
                self.show_message('+10 Points!')
                destroy(coin)
                self.coins.remove(coin)
                self.score += 10
                
        # Update enemy positions
        for enemy in self.enemies:
            # Basic AI movement
            enemy.position += enemy.direction * enemy.speed * time.dt
            
            # Bounce off boundaries
            if abs(enemy.x) > 45 or abs(enemy.z) > 45:
                enemy.direction = Vec3(
                    random.uniform(-1, 1),
                    0,
                    random.uniform(-1, 1)
                ).normalized()
                
            # Check collision with player
            if distance(enemy.position, self.player.position) < 2:
                self.flash_screen(color.rgba(1,0,0,0.3))  # Red flash
                self.show_message('Ouch!')
                self.player.health -= 1
                self.player.position = Vec3(0, 2, 0)  # Reset position
                
                if self.player.health <= 0:
                    self.show_message('Game Over!', 3)
                    invoke(application.quit, delay=3)
                    
        # Level completion check
        if len(self.coins) == 0:
            self.flash_screen(color.rgba(0,1,0,0.3))  # Green flash
            self.show_message('Level Complete!')
            self.current_level += 1
            if self.current_level < len(self.levels):
                invoke(self.load_level, self.current_level, delay=2)
            else:
                self.show_message('You Win!', 3)
                invoke(application.quit, delay=3)
                
        # Fall detection
        if self.player.y < -50:
            self.flash_screen(color.rgba(1,0,0,0.3))  # Red flash
            self.show_message('Fell off the world!')
            self.player.health -= 1
            self.player.position = Vec3(0, 2, 0)
            if self.player.health <= 0:
                self.show_message('Game Over!', 3)
                invoke(application.quit, delay=3)

if __name__ == '__main__':
    game = Mario3DEngine()
    game.run()
