import tkinter as tk
from tkinter import filedialog, ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import numpy as np


PARAMETER_MAP = {
    "pH": "pH",
    "pO2": "pO2 (mmHg)",
    "pCO2": "pCO2 (mmHg)",
    "ctHB": "tHb (g/dL)",
    "SO2": "sO2 (%)",
    "FO2Hbe": "O2Hb (%)",
    "FHHbe": "RHb (%)",
    "cK+": "K+ (mmol/L)",
    "cLac": "Lac (mmol/L)"  # Only if this column is present in the CSV
}

class ABLApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ABL Flex 800 Data Viewer")

        self.df = None

        # Folder and file load
        self.load_button = tk.Button(root, text="Load CSV File", command=self.load_file)
        self.load_button.pack(pady=5)

        # Patient ID listbox for multiple selection
        self.id_listbox = tk.Listbox(root, selectmode=tk.MULTIPLE, exportselection=0, height=6)
        self.id_listbox.pack(pady=5)
        self.id_listbox.bind("<<ListboxSelect>>", self.update_sample_names)

        # First and Second name dropdowns
        self.fname_var = tk.StringVar()
        self.fname_dropdown = ttk.Combobox(root, textvariable=self.fname_var)
        self.fname_dropdown.pack(pady=5)

        self.sname_var = tk.StringVar()
        self.sname_dropdown = ttk.Combobox(root, textvariable=self.sname_var)
        self.sname_dropdown.pack(pady=5)

        # Plot area
        self.plot_frame = tk.Frame(root)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)

        self.plot_button = tk.Button(root, text="Plot Data", command=self.plot_data)
        self.plot_button.pack(pady=5)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.df = pd.read_csv(file_path)
            print("Loaded columns:", self.df.columns.tolist())  # Debug: print all column names
            self.df = self.df.dropna(subset=["PatientId"])
            self.df["PatientId"] = self.df["PatientId"].astype(str)
            ids = sorted(self.df["PatientId"].unique())
            self.id_listbox.delete(0, tk.END)
            for i in ids:
                self.id_listbox.insert(tk.END, i)

    def update_sample_names(self, event):
        selected_indices = self.id_listbox.curselection()
        selected_ids = [self.id_listbox.get(i) for i in selected_indices]

        if not selected_ids:
            return

        subset = self.df[self.df["PatientId"].isin(selected_ids)]
        fnames = sorted(subset["First Name"].dropna().unique())
        snames = sorted(subset["Last Name"].dropna().unique())
        self.fname_dropdown["values"] = fnames
        self.sname_dropdown["values"] = snames

        if fnames:
            self.fname_var.set(fnames[0])
        if snames:
            self.sname_var.set(snames[0])

    def plot_data(self):
        selected_indices = self.id_listbox.curselection()
        selected_ids = [self.id_listbox.get(i) for i in selected_indices]
        fname = self.fname_var.get()
        sname = self.sname_var.get()

        if not selected_ids or not fname or not sname:
            print("Please make sure all selections (IDs, First Name, Last Name) are chosen.")
            return

        subset = self.df[
            self.df["PatientId"].isin(selected_ids) &
            (self.df["First Name"] == fname) &
            (self.df["Last Name"] == sname)
        ]

        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        fig, axes = plt.subplots(3, 3, figsize=(12, 9))
        axes = axes.flatten()
        plot_index = 0

        for label, col in PARAMETER_MAP.items():
            ax = axes[plot_index]
            if col not in subset.columns:
                ax.set_title(f"{label}\n(No Data Column)")
                plot_index += 1
                continue

            values = pd.to_numeric(subset[col], errors='coerce')
            values = values[(~values.isna()) & (values != 0)]  # Skip NaNs and zeros
            count = len(values)

            if count == 0:
                ax.set_title(f"{label}\n(No Valid Values)")
                plot_index += 1
                continue

            if count == 1:
                values = pd.concat([values, pd.Series([values.iloc[0] + 0.001])], ignore_index=True)

            mean = values.mean()
            std = values.std()
            median = values.median()

            ax.boxplot(values, vert=True)
            ax.set_title(f"{label}\nMean: {mean:.2f}, Median: {median:.2f}, SD: {std:.2f}\n(n={count})")
            plot_index += 1

        while plot_index < len(axes):
            fig.delaxes(axes[plot_index])
            plot_index += 1

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = ABLApp(root)
    root.mainloop()

