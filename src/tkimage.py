from PIL import Image, ImageTk 
import tkinter as tk
infile = 'out/gmi_ulA42_376371_O-71_187576_lRA42_369949_O-71_181274_640x640_sc1z19_h_mr45_AUG.png' 
root = tk.Tk()
img = Image.open(infile)
tkimage = ImageTk.PhotoImage(img)
tk.Label(root, image=tkimage).pack()
root.mainloop()