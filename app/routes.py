"""Rotas HTTP - PGM Porto Velho - Subprocuradoria Contenciosa."""
from flask import Blueprint, render_template, request, jsonify, current_app
from functools import wraps
import os, json, requests as http
from datetime import datetime, date, timedelta

bp = Blueprint('main', __name__)

# Configurações do Supabase extraídas do seu ambiente
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://vmbzykywtgzyxmoxogel.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...')

def _sb_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
    }

# --- HELPERS DO SUPABASE ---

def _sb_get(table, params=''):
    try:
        r = http.get(f'{SUPABASE_URL}/rest/v1/{table}?{params}', headers=_sb_headers(), timeout=10)
        return r.json() if r.ok else []
    except Exception as e:
        print(f'[SB GET] {table}: {e}')
        return []

def _sb_upsert_bulk(table, data_list):
    """Insere ou atualiza múltiplos registros de uma vez (Upsert)."""
    try:
        h = _sb_headers()
        # Preferencia para mesclar duplicados com base na CONSTRAINT da tabela
        h['Prefer'] = 'resolution=merge-duplicates,return=minimal'
        r = http.post(f'{SUPABASE_URL}/rest/v1/{table}', headers=h, json=data_list, timeout=15)
        return r.ok
    except Exception as e:
        print(f'[SB UPSERT] {table}: {e}')
        return False

def _sb_patch(table, key, val, data):
    try:
        r = http.patch(f'{SUPABASE_URL}/rest/v1/{table}?{key}=eq.{val}',
                       headers=_sb_headers(), json=data, timeout=10)
        return r.ok
    except Exception as e:
        print(f'[SB PATCH] {e}')
        return False

def _sb_delete(table, key, val):
    try:
        r = http.delete(f'{SUPABASE_URL}/rest/v1/{table}?{key}=eq.{val}',
                        headers=_sb_headers(), timeout=10)
        return r.ok
    except Exception as e:
        print(f'[SB DELETE] {e}')
        return False

# --- GESTÃO DE CACHE (DADOS_CACHE) ---

def cache_get(chave):
    try:
        rows = _sb_get('dados_cache', f'chave=eq.{chave}&select=valor')
        if rows and isinstance(rows, list):
            return rows[0].get('valor')
    except: pass
    return None

def cache_set(chave, valor):
    try:
        h = _sb_headers()
        h['Prefer'] = 'resolution=merge-duplicates,return=minimal'
        http.post(f'{SUPABASE_URL}/rest/v1/dados_cache', headers=h,
                  json={'chave': chave, 'valor': valor, 'atualizado': datetime.utcnow().isoformat()}, timeout=10)
    except Exception as e:
        print(f'[CACHE SET] {chave}: {e}')

# --- LÓGICA DE PARSE E FILTRO ---

_NAO_PESSOAS = {'SPF','SPJ','SPMA','GEC','AMBIENTAL','FISCAL','COMCEP','VERIFICAR','-','Sem responsavel','DISTRIBUIR',''}
_NORMALIZAR = {'ERICA':'ERICA','JEFERSON':'JEFFERSON'}

def _norm(nome):
    return _NORMALIZAR.get(nome.upper(), nome.upper()) if nome else 'Sem responsavel'

def _eh_pessoa(nome):
    if not nome or nome in _NAO_PESSOAS: return False
    if nome.startswith(('DEVOLVIDO','ESCRITORIO','GABINETE')): return False
    return True
