# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import filedialog, ttk
from os import path
import pikepdf
import io
import fitz  # PyMuPDF
from PIL import Image
import tempfile
import os

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
            self.insert(i + 1, x)
            self.curIndex = i
        elif i > self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i - 1, x)
            self.curIndex = i


def popUp(input_text):
    win = tk.Toplevel()
    win.wm_title("Information")

    l = tk.Label(win, text=input_text)
    l.grid(row=0, column=0)

    b = tk.Button(win, text="Okay", command=win.destroy)
    b.grid(row=1, column=0)


def compress_pdf_to_images(input_path, compression_level, format_type='webp'):
    """Compress PDF by converting pages to images"""
    try:
        # Set DPI and quality based on compression level
        if compression_level == 'low':
            dpi = 100
            quality = 50
            lossless = True  # Use lossless for low compression
        elif compression_level == 'medium':
            dpi = 90
            quality = 40
            lossless = False
        else:  # high compression
            dpi = 75
            quality = 30
            lossless = False

        # Open the PDF
        doc = fitz.open(input_path)

        # Create a temporary directory for images
        with tempfile.TemporaryDirectory() as temp_dir:
            image_files = []

            # Convert each page to an image
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=dpi)

                # Convert PyMuPDF pixmap to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                if format_type == 'webp':
                    image_path = os.path.join(temp_dir, f'page_{page_num}.webp')
                    img.save(image_path, 'WEBP', quality=quality, lossless=lossless, method=6)
                else:  # fallback to jpeg
                    image_path = os.path.join(temp_dir, f'page_{page_num}.jpg')
                    img.save(image_path, 'JPEG', quality=quality)

                img.close()
                image_files.append(image_path)

            # Create a new PDF from the compressed images
            pdf = pikepdf.Pdf.new()

            for img_path in image_files:
                img = Image.open(img_path)
                pdf_bytes = io.BytesIO()
                img.save(pdf_bytes, format='PDF', resolution=dpi)
                img.close()

                # Add the page to the PDF
                temp_pdf = pikepdf.Pdf.open(pdf_bytes)
                pdf.pages.extend(temp_pdf.pages)

            return pdf

    except Exception as e:
        print(f"Error compressing {input_path}: {str(e)}")
        return None


def addFiles():
    filenames = filedialog.askopenfilenames(initialdir="./", title="Wähle Dokumente",
                                            filetypes=(("PDF Dokumente", "*.pdf"), ("Alle Dateien", "*.*")))

    correct_selection = True
    for filename in filenames:
        if path.splitext(filename)[1] == ".pdf":
            listbox.insert("end", filename)
        else:
            correct_selection = False

    if correct_selection == False:
        popUp("Nur PDF-Dateien können ausgewählt werden.")


def deleteFile():
    listbox.delete("anchor")


def deleteAll():
    listbox.delete(0, "end")


def get_pdf_compression_settings(compression_level):
    """Get PDF compression settings based on level"""
    settings = {
        'compress_streams': True,
        'object_stream_mode': pikepdf.ObjectStreamMode.generate
    }

    if compression_level == 'low':
        # Basic compression
        settings['compress_streams'] = True
    elif compression_level == 'medium':
        # More aggressive compression
        settings['compress_streams'] = True
        settings['object_stream_mode'] = pikepdf.ObjectStreamMode.generate
        settings['normalize_content'] = True
    elif compression_level == 'high':
        # Maximum compression
        settings['compress_streams'] = True
        settings['object_stream_mode'] = pikepdf.ObjectStreamMode.generate
        settings['normalize_content'] = True

    return settings


