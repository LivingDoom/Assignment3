from __future__ import annotations
import cv2
import random
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os
from PIL import Image, ImageTk


class PositionValueError(Exception):
    """Raised when no tile is found at a position that was passed in
    (e.g. a (row, col) that is off the board)."""


class Tile():
    """One piece of the puzzle.

    A Tile only knows about ITSELF: where it started, where it is now, how it
    is turned/flipped, and its slice of the picture. It never looks at other
    tiles and never draws anything. Change its state through its methods,
    normally via a Transform object (see below).

    Attributes:
        original_position:    (row, col) where the tile belongs in the solved
                              picture. Never changes.
        current_position:     (row, col) where the tile currently sits on the
                              board. Changed by Swap.
        original_orientation: always 0 (solved = upright).
        current_orientation:  0, 90, 180 or 270 degrees, clockwise.
        _flipped:             True if the tile is flipped horizontally (internal).
        _is_correct:          result of the last check_is_correct() call (internal).
                              Refreshed by Puzzle.check(); the GUI uses it to
                              decide which tiles get a green tick.
        _image:               numpy array of this tile's pixels exactly as cut
                              from the picture (internal). The Tile stores it but
                              never edits it - whoever draws the board applies the
                              flip and then the rotation described by the
                              attributes above (see assemble_tiles).
    """

    def __init__(self, original_position, image) -> None:
        """
        Args:
            original_position: (row, col) home of this tile in the solved picture.
            image: numpy array (the pixels for this tile).
        """
        self.original_position = original_position
        self.current_position = original_position   # starts solved, scramble moves it later
        self.original_orientation = 0        # 0
        self.current_orientation = 0         # 0, 90, 180, 270
        self._flipped = False
        self._is_correct = False
        self._image = image

    def __str__(self) -> str:
        # Short, human-readable version (used by print(tile)).
        return (f"Original position: {self.original_position}\n")

    def __repr__(self) -> str:
        # Full debug dump of the tile's state (used when printing a list of tiles).
        return (f"Original position: {self.original_position}\n"
                f"Current position: {self.current_position}\n"
                f"Original orientation: {self.original_orientation}\n"
                f"Current orientation: {self.current_orientation}\n"
                f"Flipped horizontally: {self._flipped}\n")

    # Rotation ============================================================
    def rotate(self):
        """Rotate the tile 90 degrees clockwise.

        The orientation wraps around: 0 -> 90 -> 180 -> 270 -> 0.
        Returns the new orientation in degrees.
        """
        self.current_orientation = (self.current_orientation + 90) % 360
        return self.current_orientation

    # Flipping =============================================================
    def flip(self):
        """Flip the tile horizontally as it is DISPLAYED (flipping twice puts it back).

        The picture is drawn as: flip first, then rotate. Mirroring an already
        rotated tile therefore also reverses its rotation, which is why a tile
        at 90 or 270 degrees gets an extra 180 here. Returns nothing.
        """
        if self.current_orientation in (90, 270):
            self.current_orientation = (self.current_orientation + 180) % 360
        self._flipped = not self._flipped

    # Solve ================================================================
    def revert(self):
        self.current_position = self.original_position
        self.current_orientation = 0
        self._flipped = False
        self._is_correct = True
        return self.current_position, self.current_orientation, self._flipped, self._is_correct

    # Checks ===============================================================
    def check_is_correct(self):
        """Is this tile in its solved state?

        Correct means ALL of: back at its original position, orientation 0,
        and not flipped. Stores the answer in self._is_correct and also
        returns it (True / False).
        """
        if (self.original_orientation == self.current_orientation
                and self.original_position == self.current_position
                and self._flipped is False):
            self._is_correct = True
        else:
            self._is_correct = False
        return self._is_correct


