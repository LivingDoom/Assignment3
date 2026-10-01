import tkinter as tk
import numpy as np
import random

class Puzzle:
    def __init__(self, image_list: list[np.ndarray], grid: int):
        self._grid = grid
        self._tiles = []
        self._moves = 0
        self._move_history = []
        self._solved = False

        output = enumerate(image_list)
        for index, image in output:
            row = index // self._grid
            col = index % self._grid
            self._tiles.append(Tile((row, col), image))

    def __str__(self) -> str:
        return f"Current Moves: {self._moves}"

    def check(self):
        self._solved = all([tile.check_is_correct() for tile in self._tiles])

    def trans_helper(self, transformation):
        transformation.apply()
        self._move_history.append(transformation)
        self._moves += 1
        self.check()
        return transformation

    def rotate_tile(self, position):
        if self._solved is True: 
            return None
        tile = next((t for t in self._tiles if t.current_position == position), None)
        if tile is None: 
            raise PositionValueError(f"Tile at position {position}")
        return self.trans_helper(Rotate(tile))

    def flip_tile(self, position):
        if self._solved is True: 
            return None
        tile = next((t for t in self._tiles if t.current_position == position), None)
        if tile is None: 
            raise PositionValueError(f"Tile at position {position} is None (inside flip_tile)")
        return self.trans_helper(Flip(tile))

    def swap_tile(self, first_pos, second_pos):
        if self._solved is True: 
            return None
        tile = next((t for t in self._tiles if t.current_position == first_pos), None)
        tile2 = next((t for t in self._tiles if t.current_position == second_pos), None)
        if tile is None or tile2 is None:
            raise PositionValueError(f"Invalid swap positions: {first_pos}, {second_pos}")
        return self.trans_helper(Swap(tile, tile2))

    def solve(self):
        for tile in self._tiles:
            transformation = tile.revert()
        self._move_history = []
        self._moves = 0
        self.check()

    def scramble(self):
        count = 0
        for i in range((self._grid * (self._grid + 3))):
            i = random.choice(['rotate', 'flip', 'swap'])     
            count += 1
            if i == 'rotate':
                transformation = Rotate(random.choice(self._tiles))
                transformation.apply()
            elif i == 'flip':
                transformation = Flip(random.choice(self._tiles))
                transformation.apply()
            elif i == 'swap':
                transformation = Swap(random.choice(self._tiles), random.choice(self._tiles))
                transformation.apply()
        self.check()

    def view_history(self) -> list:
        return self._move_history

class User_moves: 
    def __init__(self, puzzle_instance): 
        self.puzzle = puzzle_instance
        self.selected_tile = None
        self.container = None  

    def set_container(self, container_widget):
        """Saves reference to parent widget hosting child tile canvas elements."""
        self.container = container_widget

    def clear_hints(self):
        if not self.container: 
            return
        for tile_widget in self.container.winfo_children():
            if isinstance(tile_widget, tk.Canvas):
                tile_widget.delete("hint_marker")

    def update_all_tile_marks(self, container_widget):
        for tile_widget in container_widget.winfo_children():
            if hasattr(tile_widget, "tile_data"):
                is_correct = tile_widget.tile_data.check_is_correct()
                tile_widget.delete("tick_mark")
                if is_correct:
                    tile_widget.create_line(
                        60, 20, 65, 25, 75, 13, 
                        fill="#00FF00", width=3, tags="tick_mark"
                    )

    def give_swap_hint(self):
        if self.puzzle._solved or not self.container: 
            return
        
        self.clear_hints() 
        misplaced_tiles = [t for t in self.puzzle._tiles if t.current_position != t.original_position]
        
        if len(misplaced_tiles) >= 2:
            hint_targets = misplaced_tiles[:2]
            
            for tile_widget in self.container.winfo_children():
                if hasattr(tile_widget, "tile_data") and tile_widget.tile_data in hint_targets:
                    tile_widget.create_oval(
                        8, 8, 72, 72, 
                        outline="#0000FF", width=3, 
                        dash=(4, 2), tags="hint_marker"
                    )

    def on_tile_click(self, event):
        if self.puzzle._solved: 
            return
        self.clear_hints() 
        
        clicked_tile = event.widget
        parent_container = clicked_tile.master
        
        if self.selected_tile is None:
            self.selected_tile = clicked_tile
            clicked_tile.config(
                highlightbackground="red",
                highlightcolor="red"
            )
        else:
            if self.selected_tile == clicked_tile:
                self.selected_tile.config(
                    highlightbackground=self.selected_tile.cget("bg"),
                    highlightcolor=self.selected_tile.cget("bg")
                )
                self.selected_tile = None
                return
                
            pos1 = self.selected_tile.tile_data.current_position
            pos2 = clicked_tile.tile_data.current_position
            
            try:
                self.puzzle.swap_tile(pos1, pos2)
                self.selected_tile.grid(row=pos2[0], column=pos2[1])
                clicked_tile.grid(row=pos1[0], column=pos1[1])
            except Exception as e:
                print(f"Swap failed: {e}")
            
            self.selected_tile.config(
                highlightbackground=self.selected_tile.cget("bg"),
                highlightcolor=self.selected_tile.cget("bg")
            )
            self.update_all_tile_marks(parent_container)
            self.selected_tile = None

    def on_tile_right_click(self, event):
        if self.puzzle._solved: 
            return
        self.clear_hints()
        
        clicked_tile = event.widget
        pos = clicked_tile.tile_data.current_position
        try:
            self.puzzle.rotate_tile(pos)
            self.update_all_tile_marks(clicked_tile.master)
        except Exception as e: 
            print(f"Rotation failure: {e}")

    def on_tile_shift_click(self, event):
        if self.puzzle._solved: 
            return
        self.clear_hints()
        
        clicked_tile = event.widget
        pos = clicked_tile.tile_data.current_position
        try:
            self.puzzle.flip_tile(pos)
            self.update_all_tile_marks(clicked_tile.master)
        except Exception as e: 
            print(f"Flip failure: {e}")


