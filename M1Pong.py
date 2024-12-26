import tkinter as tk
import time

class AtariPongEngine:
    # Original Atari constants
    HTIMER = 1.0 / 15720.0  # Horizontal sync timer (15.72KHz)
    VTIMER = 1.0 / 60.0     # Vertical sync timer (60Hz)
    SCANLINES = 262         # Total scanlines per frame
    VISIBLE_SCANLINES = 240 # Visible scanlines
    H_PIXELS = 160          # Horizontal resolution

    # Game constants matching Atari's discrete logic
    PADDLE_HEIGHT = 14      # In scanlines
    PADDLE_WIDTH = 2        # In pixels
    BALL_SIZE = 2          # 2x2 pixels like original
    PADDLE_SPEED = 1       # One scanline per frame
    SCORE_LIMIT = 11       # Original Atari score limit

    def __init__(self, root):
        self.root = root
        self.root.title("Atari Pong (Original Engine)")
        
        # Scale up the display while maintaining proportions
        self.scale = 4
        self.width = self.H_PIXELS * self.scale
        self.height = self.VISIBLE_SCANLINES * self.scale
        
        self.canvas = tk.Canvas(
            root, 
            width=self.width,
            height=self.height,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack()

        # Game state (using fixed-point math like original)
        self.ball_x = self.H_PIXELS // 2 << 4  # Fixed point 4.4
        self.ball_y = self.VISIBLE_SCANLINES // 2 << 4
        self.ball_dx = 1 << 4  # Initial ball speed (in 4.4 fixed point)
        self.ball_dy = 0
        
        # Paddle positions (in scanlines)
        self.left_y = (self.VISIBLE_SCANLINES - self.PADDLE_HEIGHT) // 2
        self.right_y = self.left_y
        
        # Scoring
        self.left_score = 0
        self.right_score = 0
        
        # Create game objects
        self.create_game_objects()
        
        # Input handling (using original's discrete input)
        self.pressed_keys = set()
        self.root.bind('<KeyPress>', self.handle_keypress)
        self.root.bind('<KeyRelease>', self.handle_keyrelease)
        
        # Timing variables
        self.last_frame_time = time.time()
        self.scanline = 0
        
        # Start the game loop
        self.update_engine()

    def create_game_objects(self):
        # Create paddles (scaled)
        self.left_paddle = self.canvas.create_rectangle(
            20 * self.scale,
            self.left_y * self.scale,
            (20 + self.PADDLE_WIDTH) * self.scale,
            (self.left_y + self.PADDLE_HEIGHT) * self.scale,
            fill='white'
        )
        
        self.right_paddle = self.canvas.create_rectangle(
            (self.H_PIXELS - 20 - self.PADDLE_WIDTH) * self.scale,
            self.right_y * self.scale,
            (self.H_PIXELS - 20) * self.scale,
            (self.right_y + self.PADDLE_HEIGHT) * self.scale,
            fill='white'
        )
        
        # Create ball (scaled)
        self.ball = self.canvas.create_rectangle(
            (self.ball_x >> 4) * self.scale,
            (self.ball_y >> 4) * self.scale,
            ((self.ball_x >> 4) + self.BALL_SIZE) * self.scale,
            ((self.ball_y >> 4) + self.BALL_SIZE) * self.scale,
            fill='white'
        )
        
        # Create scores
        self.left_score_display = self.canvas.create_text(
            self.width // 4,
            30 * self.scale,
            text='0',
            fill='white',
            font=('Courier', 20 * self.scale // 10)
        )
        
        self.right_score_display = self.canvas.create_text(
            3 * self.width // 4,
            30 * self.scale,
            text='0',
            fill='white',
            font=('Courier', 20 * self.scale // 10)
        )
        
        # Create center line (using original's dotted line pattern)
        for y in range(0, self.height, 8 * self.scale):
            self.canvas.create_rectangle(
                self.width//2 - self.scale,
                y,
                self.width//2 + self.scale,
                y + 4 * self.scale,
                fill='white'
            )

    def handle_keypress(self, event):
        self.pressed_keys.add(event.keysym)

    def handle_keyrelease(self, event):
        self.pressed_keys.discard(event.keysym)

    def update_paddles(self):
        # Original Atari paddle movement logic
        if 'w' in self.pressed_keys and self.left_y > 0:
            self.left_y -= self.PADDLE_SPEED
        if 's' in self.pressed_keys and self.left_y < self.VISIBLE_SCANLINES - self.PADDLE_HEIGHT:
            self.left_y += self.PADDLE_SPEED
            
        if 'Up' in self.pressed_keys and self.right_y > 0:
            self.right_y -= self.PADDLE_SPEED
        if 'Down' in self.pressed_keys and self.right_y < self.VISIBLE_SCANLINES - self.PADDLE_HEIGHT:
            self.right_y += self.PADDLE_SPEED
        
        # Update paddle positions
        self.canvas.coords(
            self.left_paddle,
            20 * self.scale,
            self.left_y * self.scale,
            (20 + self.PADDLE_WIDTH) * self.scale,
            (self.left_y + self.PADDLE_HEIGHT) * self.scale
        )
        
        self.canvas.coords(
            self.right_paddle,
            (self.H_PIXELS - 20 - self.PADDLE_WIDTH) * self.scale,
            self.right_y * self.scale,
            (self.H_PIXELS - 20) * self.scale,
            (self.right_y + self.PADDLE_HEIGHT) * self.scale
        )

    def update_ball(self):
        # Move ball using fixed-point math
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy
        
        # Ball-paddle collision (using original's scanline-based detection)
        ball_scanline = self.ball_y >> 4
        
        # Left paddle collision
        if (self.ball_x >> 4) <= 22 and (self.ball_x >> 4) >= 20:
            if ball_scanline >= self.left_y and ball_scanline < self.left_y + self.PADDLE_HEIGHT:
                self.ball_dx = abs(self.ball_dx)  # Reverse direction
                offset = ((ball_scanline - self.left_y) - (self.PADDLE_HEIGHT // 2))
                self.ball_dy = offset * (1 << 2)  # Apply vertical velocity based on hit position
                self.root.bell()

        # Right paddle collision
        if (self.ball_x >> 4) >= self.H_PIXELS - 22 and (self.ball_x >> 4) <= self.H_PIXELS - 20:
            if ball_scanline >= self.right_y and ball_scanline < self.right_y + self.PADDLE_HEIGHT:
                self.ball_dx = -abs(self.ball_dx)  # Reverse direction
                offset = ((ball_scanline - self.right_y) - (self.PADDLE_HEIGHT // 2))
                self.ball_dy = offset * (1 << 2)  # Apply vertical velocity based on hit position
                self.root.bell()

        # Wall collisions
        if (self.ball_y >> 4) <= 0 or (self.ball_y >> 4) >= self.VISIBLE_SCANLINES - self.BALL_SIZE:
            self.ball_dy = -self.ball_dy
            self.root.bell()

        # Scoring
        if (self.ball_x >> 4) <= 0:
            self.right_score += 1
            self.canvas.itemconfig(self.right_score_display, text=str(self.right_score))
            self.reset_ball()
        elif (self.ball_x >> 4) >= self.H_PIXELS:
            self.left_score += 1
            self.canvas.itemconfig(self.left_score_display, text=str(self.left_score))
            self.reset_ball()

        # Update ball position
        self.canvas.coords(
            self.ball,
            (self.ball_x >> 4) * self.scale,
            (self.ball_y >> 4) * self.scale,
            ((self.ball_x >> 4) + self.BALL_SIZE) * self.scale,
            ((self.ball_y >> 4) + self.BALL_SIZE) * self.scale
        )

    def reset_ball(self):
        # Reset ball to center with original starting logic
        self.ball_x = self.H_PIXELS // 2 << 4
        self.ball_y = self.VISIBLE_SCANLINES // 2 << 4
        self.ball_dx = (1 << 4) if self.ball_dx < 0 else -(1 << 4)
        self.ball_dy = 0

    def update_engine(self):
        current_time = time.time()
        elapsed = current_time - self.last_frame_time
        
        # Simulate original Atari's sync timing
        if elapsed >= self.VTIMER:
            self.last_frame_time = current_time
            # Process one frame worth of updates
            self.update_paddles()
            self.update_ball()
            
        # Schedule next update using original timing
        self.root.after(1, self.update_engine)

if __name__ == "__main__":
    root = tk.Tk()
    game = AtariPongEngine(root)
    root.mainloop()
