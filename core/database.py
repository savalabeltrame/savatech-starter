import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'savatech.db')
LOGOS_DIR = os.path.join(BASE_DIR, 'data', 'logos')


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(LOGOS_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrar(conn):
    """Agrega columnas nuevas a una base de datos ya existente."""
    migraciones = [
        ("produtos", "validade", "TEXT"),
        ("vendas", "usuario", "TEXT"),
        ("vendas", "cliente_id", "INTEGER"),
        ("vendas", "desconto", "REAL DEFAULT 0"),
    ]
    for tabla, columna, tipo in migraciones:
        try:
            conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")
        except sqlite3.OperationalError:
            pass  # la columna ya existe
            ("config_empresa", "pix_chave", "TEXT"),


def inicializar_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nome TEXT NOT NULL,
            nivel TEXT NOT NULL
        );

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

        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_producto TEXT UNIQUE NOT NULL,
            nombre_producto TEXT NOT NULL,
            categoria TEXT,
            precio_costo REAL DEFAULT 0,
            precio_venta REAL DEFAULT 0,
            estoque_atual INTEGER DEFAULT 0,
            stock_minimo INTEGER DEFAULT 5,
            validade TEXT
        );

        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            telefone TEXT,
            email TEXT,
            tipo_cliente TEXT DEFAULT 'Normal'
        );

        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_cupom INTEGER NOT NULL,
            codigo_producto TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            total REAL NOT NULL,
            forma_pagamento TEXT,
            data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usuario TEXT,
            cliente_id INTEGER,
            desconto REAL DEFAULT 0
        );

        INSERT OR IGNORE INTO usuarios (usuario, senha, nome, nivel)
        VALUES ('admin', 'admin123', 'Administrador', 'admin');
        INSERT OR IGNORE INTO usuarios (usuario, senha, nome, nivel)
VALUES ('cajero', 'cajero123', 'Operador de Caixa', 'cajero');
        INSERT OR IGNORE INTO config_empresa (id, nome_empresa, plano)
        VALUES (1, 'Minha Loja', 'Starter');
    """)
    _migrar(conn)
    conn.commit()
    conn.close()