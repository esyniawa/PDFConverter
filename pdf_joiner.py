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
import sys
from typing import List, Optional, Dict

import subprocess
from shutil import which


class PDFCompressor:
    """Handles different PDF compression methods"""

    @staticmethod
    def get_qpdf_path() -> Optional[str]:
        """Get path to qpdf binary, either bundled or system-installed"""
        # Check if running as bundled app
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = sys._MEIPASS
            qpdf_path = os.path.join(base_path, 'qpdf', 'bin', 'qpdf.exe')
            if os.path.exists(qpdf_path):
                return qpdf_path

        # Check system installation
        system_qpdf = which('qpdf')
        if system_qpdf:
            return system_qpdf

        return None

    @staticmethod
    def check_qpdf_installed() -> bool:
        """Check if qpdf is available"""
        return PDFCompressor.get_qpdf_path() is not None

    @staticmethod
    def compress_with_qpdf(input_path: str, compression_level: str) -> Optional[str]:
        """Compress PDF using qpdf"""
        try:
            output_path = input_path.replace('.pdf', '_compressed.pdf')

            # Base command with common options
            cmd = ['qpdf', '--object-streams=generate']

            if compression_level == 'low':
                cmd.extend([
                    '--compress-streams=y',
                    '--compression-level=1',
                    '--decode-level=specialized'
                ])
            else:  # high compression
                cmd.extend([
                    '--compress-streams=y',
                    '--compression-level=9',
                    '--decode-level=all',
                    '--recompress-flate'
                ])

            # Add input and output paths
            cmd.extend([input_path, output_path])

            # Run qpdf
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path

        except Exception as e:
            print(f"Error in qpdf compression: {str(e)}")
            return None

    @staticmethod
    def compress_with_pikepdf(input_path: str, compression_level: str) -> Optional[pikepdf.Pdf]:
        """Compress PDF using pikepdf's built-in methods"""
        try:
            pdf = pikepdf.open(input_path)
            if compression_level == 'none':
                return pdf

            # Apply compression settings
            pdf.remove_unreferenced_resources()
            return pdf
        except Exception as e:
            print(f"Error in pikepdf compression: {str(e)}")
            return None

    @staticmethod
    def compress_with_imaging(input_path: str, compression_level: str) -> Optional[pikepdf.Pdf]:
        """Compress PDF by converting to images and back"""
        try:
            # Compression settings based on level
            settings = {
                'low': {
                    'dpi': 80,
                    'quality': 50,
                    'format': 'WEBP'
                },
                'high': {
                    'dpi': 60,
                    'quality': 40,
                    'format': 'WEBP'
                }
            }[compression_level]

            doc = fitz.open(input_path)
            pdf = pikepdf.Pdf.new()

            with tempfile.TemporaryDirectory() as temp_dir:
                # Convert each page to image
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    pix = page.get_pixmap(dpi=settings['dpi'])
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    # Save as compressed image
                    img_buffer = io.BytesIO()
                    if settings['format'] == 'WEBP':
                        img.save(img_buffer, 'WEBP', quality=settings['quality'], method=6)
                    else:
                        img.save(img_buffer, 'JPEG', quality=settings['quality'])

                    # Convert back to PDF page
                    img_buffer.seek(0)
                    temp_img = Image.open(img_buffer)
                    pdf_buffer = io.BytesIO()
                    temp_img.save(pdf_buffer, format='PDF', resolution=settings['dpi'])
                    pdf_buffer.seek(0)

                    # Add to final PDF
                    temp_pdf = pikepdf.Pdf.open(pdf_buffer)
                    pdf.pages.extend(temp_pdf.pages)

            return pdf

        except Exception as e:
            print(f"Error in image-based compression: {str(e)}")
            return None


class DragDropListbox(tk.Listbox):
    """Listbox with drag and drop capability"""

    def __init__(self, master, **kw):
        super().__init__(master, selectmode=tk.SINGLE, **kw)
        self.bind('<Button-1>', self.set_current)
        self.bind('<B1-Motion>', self.shift_selection)
        self.cur_index = None

    def set_current(self, event):
        self.cur_index = self.nearest(event.y)

    def shift_selection(self, event):
        i = self.nearest(event.y)
        if i != self.cur_index:
            x = self.get(i)
            self.delete(i)
            self.insert(i + 1 if i < self.cur_index else i - 1, x)
            self.cur_index = i


