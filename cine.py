import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib

# ─────────────────────────────────────
# CONFIG
# ─────────────────────────────────────
DB = "cinehub.db"

st.set_page_config(
    page_title="CineHub",
    page_icon="🎬",
    layout="wide"
)

# ─────────────────────────────────────
# ESTILOS
# ─────────────────────────────────────
st.markdown("""
<style>
.stApp {
    background-color: #0f172a;
    color: white;
}

h1, h2, h3 {
    color: #f8fafc !important;
}

[data-testid="stSidebar"] {
    background-color: #111827;
}

.stButton button {
    background-color: #7c3aed;
    color: white;
    border: none;
    border-radius: 10px;
}

.stButton button:hover {
    background-color: #6d28d9;
}

div[data-testid="stMetric"] {
    background: #1e293b;
    border-radius: 12px;
    padding: 15px;
}

.stDataFrame {
    background-color: white;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────
# DB
# ─────────────────────────────────────
def conectar():
    return sqlite3.connect(DB)

def crear_db():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS peliculas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        genero TEXT,
        año INTEGER,
        calificacion REAL,
        estado TEXT,
        fecha TEXT
    )
    """)

    conn.commit()
    conn.close()

crear_db()

# ─────────────────────────────────────
# HELPERS
# ─────────────────────────────────────
def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def registrar(usuario, password):
    try:
        conn = conectar()
        c = conn.cursor()
        c.execute(
            "INSERT INTO usuarios(usuario,password) VALUES (?,?)",
            (usuario, hash_pass(password))
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False

def login(usuario, password):
    conn = conectar()
    c = conn.cursor()

    c.execute(
        "SELECT * FROM usuarios WHERE usuario=? AND password=?",
        (usuario, hash_pass(password))
    )

    data = c.fetchone()
    conn.close()

    return data

def q(sql, params=()):
    conn = conectar()
    c = conn.cursor()
    c.execute(sql, params)
    conn.commit()
    conn.close()

def df(sql):
    conn = conectar()
    data = pd.read_sql_query(sql, conn)
    conn.close()
    return data

# ─────────────────────────────────────
# SESSION
# ─────────────────────────────────────
if "login" not in st.session_state:
    st.session_state.login = False

if "user" not in st.session_state:
    st.session_state.user = ""

# ─────────────────────────────────────
# LOGIN
# ─────────────────────────────────────
if not st.session_state.login:

    st.title("🎬 CineHub")

    tab1, tab2 = st.tabs(["Iniciar sesión", "Registrarse"])

    with tab1:
        st.subheader("Login")

        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")

        if st.button("Entrar"):

            data = login(user, pw)

            if data:
                st.session_state.login = True
                st.session_state.user = user
                st.success("Bienvenido")
                st.rerun()
            else:
                st.error("Datos incorrectos")

    with tab2:
        st.subheader("Crear cuenta")

        new_user = st.text_input("Nuevo usuario")
        new_pw = st.text_input("Nueva contraseña", type="password")

        if st.button("Crear cuenta"):

            ok = registrar(new_user, new_pw)

            if ok:
                st.success("Cuenta creada")
            else:
                st.error("Ese usuario ya existe")

# ─────────────────────────────────────
# APP
# ─────────────────────────────────────
else:

    with st.sidebar:
        st.title("🎬 CineHub")
        st.write(f"Usuario: **{st.session_state.user}**")

        pagina = st.radio(
            "Menú",
            [
                "Dashboard",
                "Agregar película",
                "Biblioteca",
                "Estadísticas"
            ]
        )

        if st.button("Cerrar sesión"):
            st.session_state.login = False
            st.rerun()

    # ─────────────────────────────────
    # DASHBOARD
    # ─────────────────────────────────
    if pagina == "Dashboard":

        st.title("Dashboard")

        pelis = df("SELECT * FROM peliculas")

        total = len(pelis)

        vistas = len(pelis[pelis["estado"] == "Vista"]) if not pelis.empty else 0

        pendientes = len(pelis[pelis["estado"] == "Pendiente"]) if not pelis.empty else 0

        promedio = pelis["calificacion"].mean() if not pelis.empty else 0

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Películas", total)
        c2.metric("Vistas", vistas)
        c3.metric("Pendientes", pendientes)
        c4.metric("Calificación promedio", f"{promedio:.1f}")

        st.markdown("---")

        st.subheader("Últimas películas")

        ultimas = df("""
        SELECT titulo,genero,año,calificacion,estado
        FROM peliculas
        ORDER BY id DESC
        LIMIT 10
        """)

        if not ultimas.empty:
            st.dataframe(ultimas, use_container_width=True, hide_index=True)
        else:
            st.info("No hay películas registradas")

    # ─────────────────────────────────
    # AGREGAR
    # ─────────────────────────────────
    elif pagina == "Agregar película":

        st.title("Agregar película")

        with st.form("pelicula"):

            titulo = st.text_input("Título")
            genero = st.selectbox(
                "Género",
                [
                    "Acción",
                    "Drama",
                    "Terror",
                    "Comedia",
                    "Sci-Fi",
                    "Romance",
                    "Otro"
                ]
            )

            año = st.number_input(
                "Año",
                min_value=1900,
                max_value=2100,
                value=2025
            )

            calificacion = st.slider(
                "Calificación",
                0.0,
                10.0,
                5.0
            )

            estado = st.selectbox(
                "Estado",
                ["Vista", "Pendiente"]
            )

            guardar = st.form_submit_button(
                "Guardar película"
            )

        if guardar:

            q("""
            INSERT INTO peliculas
            (titulo,genero,año,calificacion,estado,fecha)
            VALUES (?,?,?,?,?,?)
            """,
            (
                titulo,
                genero,
                año,
                calificacion,
                estado,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))

            st.success("Película agregada")

    # ─────────────────────────────────
    # BIBLIOTECA
    # ─────────────────────────────────
    elif pagina == "Biblioteca":

        st.title("Biblioteca")

        peliculas = df("""
        SELECT *
        FROM peliculas
        ORDER BY id DESC
        """)

        if not peliculas.empty:

            buscar = st.text_input("Buscar película")

            if buscar:
                peliculas = peliculas[
                    peliculas["titulo"]
                    .str.lower()
                    .str.contains(buscar.lower())
                ]

            st.dataframe(
                peliculas[
                    [
                        "titulo",
                        "genero",
                        "año",
                        "calificacion",
                        "estado",
                        "fecha"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")

            ids = peliculas["id"].tolist()

            borrar = st.selectbox(
                "Eliminar película",
                ids
            )

            if st.button("Eliminar"):
                q(
                    "DELETE FROM peliculas WHERE id=?",
                    (borrar,)
                )

                st.warning("Película eliminada")
                st.rerun()

        else:
            st.info("Biblioteca vacía")

    # ─────────────────────────────────
    # ESTADÍSTICAS
    # ─────────────────────────────────
    elif pagina == "Estadísticas":

        st.title("Estadísticas")

        datos = df("""
        SELECT genero, COUNT(*) as total
        FROM peliculas
        GROUP BY genero
        """)

        if not datos.empty:

            st.subheader("Películas por género")

            st.bar_chart(
                datos.set_index("genero")
            )

            top = df("""
            SELECT titulo, calificacion
            FROM peliculas
            ORDER BY calificacion DESC
            LIMIT 5
            """)

            st.subheader("Top películas")

            st.dataframe(
                top,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No hay datos suficientes")