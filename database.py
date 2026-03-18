import sqlite3
import json
from datetime import datetime

DB_FILE = "routes.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            origin TEXT,
            destination TEXT,
            stops TEXT,
            total_distance REAL,
            estimated_time REAL,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_route(name, origin, destination, stops, total_distance, estimated_time):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO routes (name, origin, destination, stops, total_distance, estimated_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, origin, destination, json.dumps(stops), total_distance, estimated_time, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def load_routes():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, origin, destination, stops, total_distance, estimated_time, created_at FROM routes ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_route(route_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM routes WHERE id = ?", (route_id,))
    conn.commit()
    conn.close()
