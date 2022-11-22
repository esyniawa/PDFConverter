# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import tkinter as tk 
from tkinter import filedialog

from os import path
from PyPDF2 import PdfFileMerger

col = "#3b5a7f"

class DragDropListbox(tk.Listbox):
    def __init__(self, master, **kw):
        kw['selectmode'] = tk.SINGLE
        tk.Listbox.__init__(self, master, kw)
        self.bind('<Button-1>', self.setCurrent)
        self.bind('<B1-Motion>', self.shiftSelection)
        self.curIndex = None

    def setCurrent(self, event):
        self.curIndex = self.nearest(event.y)

    def shiftSelection(self, event):
        i = self.nearest(event.y)
        if i < self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i+1, x)
            self.curIndex = i
        elif i > self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i-1, x)
            self.curIndex = i

def popUp(input_text):
    win = tk.Toplevel()
    win.wm_title("Information")

    l = tk.Label(win, text=input_text)
    l.grid(row=0, column=0)

    b = tk.Button(win, text="Okay", command=win.destroy)
    b.grid(row=1, column=0)
        
def addFile():
    filename = filedialog.askopenfilename(initialdir="./", title="Wähle Dokument",
                                          filetypes=(("PDF Dokumente", "*.pdf"), ("Alle Dateien", "*.*")))
    
    if path.splitext(filename)[1] == ".pdf":    
        listbox.insert("end", filename)
    else:
        popUp("Nur PDF-Dateien können ausgewählt werden.")

def deleteFile():
    listbox.delete("anchor")

def deleteAll():
    listbox.delete(0, "end")
    
def mergeFiles():
    files = listbox.get(0, "end")
    
    if len(files) > 0:  
        merger = PdfFileMerger()
        for file in files:
            merger.append(file)
            
        ## write file
        outputName = outFilename.get("1.0","end-1c")
        if len(outputName)==0:
            merger.write("./combined_docs.pdf")
        else:
            if path.splitext(outputName)[1] == ".pdf":
                merger.write(outputName)
            else:
                merger.write(outputName + ".pdf")

            
if __name__ == "__main__":
    root = tk.Tk()
    root.title("JoinPDFs")
    
    canvas = tk.Canvas(root, height=500, width=1000, bg=col)
    canvas.pack()
    
    frame = tk.Frame(root, bg="white")
    frame.place(relwidth=0.8, relheight=0.8, relx=0.1, rely=0.1)
    
    listbox = DragDropListbox(frame)
    listbox.pack(expand=True, fill=tk.BOTH)
    
    ## Left side buttons
    openFile = tk.Button(root, text = "PDF hinzufügen", padx=10, pady=10, fg="white", 
                         bg=col, command=addFile)
    openFile.pack(side='left')
    
    delFile = tk.Button(root, text = "Auswahl löschen", padx=10, pady=10, fg="white", 
                           bg=col, command=deleteFile)
    delFile.pack(side='left')

    delAll = tk.Button(root, text = "Alles löschen", padx=10, pady=10, fg="white", 
                           bg=col, command=deleteAll)
    delAll.pack(side='left')

    ## Right side buttons
    mergeFiles = tk.Button(root, text = "PDFs zusammenfügen", padx=10, pady=10, fg="white", 
                            bg=col, command=mergeFiles)
    mergeFiles.pack(side='right')
    
    outFilename = tk.Text(root, height=1, width=30)
    outFilename.pack(side='right')
    
    labelFilename = tk.Label(text="Name des Dokumentes: ")
    labelFilename.pack(side="right")
    
    root.mainloop()
    


    