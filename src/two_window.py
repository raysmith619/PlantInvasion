from tkinter import *

def mainwindow(root):
    root.title("Window 1")
    Label1 = Label(root,text="abc",width=60)
    Label1.grid(row=0, column=0)


def otherwindow(parent):
    root2 = Toplevel(parent)
    root2.title("Window 2")

    Label2 = Label(root2,text="ABC" ,width=60)
    Label2.grid(row=0, column=0)

root = Tk()

mainwindow(root)
otherwindow(root)
root.mainloop()