def mergeFiles():
    files = listbox.get(0, "end")

    if not files:
        return

    try:
        # Get output filename
        outputName = outFilename.get("1.0", "end-1c")
        if len(outputName) == 0:
            output_path = "./combined_docs.pdf"
        else:
            if path.splitext(outputName)[1] == ".pdf":
                output_path = outputName
            else:
                output_path = outputName + ".pdf"

        # Get compression method and level
        compression_method = method_var.get()
        compression_level = compression_var.get()
        failed_files = []

        # Create a list to store compressed PDFs
        pdf_list = []

        for file in files:
            try:
                if compression_method == 'image' and compression_level != 'none':
                    # Use image-based compression
                    pdf = compress_pdf_to_images(file, compression_level)
                    if pdf is not None:
                        pdf_list.append(pdf)
                    else:
                        failed_files.append(path.basename(file))
                else:
                    # Just open without compression
                    pdf = pikepdf.open(file)
                    pdf_list.append(pdf)
            except Exception as e:
                print(f"Error processing {file}: {str(e)}")
                failed_files.append(path.basename(file))

        try:
            if pdf_list:
                # Create the merged PDF
                merged_pdf = pikepdf.Pdf.new()

                # Merge all PDFs
                for pdf in pdf_list:
                    merged_pdf.pages.extend(pdf.pages)

                # Apply PDF compression settings if using PDF method
                if compression_method == 'pdf' and compression_level != 'none':
                    settings = get_pdf_compression_settings(compression_level)
                else:
                    settings = {'compress_streams': True}  # minimal settings

                # Save with settings
                merged_pdf.save(output_path, **settings)

                if failed_files:
                    popUp("Einige PDFs konnten nicht verarbeitet werden:\n" + "\n".join(failed_files))
                else:
                    popUp(f"PDFs wurden erfolgreich zusammengefügt und gespeichert als: {output_path}")
            else:
                popUp("Keine PDFs konnten verarbeitet werden.")

        finally:
            # Clean up
            for pdf in pdf_list:
                pdf.close()
            if 'merged_pdf' in locals():
                merged_pdf.close()

    except Exception as e:
        popUp(f"Fehler beim Zusammenfügen der PDFs: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("JoinPDFs")

    canvas = tk.Canvas(root, height=500, width=1000, bg=col)
    canvas.pack()

    frame = tk.Frame(root, bg="white")
    frame.place(relwidth=0.8, relheight=0.8, relx=0.1, rely=0.1)

    listbox = DragDropListbox(frame)
    listbox.pack(expand=True, fill=tk.BOTH)

    scrollbar = tk.Scrollbar(listbox, orient="vertical")
    scrollbar.pack(side="right", fill="y")

    # Add compression options frame with better layout
    compression_frame = tk.LabelFrame(root, text="Komprimierungsoptionen", bg=col, fg="white")
    compression_frame.pack(side='bottom', pady=10, padx=5, fill='x')

    # Method selection
    method_frame = tk.Frame(compression_frame, bg=col)
    method_frame.pack(pady=5, fill='x')

    tk.Label(method_frame, text="Methode:", bg=col, fg="white").pack(side='left', padx=5)
    method_var = tk.StringVar(value='none')
    methods = [
        ('Keine', 'none'),
        ('PDF Optimierung (schnell)', 'pdf'),
        ('Bild Komprimierung (langsam)', 'image')
    ]

    for text, value in methods:
        tk.Radiobutton(method_frame, text=text, value=value,
                       variable=method_var, bg=col, fg="white",
                       selectcolor="black", anchor='w').pack(side='left', padx=5)

    # Level selection
    level_frame = tk.Frame(compression_frame, bg=col)
    level_frame.pack(pady=5, fill='x')

    tk.Label(level_frame, text="Stärke:", bg=col, fg="white").pack(side='left', padx=5)
    compression_var = tk.StringVar(value='none')
    levels = [
        ('Keine', 'none', 'Keine Komprimierung'),
        ('Niedrig', 'low', 'PDF: Basis-Komprimierung\nBild: 200 DPI, 85% JPEG Qualität'),
        ('Mittel', 'medium', 'PDF: Erweiterte Komprimierung + Inhaltsnormalisierung\nBild: 150 DPI, 60% JPEG Qualität'),
        ('Hoch', 'high', 'PDF: Maximum + Ressourcenbereinigung\nBild: 100 DPI, 30% JPEG Qualität')
    ]

    for text, value, tooltip in levels:
        rb = tk.Radiobutton(level_frame, text=text, value=value,
                            variable=compression_var, bg=col, fg="white",
                            selectcolor="black")
        rb.pack(side='left', padx=5)


        # Create tooltip
        def create_tooltip(widget, text):
            def show_tooltip(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

                label = tk.Label(tooltip, text=text, justify='left',
                                 background="#ffffe0", relief='solid', borderwidth=1)
                label.pack()

                def hide_tooltip():
                    tooltip.destroy()

                widget.tooltip = tooltip
                tooltip.bind('<Leave>', lambda e: hide_tooltip())
                widget.bind('<Leave>', lambda e: hide_tooltip())

            widget.bind('<Enter>', show_tooltip)


        create_tooltip(rb, tooltip)

    ## Left side buttons
    openFile = tk.Button(root, text="PDF hinzufügen", padx=10, pady=10, fg="white",
                         bg=col, command=addFiles)
    openFile.pack(side='left')

    delFile = tk.Button(root, text="Auswahl löschen", padx=10, pady=10, fg="white",
                        bg=col, command=deleteFile)
    delFile.pack(side='left')

    delAll = tk.Button(root, text="Alles löschen", padx=10, pady=10, fg="white",
                       bg=col, command=deleteAll)
    delAll.pack(side='left')

    ## Right side buttons
    mergeFiles = tk.Button(root, text="PDFs zusammenfügen", padx=10, pady=10, fg="white",
                           bg=col, command=mergeFiles)
    mergeFiles.pack(side='right')

    outFilename = tk.Text(root, height=1, width=30)
    outFilename.pack(side='right')

    labelFilename = tk.Label(text="Name des Dokumentes: ")
    labelFilename.pack(side="right")

    root.mainloop()
