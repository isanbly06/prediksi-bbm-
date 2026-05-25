import tkinter as tk
from tkinter import messagebox
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import threading, os, math

# ── PALETTE ───────────────────────────────────────────────────────────────────
BG_DARK  = "#0D1117"; BG_CARD  = "#161B22"; BG_INPUT = "#21262D"
ACCENT   = "#238636"; ACCENT_H = "#2EA043"; ACCENT2  = "#1F6FEB"
T_PRI    = "#F0F6FC"; T_MUTED  = "#8B949E"; T_OK     = "#3FB950"
T_WARN   = "#D29922"; T_ERR    = "#F85149"; BORDER   = "#30363D"
G_LOW    = "#3FB950"; G_MED    = "#D29922"; G_HIGH   = "#F85149"

F_TITLE  = ("Segoe UI", 18, "bold"); F_LBL  = ("Segoe UI", 10, "bold")
F_BODY   = ("Segoe UI", 10);         F_SML  = ("Segoe UI", 9)
F_BADGE  = ("Segoe UI", 9, "bold");  F_MONO = ("Consolas", 11)
F_BIG    = ("Segoe UI", 28, "bold")


# ── CUSTOM BUTTON ─────────────────────────────────────────────────────────────
class Btn(tk.Frame):
    def __init__(self, master, text, cmd=None, w=180, h=42,
                    bg=ACCENT, hv=ACCENT_H, fg=T_PRI,
                 font=("Segoe UI", 10, "bold"), **kw):
        super().__init__(master, bg=bg, width=w, height=h, cursor="hand2", **kw)
        self.pack_propagate(False)
        self._bg, self._hv, self._cmd = bg, hv, cmd
        self._lbl = tk.Label(self, text=text, bg=bg, fg=fg, font=font, cursor="hand2")
        self._lbl.place(relx=.5, rely=.5, anchor="center")
        for ww in (self, self._lbl):
            ww.bind("<Enter>",          lambda e: (self.config(bg=self._hv), self._lbl.config(bg=self._hv)))
            ww.bind("<Leave>",          lambda e: (self.config(bg=self._bg), self._lbl.config(bg=self._bg)))
            ww.bind("<ButtonRelease-1>", lambda e: self._cmd() if self._cmd else None)


# ── FUEL GAUGE (Canvas) ───────────────────────────────────────────────────────
class FuelGauge(tk.Canvas):
    MAX = 40.0
    def __init__(self, master, **kw):
        super().__init__(master, width=260, height=155,
                         bg=BG_CARD, highlightthickness=0, **kw)
        self._cur = 0.0; self._tgt = 0.0; self._aid = None
        self._draw(0.0)

    def set_value(self, v):
        self._tgt = max(0.0, min(v, self.MAX))
        if self._aid: self.after_cancel(self._aid)
        self._animate()

    def _animate(self):
        diff = self._tgt - self._cur
        if abs(diff) < 0.02:
            self._cur = self._tgt; self._draw(self._cur); return
        self._cur += diff * 0.18
        self._draw(self._cur)
        self._aid = self.after(14, self._animate)

    def _color(self, v):
        r = v / self.MAX
        return G_LOW if r < 0.33 else (G_MED if r < 0.66 else G_HIGH)

    def _draw(self, v):
        self.delete("all")
        cx, cy, ro = 130, 135, 100
        # Track
        self.create_arc(cx-ro, cy-ro, cx+ro, cy+ro,
                        start=0, extent=180, style="arc",
                        outline="#2D333B", width=18)
        # Value arc
        ratio = v / self.MAX
        ext   = ratio * 180
        if ext > 0.5:
            self.create_arc(cx-ro, cy-ro, cx+ro, cy+ro,
                            start=0, extent=ext, style="arc",
                            outline=self._color(v), width=18)
        # Tick marks
        for i in range(7):
            a = math.radians(i * 30)
            for ri, ro2 in [(ro-12, ro-2), (ro+2, ro+10)]:
                pass
            xi = cx + (ro-12)*math.cos(a); yi = cy - (ro-12)*math.sin(a)
            xo = cx + (ro+2 )*math.cos(a); yo = cy - (ro+2 )*math.sin(a)
            self.create_line(xi, yi, xo, yo, fill="#3D444D", width=1)
        # Needle
        na = math.radians(ratio * 180)
        nx = cx + (ro-14)*math.cos(na); ny = cy - (ro-14)*math.sin(na)
        self.create_line(cx, cy, nx, ny, fill=T_PRI, width=3, capstyle="round")
        self.create_oval(cx-5, cy-5, cx+5, cy+5, fill=T_PRI, outline="")
        # Text
        col = self._color(v) if v > 0 else T_MUTED
        self.create_text(cx, cy-28, text=f"{v:.2f}", font=F_BIG, fill=col)
        self.create_text(cx, cy-8,  text="Liter",    font=F_SML, fill=T_MUTED)
        self.create_text(cx-ro+4, cy+10, text="0",           font=F_SML, fill=T_MUTED, anchor="w")
        self.create_text(cx+ro-4, cy+10, text=f"{self.MAX:.0f}L", font=F_SML, fill=T_MUTED, anchor="e")


