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

selected_tile = None

def on_tile_click(event):
    global selected_tile
    clicked_tile = event.widget
    
    # 1. If no tile is selected yet, select this one
    if selected_tile is None:
        selected_tile = clicked_tile
        clicked_tile.config(
            highlightbackground="red",
            highlightcolor="red",
            highlightthickness=3
        )
    
    # 2. If a tile was already selected, swap their positions
    else:
        # If they clicked the same tile twice, just deselect it
        if selected_tile == clicked_tile:
            selected_tile.config(highlightthickness=0)
            selected_tile = None
            return
            
        # Get the grid coordinates of both tiles
        info1 = selected_tile.grid_info()
        info2 = clicked_tile.grid_info()
        
        # Swap their row and column layout positions
        selected_tile.grid(row=info2['row'], column=info2['column'])
        clicked_tile.grid(row=info1['row'], column=info1['column'])
        
        # Reset the selection and remove the red border
        selected_tile.config(highlightthickness=0)
        selected_tile = None


#Practice Window to test code
root = tk.Tk()
root.title("Tile Border Selection")
root.geometry("300x300")
colours = ['green', 'blue', 'yellow']
tiles = []

for i in range(3):
    for j in range(3):
        color_idx = (i + j) % len(colours)
        tile = tk.Frame(
            root, 
            width=80, 
            height=80, 
            bg= colours[color_idx],
            # bd=0 prevents default 3D borders from interfering
            bd=0 
        )
        tile.grid(row = i, column = j, padx = 10, pady = 10)
        
        # Turn off propagate so the frame stays at 80x80 pixels
        tile.pack_propagate(False) 
        
        # Bind the left mouse click (<Button-1>) to our function
        tile.bind("<Button-1>", on_tile_click)
        
        # Keep track of the tile in a list
        tiles.append(tile)



root.mainloop()