class PDFJoinerGUI:
    """Main GUI class for PDF Joiner"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF Joiner Pro")
        self.setup_styles()
        self.create_gui()

    def setup_styles(self):
        """Initialize styles and colors"""
        self.colors = {
            'primary': "#3b5a7f",
            'white': "white",
            'light_gray': "#f0f0f0"
        }

        # Configure ttk styles
        style = ttk.Style()
        style.configure('TFrame', background=self.colors['white'])
        style.configure('TLabel', background=self.colors['white'])
        style.configure('TButton', padding=5)

    def create_gui(self):
        """Create the main GUI elements"""
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # File list
        self.create_file_list()

        # Control buttons
        self.create_control_buttons()

        # Compression options
        self.create_compression_options()

        # Output options
        self.create_output_options()

    def create_file_list(self):
        """Create the file listbox with scrollbar"""
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.listbox = DragDropListbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_control_buttons(self):
        """Create the main control buttons"""
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Add PDFs", command=self.add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove Selected", command=self.delete_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear All", command=self.delete_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Merge PDFs", command=self.merge_files).pack(side=tk.RIGHT, padx=2)

    def create_compression_options(self):
        """Create compression options frame"""
        comp_frame = ttk.LabelFrame(self.main_frame, text="Compression Options", padding="5")
        comp_frame.pack(fill=tk.X, pady=5)

        # Compression method
        self.method_var = tk.StringVar(value='none')
        method_frame = ttk.Frame(comp_frame)
        method_frame.pack(fill=tk.X, pady=2)

        ttk.Label(method_frame, text="Method:").pack(side=tk.LEFT, padx=5)
        methods = [
            ('None', 'none'),
            ('QPDF (Recommended)', 'qpdf') if PDFCompressor.check_qpdf_installed() else None,
            ('Basic (pikepdf)', 'pikepdf'),
            ('Advanced (Image)', 'imaging')
        ]
        methods = [m for m in methods if m is not None]  # Remove None if qpdf not installed
        for text, value in methods:
            ttk.Radiobutton(method_frame, text=text, value=value,
                            variable=self.method_var).pack(side=tk.LEFT, padx=5)

        # Compression level
        self.level_var = tk.StringVar(value='none')
        level_frame = ttk.Frame(comp_frame)
        level_frame.pack(fill=tk.X, pady=2)

        ttk.Label(level_frame, text="Level:").pack(side=tk.LEFT, padx=5)
        levels = [
            ('None', 'none'),
            ('Low', 'low'),
            ('High', 'high')
        ]
        for text, value in levels:
            ttk.Radiobutton(level_frame, text=text, value=value,
                            variable=self.level_var).pack(side=tk.LEFT, padx=5)

    def create_output_options(self):
        """Create output filename options"""
        out_frame = ttk.Frame(self.main_frame)
        out_frame.pack(fill=tk.X, pady=5)

        ttk.Label(out_frame, text="Output filename:").pack(side=tk.LEFT, padx=5)
        self.output_entry = ttk.Entry(out_frame)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(out_frame, text=".pdf").pack(side=tk.LEFT)

    def add_files(self):
        """Add PDF files to the list"""
        filenames = filedialog.askopenfilenames(
            initialdir="./",
            title="Select PDFs",
            filetypes=(("PDF files", "*.pdf"), ("All files", "*.*"))
        )

        for filename in filenames:
            if path.splitext(filename)[1].lower() == ".pdf":
                self.listbox.insert(tk.END, filename)

    def delete_file(self):
        """Delete selected file from list"""
        selection = self.listbox.curselection()
        if selection:
            self.listbox.delete(selection)

    def delete_all(self):
        """Clear all files from list"""
        self.listbox.delete(0, tk.END)

    def merge_files(self):
        """Merge PDF files with selected compression options"""
        files = self.listbox.get(0, tk.END)
        if not files:
            self.show_message("Please add PDF files first.")
            return

        try:
            # Prepare output path
            output_name = self.output_entry.get().strip() or "merged"
            if not output_name.lower().endswith('.pdf'):
                output_name += '.pdf'

            # Process files
            pdf_list = []
            failed_files = []

            for file in files:
                try:
                    if self.method_var.get() == 'imaging':
                        pdf = PDFCompressor.compress_with_imaging(file, self.level_var.get())
                    else:
                        pdf = PDFCompressor.compress_with_pikepdf(file, self.level_var.get())

                    if pdf is not None:
                        pdf_list.append(pdf)
                    else:
                        failed_files.append(path.basename(file))
                except Exception as e:
                    print(f"Error processing {file}: {str(e)}")
                    failed_files.append(path.basename(file))

            if pdf_list:
                # Merge PDFs
                merged_pdf = pikepdf.Pdf.new()
                for pdf in pdf_list:
                    merged_pdf.pages.extend(pdf.pages)

                # Save merged PDF
                merged_pdf.save(output_name, compress_streams=True)

                message = f"PDFs merged successfully as: {output_name}"
                if failed_files:
                    message += f"\n\nFailed to process:\n" + "\n".join(failed_files)
                self.show_message(message)
            else:
                self.show_message("No PDFs could be processed.")

        except Exception as e:
            self.show_message(f"Error merging PDFs: {str(e)}")
        finally:
            # Cleanup
            for pdf in pdf_list:
                pdf.close()

    def show_message(self, message):
        """Show popup message"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Information")
        dialog.geometry("300x150")

        ttk.Label(dialog, text=message, wraplength=280).pack(pady=20)
        ttk.Button(dialog, text="OK", command=dialog.destroy).pack()

    def run(self):
        """Start the GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    app = PDFJoinerGUI()
    app.run()