class Puzzle:
    """The whole board: owns every Tile and coordinates everything that happens to them.

    Rotate / Flip / Swap classes are defined further down this file. That is
    fine: Python only looks those names up when a method actually runs.

    Attributes (all internal):
        _grid:         tiles per side (3, 4 or 5).
        _tiles:        list of Tile objects. The LIST ORDER NEVER CHANGES
                       (row-major from the original picture); a tile's place on
                       the board is its current_position.
        _moves:        number of player moves (rotate, flip or swap each = 1).
        _move_history: list of Transform objects for the player's moves.
        _solved:       True when every tile is correct. Once True, the move
                       methods refuse further input.
    """

    def __init__(self, image_list: list[np.ndarray], grid: int):
        """Build one Tile per image.

        Args:
            image_list: flat list of numpy arrays in row-major order
                        (index 0 = top-left, then along the top row, then the
                        next row down...). Must hold grid * grid images
                        (this is not checked).
            grid: tiles per side - 3, 4 or 5.
        """
        self._grid = grid
        self._tiles = []
        self._moves = 0
        self._move_history = []
        self._solved = False

        # Turn each image's list index into a (row, col) position:
        # row = index // grid, col = index % grid   e.g. grid 3, index 7 -> (2, 1)
        for index, image in enumerate(image_list):
            row = index // self._grid
            col = index % self._grid
            self._tiles.append(Tile((row, col), image))

    def __str__(self) -> str:
        return f"Current Moves: {self._moves}"

    def check(self):
        """Refresh every tile's correctness flag and update self._solved.

        Returns nothing - read puzzle._solved afterwards.
        A list (square brackets) is built on purpose: all() stops at the first
        False, so with a generator the tiles after it would never be re-checked
        and their _is_correct flags (used for the green ticks) would go stale.
        """
        self._solved = all([tile.check_is_correct() for tile in self._tiles])

    def trans_helper(self, transformation):
        """INTERNAL. The shared last step of every player move.

        Applies the transformation, records it in the history, counts the move
        and re-checks the puzzle. rotate_tile / flip_tile / swap_tile all end
        by calling this, so every move is applied, logged, counted and checked
        in exactly one place. (If apply() raises, nothing is logged or counted.)
        Returns the transformation.
        """
        transformation.apply()
        self._move_history.append(transformation)
        self._moves += 1
        self.check()
        return transformation

    def rotate_tile(self, position):
        """Player move: rotate the tile at `position` 90 degrees clockwise.

        Returns the Rotate object, or None if the puzzle is already solved
        (nothing happens and no move is counted).
        Raises PositionValueError if no tile is at `position`.
        """
        tile = None
        if self._solved is True:            # solved -> refuse all further input
            return None
        # Look up which Tile is currently sitting at `position`.
        # (We must search: the _tiles list never reorders when tiles are swapped.)
        for t in self._tiles:
            if t.current_position == position:
                tile = t
                break
        if tile is None:
            raise PositionValueError(f"Tile at position {position}")

        transformation = Rotate(tile)
        return self.trans_helper(transformation)

    def flip_tile(self, position):
        """Player move: flip the tile at `position` horizontally.

        Args:
            position: (row, col) of the tile as it currently sits on the board.
        Returns the Flip object, or None if the puzzle is already solved.
        Raises PositionValueError if no tile is at `position`.
        """
        tile = None
        if self._solved is True:
            return None
        for t in self._tiles:
            if t.current_position == position:
                tile = t
                break
        if tile is None:
            raise PositionValueError(f"Tile at position {position} is None (inside flip_tile)")

        transformation = Flip(tile)
        return self.trans_helper(transformation)

    def swap_tile(self, first_pos, second_pos):
        """Player move: swap the tiles currently at two board positions.

        Args:
            first_pos, second_pos: (row, col) positions on the board.
        Returns the Swap object, or None if the puzzle is already solved.
        Raises PositionValueError if either position has no tile.
        """
        tile = None
        tile2 = None
        if self._solved is True:
            return None
        # Two separate searches (one per position), one break each.
        for t in self._tiles:
            if t.current_position == first_pos:
                tile = t
                break
        for t2 in self._tiles:
            if t2.current_position == second_pos:
                tile2 = t2
                break
        if tile is None:
            raise PositionValueError(f"Tile at position {first_pos}")
        elif tile2 is None:
            raise PositionValueError(f"Tile at position {second_pos}")

        transformation = Swap(tile, tile2)
        return self.trans_helper(transformation)

    def solve(self):
        """Instantly solve the puzzle and clear the moves and score.
        Finishes with self.check() so _solved becomes True."""
        for tile in self._tiles:
            tile.revert()
        self._move_history = []
        self._moves = 0
        self.check()

    def scramble(self):
        """Randomly transform the board at the start of a game.

        Applies grid * (grid + 3) random Rotate / Flip / Swap transformations
        directly with .apply(), so they are NOT added to the move history and
        do NOT count as moves. Finishes with check() so _solved and the
        per-tile flags are up to date.

        Only horizontal flips are used, because that is the only flip the
        player has - a vertically flipped tile could never be undone.
        """
        for _ in range(self._grid * (self._grid + 3)):
            kind = random.choice(['rotate', 'flip', 'swap'])
            if kind == 'rotate':
                transformation = Rotate(random.choice(self._tiles))
            elif kind == 'flip':
                transformation = Flip(random.choice(self._tiles))
            else:
                # Both tiles are picked independently, so a tile can be "swapped
                # with itself" - harmless, it simply does nothing.
                transformation = Swap(random.choice(self._tiles), random.choice(self._tiles))
            transformation.apply()
        self.check()

    def view_history(self) -> list:
        """Return the player's moves (Transform objects), oldest first.
        This is the real list, not a copy - treat it as read only."""
        return self._move_history

    def get_board_image(self):
        return assemble_tiles(self._tiles, self._grid)


