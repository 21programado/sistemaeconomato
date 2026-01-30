import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os

# ================================
# RUTAS 
# ===============================
BASE_DIR = os.path.join(os.getenv("APPDATA"), "ControlEquipos")
os.makedirs(BASE_DIR, exist_ok=True)
DB_PATH = os.path.join(BASE_DIR, "registros.db")

# ===============================
# CONFIGURACIÓN
# ===============================
REGISTROS_POR_PAGINA = 25
REGISTROS_PDF = 100

# ===============================
# BASE DE DATOS
# ===============================
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registro TEXT,
    nombre TEXT,
    cargo TEXT,
    equipo TEXT,
    entrega TEXT,
    salida TEXT,
    devolucion TEXT
)
""")
conn.commit()

# ===============================
# ESTADO
# ===============================
pagina_actual = 0
filtro_equipo = ""

# ===============================
# FUNCIONES
# ===============================
def ahora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def limpiar_formulario():
    nombre_entry.delete(0, "end")
    cargo_combo.set("")
    equipo_combo.set("")
    salida_text.delete("1.0", "end")

def registrar_entrega():
    nombre = nombre_entry.get().strip()
    cargo = cargo_combo.get()
    equipo = equipo_combo.get()
    salida = salida_text.get("1.0", "end").strip()

    if not nombre or not cargo or not equipo:
        messagebox.showwarning("Datos incompletos", "Complete Nombre, Cargo y Equipo.")
        return

    if not messagebox.askyesno(
        "Confirmar entrega",
        f"¿Confirma la entrega de {equipo} a {nombre}?"
    ):
        return

    cursor.execute("""
        INSERT INTO registros (registro, nombre, cargo, equipo, entrega, salida, devolucion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        ahora(),
        nombre,
        cargo,
        equipo,
        ahora(),
        salida,
        "Pendiente"
    ))

    conn.commit()
    limpiar_formulario()
    cargar_registros()

def registrar_devolucion():
    seleccion = tree.selection()
    if not seleccion:
        messagebox.showwarning("Selección", "Seleccione un registro.")
        return

    valores = tree.item(seleccion[0], "values")
    registro_id = valores[0]

    if valores[7] != "Pendiente":
        messagebox.showinfo("Información", "Este equipo ya fue devuelto.")
        return

    if not messagebox.askyesno(
        "Confirmar devolución",
        f"¿Confirma la devolución del equipo {valores[4]}?"
    ):
        return

    cursor.execute("""
        UPDATE registros
        SET devolucion = ?
        WHERE id = ?
    """, (ahora(), registro_id))

    conn.commit()
    cargar_registros()

