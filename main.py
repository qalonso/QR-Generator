#!/usr/bin/env python3
"""
Générateur de QR Codes - Interface Tkinter
Installation : pip install -r requirements.txt
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import qrcode
from PIL import ImageTk
import os


# ── Couleurs & style ──────────────────────────────────────────────
BG        = "#0f0f0f"
CARD      = "#1a1a1a"
ACCENT    = "#00e5ff"
ACCENT2   = "#ff3cac"
TEXT      = "#f0f0f0"
SUBTEXT   = "#888888"
ENTRY_BG  = "#242424"
BORDER    = "#2e2e2e"
FONT_TITLE = ("Courier New", 22, "bold")
FONT_LABEL = ("Courier New", 10)
FONT_BTN   = ("Courier New", 11, "bold")
FONT_SMALL = ("Courier New", 9)


class QRApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QR Generator")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("520x680")

        self._qr_image = None       # PhotoImage (garde référence)
        self._last_pil  = None      # PIL Image pour la sauvegarde

        self._build_ui()
        self._center()

    # ── Centrage fenêtre ─────────────────────────────────────────
    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    # ── Construction UI ──────────────────────────────────────────
    def _build_ui(self):
        # Titre
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=30, pady=(30, 0))

        tk.Label(hdr, text="QR", font=("Courier New", 28, "bold"),
                 fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(hdr, text="GENERATOR", font=("Courier New", 28, "bold"),
                 fg=TEXT, bg=BG).pack(side="left", padx=(4, 0))

        tk.Label(self, text="Transformez n'importe quelle URL en QR Code instantanément.",
                 font=FONT_SMALL, fg=SUBTEXT, bg=BG).pack(anchor="w", padx=30, pady=(4, 20))

        # Séparateur
        tk.Frame(self, height=1, bg=BORDER).pack(fill="x", padx=30)

        # Champ URL
        tk.Label(self, text="URL", font=FONT_LABEL, fg=ACCENT, bg=BG).pack(
            anchor="w", padx=30, pady=(20, 4))

        entry_frame = tk.Frame(self, bg=BORDER, bd=0)
        entry_frame.pack(fill="x", padx=30)

        inner = tk.Frame(entry_frame, bg=ENTRY_BG)
        inner.pack(fill="x", padx=1, pady=1)

        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(inner, textvariable=self.url_var,
                                  font=("Courier New", 12), fg=TEXT, bg=ENTRY_BG,
                                  insertbackground=ACCENT, relief="flat",
                                  bd=10)
        self.url_entry.pack(fill="x")
        self.url_entry.bind("<Return>", lambda e: self._generate())
        self.url_entry.insert(0, "https://")

        # Bouton Générer
        self.btn = tk.Button(self, text="GÉNÉRER  ›",
                             font=FONT_BTN, fg=BG, bg=ACCENT,
                             activebackground=ACCENT2, activeforeground=BG,
                             relief="flat", bd=0, padx=20, pady=10,
                             cursor="hand2", command=self._generate)
        self.btn.pack(pady=(16, 0), padx=30, anchor="e")

        # Zone aperçu
        tk.Frame(self, height=1, bg=BORDER).pack(fill="x", padx=30, pady=(20, 0))

        self.preview_frame = tk.Frame(self, bg=CARD, bd=0)
        self.preview_frame.pack(fill="both", expand=True, padx=30, pady=20)

        self.placeholder = tk.Label(self.preview_frame,
                                    text="[ aperçu du QR Code ]",
                                    font=FONT_SMALL, fg=SUBTEXT, bg=CARD)
        self.placeholder.pack(expand=True)

        self.qr_label = tk.Label(self.preview_frame, bg=CARD)

        # Statut + bouton sauvegarder
        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="x", padx=30, pady=(0, 20))

        self.status_var = tk.StringVar(value="")
        tk.Label(bottom, textvariable=self.status_var,
                 font=FONT_SMALL, fg=SUBTEXT, bg=BG).pack(side="left")

        self.save_btn = tk.Button(bottom, text="💾  SAUVEGARDER",
                                  font=FONT_SMALL, fg=ACCENT, bg=BG,
                                  activeforeground=ACCENT2, activebackground=BG,
                                  relief="flat", bd=0, cursor="hand2",
                                  command=self._save)
        # Affiché seulement après génération

    # ── Génération ───────────────────────────────────────────────
    def _generate(self):
        url = self.url_var.get().strip()
        if not url or url == "https://":
            self._shake()
            return

        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        try:
            self.btn.config(text="...", state="disabled")
            self.update()

            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=8,
                border=3,
            )
            qr.add_data(url)
            qr.make(fit=True)

            pil_img = qr.make_image(fill_color="#0f0f0f", back_color="#ffffff")
            self._last_pil = pil_img

            # Redimensionne pour l'aperçu
            size = 240
            pil_img_resized = pil_img.resize((size, size))
            self._qr_image = ImageTk.PhotoImage(pil_img_resized)

            # Affiche
            self.placeholder.pack_forget()
            self.qr_label.config(image=self._qr_image, padx=10, pady=10)
            self.qr_label.pack(expand=True)

            # Sauvegarde automatique dans medias/
            os.makedirs("medias", exist_ok=True)
            safe_name = url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_")
            auto_path = os.path.join("medias", f"qrcode_{safe_name[:50]}.png")
            pil_img.save(auto_path)

            self.status_var.set(f"✓  Sauvegardé → {auto_path}")
            self.save_btn.pack(side="right")
            self.btn.config(text="GÉNÉRER  ›", state="normal")

        except Exception as e:
            messagebox.showerror("Erreur", str(e))
            self.btn.config(text="GÉNÉRER  ›", state="normal")

    # ── Sauvegarde ───────────────────────────────────────────────
    def _save(self):
        if self._last_pil is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("Tous les fichiers", "*.*")],
            initialfile="qrcode.png",
            title="Enregistrer le QR Code"
        )
        if path:
            self._last_pil.save(path)
            self.status_var.set(f"💾  Sauvegardé : {os.path.basename(path)}")

    # ── Animation shake si champ vide ────────────────────────────
    def _shake(self):
        x0 = self.winfo_x()
        for dx in [8, -8, 6, -6, 4, -4, 0]:
            self.geometry(f"+{x0 + dx}+{self.winfo_y()}")
            self.update()
            self.after(30)


if __name__ == "__main__":
    app = QRApp()
    app.mainloop()