# Grid sizes the player can choose from.
small_grid = 3
medium_grid = 4
large_grid = 5


# =============================================================================
# TRANSFORMS
# Each one wraps a single action on tile(s). Build it with the tile object(s)
# to act on, then call .apply(). Building a Transform does nothing by itself.
# Transforms never log or count moves - only Puzzle's *_tile methods do that
# (that is why scramble() can use them without affecting the move count).
# =============================================================================
class Transform:
    """Base class. Every subclass must override apply()."""

    def __init__(self) -> None:
        ...

    def apply(self):
        """Perform the action. Subclasses must implement this."""
        raise NotImplementedError


class Rotate(Transform):
    """Rotate one tile 90 degrees clockwise."""

    def __init__(self, tile) -> None:
        """Args: tile - the Tile object (not a position) to rotate."""
        super().__init__()
        self.tile = tile

    def __repr__(self) -> str:
        return f"Rotated tile at {self.tile.current_position}"

    def apply(self):
        """Rotate the tile. Returns the tile's new orientation in degrees."""
        return self.tile.rotate()


class Flip(Transform):
    """Flip one tile horizontally."""

    def __init__(self, tile) -> None:
        """Args: tile - the Tile object (not a position) to flip."""
        super().__init__()
        self.tile = tile

    def __repr__(self) -> str:
        return f"Flipped the tile at {self.tile.current_position}"

    def apply(self):
        """Flip the tile. Returns None (Tile.flip returns nothing)."""
        return self.tile.flip()


class Swap(Transform):
    """Exchange the board positions of two tiles."""

    def __init__(self, first_tile, second_tile) -> None:
        """Args: first_tile, second_tile - Tile objects (not positions)."""
        super().__init__()
        self.first_tile = first_tile
        self.second_tile = second_tile

    def __repr__(self) -> str:
        return f"Swapped {self.first_tile.current_position} tile with {self.second_tile.current_position} "

    def apply(self):
        """Swap the two tiles' current_position values.
        Returns (position1, position2) as they were BEFORE the swap.
        Note: the swap logic lives here, not in Tile, because Tile is not
        meant to know about other tiles."""
        position1 = self.first_tile.current_position
        position2 = self.second_tile.current_position
        self.first_tile.current_position = position2
        self.second_tile.current_position = position1
        return position1, position2


# Loads and resizes and cuts the image.

class CreateImage:
    def __init__(self, path, grid_size, target=777) -> None:
        self.grid_size = grid_size
        self._image = load_image(path, grid_size, target)

    def get_image(self):
        return self._image

    def get_tiles(self):
        return split_into_tiles(self._image, self.grid_size)


############################################################### OPENCV SECTION #################################################################################

def make_square_img(img):
    height, width = img.shape[:2]
    side = max(height, width)

    return cv2.resize(img, (side, side))


def load_image(path, grid_size, target=777):
    img = cv2.imread(path)

    if img is None:
        raise FileNotFoundError("File could not be opened. Try different file.")

    img = make_square_img(img)

    min_tile = 10                                                                        # TODO: needs to be tuned
    side = img.shape[0]
    if side < grid_size * min_tile:
        raise ValueError("Image too small try larger image or smaller grid.")

    new_side = target // grid_size * grid_size

    img = cv2.resize(img, (new_side, new_side))

    return img