# ===============================
# CARGA DE REGISTROS (PAGINADA)
# ===============================
def cargar_registros():
    global pagina_actual

    for i in tree.get_children():
        tree.delete(i)

    offset = pagina_actual * REGISTROS_POR_PAGINA

    if filtro_equipo:
        cursor.execute("""
            SELECT COUNT(*) FROM registros WHERE equipo = ?
        """, (filtro_equipo,))
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT id, registro, nombre, cargo, equipo, entrega, salida, devolucion
            FROM registros
            WHERE equipo = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (filtro_equipo, REGISTROS_POR_PAGINA, offset))
    else:
        cursor.execute("SELECT COUNT(*) FROM registros")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT id, registro, nombre, cargo, equipo, entrega, salida, devolucion
            FROM registros
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (REGISTROS_POR_PAGINA, offset))

    filas = cursor.fetchall()

    for row in filas:
        tag = "pendiente" if row[7] == "Pendiente" else "devuelto"
        tree.insert("", "end", values=row, tags=(tag,))

    total_paginas = max(1, (total + REGISTROS_POR_PAGINA - 1) // REGISTROS_POR_PAGINA)
    lbl_pagina.config(text=f"Página {pagina_actual + 1} de {total_paginas}")

    btn_anterior.config(state="normal" if pagina_actual > 0 else "disabled")
    btn_siguiente.config(state="normal" if pagina_actual < total_paginas - 1 else "disabled")

def pagina_anterior():
    global pagina_actual
    if pagina_actual > 0:
        pagina_actual -= 1
        cargar_registros()

def pagina_siguiente():
    global pagina_actual
    pagina_actual += 1
    cargar_registros()

# ===============================
# BÚSQUEDA
# ===============================
def buscar_por_equipo():
    global filtro_equipo, pagina_actual
    filtro_equipo = equipo_busqueda.get().strip()
    pagina_actual = 0
    cargar_registros()

def limpiar_busqueda():
    global filtro_equipo, pagina_actual
    filtro_equipo = ""
    equipo_busqueda.delete(0, "end")
    pagina_actual = 0
    cargar_registros()

# ===============================
# PDF
# ===============================
def exportar_pdf():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        messagebox.showerror(
            "PDF no disponible",
            "No está instalada la librería 'reportlab'.\n\npip install reportlab"
        )
        return

    cursor.execute("""
        SELECT registro, nombre, cargo, equipo, entrega, salida, devolucion
        FROM registros
        ORDER BY id DESC
        LIMIT ?
    """, (REGISTROS_PDF,))

    filas = cursor.fetchall()

    if not filas:
        messagebox.showinfo("PDF", "No hay registros para exportar.")
        return

    pdf_path = os.path.join(BASE_DIR, f"ultimos_{REGISTROS_PDF}_registros.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    y = height - 40
    c.setFont("Helvetica", 9)
    c.drawString(40, y, f"Últimos {REGISTROS_PDF} registros - Control de Equipos")
    y -= 30

    for fila in filas:
        linea = " | ".join(fila)
        if y < 40:
            c.showPage()
            c.setFont("Helvetica", 9)
            y = height - 40
        c.drawString(40, y, linea[:120])
        y -= 14

    c.save()
    messagebox.showinfo("PDF generado", f"Archivo creado:\n{pdf_path}")

# ===============================
# INTERFAZ
# ===============================
root = tk.Tk()
root.title("Control de Entrega y Devolución de Equipos")
root.state("zoomed")

main = ttk.Frame(root, padding=15)
main.pack(fill="both", expand=True)

ttk.Label(
    main,
    text="Control de Entrega y Devolución de Equipos y Materiales",
    font=("Segoe UI", 16, "bold")
).pack(pady=10)

# -------------------------------
# FORMULARIO
# -------------------------------
form = ttk.Frame(main)
form.pack(fill="x", pady=10)

ttk.Label(form, text="Nombre").grid(row=0, column=0, padx=5, pady=5)
nombre_entry = ttk.Entry(form, width=30)
nombre_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(form, text="Cargo").grid(row=0, column=2, padx=5, pady=5)
cargo_combo = ttk.Combobox(
    form, width=28, state="readonly",
    values=[
        "Auxiliar de Enfermería",
        "Licenciada en Enfermería",
        "Practicante Interno",
        "Médico",
        "ASG",
        "Otro"
    ]
)
cargo_combo.grid(row=0, column=3, padx=5, pady=5)

ttk.Label(form, text="Equipo").grid(row=1, column=0, padx=5, pady=5)
equipo_combo = ttk.Combobox(
    form, width=28, state="readonly",
    values=[
        "Monitor 1", "Monitor 2", "ECG", "Saturómetro",
        "Otoscopio", "Valija de Traslado", "Videolaringo", "Otro"
    ]
)
equipo_combo.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(form, text="Salida / Destino").grid(row=1, column=2, padx=(20, 5), pady=5)
salida_text = tk.Text(form, width=30, height=3)
salida_text.grid(row=1, column=3, padx=5, pady=5)

# -------------------------------
# BOTONES
# -------------------------------
botones = ttk.Frame(main)
botones.pack(pady=10)

ttk.Button(botones, text="Registrar Entrega", command=registrar_entrega).pack(side="left", padx=5)
ttk.Button(botones, text="Registrar Devolución", command=registrar_devolucion).pack(side="left", padx=5)
ttk.Button(botones, text="Exportar PDF", command=exportar_pdf).pack(side="left", padx=5)

# -------------------------------
# BÚSQUEDA
# -------------------------------
busqueda = ttk.Frame(main)
busqueda.pack(fill="x", pady=5)

ttk.Label(busqueda, text="Buscar por equipo:").pack(side="left", padx=5)
equipo_busqueda = ttk.Entry(busqueda, width=25)
equipo_busqueda.pack(side="left", padx=5)
ttk.Button(busqueda, text="Buscar", command=buscar_por_equipo).pack(side="left", padx=5)
ttk.Button(busqueda, text="Limpiar", command=limpiar_busqueda).pack(side="left", padx=5)

# -------------------------------
# TABLA
# -------------------------------
tabla_frame = ttk.Frame(main)
tabla_frame.pack(fill="both", expand=True)

cols = ("ID", "Registro", "Nombre", "Cargo", "Equipo", "Entrega", "Salida/Destino", "Devolución")
tree = ttk.Treeview(tabla_frame, columns=cols, show="headings")

for c in cols:
    tree.heading(c, text=c)
    if c == "ID":
        tree.column(c, width=0, stretch=False)
    elif c == "Salida/Destino":
        tree.column(c, width=260)
    else:
        tree.column(c, width=180)

tree.pack(side="left", fill="both", expand=True)

scroll = ttk.Scrollbar(tabla_frame, orient="vertical", command=tree.yview)
scroll.pack(side="right", fill="y")
tree.configure(yscrollcommand=scroll.set)

tree.tag_configure("pendiente", background="#F57E67")
tree.tag_configure("devuelto", background="#e5ffe5")

# -------------------------------
# PAGINACIÓN
# -------------------------------
paginacion = ttk.Frame(main)
paginacion.pack(pady=5)

btn_anterior = ttk.Button(paginacion, text="⟵ Anterior", command=pagina_anterior)
btn_anterior.pack(side="left", padx=5)

lbl_pagina = ttk.Label(paginacion, text="Página 1 de 1")
lbl_pagina.pack(side="left", padx=10)

btn_siguiente = ttk.Button(paginacion, text="Siguiente ⟶", command=pagina_siguiente)
btn_siguiente.pack(side="left", padx=5)

# ===============================
# INICIO
# ===============================
cargar_registros()
root.mainloop()

