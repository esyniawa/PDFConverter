# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import tkinter as tk 
from tkinter import filedialog

import PyPDF2

col = "#263D42"
filenames = []

def addFile():
    for widget in frame.winfo_children():
        widget.destroy()
    
    filename = filedialog.askopenfilename(initialdir="./", title="Wähle Dokument",
                                          filetypes=(("PDF Dokumente", "*.pdf"), ("Alle Dateien", "*.*")))
    filenames.append(filename)
    
    for ele in filenames:
        label = tk.Label(frame, text=ele, bg="white")
        label.pack()

def deleteFiles():
    for widget in frame.winfo_children():
        widget.destroy()
        
    filenames.clear()
    
    
    
def mergeFiles():
    merger = PyPDF2.PdfFileMerger()
    for file in filenames:
        if file[-3:].lower() == "pdf":
            merger.append(file)
        
    merger.write("./combined_docs.pdf")
    
if __name__ == "__main__":
    
    root = tk.Tk()

    canvas = tk.Canvas(root, height=600, width=600, bg=col)
    canvas.pack()
    
    frame = tk.Frame(root, bg="white")
    frame.place(relwidth=0.8, relheight=0.8, relx=0.1, rely=0.1)
    
    openFile = tk.Button(root, text = "PDF hinzufügen", padx=10, pady=10, fg="white", 
                         bg=col, command=addFile)
    openFile.pack(side='left')
    
    delFiles = tk.Button(root, text = "Auswahl löschen", padx=10, pady=10, fg="white", 
                           bg=col, command=deleteFiles)
    delFiles.pack(side='left')
    
    mergeFiles = tk.Button(root, text = "PDFs zusammenfügen", padx=10, pady=10, fg="white", 
                            bg=col, command=mergeFiles)
    mergeFiles.pack(side='right')
    
    
    root.mainloop()
    




    