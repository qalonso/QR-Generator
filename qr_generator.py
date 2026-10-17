#!/usr/bin/env python3
"""
Générateur de QR Codes - Interface Tkinter (URL + Wi-Fi)
Installation : pip install -r requirements.txt
"""

import re
import tkinter as tk
from tkinter import filedialog, messagebox
import qrcode
from PIL import Image, ImageTk
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
FONT_FAMILY = "Courier New"

# ── Adaptation à l'écran ──────────────────────────────────────────
# Toutes les tailles ci-dessous sont définies pour un écran de 720 px
# de haut, puis multipliées par un facteur calculé selon l'écran réel.
BASE_SCREEN_H = 720
MIN_SCALE, MAX_SCALE = 0.85, 1.6

LAYOUTS = {
    "landscape": {"size": (920, 600), "min": (780, 560), "left_w": 440},
    "portrait":  {"size": (520, 860), "min": (460, 700)},
}

# Rééchantillonnage de qualité pour l'aperçu (compatible Pillow ancien/récent)
RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS

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
        self.resizable(True, True)

        self.ui_scale = self._compute_scale()
        self.layout_mode = "landscape"     # "landscape" ou "portrait"
        self.mode = "url"                  # "url" ou "wifi"

        self._qr_image = None       # PhotoImage (garde référence)
        self._last_pil  = None      # PIL Image pour la sauvegarde
        self._last_render_size = None
        self._render_job = None

        self._build_ui()
        self._set_mode("url")
        self._apply_layout()

    # ── Échelle / helpers de taille ──────────────────────────────
    def _compute_scale(self):
        s = self.winfo_screenheight() / BASE_SCREEN_H
        return max(MIN_SCALE, min(s, MAX_SCALE))

    def px(self, n):
        """Convertit une taille de base en pixels réels."""
        return int(round(n * self.ui_scale))

    def font(self, size, bold=False):
        s = max(8, int(round(size * self.ui_scale)))
        return (FONT_FAMILY, s, "bold") if bold else (FONT_FAMILY, s)

    # ── Helpers UI ───────────────────────────────────────────────
    def _make_entry(self, parent, var, show=None, label=""):
        """Crée un champ de saisie stylé (label + entry). Retourne l'Entry."""
        if label:
            tk.Label(parent, text=label, font=self.font(10), fg=ACCENT, bg=BG).pack(
                anchor="w", pady=(self.px(14), self.px(4)))

        border = tk.Frame(parent, bg=BORDER, bd=0)
        border.pack(fill="x")
        inner = tk.Frame(border, bg=ENTRY_BG)
        inner.pack(fill="x", padx=1, pady=1)

        entry = tk.Entry(inner, textvariable=var, font=self.font(12),
                         fg=TEXT, bg=ENTRY_BG, insertbackground=ACCENT,
                         disabledbackground=CARD, disabledforeground=SUBTEXT,
                         relief="flat", bd=self.px(10), show=show or "")
        entry.pack(fill="x")
        entry.bind("<Return>", lambda e: self._generate())
        return entry

    # ── Construction UI ──────────────────────────────────────────
    def _build_ui(self):
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(fill="both", expand=True)

        # ══ Bloc saisie (gauche en paysage, haut en portrait) ════
        self.input_col = tk.Frame(self.main, bg=BG)
        self.input_pad = tk.Frame(self.input_col, bg=BG)
        self.input_pad.pack(fill="both", expand=True)
        p = self.input_pad

        # Titre + bouton de changement d'affichage
        hdr = tk.Frame(p, bg=BG)
        hdr.pack(fill="x")

        tk.Label(hdr, text="QR", font=self.font(28, True),
                 fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(hdr, text="GENERATOR", font=self.font(28, True),
                 fg=TEXT, bg=BG).pack(side="left", padx=(4, 0))

        self.layout_btn = tk.Button(hdr, text="", font=self.font(9),
                                    fg=ACCENT, bg=CARD,
                                    activeforeground=BG, activebackground=ACCENT,
                                    relief="flat", bd=0,
                                    padx=self.px(10), pady=self.px(4),
                                    cursor="hand2", command=self._toggle_layout)
        self.layout_btn.pack(side="right")

        self.subtitle = tk.Label(p, text="", font=self.font(9),
                                 fg=SUBTEXT, bg=BG, justify="left", wraplength=300)
        self.subtitle.pack(anchor="w", pady=(4, self.px(20)))
        # Le texte se réadapte à la largeur disponible
        p.bind("<Configure>",
               lambda e: self.subtitle.config(wraplength=max(100, e.width - 4)))

        # Séparateur
        tk.Frame(p, height=1, bg=BORDER).pack(fill="x")

        # Sélecteur de mode (onglets)
        tabs = tk.Frame(p, bg=BG)
        tabs.pack(fill="x", pady=(self.px(16), 0))

        self.tab_url = tk.Button(tabs, text="URL", font=self.font(10),
                                 relief="flat", bd=0,
                                 padx=self.px(16), pady=self.px(6),
                                 cursor="hand2",
                                 command=lambda: self._set_mode("url"))
        self.tab_url.pack(side="left")

        self.tab_wifi = tk.Button(tabs, text="WI-FI", font=self.font(10),
                                  relief="flat", bd=0,
                                  padx=self.px(16), pady=self.px(6),
                                  cursor="hand2",
                                  command=lambda: self._set_mode("wifi"))
        self.tab_wifi.pack(side="left", padx=(6, 0))

        # Conteneur des formulaires
        self.form_container = tk.Frame(p, bg=BG)
        self.form_container.pack(fill="x")

        self._build_url_form()
        self._build_wifi_form()

        # Bouton Générer
        self.btn = tk.Button(p, text="GÉNÉRER  ›",
                             font=self.font(11, True), fg=BG, bg=ACCENT,
                             activebackground=ACCENT2, activeforeground=BG,
                             relief="flat", bd=0,
                             padx=self.px(20), pady=self.px(10),
                             cursor="hand2", command=self._generate)
        self.btn.pack(pady=(self.px(16), 0), anchor="e")

        # ══ Séparateur entre les deux blocs ══════════════════════
        self.sep = tk.Frame(self.main, bg=BORDER)

        # ══ Bloc aperçu (droite en paysage, bas en portrait) ═════
        self.preview_col = tk.Frame(self.main, bg=BG)
        self.preview_pad = tk.Frame(self.preview_col, bg=BG)
        self.preview_pad.pack(fill="both", expand=True)

        self.preview_frame = tk.Frame(self.preview_pad, bg=CARD, bd=0)
        self.preview_frame.pack(fill="both", expand=True, pady=(0, self.px(12)))
        self.preview_frame.pack_propagate(False)   # taille dictée par la fenêtre
        self.preview_frame.bind("<Configure>", self._schedule_render)

        self.placeholder = tk.Label(self.preview_frame,
                                    text="[ aperçu du QR Code ]",
                                    font=self.font(9), fg=SUBTEXT, bg=CARD)
        self.placeholder.pack(expand=True)

        self.qr_label = tk.Label(self.preview_frame, bg=CARD,
                                 padx=self.px(10), pady=self.px(10))

        # Statut + bouton sauvegarder
        bottom = tk.Frame(self.preview_pad, bg=BG)
        bottom.pack(fill="x")

        self.status_var = tk.StringVar(value="")
        tk.Label(bottom, textvariable=self.status_var,
                 font=self.font(9), fg=SUBTEXT, bg=BG,
                 justify="left", wraplength=self.px(260)).pack(side="left")

        self.save_btn = tk.Button(bottom, text="💾  SAUVEGARDER",
                                  font=self.font(9), fg=ACCENT, bg=BG,
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
                       font=self.font(9), fg=SUBTEXT, bg=BG,
                       activeforeground=TEXT, activebackground=BG,
                       selectcolor=ENTRY_BG, relief="flat", bd=0,
                       highlightthickness=0, cursor="hand2").pack(
            anchor="w", pady=(self.px(6), 0))

        # Sécurité
        tk.Label(self.wifi_form, text="SÉCURITÉ", font=self.font(10),
                 fg=ACCENT, bg=BG).pack(anchor="w", pady=(self.px(14), self.px(4)))

        sec_row = tk.Frame(self.wifi_form, bg=BG)
        sec_row.pack(fill="x")

        self.sec_var = tk.StringVar(value="WPA")
        for text, value in [("WPA/WPA2/WPA3", "WPA"), ("WEP", "WEP"), ("Aucune", "nopass")]:
            tk.Radiobutton(sec_row, text=text, value=value,
                           variable=self.sec_var, command=self._on_security_change,
                           font=self.font(9), fg=TEXT, bg=BG,
                           activeforeground=ACCENT, activebackground=BG,
                           selectcolor=ENTRY_BG, relief="flat", bd=0,
                           highlightthickness=0, cursor="hand2").pack(
                side="left", padx=(0, self.px(14)))

        # Réseau masqué
        self.hidden_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.wifi_form, text="Réseau masqué",
                       variable=self.hidden_var,
                       font=self.font(9), fg=TEXT, bg=BG,
                       activeforeground=ACCENT, activebackground=BG,
                       selectcolor=ENTRY_BG, relief="flat", bd=0,
                       highlightthickness=0, cursor="hand2").pack(
            anchor="w", pady=(self.px(12), 0))

    # ── Disposition paysage / portrait ───────────────────────────
    def _toggle_layout(self):
        self.layout_mode = "portrait" if self.layout_mode == "landscape" else "landscape"
        self._apply_layout()

    def _apply_layout(self):
        lm = self.layout_mode
        cfg = LAYOUTS[lm]
        edge = self.px(30)
        gap = self.px(24)

        for w in (self.input_col, self.sep, self.preview_col):
            w.pack_forget()

        if lm == "landscape":
            # Saisie à gauche (largeur fixe), aperçu à droite
            self.input_col.config(width=self.px(cfg["left_w"]))
            self.input_col.pack_propagate(False)
            self.input_col.pack(side="left", fill="y")

            self.sep.config(width=1, height=1)
            self.sep.pack(side="left", fill="y", pady=edge)

            self.preview_col.pack(side="left", fill="both", expand=True)

            self.input_pad.pack_configure(padx=(edge, gap), pady=(edge, edge))
            self.preview_pad.pack_configure(padx=(gap, edge), pady=(edge, edge))
            self.layout_btn.config(text="⇄  PORTRAIT")
        else:
            # Saisie en haut, aperçu en bas
            self.input_col.pack_propagate(True)
            self.input_col.pack(side="top", fill="x")

            self.sep.config(width=1, height=1)
            self.sep.pack(side="top", fill="x", padx=edge)

            self.preview_col.pack(side="top", fill="both", expand=True)

            self.input_pad.pack_configure(padx=(edge, edge), pady=(edge, self.px(16)))
            self.preview_pad.pack_configure(padx=(edge, edge), pady=(self.px(16), self.px(20)))
            self.layout_btn.config(text="⇄  PAYSAGE")

        # Taille de la fenêtre adaptée à l'écran, puis centrage
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = min(self.px(cfg["size"][0]), int(sw * 0.95))
        h = min(self.px(cfg["size"][1]), int(sh * 0.90))
        mw = min(self.px(cfg["min"][0]), w)
        mh = min(self.px(cfg["min"][1]), h)
        self.minsize(mw, mh)

        x = (sw - w) // 2
        y = max(0, (sh - h) // 2 - self.px(20))
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._last_render_size = None
        self._schedule_render()

    # ── Gestion des modes URL / Wi-Fi ────────────────────────────
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

    # ── Aperçu : taille adaptée à l'espace disponible ────────────
    def _schedule_render(self, _event=None):
        if self._render_job is not None:
            self.after_cancel(self._render_job)
        self._render_job = self.after(40, self._render_preview)

    def _render_preview(self):
        self._render_job = None
        if self._last_pil is None:
            return

        w = self.preview_frame.winfo_width()
        h = self.preview_frame.winfo_height()
        if w <= 1 or h <= 1:
            return

        margin = self.px(20) * 2
        size = max(self.px(120), min(w, h) - margin)

        if size == self._last_render_size and self._qr_image is not None:
            return
        self._last_render_size = size

        resized = self._last_pil.resize((size, size), RESAMPLE)
        self._qr_image = ImageTk.PhotoImage(resized)
        self.qr_label.config(image=self._qr_image)

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

            # Affiche (l'aperçu est redimensionné selon l'espace disponible)
            self.placeholder.pack_forget()
            self.qr_label.pack(expand=True)
            self._last_render_size = None
            self._render_preview()

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