def split_into_tiles(img, grid_size):
    tile_side = img.shape[0] // grid_size
    tiles = []

    for rows in range(grid_size):
        for columns in range(grid_size):
            y = tile_side * rows
            x = tile_side * columns
            tile = img[y: y + tile_side, x: x + tile_side].copy()
            tiles.append(tile)

    return tiles


def rotate_tile(tile_img, angle):
    if angle == 90:
        return cv2.rotate(tile_img, cv2.ROTATE_90_CLOCKWISE)
    if angle == 180:
        return cv2.rotate(tile_img, cv2.ROTATE_180)
    if angle == 270:
        return cv2.rotate(tile_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        raise ValueError(f"Invalid angle: {angle}. Must be 90, 180, or 270.")


def flip_tile(tile_img, direction):
    if direction == 'horizontal':
        return cv2.flip(tile_img, 1)
    if direction == 'vertical':
        return cv2.flip(tile_img, 0)
    else:
        raise ValueError(f"Invalid direction: {direction}. Must be horizontal or vertical.")


def transform_count(grid_size):
    return grid_size * (grid_size - 1)


def assemble_tiles(tiles, grid_size):
    tile_side = tiles[0]._image.shape[0]
    side = tile_side * grid_size
    canvas = np.zeros((side, side, 3), dtype=np.uint8)

    for tile in tiles:
        row, column = tile.current_position
        y = tile_side * row
        x = tile_side * column

        image = tile._image

        if tile._flipped:
            image = flip_tile(image, 'horizontal')

        if tile.current_orientation != 0:
            image = rotate_tile(image, tile.current_orientation)

        canvas[y: tile_side + y, x: x + tile_side] = image

    return canvas


############################################################### USER INTERACTION / SOLVE / HINT #################################################################################
"""
Kayla Section Remove before submission:
Solving the Puzzle
    - Left click selects a tile (coloured border). A second left click on a
      different tile swaps the two and clears the selection. Clicking the
      same tile again deselects it.
    - Right click rotates a tile 90 degrees clockwise.
    - Shift + left click flips a tile horizontally.
    - A tile in the right place and orientation gets a small green tick.

Moves and score
    - Each swap, rotate or flip is one move. Selecting does not count.
    - When every tile is correct the player is told and input stops.

Hints
    - Hint marks one incorrect tile with a blue circle on the puzzle and its
      home position with a blue circle on the original. The circles go away
      after the next move. At most 3 hints per image, then the button is
      disabled.
    - Solve undoes everything instantly and clears moves and score.
"""


class UserMoves:
    """Turns player input into Puzzle moves, and owns the selection and hint state.

    This class never draws anything and never touches Tk. The GUI works out
    WHICH tile was clicked (a (row, col) board position) and calls the
    matching method here, then redraws from the state held here and in Puzzle.
    Puzzle stays the single source of truth for tile positions.
    """

    MAX_HINTS = 3

    def __init__(self, puzzle: Puzzle):
        self.puzzle = puzzle
        self.selected_pos = None        # (row, col) of the selected tile, or None
        self.hints_left = self.MAX_HINTS
        self.hint_tile = None           # Tile currently marked by a hint, or None

    def _after_move(self, result):
        """A real move happened (Puzzle returned a Transform): hints expire."""
        if result is None:              # puzzle was already solved, nothing happened
            return False
        self.hint_tile = None
        return True

    def click(self, pos):
        """Left click. Returns True only if a swap actually happened."""
        if self.puzzle._solved:
            return False
        if self.selected_pos is None:               # first click: select
            self.selected_pos = pos
            return False
        if self.selected_pos == pos:                # same tile again: deselect
            self.selected_pos = None
            return False
        first, self.selected_pos = self.selected_pos, None
        return self._after_move(self.puzzle.swap_tile(first, pos))

    def rotate(self, pos):
        """Right click. Returns True if the tile was rotated."""
        return self._after_move(self.puzzle.rotate_tile(pos))

    def flip(self, pos):
        """Shift + left click. Returns True if the tile was flipped."""
        return self._after_move(self.puzzle.flip_tile(pos))

    def hint(self):
        """Pick one incorrect tile to mark. Returns the Tile, or None if no
        hints are left or there is nothing left to fix. Not a move."""
        if self.hints_left <= 0 or self.puzzle._solved:
            return None
        wrong = [t for t in self.puzzle._tiles if not t._is_correct]
        if not wrong:
            return None
        self.hint_tile = random.choice(wrong)
        self.hints_left -= 1
        return self.hint_tile

    def solve(self):
        """Solve instantly (Puzzle clears moves and score) and reset UI state."""
        self.puzzle.solve()
        self.selected_pos = None
        self.hint_tile = None

    def can_hint(self):
        return self.hints_left > 0 and not self.puzzle._solved


############################################################### GUI SECTION #################################################################################


class ImagePuzzleGame:

    def __init__(self, window):
        # Main Window
        self.window = window
        self.window.title("Image Puzzle Window")
        try:
            self.window.state("zoomed")                 # Windows
        except tk.TclError:
            try:
                self.window.attributes("-zoomed", True)  # Linux
            except tk.TclError:
                pass

        # Selecting the image
        self.selected_image = ""

        # Game state (None until an image has been loaded)
        self.creator = None
        self.puzzle = None
        self.user_moves = None
        self.grid_size = 3

        # Where the board sits on each canvas, so clicks can be mapped to tiles
        self.board_left = self.board_top = self.board_size = 0
        self.orig_left = self.orig_top = self.orig_size = 0

        self.create_layout()
        self.create_widgets()

    def create_layout(self):
        # TOP TITLE
        self.title_frame = ttk.Frame(self.window)
        self.title_frame.pack(fill="x", padx=5, pady=5)
        self.title_label = tk.Label(self.title_frame, text="*** IMAGE PUZZLE GAME ***", font=("Arial", 20, "bold"), fg="red")
        self.title_label.pack(pady=5)

        # IMAGE AND GAME CONTROLS
        self.controls_frame = ttk.Frame(self.window)
        self.controls_frame.pack(fill="x", padx=5, pady=5)
        for column in range(6):
            self.controls_frame.columnconfigure(column, weight=1)
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # ORIGINAL IMAGE
        self.original_frame = tk.Frame(self.main_frame, bd=2, relief="solid")
        self.original_frame.pack(side="left", fill="both", expand=True, padx=4)
        self.original_heading = tk.Label(self.original_frame, text="ORIGINAL IMAGE", font=("Arial", 14, "bold"))
        self.original_heading.pack(pady=5)
        self.original_canvas = tk.Canvas(self.original_frame, bg="white", highlightthickness=0)
        self.original_canvas.pack(fill="both", expand=True)

        # PUZZLE IMAGE
        self.puzzle_frame = tk.LabelFrame(self.main_frame, bd=2, relief="solid")
        self.puzzle_frame.pack(side="right", fill="both", expand=True, padx=4)
        self.puzzle_heading = tk.Label(self.puzzle_frame, text="PUZZLE IMAGE", font=("Arial", 14, "bold"))
        self.puzzle_heading.pack(pady=5)
        self.puzzle_canvas = tk.Canvas(self.puzzle_frame, bg="white", highlightthickness=0)
        self.puzzle_canvas.pack(fill="both", expand=True)

        # Mouse input on the puzzle board
        self.puzzle_canvas.bind("<Button-1>", self.on_left_click)
        self.puzzle_canvas.bind("<Shift-Button-1>", self.on_shift_click)
        self.puzzle_canvas.bind("<Button-3>", self.on_right_click)
        self.puzzle_canvas.bind("<Button-2>", self.on_right_click)    # right click on macOS

        # BOTTOM STATUS BAR
        self.bottom_frame = ttk.Frame(self.window)
        self.bottom_frame.pack(fill="x", padx=5, pady=5)
        for column in range(7):
            self.bottom_frame.columnconfigure(column, weight=1)

    def create_widgets(self):
        # Open Image button
        self.open_button = tk.Button(self.controls_frame, text="Open An Image From Your Files Here", font=("Arial", 12), bg="white", fg="blue", bd=2, relief="solid", padx=15, pady=8, command=self.click_image)
        self.open_button.grid(row=0, column=0, padx=10, pady=5)
        # Chosen image
        self.chose_image_label = tk.Label(self.controls_frame, text="You have chosen Image:", font=("Arial", 12))
        self.chose_image_label.grid(row=0, column=1, padx=10)
        self.image_entry = tk.Entry(self.controls_frame, width=25, font=("Arial", 12))
        self.image_entry.grid(row=0, column=2, padx=10)

        # Grid size
        self.grid_label = tk.Label(self.controls_frame, text="Choose Your Grid Size:", font=("Arial", 12))
        self.grid_label.grid(row=0, column=3, padx=10)
        self.grid_box = ttk.Combobox(self.controls_frame, values=["3 x 3", "4 x 4", "5 x 5"], width=15, font=("Arial", 12), state="disabled")
        self.grid_box.current(0)
        self.grid_box.grid(row=0, column=4, padx=10)

        # Load button
        self.load_image_button = tk.Button(self.controls_frame, text="Load Image For Puzzle Game", font=("Arial", 12), bg="white", fg="blue", bd=2, relief="solid", padx=15, pady=8, command=self.load_image)
        self.load_image_button.grid(row=0, column=5, padx=20)

        # Bottom row
        self.status = tk.Label(self.bottom_frame, text="Status:", font=("Arial", 12))
        self.status.grid(row=0, column=0, padx=10)
        self.moves = tk.Label(self.bottom_frame, text="Number of Moves:", font=("Arial", 12))
        self.moves.grid(row=0, column=2, padx=40)
        self.incorrect_tiles = tk.Label(self.bottom_frame, text="Number of Incorrect Tiles:", font=("Arial", 12))
        self.incorrect_tiles.grid(row=0, column=4, padx=10)
        self.hints_left = tk.Label(self.bottom_frame, text="Hints Left:", font=("Arial", 12))
        self.hints_left.grid(row=0, column=6, padx=10)
        self.hint_button = tk.Button(self.bottom_frame, text="Hints", font=("Arial", 14), bg="white", fg="red", bd=2, relief="solid", padx=15, pady=8, command=self.hint)
        self.hint_button.grid(row=0, column=8, padx=40)
        self.solved_button = tk.Button(self.bottom_frame, text="Solve", font=("Arial", 14), bg="white", fg="green", bd=2, relief="solid", padx=15, pady=8, command=self.solve)
        self.solved_button.grid(row=0, column=9, padx=40)
        self.instructions_button = tk.Button(self.bottom_frame, text="Instructions", font=("Arial", 14), bg="white", fg="blue", bd=2, relief="solid", padx=15, pady=8, command=self.instructions)
        self.instructions_button.grid(row=0, column=10, padx=40)

    def instructions(self):
        messagebox.showinfo(
            "How to Play",
            "1. Open and choose an image from your file.\n"
            "2. Select your grid size.\n"
            "3. Load your picture and grid size\n"
            "4. Restore the scrambled tiles to solve the puzzle.\n"
            "5. Left click on the tile selects, the selected tile is highlighted with a coloured border.\n"
            "6. Left clicking a second tile swaps the two tiles and clears the selection.\n"
            "7. Left clicking the same tile again deselects it.\n"
            "8. Right click on a tile rotates it 90 degrees clockwise.\n"
            "9. Shift + left click on a tile flips it horizontally.\n"
            "10. A small green tick will show when you have it right.\n"
            "11. Use hints if you get stuck, only 3 allowed.\n"
            "12. You will be notified of the number of moves and number of tiles still incorrect.\n"
            "13. When all tiles are in the correct position, you win!! GAME OVER.\n"
            "14. You can load another game. Good Luck."
        )

    # Open Image ===========================================================
    def click_image(self):
        file_path = filedialog.askopenfilename(
            title="choose an Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("JPG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("BMP files", "*.bmp")
            ]
        )
        if file_path:
            self.selected_image = file_path
            image_name = os.path.basename(file_path)  # The file name
            self.image_entry.delete(0, tk.END)
            self.image_entry.insert(0, image_name)
            self.grid_box.config(state="readonly")

    # Load Image ===========================================================
    def load_image(self):
        if self.selected_image == "":
            messagebox.showwarning("No Image Selected", "Please choose an image first")
            return

        grid_size = int(self.grid_box.get().split(" ")[0])

        try:
            creator = CreateImage(self.selected_image, grid_size)
        except (FileNotFoundError, ValueError) as e:
            messagebox.showerror("Could not Load image.", str(e))
            return

        # Only switch over once loading has succeeded, so a failed load leaves
        # the old game (and its grid size) intact.
        self.creator = creator
        self.grid_size = grid_size
        self.puzzle = Puzzle(self.creator.get_tiles(), self.grid_size)
        self.puzzle.scramble()
        while self.puzzle._solved:          # extremely unlikely, but never start solved
            self.puzzle.scramble()
        self.user_moves = UserMoves(self.puzzle)

        self.display_original_image()
        self.refresh_board()

    # Display ==============================================================
    def display_original_image(self):
        if self.creator is None:
            return
        image = Image.fromarray(cv2.cvtColor(self.creator.get_image(), cv2.COLOR_BGR2RGB))
        width = self.original_canvas.winfo_width()
        height = self.original_canvas.winfo_height()
        image.thumbnail((max(1, width - 40), max(1, height - 20)), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.original_canvas.original_photo = photo
        self.original_canvas.delete("original_image")
        self.original_canvas.create_image(width / 2, height / 2, image=photo, anchor="center", tags="original_image")

        # Remember where the picture landed (used to place the hint circle)
        self.orig_size = min(photo.width(), photo.height())
        self.orig_left = (width - photo.width()) / 2
        self.orig_top = (height - photo.height()) / 2

        self.draw_original_overlay()
        self.original_canvas.bind("<Configure>", self.resize_original_image)

    def display_puzzle_image(self, puzzle_image):
        image = Image.fromarray(cv2.cvtColor(puzzle_image, cv2.COLOR_BGR2RGB))
        width = self.puzzle_canvas.winfo_width()
        height = self.puzzle_canvas.winfo_height()
        image.thumbnail((max(1, width - 40), max(1, height - 20)), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.canvas_puzzle_photo = photo

        for tag in ("puzzle_image", "puzzle_grid", "tick", "selection", "hint"):
            self.puzzle_canvas.delete(tag)
        self.puzzle_canvas.create_image(width / 2, height / 2, image=photo, anchor="center", tags="puzzle_image")

        # Remember where the board sits so clicks can be mapped to tiles
        self.board_size = min(photo.width(), photo.height())
        self.board_left = (width - photo.width()) / 2
        self.board_top = (height - photo.height()) / 2

        self.faint_puzzle_grid(self.grid_size)
        self.draw_overlays()
        self.puzzle_canvas.bind("<Configure>", self.resize_puzzle_image)

    def faint_puzzle_grid(self, grid_size):
        left, top, size = self.board_left, self.board_top, self.board_size
        tile_size = size / grid_size
        for i in range(1, grid_size):
            x = left + i * tile_size
            y = top + i * tile_size
            self.puzzle_canvas.create_line(x, top, x, top + size, fill="grey", width=2, tags="puzzle_grid")
            self.puzzle_canvas.create_line(left, y, left + size, y, fill="grey", width=2, tags="puzzle_grid")
        self.puzzle_canvas.create_rectangle(left, top, left + size, top + size, outline="grey", width=2, tags="puzzle_grid")

    def resize_original_image(self, event):
        if self.creator is None:
            return
        self.display_original_image()

    def resize_puzzle_image(self, event):
        if self.puzzle is None:
            return
        self.display_puzzle_image(self.puzzle.get_board_image())

    # Overlays: ticks, selection border, hint circles =======================
    def draw_overlays(self):
        """Green ticks, the selection border and the hint circle on the puzzle.
        Called at the end of display_puzzle_image, so they survive resizes."""
        canvas = self.puzzle_canvas
        for tag in ("tick", "selection", "hint"):
            canvas.delete(tag)
        if self.puzzle is None or self.user_moves is None or self.board_size == 0:
            return

        tile_px = self.board_size / self.grid_size

        for tile in self.puzzle._tiles:
            if tile._is_correct:
                self.draw_tick(tile.current_position, tile_px)

        hint_tile = self.user_moves.hint_tile
        if hint_tile is not None:
            self.draw_hint_circle(canvas, self.board_left, self.board_top, tile_px, hint_tile.current_position)

        selected = self.user_moves.selected_pos
        if selected is not None:
            row, col = selected
            x0 = self.board_left + col * tile_px
            y0 = self.board_top + row * tile_px
            canvas.create_rectangle(x0 + 2, y0 + 2, x0 + tile_px - 2, y0 + tile_px - 2,
                                    outline="red", width=4, tags="selection")

    def draw_tick(self, pos, tile_px):
        """A small green tick in the top-right corner of a tile (white outline
        underneath so it shows on light and dark pictures)."""
        row, col = pos
        s = max(8, tile_px * 0.11)
        cx = self.board_left + (col + 1) * tile_px - 8 - s
        cy = self.board_top + row * tile_px + 8
        points = (cx, cy + 0.5 * s, cx + 0.35 * s, cy + 0.9 * s, cx + s, cy)
        self.puzzle_canvas.create_line(*points, fill="white", width=8, capstyle="round", joinstyle="round", tags="tick")
        self.puzzle_canvas.create_line(*points, fill="green", width=4, capstyle="round", joinstyle="round", tags="tick")

    def draw_hint_circle(self, canvas, left, top, tile_px, pos):
        row, col = pos
        cx = left + (col + 0.5) * tile_px
        cy = top + (row + 0.5) * tile_px
        r = tile_px * 0.35
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="blue", width=5, tags="hint")

    def draw_original_overlay(self):
        """Blue circle on the original image at the hinted tile's home position."""
        self.original_canvas.delete("hint")
        if self.user_moves is None or self.user_moves.hint_tile is None or self.orig_size == 0:
            return
        tile_px = self.orig_size / self.grid_size
        self.draw_hint_circle(self.original_canvas, self.orig_left, self.orig_top, tile_px,
                              self.user_moves.hint_tile.original_position)

    # Redraw + labels ======================================================
    def refresh_board(self):
        self.display_puzzle_image(self.puzzle.get_board_image())
        self.draw_original_overlay()
        self.update_status()

    def update_status(self):
        incorrect = sum(1 for t in self.puzzle._tiles if not t._is_correct)
        self.moves.config(text=f"Number of Moves: {self.puzzle._moves}")
        self.incorrect_tiles.config(text=f"Number of Incorrect Tiles: {incorrect}")
        self.status.config(text="Status: Solved!" if self.puzzle._solved else "Status: Playing")
        self.hints_left.config(text=f"Hints Left: {self.user_moves.hints_left}")
        self.hint_button.config(state="normal" if self.user_moves.can_hint() else "disabled")

    # Mouse handling =======================================================
    def tile_at(self, event):
        """Return the (row, col) under the mouse, or None if the click doesn't count
        (no game loaded, puzzle already solved, or click outside the board)."""
        if self.puzzle is None or self.user_moves is None or self.puzzle._solved:
            return None
        x = event.x - self.board_left
        y = event.y - self.board_top
        if not (0 <= x < self.board_size and 0 <= y < self.board_size):
            return None
        tile_px = self.board_size / self.grid_size
        return (int(y // tile_px), int(x // tile_px))

    def on_left_click(self, event):
        pos = self.tile_at(event)
        if pos is not None:
            self.after_move(self.user_moves.click(pos))

    def on_right_click(self, event):
        pos = self.tile_at(event)
        if pos is not None:
            self.after_move(self.user_moves.rotate(pos))

    def on_shift_click(self, event):
        pos = self.tile_at(event)
        if pos is not None:
            self.after_move(self.user_moves.flip(pos))

    def after_move(self, moved):
        """Redraw, and announce the win if this move finished the puzzle."""
        self.refresh_board()
        if moved and self.puzzle._solved:
            messagebox.showinfo("Puzzle Solved!",
                                f"Well done! You solved it in {self.puzzle._moves} moves.\n"
                                "Load another image to keep playing.")

    # Buttons ==============================================================
    def hint(self):
        if self.user_moves is None:
            return
        if self.user_moves.hint() is not None:
            self.refresh_board()

    def solve(self):
        if self.user_moves is None:
            return
        self.user_moves.solve()
        self.refresh_board()


if __name__ == "__main__":
    window = tk.Tk()
    game = ImagePuzzleGame(window)
    window.mainloop()