################################################################################## FROM README ####################################################################################
# import cv2 
# import random 
# import tkinter as tk 
# import numpy as np 
# from PIL import Image, ImageTk

# IMAGE_CACHE = {}

# class Winner(Exception): """Raised when the puzzle is solved."""

# class PositionValueError(Exception): """Raised when a requested position is not found on the grid."""

# class Tile: 
#     def __init__(self, original_position, image) -> None:
#         self.original_position = original_position
#         self.current_position = original_position
#         self.original_orientation = 0
#         self.current_orientation = 0
#         self._flipped_vert = False
#         self._flipped_horz = False
#         self._is_correct = False
#         self._image = image
#         self.display_image = image.copy()

# def __repr__(self) -> str:
#     return (
#         f"Tile(Orig: {self.original_position}, Curr: {self.current_position}, "
#         f"Rot: {self.current_orientation}°, H-Flip: {self._flipped_horz})"
#     )

# def rotate(self, direction: str):
#     """Rotates tracking state and updates internal image arrays."""
#     if direction not in ("cw", "ccw"):
#         raise ValueError("Use 'cw' (clockwise) or 'ccw' (counter-clockwise).")

#     if direction == "cw":
#         self.current_orientation = (self.current_orientation + 90) % 360
#         self.display_image = cv2.rotate(self.display_image, cv2.ROTATE_90_CLOCKWISE)
#     else:
#         self.current_orientation = (self.current_orientation - 90) % 360
#         self.display_image = cv2.rotate(self.display_image, cv2.ROTATE_90_COUNTERCLOCKWISE)

#     return self.current_orientation

# def flip(self, direction: str):
#     """Flips tracking state and updates internal image arrays."""
#     if direction in ("horizontal", "horz"):
#         self._flipped_horz = not self._flipped_horz
#         self.display_image = cv2.flip(self.display_image, 1)
#     elif direction in ("vertical", "vert"):
#         self._flipped_vert = not self._flipped_vert
#         self.display_image = cv2.flip(self.display_image, 0)
#     else:
#         raise ValueError("Invalid direction. Use 'horizontal' or 'vertical'.")

# def check_is_correct(self) -> bool:
#     """Verifies if the tile matches its original state and position."""
#     if (
#         self.original_position == self.current_position
#         and self.current_orientation == self.original_orientation
#         and not self._flipped_horz
#         and not self._flipped_vert
#     ):
#         self._is_correct = True
#     else:
#         self._is_correct = False
#     return self._is_correct

# class Puzzle: 
#     def __init__(self, image_path: str, grid_size: int, target_size: int = 500):
#         self._grid = grid_size
#         self._moves = 0
#         self._move_history = []
#         self.target_size = target_size

#         full_image = self._prepare_image(image_path, target_size)
#         image_tiles = self._split_tiles(full_image)

#         self._tiles = []
#         for index, img_snippet in enumerate(image_tiles):
#             row = index // self._grid
#             col = index % self._grid
#             self._tiles.append(Tile((row, col), img_snippet))

# def _prepare_image(self, path: str, target: int) -> np.ndarray:
#     img = cv2.imread(path)
#     if img is None:
#         img = np.zeros((300, 300, 3), dtype=np.uint8)
#         cv2.putText(img, "PUZZLE", (40, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 165, 255), 4)
#         cv2.rectangle(img, (15, 15), (285, 285), (0, 255, 0), 4)