# ── MAIN APP ──────────────────────────────────────────────────────────────────
SLIDERS = [
    # (label, unit, name, min, max, default, row, col)
    ("🛣️ Jarak Tempuh",    "km",   "jarak",     0,   500, 50,  0, 0),
    ("⚡ Kecepatan",        "km/h", "kecepatan", 0,   200, 80,  0, 1),
    ("🌡️ Suhu Interior",   "°C",   "suhu_in",  -10,  50,  25,  1, 0),
    ("🌤️ Suhu Eksterior",  "°C",   "suhu_out", -10,  50,  30,  1, 1),
]

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⛽ Prediksi Konsumsi BBM")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        W, H = 760, 860
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.model = None; self.r2 = None
        self._pulse = 0; self._deb = None; self._history = []
        self._svars = {}; self._evars = {}

        # ── Scrollable container ──
        self._main_canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0)
        self._scrollbar   = tk.Scrollbar(self, orient="vertical",
                                            command=self._main_canvas.yview)
        self._main_canvas.configure(yscrollcommand=self._scrollbar.set)
        self._scrollbar.pack(side="right", fill="y")
        self._main_canvas.pack(side="left", fill="both", expand=True)
        self._frame = tk.Frame(self._main_canvas, bg=BG_DARK)
        self._win_id = self._main_canvas.create_window(
            (0, 0), window=self._frame, anchor="nw")
        self._frame.bind("<Configure>", self._on_frame_cfg)
        self._main_canvas.bind("<Configure>", self._on_canvas_cfg)
        self.bind_all("<MouseWheel>",
                        lambda e: self._main_canvas.yview_scroll(
                            int(-1*(e.delta/120)), "units"))

        self._build(); self._train_thread()

    def _on_frame_cfg(self, e):
        self._main_canvas.configure(
            scrollregion=self._main_canvas.bbox("all"))

    def _on_canvas_cfg(self, e):
        self._main_canvas.itemconfig(self._win_id, width=e.width)

    # ─── BUILD UI ──────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        h = tk.Frame(self._frame, bg=BG_DARK, pady=12); h.pack(fill="x", padx=28)
        tk.Label(h, text="⛽  Prediksi Konsumsi BBM",
                    font=F_TITLE, bg=BG_DARK, fg=T_PRI).pack()
        tk.Label(h, text="Real-time · Random Forest · Interactive Dashboard",
                    font=F_SML, bg=BG_DARK, fg=T_MUTED).pack(pady=(2,0))

        # Status + chips
        sr = tk.Frame(self._frame, bg=BG_DARK); sr.pack(fill="x", padx=28, pady=(0,4))
        self._bdot = tk.Label(sr, text="●", font=F_BADGE, bg=BG_DARK, fg=T_WARN)
        self._bdot.pack(side="left", padx=(0,4))
        self._blbl = tk.Label(sr, text="Memuat model...", font=F_BADGE, bg=BG_DARK, fg=T_WARN)
        self._blbl.pack(side="left")

        cr = tk.Frame(self._frame, bg=BG_DARK); cr.pack(fill="x", padx=28, pady=(0,6))
        self._cr2 = self._chip(cr, "R² Score",   "—", ACCENT2)
        self._cds = self._chip(cr, "Data",        "—", T_PRI)
        self._chip(cr, "Model", "Random Forest", T_MUTED)

        tk.Frame(self._frame, bg=BORDER, height=1).pack(fill="x", padx=28, pady=4)

        # Slider card
        sc = self._card(self._frame)
        sc.pack(fill="x", padx=28, pady=6, ipady=6)
        tk.Label(sc, text="🎛️  Parameter Input  — geser slider atau ketik nilai",
                    font=F_LBL, bg=BG_CARD, fg=T_PRI, anchor="w"
                    ).pack(fill="x", padx=18, pady=(12,4))
        tk.Frame(sc, bg=BORDER, height=1).pack(fill="x", padx=18, pady=(0,8))

        g = tk.Frame(sc, bg=BG_CARD); g.pack(fill="x", padx=18, pady=(0,6))
        g.columnconfigure(0, weight=1); g.columnconfigure(1, weight=1)
        for lbl, unit, name, mn, mx, dflt, row, col in SLIDERS:
            self._slider_block(g, lbl, unit, name, mn, mx, dflt, row, col)

        # Gauge + efficiency row
        gr = tk.Frame(self._frame, bg=BG_DARK); gr.pack(fill="x", padx=28, pady=6)

        gc = self._card(gr); gc.pack(side="left", fill="both", expand=True, padx=(0,5))
        tk.Label(gc, text="📊  Gauge BBM", font=F_LBL, bg=BG_CARD, fg=T_MUTED,
                    anchor="w").pack(padx=16, pady=(12,4), anchor="w")
        self.gauge = FuelGauge(gc); self.gauge.pack(padx=10, pady=(0,10))

        ec = self._card(gr); ec.pack(side="left", fill="both", expand=True, padx=(5,0))
        tk.Label(ec, text="⚡  Efisiensi", font=F_LBL, bg=BG_CARD, fg=T_MUTED,
                    anchor="w").pack(padx=16, pady=(12,4), anchor="w")
        tk.Frame(ec, bg=BORDER, height=1).pack(fill="x", padx=16)
        self._eico = tk.Label(ec, text="—", font=("Segoe UI", 34), bg=BG_CARD, fg=T_MUTED)
        self._eico.pack(pady=(12,2))
        self._elbl = tk.Label(ec, text="Belum dihitung",
                                font=("Segoe UI", 11, "bold"), bg=BG_CARD, fg=T_MUTED)
        self._elbl.pack()
        self._esub = tk.Label(ec, text="", font=F_SML, bg=BG_CARD, fg=T_MUTED,
                                wraplength=180, justify="center")
        self._esub.pack(pady=(4,0))
        tk.Frame(ec, bg=BORDER, height=1).pack(fill="x", padx=16, pady=8)
        self._rvars = {}
        for key, lbl in [("bbm","Prediksi BBM"),("jarak","Jarak"),("speed","Kecepatan")]:
            rf = tk.Frame(ec, bg=BG_CARD); rf.pack(fill="x", padx=16, pady=2)
            tk.Label(rf, text=lbl, font=F_SML, bg=BG_CARD, fg=T_MUTED).pack(side="left")
            v = tk.StringVar(value="—"); self._rvars[key] = v
            tk.Label(rf, textvariable=v, font=("Segoe UI", 9, "bold"),
                        bg=BG_CARD, fg=T_PRI).pack(side="right")

        # Buttons
        br = tk.Frame(self._frame, bg=BG_DARK); br.pack(pady=8)
        Btn(br, "🔍  Hitung Manual", cmd=self._predict_manual,
            w=200, h=44, bg=ACCENT, hv=ACCENT_H).pack(side="left", padx=5)
        Btn(br, "💾  Simpan Riwayat", cmd=self._save_history,
            w=180, h=44, bg=ACCENT2, hv="#2563EB").pack(side="left", padx=5)
        Btn(br, "🔄  Reset", cmd=self._reset,
            w=110, h=44, bg=BG_INPUT, hv="#30363D").pack(side="left", padx=5)

        # History
        hc = self._card(self._frame); hc.pack(fill="x", padx=28, pady=(4,10), ipady=4)
        tk.Label(hc, text="📋  Riwayat Prediksi",
                    font=F_LBL, bg=BG_CARD, fg=T_PRI, anchor="w"
                    ).pack(padx=18, pady=(12,4), anchor="w")
        tk.Frame(hc, bg=BORDER, height=1).pack(fill="x", padx=18)

        hdr_f = tk.Frame(hc, bg=BG_INPUT); hdr_f.pack(fill="x", padx=18, pady=(4,0))
        for col_txt, w in [("Jarak",70),("Kecepatan",80),("Suhu In",70),
                            ("Suhu Out",70),("BBM (L)",75),("Rating",90)]:
            tk.Label(hdr_f, text=col_txt, font=F_BADGE, bg=BG_INPUT,
                        fg=T_MUTED, width=w//8, anchor="w",
                        padx=6, pady=3).pack(side="left")

        self._hbody = tk.Frame(hc, bg=BG_CARD)
        self._hbody.pack(fill="x", padx=18, pady=(0,6))
        self._no_hist = tk.Label(self._hbody,
            text="Belum ada riwayat. Klik 'Simpan Riwayat' setelah prediksi.",
            font=F_SML, bg=BG_CARD, fg=T_MUTED)
        self._no_hist.pack(pady=8)

        # Footer
        tk.Frame(self._frame, bg=BORDER, height=1).pack(fill="x", padx=28)
        tk.Label(self._frame, text="Kelompok Dataset · Praktikum Bu Radiyah · 2026",
                    font=F_SML, bg=BG_DARK, fg=T_MUTED).pack(pady=6)

    def _card(self, parent):
        return tk.Frame(parent, bg=BG_CARD,
                        highlightthickness=1, highlightbackground=BORDER)

    def _chip(self, parent, title, value, color):
        f = tk.Frame(parent, bg=BG_INPUT,
                        highlightthickness=1, highlightbackground=BORDER)
        f.pack(side="left", padx=5, pady=3, ipadx=8, ipady=3)
        tk.Label(f, text=title, font=F_SML, bg=BG_INPUT, fg=T_MUTED).pack(anchor="w")
        lbl = tk.Label(f, text=value, font=("Segoe UI", 10, "bold"),
                        bg=BG_INPUT, fg=color)
        lbl.pack(anchor="w")
        return lbl

    # ─── SLIDER BLOCK ──────────────────────────────────────────────────────────
    def _slider_block(self, parent, label, unit, name, mn, mx, dflt, row, col):
        wrap = tk.Frame(parent, bg=BG_CARD)
        wrap.grid(row=row, column=col, sticky="nsew", padx=8, pady=6)

        top = tk.Frame(wrap, bg=BG_CARD); top.pack(fill="x")
        tk.Label(top, text=label, font=F_LBL, bg=BG_CARD,
                    fg=T_MUTED, anchor="w").pack(side="left")

        evar = tk.StringVar(value=str(dflt))
        self._evars[name] = evar
        ew = tk.Frame(top, bg=BG_INPUT,
                        highlightthickness=1, highlightbackground=BORDER)
        ew.pack(side="right")
        ent = tk.Entry(ew, textvariable=evar, font=F_MONO,
                        bg=BG_INPUT, fg=T_PRI, insertbackground=T_PRI,
                        relief="flat", bd=4, width=7)
        ent.pack(side="left")
        tk.Label(ew, text=unit, font=F_SML, bg=BG_INPUT,
                    fg=T_MUTED, padx=4).pack(side="right")

        svar = tk.DoubleVar(value=dflt)
        self._svars[name] = svar

        sl = tk.Scale(wrap, from_=mn, to=mx, resolution=0.5,
                        orient="horizontal", variable=svar,
                        bg=BG_CARD, fg=T_PRI, troughcolor=BG_INPUT,
                        activebackground=ACCENT, highlightthickness=0,
                        sliderrelief="flat", bd=0, sliderlength=18,
                        length=310, showvalue=False,
                        command=lambda v, n=name: self._on_slider(n, v))
        sl.pack(fill="x", pady=(2,0))

        rr = tk.Frame(wrap, bg=BG_CARD); rr.pack(fill="x")
        tk.Label(rr, text=f"{mn}", font=F_SML, bg=BG_CARD, fg=T_MUTED).pack(side="left")
        tk.Label(rr, text=f"{mx} {unit}", font=F_SML, bg=BG_CARD, fg=T_MUTED).pack(side="right")

        # Entry → slider sync
        def _sync(*args, n=name, sv=svar, lo=mn, hi=mx):
            try:
                v = float(self._evars[n].get())
                sv.set(max(lo, min(hi, v)))
                self._debounce()
            except ValueError:
                pass
        evar.trace_add("write", _sync)

        ent.bind("<FocusIn>",  lambda e, x=ew: x.config(highlightbackground=ACCENT2))
        ent.bind("<FocusOut>", lambda e, x=ew: x.config(highlightbackground=BORDER))
        ent.bind("<Return>",   lambda e: self._predict_live())

    def _on_slider(self, name, value):
        try:
            self._evars[name].set(f"{float(value):.1f}")
        except Exception:
            pass
        self._debounce()

    def _debounce(self):
        if self._deb: self.after_cancel(self._deb)
        self._deb = self.after(80, self._predict_live)

    # ─── MODEL TRAINING ────────────────────────────────────────────────────────
    def _train_thread(self):
        self._pid = self.after(500, self._pulse_badge)
        threading.Thread(target=self._train, daemon=True).start()

    def _train(self):
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            df = pd.read_csv(os.path.join(base, "konsumsibbm.csv"))
            df = df[['distance','consume','speed','temp_inside','temp_outside']]
            for c in ['distance','consume','temp_inside','temp_outside']:
                df[c] = df[c].astype(str).str.replace(',','.')
            for c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            df = df.dropna()
            df['total_bbm'] = (df['consume'] * df['distance']) / 100
            df.to_csv(os.path.join(base, "data_bersih.csv"), index=False)
            X = df[['distance','speed','temp_inside','temp_outside']]
            y = df['consume']
            Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model.fit(Xtr, ytr)
            self.r2    = r2_score(yte, self.model.predict(Xte))
            self.after(0, lambda: self._on_ready(len(df)))
        except Exception as ex:
            self.after(0, lambda: self._on_err(str(ex)))

    def _on_ready(self, n):
        if hasattr(self, '_pid'): self.after_cancel(self._pid)
        self._bdot.config(fg=T_OK); self._blbl.config(text="✓ Model siap", fg=T_OK)
        self._cr2.config(text=f"{self.r2:.4f}", fg=T_OK)
        self._cds.config(text=f"{n} baris", fg=T_PRI)
        self._predict_live()

    def _on_err(self, err):
        if hasattr(self, '_pid'): self.after_cancel(self._pid)
        self._bdot.config(fg=T_ERR)
        self._blbl.config(text=f"Error: {err}", fg=T_ERR)

    def _pulse_badge(self):
        self._pulse ^= 1
        self._bdot.config(fg=T_WARN if self._pulse else T_MUTED)
        self._pid = self.after(500, self._pulse_badge)

    # ─── PREDICTION ────────────────────────────────────────────────────────────
    def _get_vals(self):
        return {n: self._svars[n].get() for *_, n, _mn, _mx, _d, _r, _c in SLIDERS}

    def _predict_live(self):
        if not self.model: return
        v = self._get_vals()
        si_f = (v['suhu_in']  * 9/5) + 32
        so_f = (v['suhu_out'] * 9/5) + 32
        inp  = pd.DataFrame([[v['jarak'], v['kecepatan'], si_f, so_f]],
                            columns=['distance','speed','temp_inside','temp_outside'])
        consume_pred = max(0, float(self.model.predict(inp)[0]))
        p = (consume_pred * v['jarak']) / 100
        self.gauge.set_value(p)
        self._rvars['bbm'].set(f"{p:.2f} L")
        self._rvars['jarak'].set(f"{v['jarak']:.1f} km")
        self._rvars['speed'].set(f"{v['kecepatan']:.1f} km/h")
        self._set_efficiency(p)
        self._last_pred = (v, p)

    def _predict_manual(self):
        self._predict_live()
        self._flash_gauge()

    def _set_efficiency(self, p):
        if p < 3:
            ico, lbl, sub, col = "🟢","Sangat Efisien","Konsumsi sangat rendah!",T_OK
        elif p < 6:
            ico, lbl, sub, col = "🟡","Cukup Efisien","Konsumsi dalam batas wajar",T_WARN
        elif p < 10:
            ico, lbl, sub, col = "🟠","Kurang Efisien","Pertimbangkan kurangi kecepatan",T_WARN
        else:
            ico, lbl, sub, col = "🔴","Boros","Konsumsi sangat tinggi!",T_ERR
        self._eico.config(text=ico, fg=col)
        self._elbl.config(text=lbl, fg=col)
        self._esub.config(text=sub)

    def _flash_gauge(self, step=0):
        colors = [ACCENT, "#2EA043", ACCENT, "#2EA043", BORDER]
        self.gauge.config(highlightbackground=colors[min(step, len(colors)-1)])
        if step < len(colors)-1:
            self.after(100, lambda: self._flash_gauge(step+1))

    # ─── HISTORY ───────────────────────────────────────────────────────────────
    def _save_history(self):
        if not hasattr(self, '_last_pred'):
            messagebox.showinfo("Info", "Hitung prediksi terlebih dahulu!")
            return
        v, p = self._last_pred
        if len(self._history) >= 8: self._history.pop(0)
        rating = "⚡ Efisien" if p < 3 else ("✅ Wajar" if p < 6 else ("⚠️ Boros" if p < 10 else "❌ Sangat Boros"))
        self._history.append((v['jarak'], v['kecepatan'], v['suhu_in'], v['suhu_out'], p, rating))
        self._render_history()

    def _render_history(self):
        for w in self._hbody.winfo_children(): w.destroy()
        if not self._history:
            self._no_hist = tk.Label(self._hbody, text="Belum ada riwayat.",
                                        font=F_SML, bg=BG_CARD, fg=T_MUTED)
            self._no_hist.pack(pady=8); return
        for i, (jk, sp, si, so, bbm, rat) in enumerate(reversed(self._history)):
            row_bg = BG_INPUT if i % 2 == 0 else BG_CARD
            rf = tk.Frame(self._hbody, bg=row_bg); rf.pack(fill="x")
            vals = [f"{jk:.0f} km", f"{sp:.0f} km/h",
                    f"{si:.1f}°C",  f"{so:.1f}°C",
                    f"{bbm:.2f} L", rat]
            cols = [T_PRI, T_PRI, T_MUTED, T_MUTED,
                    T_OK if bbm < 6 else T_ERR, T_PRI]
            widths = [70, 80, 70, 70, 75, 90]
            for val, col, w in zip(vals, cols, widths):
                tk.Label(rf, text=val, font=F_SML, bg=row_bg,
                            fg=col, width=w//8, anchor="w",
                            padx=6, pady=4).pack(side="left")

    # ─── RESET ─────────────────────────────────────────────────────────────────
    def _reset(self):
        defaults = {"jarak":50, "kecepatan":80, "suhu_in":25, "suhu_out":30}
        for n, d in defaults.items():
            self._svars[n].set(d)
            self._evars[n].set(str(d))
        self.gauge.set_value(0)
        for v in self._rvars.values(): v.set("—")
        self._eico.config(text="—", fg=T_MUTED)
        self._elbl.config(text="Belum dihitung", fg=T_MUTED)
        self._esub.config(text="")
        if hasattr(self, '_last_pred'): del self._last_pred


if __name__ == "__main__":
    app = App()
    app.mainloop()