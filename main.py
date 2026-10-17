#!/usr/bin/env python3
"""
Générateur de QR Codes - Interface Tkinter (URL + Wi-Fi)
Installation : pip install -r requirements.txt
"""

import re
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

SUBTITLES = {
    "url":  "Transformez n'importe quelle URL en QR Code instantanément.",
    "wifi": "Partagez votre Wi-Fi : scannez, et c'est connecté.",
}


def escape_wifi(value: str) -> str:
    """Échappe les caractères spéciaux du format WIFI: (\\ ; , : ")."""
    return re.sub(r'([\\;,:"])', r'\\\1', value)


class QRApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QR Generator")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("520x820")

        self._qr_image = None       # PhotoImage (garde référence)
        self._last_pil  = None      # PIL Image pour la sauvegarde
        self.mode = "url"

        self._build_ui()
        self._set_mode("url")
        self._center()

    # ── Centrage fenêtre ─────────────────────────────────────────
    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    # ── Helpers UI ───────────────────────────────────────────────
    def _make_entry(self, parent, var, show=None, label=""):
        """Crée un champ de saisie stylé (label + entry). Retourne l'Entry."""
        if label:
            tk.Label(parent, text=label, font=FONT_LABEL, fg=ACCENT, bg=BG).pack(
                anchor="w", pady=(14, 4))

        border = tk.Frame(parent, bg=BORDER, bd=0)
        border.pack(fill="x")
        inner = tk.Frame(border, bg=ENTRY_BG)
        inner.pack(fill="x", padx=1, pady=1)

        entry = tk.Entry(inner, textvariable=var, font=("Courier New", 12),
                         fg=TEXT, bg=ENTRY_BG, insertbackground=ACCENT,
                         disabledbackground=CARD, disabledforeground=SUBTEXT,
                         relief="flat", bd=10, show=show or "")
        entry.pack(fill="x")
        entry.bind("<Return>", lambda e: self._generate())
        return entry

    # ── Construction UI ──────────────────────────────────────────
    def _build_ui(self):
        # Titre
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=30, pady=(30, 0))

        tk.Label(hdr, text="QR", font=("Courier New", 28, "bold"),
                 fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(hdr, text="GENERATOR", font=("Courier New", 28, "bold"),
                 fg=TEXT, bg=BG).pack(side="left", padx=(4, 0))

        self.subtitle = tk.Label(self, text="", font=FONT_SMALL,
                                 fg=SUBTEXT, bg=BG)
        self.subtitle.pack(anchor="w", padx=30, pady=(4, 20))

        # Séparateur
        tk.Frame(self, height=1, bg=BORDER).pack(fill="x", padx=30)

        # Sélecteur de mode (onglets)
        tabs = tk.Frame(self, bg=BG)
        tabs.pack(fill="x", padx=30, pady=(16, 0))

        self.tab_url = tk.Button(tabs, text="URL", font=FONT_LABEL,
                                 relief="flat", bd=0, padx=16, pady=6,
                                 cursor="hand2",
                                 command=lambda: self._set_mode("url"))
        self.tab_url.pack(side="left")

        self.tab_wifi = tk.Button(tabs, text="WI-FI", font=FONT_LABEL,
                                  relief="flat", bd=0, padx=16, pady=6,
                                  cursor="hand2",
                                  command=lambda: self._set_mode("wifi"))
        self.tab_wifi.pack(side="left", padx=(6, 0))

        # Conteneur des formulaires
        self.form_container = tk.Frame(self, bg=BG)
        self.form_container.pack(fill="x", padx=30)

        self._build_url_form()
        self._build_wifi_form()

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

    def _build_url_form(self):
        self.url_form = tk.Frame(self.form_container, bg=BG)

        self.url_var = tk.StringVar(value="https://")
        self.url_entry = self._make_entry(self.url_form, self.url_var, label="URL")

    def _build_wifi_form(self):
        self.wifi_form = tk.Frame(self.form_container, bg=BG)

        # SSID
        self.ssid_var = tk.StringVar()
        self.ssid_entry = self._make_entry(self.wifi_form, self.ssid_var,
                                           label="NOM DU RÉSEAU (SSID)")

        # Mot de passe
        self.pwd_var = tk.StringVar()
        self.pwd_entry = self._make_entry(self.wifi_form, self.pwd_var,
                                          show="•", label="MOT DE PASSE")

        self.show_pwd_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.wifi_form, text="Afficher le mot de passe",
                       variable=self.show_pwd_var, command=self._toggle_pwd,
                       font=FONT_SMALL, fg=SUBTEXT, bg=BG,
                       activeforeground=TEXT, activebackground=BG,
                       selectcolor=ENTRY_BG, relief="flat", bd=0,
                       highlightthickness=0, cursor="hand2").pack(anchor="w", pady=(6, 0))

        # Sécurité
        tk.Label(self.wifi_form, text="SÉCURITÉ", font=FONT_LABEL,
                 fg=ACCENT, bg=BG).pack(anchor="w", pady=(14, 4))

        sec_row = tk.Frame(self.wifi_form, bg=BG)
        sec_row.pack(fill="x")

        self.sec_var = tk.StringVar(value="WPA")
        for text, value in [("WPA/WPA2/WPA3", "WPA"), ("WEP", "WEP"), ("Aucune", "nopass")]:
            tk.Radiobutton(sec_row, text=text, value=value,
                           variable=self.sec_var, command=self._on_security_change,
                           font=FONT_SMALL, fg=TEXT, bg=BG,
                           activeforeground=ACCENT, activebackground=BG,
                           selectcolor=ENTRY_BG, relief="flat", bd=0,
                           highlightthickness=0, cursor="hand2").pack(side="left", padx=(0, 14))

        # Réseau masqué
        self.hidden_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.wifi_form, text="Réseau masqué",
                       variable=self.hidden_var,
                       font=FONT_SMALL, fg=TEXT, bg=BG,
                       activeforeground=ACCENT, activebackground=BG,
                       selectcolor=ENTRY_BG, relief="flat", bd=0,
                       highlightthickness=0, cursor="hand2").pack(anchor="w", pady=(12, 0))

    # ── Gestion des modes ────────────────────────────────────────
    def _set_mode(self, mode):
        self.mode = mode
        self.url_form.pack_forget()
        self.wifi_form.pack_forget()

        if mode == "url":
            self.url_form.pack(fill="x")
            self.url_entry.focus_set()
        else:
            self.wifi_form.pack(fill="x")
            self.ssid_entry.focus_set()

        # Style des onglets
        for btn, name in ((self.tab_url, "url"), (self.tab_wifi, "wifi")):
            if name == mode:
                btn.config(fg=BG, bg=ACCENT, activebackground=ACCENT,
                           activeforeground=BG)
            else:
                btn.config(fg=SUBTEXT, bg=CARD, activebackground=CARD,
                           activeforeground=TEXT)

        self.subtitle.config(text=SUBTITLES[mode])

    def _toggle_pwd(self):
        self.pwd_entry.config(show="" if self.show_pwd_var.get() else "•")

    def _on_security_change(self):
        if self.sec_var.get() == "nopass":
            self.pwd_var.set("")
            self.pwd_entry.config(state="disabled")
        else:
            self.pwd_entry.config(state="normal")

    # ── Construction des données du QR ───────────────────────────
    def _build_payload(self):
        """Retourne (données, nom_de_fichier_sûr) ou None si invalide."""
        if self.mode == "url":
            url = self.url_var.get().strip()
            if not url or url == "https://":
                return None
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url

            safe = url.replace("https://", "").replace("http://", "")
            safe = safe.replace("/", "_").replace(".", "_")
            return url, safe

        # Mode Wi-Fi
        ssid = self.ssid_var.get()
        security = self.sec_var.get()
        password = self.pwd_var.get()

        if not ssid.strip():
            return None
        if security != "nopass" and not password:
            return None

        data = f"WIFI:T:{security};S:{escape_wifi(ssid)};"
        if security != "nopass":
            data += f"P:{escape_wifi(password)};"
        if self.hidden_var.get():
            data += "H:true;"
        data += ";"

        safe = "wifi_" + re.sub(r"[^\w\-]+", "_", ssid)
        return data, safe

    # ── Génération ───────────────────────────────────────────────
    def _generate(self):
        payload = self._build_payload()
        if payload is None:
            self._shake()
            return
        data, safe_name = payload

        try:
            self.btn.config(text="...", state="disabled")
            self.update()

            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=8,
                border=3,
            )
            qr.add_data(data)
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