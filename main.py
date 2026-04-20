#!/usr/bin/env python3
"""
PERT Project Scheduler - SE Assignment HW-03
Simple GUI using tkinter
IPO: Input → Processing → Output
"""

import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict, deque


# ─────────────────────────────────────────────
#  PERT LOGIC
# ─────────────────────────────────────────────

def pert_et(o, m, p):
    return round((o + 4 * m + p) / 6)

def topo_sort(tasks, deps):
    in_deg = {t: 0 for t in tasks}
    graph  = defaultdict(list)
    for t, d in deps.items():
        for dep in d:
            graph[dep].append(t)
            in_deg[t] += 1
    q, order = deque([t for t in tasks if in_deg[t] == 0]), []
    while q:
        n = q.popleft(); order.append(n)
        for nb in graph[n]:
            in_deg[nb] -= 1
            if in_deg[nb] == 0: q.append(nb)
    return order

def compute(tasks_et, deps):
    order = topo_sort(tasks_et, deps)
    succ  = defaultdict(list)
    for t, d in deps.items():
        for dep in d: succ[dep].append(t)

    ES, EF = {}, {}
    for t in order:
        ES[t] = max((EF[p] for p in deps[t]), default=0)
        EF[t] = ES[t] + tasks_et[t]

    dur = max(EF.values())

    LF, LS = {}, {}
    for t in reversed(order):
        LF[t] = min((LS[s] for s in succ[t]), default=dur)
        LS[t] = LF[t] - tasks_et[t]

    slack    = {t: round(LS[t] - ES[t], 1) for t in tasks_et}
    critical = [t for t in order if abs(slack[t]) < 0.01]
    return dict(order=order, ES=ES, EF=EF, LS=LS, LF=LF,
                slack=slack, critical=critical, duration=dur, succ=succ)


def min_workers_needed(tasks_et, sched):
    """Peak concurrent tasks = minimum workers required."""
    if not tasks_et:
        return 0
    dur  = int(sched["duration"])
    peak = 0
    for time in range(dur):
        active = sum(1 for t in tasks_et
                     if sched["ES"][t] <= time < sched["EF"][t])
        peak = max(peak, active)
    return peak


def assign_workers(tasks_et, deps, workers, sched):
    if not workers:
        workers = ["Worker1"]
    free   = {w: 0 for w in workers}
    result = []
    for t in sched["order"]:
        start     = sched["ES"][t]
        available = [w for w in workers if free[w] <= start]
        if available:
            w = min(available, key=lambda x: free[x])
        else:
            w     = min(workers, key=lambda x: free[x])
            start = free[w]
        end     = start + tasks_et[t]
        free[w] = end
        result.append((w, t, start, end))
    return result


# ─────────────────────────────────────────────
#  DEMO DATA
# ─────────────────────────────────────────────

DEMO_TASKS = {
    "A": (8,8,8),   "B": (10,10,10), "C": (8,8,8),
    "D": (9,9,9),   "E": (5,5,5),    "F": (3,3,3),
    "G": (2,2,2),   "H": (4,4,4),    "I": (3,3,3),
}
DEMO_DEPS = {
    "A": [],        "B": [],         "C": ["A","B"], "D": ["A"],
    "E": ["B"],     "F": ["C","D"],  "G": ["D","E"],
    "H": ["F","G"], "I": ["E","F"],
}
DEMO_WORKERS = ["Bob", "Bill", "Tom"]


# ─────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────

class PERTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PERT Scheduler \u2014 SE HW-03")
        self.root.geometry("1100x750")
        self.root.configure(bg="#0f1117")
        self.root.resizable(True, True)

        self.tasks       = {}
        self.deps        = {}
        self.workers     = []
        self.sched       = None
        self.assigns     = None
        self.min_workers = 0

        self._style()
        self._build()
        self._load_demo()
        self._calculate()

    # ── Styling ─────────────────────────────
    def _style(self):
        s = ttk.Style()
        s.theme_use("clam")
        bg    = "#0f1117"; panel = "#1a1d27"
        acc   = "#00d4ff"; txt   = "#e8eaf0"
        crit  = "#ff4560"; muted = "#6b7280"

        s.configure("TFrame",       background=bg)
        s.configure("TLabel",       background=bg,    foreground=txt,  font=("Consolas", 10))
        s.configure("TEntry",       fieldbackground=panel, foreground=txt,
                    insertcolor=acc, font=("Consolas", 10))
        s.configure("TButton",      background=acc,   foreground=bg,
                    font=("Consolas", 10, "bold"), relief="flat", padding=6)
        s.map("TButton",            background=[("active","#00a8cc")])
        s.configure("Demo.TButton", background="#2d3142", foreground=acc,
                    font=("Consolas", 10), relief="flat", padding=6)
        s.map("Demo.TButton",       background=[("active","#3d4252")])
        s.configure("Treeview",          background=panel, foreground=txt,
                    fieldbackground=panel, rowheight=26, font=("Consolas", 10))
        s.configure("Treeview.Heading",  background="#252836", foreground=acc,
                    font=("Consolas", 10, "bold"), relief="flat")
        s.map("Treeview",                background=[("selected","#2d3142")])

        self.CLR = dict(bg=bg, panel=panel, acc=acc, txt=txt,
                        crit=crit, muted=muted, ok="#00e676", warn="#ffd600")

    # ── Layout ──────────────────────────────
    def _build(self):
        C = self.CLR
        tk.Frame(self.root, bg=C["acc"], height=3).pack(fill="x")

        tf = tk.Frame(self.root, bg=C["bg"])
        tf.pack(fill="x", padx=15, pady=(10,0))
        tk.Label(tf, text="PERT PROJECT SCHEDULER",
                 font=("Consolas",16,"bold"), bg=C["bg"], fg=C["acc"]).pack(side="left")
        tk.Label(tf, text="  SE Assignment HW-03  |  IPO Model",
                 font=("Consolas",10), bg=C["bg"], fg=C["muted"]).pack(side="left", pady=4)

        main = tk.Frame(self.root, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=15, pady=10)

        # Scrollable left panel
        lo = tk.Frame(main, bg=C["bg"], width=300)
        lo.pack(side="left", fill="y", padx=(0,10))
        lo.pack_propagate(False)

        lc = tk.Canvas(lo, bg=C["bg"], highlightthickness=0, width=284)
        lc.pack(side="left", fill="both", expand=True)
        ls = tk.Scrollbar(lo, orient="vertical", command=lc.yview)
        ls.pack(side="right", fill="y")
        lc.configure(yscrollcommand=ls.set)

        left    = tk.Frame(lc, bg=C["bg"])
        left_id = lc.create_window((0,0), window=left, anchor="nw")
        left.bind("<Configure>",
                  lambda e: lc.configure(scrollregion=lc.bbox("all")))
        lc.bind("<Configure>",
                lambda e: lc.itemconfig(left_id, width=e.width))
        lc.bind_all("<MouseWheel>",
                    lambda e: lc.yview_scroll(int(-1*(e.delta/120)), "units"))

        right = tk.Frame(main, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)

        self._build_inputs(left)
        self._build_outputs(right)

    def _panel(self, parent, title):
        C = self.CLR
        f = tk.Frame(parent, bg=C["panel"], bd=0)
        f.pack(fill="x", pady=(0,8))
        tk.Label(f, text=f"  {title}", font=("Consolas",10,"bold"),
                 bg=C["panel"], fg=C["acc"]).pack(anchor="w", padx=8, pady=(6,2))
        tk.Frame(f, bg=C["acc"], height=1).pack(fill="x", padx=8)
        return f

    # ── Left: Inputs ─────────────────────────
    def _build_inputs(self, parent):
        C = self.CLR

        # Workers
        wp = self._panel(parent, "<<INPUT>> Workers")
        self.worker_var = tk.StringVar(value="Bob, Bill, Tom")
        tk.Entry(wp, textvariable=self.worker_var,
                 bg=C["panel"], fg=C["txt"], insertbackground=C["acc"],
                 font=("Consolas",10), bd=0, highlightthickness=1,
                 highlightcolor=C["acc"], highlightbackground="#2d3142"
                 ).pack(fill="x", padx=8, pady=6)
        tk.Label(wp, text="  comma-separated names",
                 bg=C["panel"], fg=C["muted"],
                 font=("Consolas",8)).pack(anchor="w", padx=8, pady=(0,6))

        # Add Task
        tp = self._panel(parent, "<<INPUT>> Add Task")
        fields = [("Task ID","tid"),("Optimistic (O)","o"),
                  ("Most Likely (M)","m"),("Pessimistic (P)","p"),
                  ("Dependencies","dep")]
        self.entries = {}
        for lbl, key in fields:
            tk.Label(tp, text=f"  {lbl}", bg=C["panel"], fg=C["muted"],
                     font=("Consolas",9)).pack(anchor="w", padx=8)
            v = tk.StringVar()
            tk.Entry(tp, textvariable=v, bg="#252836", fg=C["txt"],
                     insertbackground=C["acc"], font=("Consolas",10),
                     bd=0, highlightthickness=1,
                     highlightcolor=C["acc"], highlightbackground="#2d3142"
                     ).pack(fill="x", padx=8, pady=(0,4))
            self.entries[key] = v
        tk.Label(tp, text="  deps: comma-separated IDs or blank",
                 bg=C["panel"], fg=C["muted"],
                 font=("Consolas",8)).pack(anchor="w", padx=8, pady=(0,2))
        bf2 = tk.Frame(tp, bg=C["panel"])
        bf2.pack(fill="x", padx=8, pady=6)
        ttk.Button(bf2, text="Add Task",  command=self._add_task).pack(side="left", padx=(0,4))
        ttk.Button(bf2, text="Clear All", command=self._clear,
                   style="Demo.TButton").pack(side="left")

        # Tasks Added
        lp = self._panel(parent, "Tasks Added")
        self.task_list = tk.Listbox(lp, bg="#252836", fg=C["txt"],
                                    font=("Consolas",9), height=7,
                                    selectbackground=C["acc"], selectforeground=C["bg"],
                                    bd=0, highlightthickness=0)
        self.task_list.pack(fill="x", padx=8, pady=6)

        # Min Workers Needed
        mwp = self._panel(parent, "<<o>> Min Workers Needed")
        self.min_workers_lbl = tk.Label(
            mwp, text="\u2014",
            font=("Consolas", 28, "bold"),
            bg=C["panel"], fg=C["warn"]
        )
        self.min_workers_lbl.pack(pady=(8, 2))
        tk.Label(mwp, text="  peak concurrent tasks  |  ES/EF analysis",
                 bg=C["panel"], fg=C["muted"],
                 font=("Consolas",8)).pack(anchor="w", padx=8, pady=(0,8))

        # Action buttons
        bf = tk.Frame(parent, bg=C["bg"])
        bf.pack(fill="x", pady=4)
        ttk.Button(bf, text="Calculate", command=self._calculate).pack(fill="x", pady=2)
        ttk.Button(bf, text="Load Demo", command=self._load_demo,
                   style="Demo.TButton").pack(fill="x", pady=2)
        sl = tk.Frame(bf, bg=C["bg"])
        sl.pack(fill="x", pady=2)
        ttk.Button(sl, text="Save Data", command=self._save,
                   style="Demo.TButton").pack(side="left", fill="x", expand=True, padx=(0,3))
        ttk.Button(sl, text="Load File", command=self._load,
                   style="Demo.TButton").pack(side="left", fill="x", expand=True)

    # ── Right: Outputs ───────────────────────
    def _build_outputs(self, parent):
        C = self.CLR
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)
        st = ttk.Style()
        st.configure("TNotebook",     background=C["bg"], borderwidth=0)
        st.configure("TNotebook.Tab", background="#1a1d27", foreground=C["muted"],
                     font=("Consolas",10), padding=[12,4])
        st.map("TNotebook.Tab",       background=[("selected","#252836")],
                                      foreground=[("selected",C["acc"])])

        # Tab 1 — PERT Table
        t1   = tk.Frame(nb, bg=C["bg"])
        nb.add(t1, text="  PERT Table  ")
        cols = ("Task","O","M","P","ET","ES","EF","LS","LF","Slack","Critical")
        wids = [50,40,40,40,40,50,50,50,50,60,80]
        self.tree = ttk.Treeview(t1, columns=cols, show="headings", height=12)
        for c, w in zip(cols, wids):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        self.tree.tag_configure("crit", foreground=C["crit"], font=("Consolas",10,"bold"))
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.result_lbl = tk.Label(t1, text="", font=("Consolas",11,"bold"),
                                   bg=C["bg"], fg=C["ok"])
        self.result_lbl.pack(pady=4)

        # Tab 2 — Schedule
        t2 = tk.Frame(nb, bg=C["bg"])
        nb.add(t2, text="  Schedule  ")
        self.sched_frame = t2

        # Tab 3 — Gantt
        t3 = tk.Frame(nb, bg=C["bg"])
        nb.add(t3, text="  Gantt Chart  ")
        self.gantt_canvas = tk.Canvas(t3, bg=C["bg"], highlightthickness=0)
        self.gantt_canvas.pack(fill="both", expand=True)
        self.gantt_canvas.bind("<Configure>", lambda e: self._draw_gantt())

        # Tab 4 — Network
        t4 = tk.Frame(nb, bg=C["bg"])
        nb.add(t4, text="  Network  ")
        self.net_canvas = tk.Canvas(t4, bg=C["bg"], highlightthickness=0)
        self.net_canvas.pack(fill="both", expand=True)
        self.net_canvas.bind("<Configure>", lambda e: self._draw_network())

    # ── Actions ─────────────────────────────

    def _save(self):
        import json
        from tkinter import filedialog
        if not self.tasks:
            messagebox.showwarning("Nothing to Save", "Add some tasks first.")
            return
        file = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files","*.json"),("All files","*.*")],
            title="Save PERT Data")
        if not file: return
        data = {
            "workers": [w.strip() for w in self.worker_var.get().split(",") if w.strip()],
            "tasks":   {t: list(v) for t, v in self.tasks.items()},
            "deps":    self.deps
        }
        with open(file, "w") as f:
            json.dump(data, f, indent=2)
        messagebox.showinfo("Saved", f"Project saved to:\n{file}")

    def _load(self):
        import json
        from tkinter import filedialog
        file = filedialog.askopenfilename(
            filetypes=[("JSON files","*.json"),("All files","*.*")],
            title="Load PERT Data")
        if not file: return
        try:
            with open(file) as f:
                data = json.load(f)
            self._clear()
            self.worker_var.set(", ".join(data["workers"]))
            self.tasks = {t: tuple(v) for t, v in data["tasks"].items()}
            self.deps  = data["deps"]
            for t in sorted(self.tasks):
                o, m, p = self.tasks[t]
                d = ",".join(self.deps.get(t, [])) or "\u2014"
                self.task_list.insert(tk.END,
                    f"  {t}  O={int(o)} M={int(m)} P={int(p)}  deps:[{d}]")
            messagebox.showinfo("Loaded", f"Loaded {len(self.tasks)} tasks from:\n{file}")
            self._calculate()
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def _add_task(self):
        try:
            tid = self.entries["tid"].get().strip().upper()
            o   = float(self.entries["o"].get())
            m   = float(self.entries["m"].get())
            p   = float(self.entries["p"].get())
            dep = self.entries["dep"].get().strip()
            if not tid: raise ValueError("Task ID required")
            if not (o <= m <= p): raise ValueError("Need O \u2264 M \u2264 P")
            self.tasks[tid] = (o, m, p)
            self.deps[tid]  = [d.strip().upper() for d in dep.split(",") if d.strip()]
            self.task_list.delete(0, tk.END)
            for t in sorted(self.tasks):
                o, m, p = self.tasks[t]
                d = ",".join(self.deps.get(t, [])) or "\u2014"
                self.task_list.insert(tk.END,
                    f"  {t}  O={int(o)} M={int(m)} P={int(p)}  deps:[{d}]")
            for k in self.entries: self.entries[k].set("")
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def _clear(self):
        self.tasks.clear(); self.deps.clear()
        self.worker_var.set("")
        self.min_workers = 0
        self.min_workers_lbl.config(text="\u2014")
        self.task_list.delete(0, tk.END)
        self.tree.delete(*self.tree.get_children())
        self.gantt_canvas.delete("all")
        self.net_canvas.delete("all")
        self.result_lbl.config(text="")

    def _load_demo(self):
        self._clear()
        self.tasks = dict(DEMO_TASKS)
        self.deps  = {k: list(v) for k, v in DEMO_DEPS.items()}
        self.worker_var.set(", ".join(DEMO_WORKERS))
        for t in sorted(self.tasks):
            o, m, p = self.tasks[t]
            d = ",".join(self.deps[t]) or "\u2014"
            self.task_list.insert(tk.END,
                f"  {t}  O={int(o)} M={int(m)} P={int(p)}  deps:[{d}]")

    def _calculate(self):
        if not self.tasks: return
        try:
            workers = [w.strip() for w in self.worker_var.get().split(",") if w.strip()]
            if not workers: workers = ["Worker1"]
            tasks_et     = {t: pert_et(*v) for t, v in self.tasks.items()}
            self.sched   = compute(tasks_et, self.deps)
            self.assigns = assign_workers(tasks_et, self.deps, workers, self.sched)
            self.min_workers = min_workers_needed(tasks_et, self.sched)
            self.min_workers_lbl.config(text=str(self.min_workers))
            self._draw_table(tasks_et)
            self._draw_schedule(workers)
            self._draw_gantt()
            self._draw_network(tasks_et)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ── Tab 1: PERT Table ───────────────────
    def _draw_table(self, tasks_et):
        C = self.CLR; s = self.sched
        self.tree.delete(*self.tree.get_children())
        for t in sorted(self.tasks):
            o, m, p = self.tasks[t]
            tag = "crit" if t in s["critical"] else ""
            cp  = "\u2605 YES" if t in s["critical"] else ""
            self.tree.insert("", "end", tags=(tag,), values=(
                t, int(o), int(m), int(p), tasks_et[t],
                int(s["ES"][t]), int(s["EF"][t]),
                int(s["LS"][t]), int(s["LF"][t]),
                int(s["slack"][t]), cp))
        total_slack = sum(s["slack"].values())
        cp_str = " \u2192 ".join(s["critical"])
        self.result_lbl.config(
            text=(f"Critical Path: {cp_str}   |   "
                  f"Duration: {int(s['duration'])} units   |   "
                  f"Min Workers: {self.min_workers}   |   "
                  f"Total Slack: {total_slack:.1f}"))

    # ── Tab 2: Schedule ─────────────────────
    def _draw_schedule(self, workers):
        C = self.CLR
        for w in self.sched_frame.winfo_children(): w.destroy()
        s    = self.sched
        asgn = {t: (w, ws, we) for w, t, ws, we in self.assigns}
        cols = ["Task","Start","Finish","ET","Slack","C.Path"] + workers
        wids = [60,60,60,50,60,70] + [90]*len(workers)
        tree = ttk.Treeview(self.sched_frame, columns=cols, show="headings", height=14)
        tree.tag_configure("crit", foreground=C["crit"], font=("Consolas",10,"bold"))
        for c, w in zip(cols, wids):
            tree.heading(c, text=c); tree.column(c, width=w, anchor="center")
        for t in sorted(self.tasks):
            w, ws, we = asgn[t]
            cp  = "\u2605" if t in s["critical"] else ""
            tag = "crit"  if t in s["critical"] else ""
            row = [t, int(s["ES"][t]), int(s["EF"][t]),
                   int(s["EF"][t]-s["ES"][t]), int(s["slack"][t]), cp]
            for worker in workers:
                row.append(f"{int(ws)}\u2192{int(we)}" if worker == w else "\u2014")
            tree.insert("", "end", values=row, tags=(tag,))
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        tk.Label(self.sched_frame,
                 text=(f"  Min workers needed (predicted): {self.min_workers}   |   "
                       f"Critical Path: {' \u2192 '.join(s['critical'])}"),
                 bg=C["bg"], fg=C["ok"], font=("Consolas",10,"bold")).pack(pady=4)

    # ── Tab 3: Gantt Chart ──────────────────
    def _draw_gantt(self):
        C = self.CLR; cv = self.gantt_canvas
        cv.delete("all"); cv.update_idletasks()
        W, H = cv.winfo_width(), cv.winfo_height()
        if W < 50 or H < 50:
            cv.after(100, self._draw_gantt); return
        if not self.sched or not self.assigns: return

        s = self.sched; dur = int(s["duration"])
        tasks = sorted(self.tasks); n = len(tasks)
        label_w = 150; margin_r = 20; margin_t = 50
        row_h = max(28, (H - margin_t - 30) // max(n, 1))
        scale = (W - label_w - margin_r) / (dur + 1)

        cv.create_text(W//2, 18,
                       text="GANTT CHART \u2014 Task Assignments Over Time",
                       fill=C["acc"], font=("Consolas",11,"bold"))
        for t in range(0, dur+2, 5):
            x = label_w + t * scale
            cv.create_line(x, margin_t-10, x, margin_t+n*row_h, fill="#252836", width=1)
            cv.create_text(x, margin_t-15, text=str(t), fill=C["muted"], font=("Consolas",9))

        asgn = {t: (w, ws, we) for w, t, ws, we in self.assigns}
        for i, task in enumerate(tasks):
            w, ws, we = asgn[task]
            y      = margin_t + i * row_h
            x1     = label_w + ws * scale
            x2     = label_w + we * scale
            is_c   = task in s["critical"]
            color  = C["crit"] if is_c else "#2563eb"
            border = "#ff6b80" if is_c else "#60a5fa"
            lcolor = C["crit"] if is_c else C["txt"]
            weight = "bold"    if is_c else "normal"
            if i % 2 == 0:
                cv.create_rectangle(0, y, W, y+row_h, fill="#13161f", outline="")
            cv.create_text(label_w-8, y+row_h//2,
                           text=f"{task}  ({w})", anchor="e",
                           fill=lcolor, font=("Consolas",9,weight))
            cv.create_rectangle(x1+2, y+4, x2+2, y+row_h-4, fill="#000000", outline="")
            cv.create_rectangle(x1, y+3, x2, y+row_h-3, fill=color, outline=border, width=1)
            if x2-x1 > 24:
                cv.create_text((x1+x2)/2, y+row_h/2,
                               text=f"t={int(we-ws)}",
                               fill="white", font=("Consolas",8,"bold"))

        lx = 10; ly = H - 22
        cv.create_rectangle(lx,    ly, lx+12, ly+12, fill=C["crit"],  outline="")
        cv.create_text(lx+16, ly+6, text="Critical",     anchor="w",
                       fill=C["txt"], font=("Consolas",9))
        cv.create_rectangle(lx+90, ly, lx+102, ly+12, fill="#2563eb", outline="")
        cv.create_text(lx+106, ly+6, text="Non-critical", anchor="w",
                       fill=C["txt"], font=("Consolas",9))
        cv.create_text(W-10, ly+6,
                       text=f"Min workers needed: {self.min_workers}",
                       anchor="e", fill=C["warn"], font=("Consolas",9,"bold"))

    # ── Tab 4: Network Diagram ──────────────
    def _draw_network(self, tasks_et=None):
        C = self.CLR; cv = self.net_canvas
        cv.delete("all"); cv.update_idletasks()
        W, H = cv.winfo_width(), cv.winfo_height()
        if W < 50 or H < 50:
            cv.after(100, lambda: self._draw_network(tasks_et)); return
        if not self.sched: return
        if tasks_et is None:
            tasks_et = {t: pert_et(*v) for t, v in self.tasks.items()}
        s = self.sched

        level_of = {}
        def get_level(t):
            if t in level_of: return level_of[t]
            d = self.deps.get(t, [])
            level_of[t] = (1 + max(get_level(x) for x in d)) if d else 0
            return level_of[t]
        for t in s["order"]: get_level(t)
        levels  = defaultdict(list)
        for t, lv in level_of.items(): levels[lv].append(t)
        max_lvl = max(levels)

        pad_x = 80; pad_y = 70
        node_w = 100; node_h = 56
        uw = W - 2*pad_x; uh = H - 2*pad_y
        pos = {}
        for lvl in range(max_lvl+1):
            nodes = sorted(levels[lvl])
            x = pad_x + lvl * uw / max(max_lvl, 1)
            for i, t in enumerate(nodes):
                pos[t] = (x, pad_y + (i+0.5)*uh/len(nodes))

        for t, dl in self.deps.items():
            for dep in dl:
                if dep not in pos or t not in pos: continue
                x1,y1 = pos[dep]; x2,y2 = pos[t]
                both_c = dep in s["critical"] and t in s["critical"]
                cv.create_line(x1,y1,x2,y2,
                               fill=C["crit"] if both_c else "#3a4060",
                               width=2 if both_c else 1,
                               arrow=tk.LAST, arrowshape=(10,12,4))

        hw = node_w//2; hh = node_h//2
        for t, (x, y) in pos.items():
            is_c   = t in s["critical"]
            fill   = C["crit"]  if is_c else "#1e3a5f"
            border = "#ff6b80"  if is_c else C["acc"]
            cv.create_rectangle(x-hw+3, y-hh+3, x+hw+3, y+hh+3, fill="#050810", outline="")
            cv.create_rectangle(x-hw, y-hh, x+hw, y+hh, fill=fill, outline=border, width=2)
            cv.create_text(x, y-14, text=t, fill="white", font=("Consolas",13,"bold"))
            cv.create_text(x, y+2,
                           text=f"ES={int(s['ES'][t])}  EF={int(s['EF'][t])}",
                           fill="#cccccc", font=("Consolas",8))
            cv.create_text(x, y+16,
                           text=f"t={tasks_et[t]}   slack={int(s['slack'][t])}",
                           fill=C["warn"] if not is_c else "#ffaaaa",
                           font=("Consolas",8))

        cv.create_text(W//2, 20, text="TASK NETWORK DIAGRAM",
                       fill=C["acc"], font=("Consolas",11,"bold"))
        lx = 10; ly = H - 22
        cv.create_rectangle(lx,    ly, lx+12, ly+12, fill=C["crit"],  outline="")
        cv.create_text(lx+16, ly+6, text="Critical", anchor="w",
                       fill=C["txt"], font=("Consolas",9))
        cv.create_rectangle(lx+90, ly, lx+102, ly+12, fill="#1e3a5f", outline=C["acc"])
        cv.create_text(lx+106, ly+6, text="Normal", anchor="w",
                       fill=C["txt"], font=("Consolas",9))
        cv.create_text(W-10, ly+6,
                       text=f"Min workers needed: {self.min_workers}",
                       anchor="e", fill=C["warn"], font=("Consolas",9,"bold"))


# ─────────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app  = PERTApp(root)
    root.mainloop()
