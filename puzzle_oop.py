"""
puzzle_oop.py
=============
OOP core of the tile-puzzle game (HIT137 Group Assignment 3).

BIG PICTURE
-----------
    OpenCV part  -->  list of tile images  -->  Puzzle  -->  many Tile objects
                                                  |
                                                  +-- uses Transform objects (Rotate / Flip / Swap)
                                                      to change the tiles

    * Tile      - one piece of the picture. Knows only about ITSELF (where it is,
                  how it is turned/flipped, its pixels). Never draws anything.
    * Transform - base class for one action on tile(s). Subclasses Rotate, Flip
                  and Swap each implement apply(). Puzzle calls apply() without
                  caring which subclass it holds (polymorphism).
    * Puzzle    - owns all the Tiles, performs and records the player's moves,
                  scrambles the board and tracks whether it is solved.

QUICK START (what the GUI / other modules call)
-----------------------------------------------
    puzzle = Puzzle(tile_images, grid)               # tile_images: list of grid*grid numpy arrays
    puzzle.scramble()                                # call ONCE straight after creating the puzzle
    puzzle.rotate_tile((1, 2))                       # right click       -> rotate 90 deg clockwise
    puzzle.flip_tile('horizontal', (1, 2))           # shift + left click -> flip
    puzzle.swap_tile((0, 0), (2, 1))                 # second left click  -> swap two tiles

POSITIONS
---------
A position is always a (row, col) tuple, (0, 0) = top-left. When you pass a
position to a Puzzle method it means "the tile that is CURRENTLY sitting
there on the board", not "the tile that started there".

READING STATE FROM OTHER MODULES (read only - never assign to these)
--------------------------------------------------------------------
    puzzle._solved          True once every tile is correct (input is then refused)
    puzzle._moves           number of player moves so far (scramble moves do not count)
    puzzle._tiles           list of Tile objects (list order never changes;
                            use each tile's current_position to know where it is drawn)
    puzzle.view_history()   list of the player's moves, oldest first
"""
import cv2      # only used by the test block at the bottom for now (image drawing code will need it later)
import random
import numpy as np
# import OpenCV as ocv

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
        _flipped_vert:        True if the tile is flipped vertically (internal).
        _flipped_horz:        True if the tile is flipped horizontally (internal).
        _is_correct:          result of the last check_is_correct() call (internal).
                              Refreshed by Puzzle.check(); the GUI can use it to
                              decide which tiles get a green tick.
        _image:               numpy array of this tile's pixels exactly as cut
                              from the picture (internal). The Tile stores it but
                              never edits it - whoever draws the board applies the
                              flips / rotation described by the attributes above.
                              NOTE: the order to apply them in (flip, then rotate)
                              still needs agreeing with the OpenCV / GUI members.
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
        return( f"Original position: {self.original_position}\n"
                # f"Current position: {self.current_position}\n"
                # f"Original orientation: {self.original_orientation}\n"
                # f"Current orientation: {self.current_orientation}\n"
                # f"Flipped horizontally: {self._flipped_horz}\n"
               )

    def __repr__(self) -> str:
        # Full debug dump of the tile's state (used when printing a list of tiles).
        return( f"Original position: {self.original_position}\n"
                f"Current position: {self.current_position}\n"
                f"Original orientation: {self.original_orientation}\n"
                f"Current orientation: {self.current_orientation}\n"
                f"Flipped horizontally: {self._flipped}\n"
              )


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
        """Toggle the flip (flipping twice puts it back). Returns nothing."""
        """ Revamped this to have one """
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
        and not flipped in either direction. Stores the answer in
        self._is_correct and also returns it (True / False).
        """
        if self.original_orientation == self.current_orientation and self.original_position == self.current_position and self._flipped == False:
            self._is_correct = True
            return self._is_correct
        else:
            self._is_correct = False
            return self._is_correct


class Puzzle:
    """The whole board: owns every Tile and coordinates everything that happens to them.

    Rotate / Flip / Swap classes are defined further down this file. That is
    fine: Python only looks those names up when a method actually runs.

    Attributes (all internal, see the module docstring for what to read):
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
        output = enumerate(image_list)
        for index, image in output:
            row = index // self._grid
            col = index % self._grid
            self._tiles.append(Tile((row,col),image))

        # print(f"Grid size: {grid}")                                 # Remove when submitting.

    def __str__(self) -> str:
        return f"Current Moves: {self._moves}"

    def check(self):
        """Refresh every tile's correctness flag and update self._solved.

        Returns nothing - read puzzle._solved afterwards.
        A list (square brackets) is built on purpose: all() stops at the first
        False, so with a generator the tiles after it would never be re-checked
        and their _is_correct flags (used for the green ticks) would go stale.
        """
        # all() checks True for each item in an iterator supplied, and returns True if all are True.
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
        """Player move: flip the tile at `position`.

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
                transformation = tile.revert()
            self._move_history = []
            self._moves = 0
            self.check()
            
            

    def scramble(self):
        """Randomly transform the board at the start of a game.

        Call ONCE, right after creating the Puzzle. Applies grid * (grid + 3)
        random Rotate / Flip / Swap transformations directly with .apply(),
        so they are NOT added to the move history and do NOT count as moves.
        Finishes with check() so _solved and the per-tile flags are up to date.
        The print lines are debug output - remove before submitting.

        KNOWN ISSUE: the assignment gives the player only ONE flip (horizontal),
        but this method can also flip tiles VERTICALLY. A tile left vertically
        flipped can never be undone by the player, so the puzzle may be
        impossible to solve. This needs fixing and I'm thinking of taking vertical 
        flips as the istructions stipulates "Flip – a tile is flipped horizontally 
        or vertically." Keyword OR not AND.

        Update: I have removed the flip vertical option from the scramble method. 
        Now the scramble method only uses flip, rotate and swap.
        
        Will remove these comments before final submission.
        """
        count = 0
        for i in range((self._grid * (self._grid + 3))):
            i = random.choice(['rotate', 'flip', 'swap'])     # which kind of transformation
            count += 1
            # print(f"{count}: {i}")
            if i == 'rotate':
                transformation = Rotate(random.choice(self._tiles))
                transformation.apply()
            elif i == 'flip':
                transformation = Flip(random.choice(self._tiles))
                transformation.apply()
            elif i == 'swap':
                # Both tiles are picked independently, so a tile can be "swapped
                # with itself" - harmless, it simply does nothing.
                transformation = Swap(random.choice(self._tiles),random.choice(self._tiles))
                transformation.apply()
        self.check()

    def view_history(self) -> list:
        """Return the player's moves (Transform objects), oldest first.
        This is the real list, not a copy - treat it as read only."""
        return self._move_history


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
    """Flip one tile horizontally or vertically."""

    def __init__(self, tile) -> None:
        """
        Args:
            tile: the Tile object (not a position) to flip.
        """
        super().__init__()
        self.tile = tile

    def __repr__(self) -> str:
        return f"Flipped the tile at {self.tile.current_position}"

    def apply(self):
        """Flip the tile. Raises ValueError for any other direction string.
        Returns None (the Tile flip methods return nothing)."""
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
    def __init__(self, path, grid_size, target) -> None:
        self.grid_size = grid_size
        self._image = load_image(path, grid_size, target)

    def get_image(self):
        return self._image

    def get_tiles(self):
        return split_into_tiles(self._image, self.grid_size)




############################################################### OPENCV SECTION #################################################################################

# TODO: match parameter names with other members
# NOTE: No function for swap tiles. It is in Ibi's code.
# NOTE: Will delete all comments later.



def make_square_img(img):
    height, width = img.shape[:2]
    side = max(height, width)

    return cv2.resize(img, (side, side))




def load_image(path, grid_size, target = 777):
    img  = cv2.imread(path)

    if img is None:
        raise FileNotFoundError("File could not be opened. Try different file.")

    img = make_square_img(img)

    min_tile = 10                                                                        # TODO: needs to be tuned
    side = img.shape[0]
    if side < grid_size * min_tile:
        raise ValueError("Image too small try larger imag or smaller grid.")

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
            tile = img[y : y + tile_side , x : x + tile_side].copy()
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
        raise ValueError("Invalid direction: {direction}. Must be horizontal or vertical.")




def transform_count(grid_size):
    return grid_size * (grid_size - 1)




def assemble_tiles(tiles, grid_size):
    tile_side = tiles[0]._image.shape[0]
    side = tile_side * grid_size
    canvas = np.zeros((side, side, 3), dtype = np.uint8)

    for tile in tiles:
        row, column = tile.current_position
        y = tile_side * row
        x = tile_side * column

        image = tile._image

        if tile._flipped:
            image = flip_tile(image, 'horizontal')

        if tile.current_orientation != 0:
            image = rotate_tile(image, tile.current_orientation)

        canvas[y : tile_side + y, x : tile_side + x] = image

    return canvas


# =============================================================================
# SCRATCH TESTING - only runs when this file is executed directly
# (oop.py), NOT when another module imports it.
# =============================================================================
if __name__ == "__main__":
    path = "1200px.png"
    pic = cv2.imread(path)

    if pic is None:
        raise FileNotFoundError(f"Could not load {path}")


    image = CreateImage(path, small_grid, 777)
    image_tiles = image.get_tiles()
    get_image = image.get_image()
    cv2.imshow("Original Image", get_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    

    puzzle = Puzzle(image_tiles, large_grid)

    puzzle.swap_tile((0, 0), (1, 1))
    puzzle.rotate_tile((0, 0))
    puzzle.flip_tile((0, 1))
    print(puzzle._tiles[0])
    puzzle.scramble()

    puzzle_image = assemble_tiles(puzzle._tiles, small_grid)

    cv2.imshow("Puzzle Image", puzzle_image)
    cv2.waitKey(0)


    print(puzzle.view_history())
    
