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

    def check_tile_status(self, tile):
        #Checks if tile matches to goal state and draws/removes the tick
        info = tile.grid_info()
        
        is_correct_pos = (int(info['row']) == tile.goal_row and int(info['column']) == tile.goal_col)
        is_correct_orient = (tile.rotation == tile.goal_rotation and tile.flipped_horizontal == tile.goal_flipped)
        
        tile.delete("tick_mark")
        
        if is_correct_pos and is_correct_orient:
            #Small green tick top-right
            tile.create_line(
                60, 20, 65, 25, 75, 13, 
                fill="#00FF00", 
                width=3, 
                tags="tick_mark"
            )

    def on_tile_click(self, event):
        clicked_tile = event.widget
        
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
                
            info1 = self.selected_tile.grid_info()
            info2 = clicked_tile.grid_info()
            
            #Swap tile positions
            self.selected_tile.grid(row=info2['row'], column=info2['column'])
            clicked_tile.grid(row=info1['row'], column=info1['column'])
            
            self.selected_tile.config(
                highlightbackground=self.selected_tile.cget("bg"),
                highlightcolor=self.selected_tile.cget("bg")
            )
            
            self.check_tile_status(self.selected_tile)
            self.check_tile_status(clicked_tile)
            
            self.selected_tile = None

    def on_tile_right_click(self, event):
        clicked_tile = event.widget
        clicked_tile.rotation = (clicked_tile.rotation + 90) % 360
        self.check_tile_status(clicked_tile)

    def on_tile_shift_click(self, event):
        clicked_tile = event.widget
        clicked_tile.flipped_horizontal = not clicked_tile.flipped_horizontal
        self.check_tile_status(clicked_tile)