#     h, w = img.shape[:2]
#     side = max(h, w)
#     img = cv2.resize(img, (side, side))
#     new_side = (target // self._grid) * self._grid
#     return cv2.resize(img, (new_side, new_side))

# def _split_tiles(self, img: np.ndarray) -> list[np.ndarray]:
#     tile_side = img.shape[0] // self._grid
#     tiles = []
#     for row in range(self._grid):
#         for col in range(self._grid):
#             y = tile_side * row
#             x = tile_side * col
#             tiles.append(img[y : y + tile_side, x : x + tile_side].copy())
#     return tiles

# def check(self) -> bool:
#     return all(tile.check_is_correct() for tile in self._tiles)

# def rotate_tile(self, direction: str, orig_pos: tuple[int, int]):
#     tile = self._get_tile_by_orig_pos(orig_pos)
#     transformation = Rotate(direction, tile)
#     transformation.apply()
#     self._move_history.append(transformation)
#     self._moves += 1

# def flip_tile(self, direction: str, orig_pos: tuple[int, int]):
#     tile = self._get_tile_by_orig_pos(orig_pos)
#     transformation = Flip(direction, tile)
#     transformation.apply()
#     self._move_history.append(transformation)
#     self._moves += 1

# def swap_tile(self, first_orig: tuple[int, int], second_orig: tuple[int, int]):
#     tile1 = self._get_tile_by_orig_pos(first_orig)
#     tile2 = self._get_tile_by_orig_pos(second_orig)
#     transformation = Swap(tile1, tile2)
#     transformation.apply()
#     self._move_history.append(transformation)
#     self._moves += 1

# def _get_tile_by_orig_pos(self, orig_pos: tuple[int, int]) -> Tile:
#     for tile in self._tiles:
#         if tile.original_position == orig_pos:
#             return tile
#     raise PositionValueError(f"No tile found tracking original coordinates {orig_pos}")

# def scramble(self):
#     count = 6 #Need adjusment for other grids

#     for _ in range(count):
#         transform_type = random.choice(["rotate", "flip", "swap"])

#         r1 = random.randint(0, self._grid - 1)
#         c1 = random.randint(0, self._grid - 1)

#         if transform_type == "rotate":
#             direction = random.choice(["cw", "ccw"])
#             self.rotate_tile(direction, (r1, c1))

#         elif transform_type == "flip":
#             direction = random.choice(["horizontal", "vertical"])
#             self.flip_tile(direction, (r1, c1))

#         elif transform_type == "swap":
#             r2 = random.randint(0, self._grid - 1)
#             c2 = random.randint(0, self._grid - 1)
#             while (r1, c1) == (r2, c2):
#                 r2 = random.randint(0, self._grid - 1)
#                 c2 = random.randint(0, self._grid - 1)
            
#             self.swap_tile((r1, c1), (r2, c2))

# class TkTileCanvas(tk.Canvas): 
#     def __init__(self, parent, tile_back_object: Tile, side_length: int, *args, **kwargs):
#         super().__init__(parent, width=side_length, height=side_length, highlightthickness=2, *args, **kwargs)
#         self.tile_data = tile_back_object
#         self.side_length = side_length
#         self.tk_image_ref = None
#         self.update_visual()

# def update_visual(self):
#     """Converts internal BGR OpenCV state and explicitly registers it to this widget context."""
#     rgb_img = cv2.cvtColor(self.tile_data.display_image, cv2.COLOR_BGR2RGB)
#     pil_img = Image.fromarray(rgb_img)

#     self.tk_image_ref = ImageTk.PhotoImage(image=pil_img, master=self)
    
#     self.delete("all")
#     self.create_image(0, 0, anchor="nw", image=self.tk_image_ref)

# class UserMoves: 
#     def __init__(self, puzzle_backend: Puzzle):
#         self.selected_tile = None
#         self.puzzle = puzzle_backend
#         self.original_bg = None

# def check_tile_status(self, tile_widget: TkTileCanvas):
#     """Checks structural layout status and renders success markers dynamically."""
#     tile = tile_widget.tile_data
#     info = tile_widget.grid_info()
    
#     current_row = int(info.get('row', 0))
#     current_col = int(info.get('column', 0))
    
#     tile.current_position = (current_row, current_col)
#     is_correct = tile.check_is_correct()
#     tile_widget.delete("tick_mark")
    
#     if is_correct:
#         tile_widget.create_line(
#         tile_widget.side_length - 25, 20, 
#         tile_widget.side_length - 20, 25, 
#         tile_widget.side_length - 10, 13, 
#         fill='light green', 
#         width=3, 
#         tags="tick_mark"
#         )

