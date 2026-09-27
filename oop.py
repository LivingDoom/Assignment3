# OOP .py file for the all objects needed for to create the puzzle game.
import cv2
import random
import numpy as np

pic = cv2.imread("small_shapes.png")

if pic is None:
    raise FileNotFoundError("Could not load small_shapes.png")

snippet = pic[100:200, 100:200]

class Winner(Exception):
    """Raised when the puzzle is solved."""

class PositionValueError(Exception):
    """Raise error for position no found"""

class Tile():
    
    def __init__(self, original_position, image) -> None:
        

        self.original_position = original_position
        self.current_position = original_position
        self.original_orientation = 0        # 0
        self.current_orientation = 0         # 0, 90, 180, 270
        self._flipped_vert = False
        self._flipped_horz = False
        self._is_correct = False
        self._image = image

    def __str__(self) -> str:
        return( f"Original position: {self.original_position}\n"
                # f"Current position: {self.current_position}\n"
                # f"Original orientation: {self.original_orientation}\n"
                # f"Current orientation: {self.current_orientation}\n"
                # f"Flipped horizontally: {self._flipped_horz}\n"
                # f"Flipped vertically: {self._flipped_vert}\n"
               )       

    def __repr__(self) -> str:
        return( f"Original position: {self.original_position}\n"
                f"Current position: {self.current_position}\n"
                f"Original orientation: {self.original_orientation}\n"
                f"Current orientation: {self.current_orientation}\n"
                f"Flipped horizontally: {self._flipped_horz}\n"
                f"Flipped vertically: {self._flipped_vert}\n"
              )
    

    # Rotation ============================================================
    def rotate(self, direction):
        if direction not in ('cw', 'ccw'):
            raise ValueError(f"{direction} is not a valid input, use cw or ccw for rotation input")
        step = 90 if direction == 'cw' else -90
        self.current_orientation = (self.current_orientation + step)% 360
        return self.current_orientation


    # Flipping =============================================================   
    def flip_vert(self):
        self._flipped_vert = not self._flipped_vert
    def flip_horz(self):
        self._flipped_horz = not self._flipped_horz

    # Checks ===============================================================
    def check_is_correct(self):
        if self.original_orientation == self.current_orientation and self.original_position == self.current_position and self._flipped_horz == False and self._flipped_vert == False:
            self._is_correct = True
            return self._is_correct
        else:
            self._is_correct = False
            return self._is_correct
        

class Puzzle:
    # This is the section where OpenCV's split up image will come into the function.
    # CreateImage class below is what i was aiming to make the images from, then pass it into this class.

    def __init__(self, image_list: list[np.ndarray], grid: int): 
        self._grid = grid
        self._tiles = []
        self._moves = 0
        self._move_history = []
        self._correct_list = []
        
        output = enumerate(image_list)
        for index, image in output:
            row = index // self._grid
            col = index % self._grid
            self._tiles.append(Tile((row,col),image))

        # print(self._tiles)
        # for i in self._tiles:
        #     print(repr(i))
        # self.check()

    def __str__(self) -> str:
        return f"Current Moves: {self._moves}"
        
    def check(self):
        # all() checks True for each item in an iterator supplied, and returns True if all are True.
        return all(tile.check_is_correct() for tile in self._tiles)

    def rotate_tile(self, direction, position):
        tile = None
        for t in self._tiles:
            if t.current_position == position:
                tile = t
                break
        if tile is None:
            raise PositionValueError(f"Tile at position {position}")
        
        transformation = Rotate(direction, tile)
        transformation.apply()
        self._move_history.append(transformation)
        self._moves += 1
        return transformation

    def flip_tile(self, direction, position):
            tile = None
            for t in self._tiles:
                if t.current_position == position:
                    tile = t
                    break
            if tile is None:
                raise PositionValueError(f"Tile at position {position}")
            
            transformation = Flip(direction, tile)
            transformation.apply()
            self._move_history.append(transformation)
            self._moves += 1
            return transformation
    
    def swap_tile(self, first_pos, second_pos):
        tile = None
        tile2 = None
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
        transformation.apply()
        self._move_history.append(transformation)
        self._moves += 1
        return transformation

    def scramble(self, count):
        pass
    
    def view_history(self) -> list:
        return self._move_history
        

small_grid = 3
medium_grid = 4
large_grid = 5

# To reach inner objects in Puzzle._tiles list: 
# puzzle._tiles[0].rotate('cw') will change the rotate value, etc... 
# access Obj Name -> method/data type inside the puzzle -> the method/data type inside Tile class 
# as it's being created by puzzle -> then assign/change/view the value accordingly.


class Transform:
    def __init__(self) -> None:
        ...
    
    def apply(self):
        raise NotImplementedError

class Rotate(Transform):
    def __init__(self, direction, tile) -> None:
        super().__init__()
        self.direction = direction
        self.tile = tile

    def __repr__(self) -> str:
        return f"Rotate({self.direction}, tile at {self.tile.current_position})"
    
    def apply(self):
        return self.tile.rotate(self.direction)

class Flip(Transform):
    def __init__(self, function, tile) -> None:
        super().__init__()
        self.function = function
        self.tile = tile

    def __repr__(self) -> str:
        return f"Fliped the tile {self.function} at {self.tile.current_position}"
    
    def apply(self):
        if self.function not in ('horz','vert'):
            raise ValueError(f"Incorrect flip direction given. Use 'horz' of 'vert' only.")
        result = self.tile.flip_horz() if self.function == 'horz' else self.tile.flip_vert()
        return result
        
class Swap(Transform): 
    def __init__(self, first_tile, second_tile) -> None:
        super().__init__()
        self.first_tile = first_tile
        self.second_tile = second_tile

    def __repr__(self) -> str:
        return f"Swapped {self.first_tile.current_position} tile with {self.second_tile.current_position} "

    def apply(self):
        position1 = self.first_tile.current_position
        position2 = self.second_tile.current_position
        self.first_tile.current_position = position2
        self.second_tile.current_position = position1
        return position1, position2

class CreateImage:
    def __init__(self) -> None:
        pass



puzzle = Puzzle(snippet, large_grid)
puzzle._tiles[0].rotate('cw')
print(puzzle.check())
puzzle._tiles[0].rotate('ccw')
print(puzzle.check())
puzzle.rotate_tile('ccw', (0,0))
puzzle.swap_tile(puzzle._tiles[0].current_position, puzzle._tiles[0].current_position)
puzzle.flip_tile( 'vert', puzzle._tiles[2].current_position)
print (puzzle.view_history())

# t = random.choice(puzzle._tiles)
# print(t)

# d = random.choice(['cw','ccw'])
# print(d)

# f = random.choice(['horz','vert'])
# print(f)

