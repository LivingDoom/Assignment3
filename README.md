# Assignment3
Software Now - Assignment3


# main.py

Group Name: [DAN/EXT12] 
Group Members:

[Kayla Edwards]                 -           [S396018] 

[Jonathan William McPhail]      -           [S368879] 

[Ibrahim Najjarine]             -           [S407912] 

[Glen Mark Pasigna]             -           [S328808] 



import tkinter as tk

class User_moves():
    def __init__(self):

        self.selected_tile = None

    def on_tile_click(self, event):
        clicked_tile = event.widget
        
        if self.selected_tile is None:
            self.selected_tile = clicked_tile
            clicked_tile.config(
                highlightbackground="red",
                highlightcolor="red",
                highlightthickness=3
            )

        else:
            #Reset border clicking same tile
            if self.selected_tile == clicked_tile:
                self.selected_tile.config(highlightthickness=0)
                self.selected_tile = None
                return
                
            # Get both tiles locations
            info1 = self.selected_tile.grid_info()
            info2 = clicked_tile.grid_info()
            
            # Swap tile positions
            self.selected_tile.grid(row=info2['row'], column=info2['column'])
            clicked_tile.grid(row=info1['row'], column=info1['column'])
            
            #Reset
            self.selected_tile.config(highlightthickness=0)
            self.selected_tile = None

    def on_tile_right_click(self, event):
        clicked_tile = event.widget
        clicked_tile.rotation = (clicked_tile.rotation + 90) % 360

    def on_tile_shift_click(self, event):
        clicked_tile = event.widget
        clicked_tile.flipped_horizontal = not clicked_tile.flipped_horizontal
