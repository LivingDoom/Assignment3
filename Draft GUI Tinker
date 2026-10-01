from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os
from PIL import Image, ImageTk

class ImagePuzzleGame:

    def __init__(self, window):
# Main Window
        self.window = window
        self.window.title("Image Puzzle Window")
        self.window.state("zoomed")

# Selecting the image
        self.selected_image = ""

#Canvas area
        self.create_layout()
        self.create_widgets()

    def create_layout(self):
#TOP TITLE
        self.title_frame = ttk.Frame(self.window)
        self.title_frame.pack(fill="x", padx=5, pady=5)
        self.title_label = tk.Label(self.title_frame, text="*** IMAGE PUZZLE GAME ***", font=("Arial", 20, "bold"), fg="red")
        self.title_label.pack(pady=5)
           
#IMAGE AND GAME CONTROLS
        self.controls_frame = ttk.Frame(self.window)
        self.controls_frame.pack(fill="x", padx=5, pady=5)
        for column in range(6):
            self.controls_frame.columnconfigure(column, weight=1)
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
       
#ORIGINAL IMAGE
        self.original_frame = tk.Frame(self.main_frame, bd=2, relief="solid")
        self.original_frame.pack(side="left", fill="both", expand=True, padx=4)
        self.original_heading = tk.Label(self.original_frame, text="ORIGINAL IMAGE", font=("Arial", 14, "bold"))
        self.original_heading.pack(pady=5)
        self.original_canvas = tk.Canvas(self.original_frame, bg="white", highlightthickness=0)
        self.original_canvas.pack(fill="both", expand=True)
       
#PUZZLE IMAGE
        self.puzzle_frame = tk.LabelFrame(self.main_frame, bd=2, relief="solid")
        self.puzzle_frame.pack(side="right", fill="both", expand=True, padx=4)
        self.puzzle_heading =tk.Label(self.puzzle_frame, text="PUZZLE IMAGE", font=("Arial", 14, "bold"))
        self.puzzle_heading.pack(pady=5)
        self.puzzle_canvas = tk.Canvas(self.puzzle_frame, bg="white", highlightthickness=0)
        self.puzzle_canvas.pack(fill="both", expand=True)
     
#BOTTOM STATUS BAR
        self.bottom_frame = ttk.Frame(self.window)
        self.bottom_frame.pack(fill="x", padx=5, pady=5)
        for column in range(7):
            self.bottom_frame.columnconfigure(column, weight=1)
 
    def create_widgets(self):
#Open Image button
        self.open_button = tk.Button(self.controls_frame, text="Open An Image From Your Files Here", font=("Arial", 12), bg="white", fg="blue", bd=2, relief="solid", padx=15, pady=8, command=self.click_image)
        self.open_button.grid(row=0, column=0, padx=10, pady=5)
#Chose Image
        self.chose_image_label = tk.Label(self.controls_frame, text="You have chosen Image:", font=("Arial", 12))
        self.chose_image_label.grid(row=0, column=1, padx=10)
        self.image_entry = tk.Entry(self.controls_frame, width=25, font=("Arial", 12))
        self.image_entry.grid(row=0, column=2, padx=10)
        
#Grid size
        self.grid_label = tk.Label(self.controls_frame, text="Choose Your Grid Size:", font=("Arial", 12))
        self.grid_label.grid(row=0, column=3, padx=10)
        self.grid_box = ttk.Combobox(self.controls_frame, values=["3 x 3", "4 x 4", "5 x 5"], width=15, font=("Arial", 12), state="disabled") 
        self.grid_box.current(0)
        self.grid_box.grid(row=0, column=4, padx=10)

#Image button
        self.load_image_button = tk.Button(self.controls_frame, text="Load Image For Puzzle Game", font=("Arial", 12), bg="white", fg="blue", bd=2, relief="solid", padx=15, pady=8, command=self.load_image)
        self.load_image_button.grid(row=0, column=5, padx=20)

#Bottom Buttons
#Status
        self.status = tk.Label(self.bottom_frame, text="Status:", font=("Arial", 12))
        self.status.grid(row=0, column=0, padx=10)
#Moves
        self.moves = tk.Label(self.bottom_frame, text="Number of Moves:", font=("Arial", 12))
        self.moves.grid(row=0, column=2, padx=40)
#Incorrect tiles
        self.incorrect_tiles = tk.Label(self.bottom_frame, text="Number of Incorrect Tiles:", font=("Arial", 12))
        self.incorrect_tiles.grid(row=0, column=4, padx=10)
#Number of Hints left
        self.hints_left = tk.Label(self.bottom_frame, text="Hints Left:", font=("Arial", 12))
        self.hints_left.grid(row=0, column=6, padx=10)
#Hint Button
        self.hint_button = tk.Button(self.bottom_frame, text="Hints", font=("Arial", 14), bg="white", fg="red", bd=2, relief="solid", padx=15, pady=8, command=self.hint)
        self.hint_button.grid(row=0, column=8, padx=40)
#Solved
        self.solved_button = tk.Button(self.bottom_frame, text="Solve", font=("Arial", 14), bg="white", fg="green", bd=2, relief="solid", padx=15, pady=8, command=self.solve)
        self.solved_button.grid(row=0, column=9, padx=40)
#Instructions
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

#Open Image
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
            image_name = os.path.basename(file_path) #The file name
            self.image_entry.delete(0, tk.END)
            self.image_entry.insert(0, image_name)
            self.grid_box.config(state="readonly")
#Load Image
    def load_image(self):
        if self.selected_image == "":
            messagebox.showwarning("No Image Selected", "Please choose an image first")
            return
        
# Get grid size
        grid_text = self.grid_box.get()
        grid_size = int(grid_text.split(" ")[0])

        print("Image:", self.selected_image)
        print("Grid:", grid_size)

        self.display_original_image()

#Display of Image Left side
    def display_original_image(self):
        image = Image.open(self.selected_image)
        width = self.original_canvas.winfo_width()
        height = self.original_canvas.winfo_height()
        max_width = width - 40
        max_height = height - 20
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.original_canvas.original_photo = photo
        x = width / 2
        y = height / 2
        self.original_canvas.create_image(x, y, image=photo, anchor="center")
        self.original_canvas.bind("<Configure>", self.resize_original_image)

    def resize_original_image(self, event):
        if self.selected_image == "":
            return
        self.display_original_image()

    def hint(self):
        print("Hint button pressed")
    def solve(self):
        print("Solve button pressed")


window = tk.Tk()
game = ImagePuzzleGame(window)
window.mainloop()