# def on_tile_click(self, event):
#     clicked_tile = event.widget
    
#     if self.selected_tile is None:
#         # 1. First Tile Clicked
#         self.selected_tile = clicked_tile
#         self.original_bg = clicked_tile.cget("highlightbackground")
#         clicked_tile.config(highlightbackground="red")
#     else:
#         # 2. Deselecting by clicking the same piece twice
#         if self.selected_tile == clicked_tile:
#             clicked_tile.config(highlightbackground=self.original_bg)
#             self.selected_tile = None
#             return
            
#         # 3. Second Tile Clicked (Swapping Mechanics)
#         # Pull the current visual positions directly from the UI layout grid
#         info1 = self.selected_tile.grid_info()
#         info2 = clicked_tile.grid_info()
        
#         pos1 = (int(info1['row']), int(info1['column']))
#         pos2 = (int(info2['row']), int(info2['column']))
        
#         # Execute the swap in the backend puzzle engine using current board locations
#         self.puzzle.swap_tile(pos1, pos2)
        
#         # FIX: Properly separate row and column by indexing the coordinate tuples
#         self.selected_tile.grid(row=pos2[0], column=pos2[1])
#         clicked_tile.grid(row=pos1[0], column=pos1[1])
        
#         # Unselect and clean up highlight borders safely
#         self.selected_tile.config(highlightbackground=self.original_bg)
        
#         # Update checkmark tracking states for both targets
#         self.check_tile_status(self.selected_tile)
#         self.check_tile_status(clicked_tile)
        
#         self.selected_tile = None

# def on_tile_right_click(self, event):
#     clicked_tile = event.widget
#     info = clicked_tile.grid_info()
#     current_pos = (int(info['row']), int(info['column']))
    
#     # Pass the active board position to the engine rather than original position
#     self.puzzle.rotate_tile("cw", current_pos)
#     clicked_tile.update_visual()
#     self.check_tile_status(clicked_tile)

# def on_tile_shift_click(self, event):
#     clicked_tile = event.widget
#     info = clicked_tile.grid_info()
#     current_pos = (int(info['row']), int(info['column']))
    
#     # Pass the active board position to the engine rather than original position
#     self.puzzle.flip_tile("horizontal", current_pos)
#     clicked_tile.update_visual()
#     self.check_tile_status(clicked_tile)

# class Transform: 
#     def apply(self): raise NotImplementedError

# class Rotate(Transform): 
#     def __init__(self, direction: str, tile: Tile) -> None: self.direction, self.tile = direction, tile

# def apply(self): 
#     return self.tile.rotate(self.direction)

# class Flip(Transform): 
#     def __init__(self, direction: str, tile: Tile) -> None: self.direction, self.tile = direction, tile

# def apply(self): 
#     return self.tile.flip(self.direction)

# class Swap(Transform): 
#     def __init__(self, first_tile: Tile, second_tile: Tile) -> None: self.first_tile, self.second_tile = first_tile, second_tile

# def apply(self):
#     p1, p2 = self.first_tile.current_position, self.second_tile.current_position
#     return p1, p2

# #Test if name == "main": try: if root.winfo_exists(): root.destroy() except (NameError, tk.TclError): pass

# root = tk.Tk()
# root.title("Main Gameplay Board")

# GRID_SIZE = 3
# TARGET_PIXEL_SIZE = 450
# TILE_SIDE = TARGET_PIXEL_SIZE // GRID_SIZE

# game_puzzle = Puzzle("small_shapes.png", grid_size=GRID_SIZE, target_size=TARGET_PIXEL_SIZE)
# controller = UserMoves(game_puzzle)

# try:
#     game_puzzle.scramble()
# except AttributeError:
#     pass

# for t_obj in game_puzzle._tiles:
#     r, c = t_obj.current_position
    
#     ui_tile = TkTileCanvas(root, t_obj, TILE_SIDE)
#     ui_tile.grid(row=r, column=c, padx=2, pady=2)
    
#     ui_tile.update_visual()
    
#     controller.check_tile_status(ui_tile)
    
#     ui_tile.bind("<Button-1>", controller.on_tile_click)              # Left Click (Select / Swap)
#     ui_tile.bind("<Button-2>", controller.on_tile_right_click)        # Mac Right Click (Rotate)
#     ui_tile.bind("<Button-3>", controller.on_tile_right_click)        # Windows Right Click (Rotate)
#     ui_tile.bind("<Shift-Button-1>", controller.on_tile_shift_click)  # Shift + Left Click (Flip)

    
# root.mainloop()

