import sqlite3
import os

# Ruta estándar de la base de datos dentro de tu proyecto
DB_PATH = "data/sistema.db"

def get_connection():
    """Establece una conexión segura con la base de datos SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_db():
    """Crea las tablas originales del sistema e inyecta actualizaciones de forma segura"""
    dir_name = os.path.dirname(DB_PATH)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Crear la tabla de configuración original
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_empresa (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            nome_empresa TEXT DEFAULT 'Minha Loja',
            cnpj TEXT,
            endereco TEXT,
            telefone TEXT,
            email TEXT,
            logo_path TEXT,
            plano TEXT DEFAULT 'Starter'
        );
    """)
    
    # Inyectar una fila por defecto si la tabla está completamente vacía
    cursor.execute("SELECT COUNT(*) FROM config_empresa")
    if cursor.fetchone() == 0:
        cursor.execute("""
            INSERT INTO config_empresa (id, nome_empresa, plano) 
            VALUES (1, 'Minha Loja', 'Starter');
        """)
    
    # 2. Inyector de seguridad automático para el Pix
    try:
        cursor.execute("ALTER TABLE config_empresa ADD COLUMN pix_chave TEXT;")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # 3. Crear el resto de las tablas del sistema (Estructura expandida 100% compatible)
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nome TEXT NOT NULL,
            nivel TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_producto TEXT UNIQUE NOT NULL,
            nombre_producto TEXT NOT NULL,
            categoria TEXT,
            precio_costo REAL,
            precio_venta REAL,
            estoque_atual REAL,
            stock_minimo REAL,
            validade TEXT,
            data_vencimento TEXT
        );

        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT,
            telefone TEXT,
            email TEXT
        );

        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_cupom TEXT,
            data_venda TEXT,
            codigo_producto TEXT,
            cantidad REAL,
            precio_unitario REAL,
            total REAL,
            forma_pagamento TEXT
        );

        CREATE TABLE IF NOT EXISTS cierres_caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            total_ventas REAL,
            diferencia REAL
        );
    """)
    
    # Inyectar un usuario administrador por defecto si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone() == 0:
        cursor.execute("""
            INSERT INTO usuarios (usuario, senha, nome, nivel) 
            VALUES ('admin', 'admin', 'Administrador', 'admin');
        """)
    
    conn.commit()
    conn.close()
