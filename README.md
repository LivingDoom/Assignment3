# Assignment3
Software Now - Assignment3


# main.py

Group Name: [DAN/EXT12] 
Group Members:

[Kayla Edwards]                 -           [S396018] 

[Jonathan William McPhail]      -           [S368879] 

[Ibrahim Najjarine]             -           [S407912] 

[Glen Mark Pasigna]             -           [S328808] 



import cv2
import numpy as np
import random
import tkinter as tk
from PIL import Image, ImageTk



def make_square_img(img):
    height, width = img.shape[:2]
    side = max(height, width)
    return cv2.resize(img, (side, side))


def load_image(path, grid_size, target=450): # 450 divides cleanly by 3, 5
    img = cv2.imread(path)
    if img is None:
        # Fallback dummy image if file doesn't exist so the GUI still runs
        img = np.zeros((450, 450, 3), dtype=np.uint8)
        cv2.putText(img, "Puzzle Image", (50, 225), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
    
    img = make_square_img(img)
    new_side = (target // grid_size) * grid_size
    img = cv2.resize(img, (new_side, new_side))
    return img


def split_into_tiles(img, grid_size):
    tile_side = img.shape[0] // grid_size
    tiles = []
    for rows in range(grid_size):
        for columns in range(grid_size):
            y = tile_side * rows
            x = tile_side * columns
            tile = img[y : y + tile_side, x : x + tile_side].copy()
            tiles.append(tile)
    return tiles


class PuzzleTile(tk.Canvas):
    #Individual tile data and image states
    def __init__(self, parent, cv2_base_img, tile_id, goal_row, goal_col, side_length):
        super().__init__(parent, width=side_length, height=side_length, 
                         highlightthickness=2, bd=0)
        
        self.tile_id = tile_id
        self.cv2_base_img = cv2_base_img
        self.side_length = side_length
        
        self.goal_row = goal_row
        self.goal_col = goal_col
        self.rotation = 0
        self.flipped_horizontal = False
        
        self.goal_rotation = 0
        self.goal_flipped = False
        
        self.update_visual()

    def update_visual(self):
        
        rgb_img = cv2.cvtColor(self.cv2_base_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
        
        if self.flipped_horizontal:
            pil_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
        if self.rotation != 0:
            pil_img = pil_img.rotate(-self.rotation)
            
        self.tk_photo = ImageTk.PhotoImage(image=pil_img)
        
        self.delete("all")
        self.create_image(self.side_length // 2, self.side_length // 2, image=self.tk_photo)


class User_moves:

    def __init__(self):
        self.selected_tile = None

    def check_tile_status(self, tile):
        # Checks tile goal state and draws/removes the tick
        info = tile.grid_info()
 
        is_correct_pos = (int(info['row']) == tile.goal_row and int(info['column']) == tile.goal_col)
        is_correct_orient = (tile.rotation == tile.goal_rotation and tile.flipped_horizontal == tile.goal_flipped)
        
        tile.delete("tick_mark")
        
        if is_correct_pos and is_correct_orient:
            #Green tick top-right
            tile.create_line(
                tile.side_length - 25, 20, 
                tile.side_length - 20, 25, 
                tile.side_length - 10, 13, 
                fill= 'light green', 
                width=3, 
                tags="tick_mark"
            )

    def on_tile_click(self, event):
        clicked_tile = event.widget
        
        if self.selected_tile is None:
            self.selected_tile = clicked_tile
            clicked_tile.config(highlightbackground="red")
        else:
            if self.selected_tile == clicked_tile:
                self.selected_tile.config(highlightbackground=self.selected_tile.cget("bg"))
                self.selected_tile = None
                return
                
            info1 = self.selected_tile.grid_info()
            info2 = clicked_tile.grid_info()
            
            # Swap tile coordinates
            self.selected_tile.grid(row=info2['row'], column=info2['column'])
            clicked_tile.grid(row=info1['row'], column=info1['column'])
            
            self.selected_tile.config(highlightbackground=self.selected_tile.cget("bg"))
            
            self.check_tile_status(self.selected_tile)
            self.check_tile_status(clicked_tile)
            
            self.selected_tile = None

    def on_tile_right_click(self, event):
        clicked_tile = event.widget
        clicked_tile.rotation = (clicked_tile.rotation + 90) % 360
        clicked_tile.update_visual() # VISUAL UPDATE RE-RENDER ADDED
        self.check_tile_status(clicked_tile)

    def on_tile_shift_click(self, event):
        clicked_tile = event.widget
        clicked_tile.flipped_horizontal = not clicked_tile.flipped_horizontal
        clicked_tile.update_visual() # VISUAL UPDATE RE-RENDER ADDED
        self.check_tile_status(clicked_tile)


def run_puzzle_game(img_path="small_shapes.png", grid_size=3):
    root = tk.Tk()
    root.title("Scrambled Mosaic Puzzle Engine")
    
    cv2_master = load_image(img_path, grid_size, target=450)
    cv2_tiles = split_into_tiles(cv2_master, grid_size)
    
    tile_side = cv2_master.shape[0] // grid_size
    moves_engine = User_moves()
    
    game_tiles = []
    tile_index = 0
    
    for r in range(grid_size):
        for c in range(grid_size):
            tile = PuzzleTile(root, cv2_tiles[tile_index], tile_index, r, c, tile_side)
            
            tile.bind("<Button-1>", moves_engine.on_tile_click)
            tile.bind("<Button-2>", moves_engine.on_tile_right_click) # macOS Right-click
            tile.bind("<Button-3>", moves_engine.on_tile_right_click) # Windows/Linux Right-click
            tile.bind("<Shift-Button-1>", moves_engine.on_tile_shift_click)
            
            game_tiles.append(tile)
            tile_index += 1

    #SHuffle tiles randomly for gameplay
    shuffled_tiles = game_tiles.copy()
    random.shuffle(shuffled_tiles)
    
    idx = 0
    for r in range(grid_size):
        for c in range(grid_size):
            t = shuffled_tiles[idx]
            
            #Apply random spin/flip
            t.rotation = random.choice([0, 90, 180, 270])
            t.flipped_horizontal = random.choice([True, False])
            t.update_visual()
            
            #Place onto Grid layout
            t.grid(row=r, column=c, padx=1, pady=1)
            moves_engine.check_tile_status(t)
            idx += 1
            
    root.mainloop()


if __name__ == "__main__":
    run_puzzle_game(img_path="small_shapes.png", grid_size=3)
