"""Rotas HTTP - PGM Porto Velho - Subprocuradoria Contenciosa."""
from flask import Blueprint, render_template, request, jsonify, current_app
from functools import wraps
import os, json, requests as http
from datetime import datetime, date

bp = Blueprint('main', __name__)

# Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

def _sb_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
    }

def _sb_get(table, params=''):
    try:
        r = http.get(f'{SUPABASE_URL}/rest/v1/{table}?{params}', headers=_sb_headers(), timeout=10)
        return r.json() if r.ok else []
    except Exception as e:
        print(f'[SB GET] {table}: {e}')
        return []

def _sb_post(table, data):
    try:
        r = http.post(f'{SUPABASE_URL}/rest/v1/{table}', headers=_sb_headers(), json=data, timeout=10)
        result = r.json()
        return result[0] if r.ok and isinstance(result, list) and result else result
    except Exception as e:
        print(f'[SB POST] {table}: {e}')
        return {}

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

# Cache
_mem = {}

def cache_get(chave):
    try:
        rows = _sb_get('dados_cache', f'chave=eq.{chave}&select=valor')
        if rows and isinstance(rows, list) and rows[0].get('valor') is not None:
            _mem[chave] = rows[0]['valor']
            return rows[0]['valor']
    except Exception:
        pass
    return _mem.get(chave)

def cache_set(chave, valor):
    _mem[chave] = valor
    try:
        h = _sb_headers()
        r = http.patch(
            f'{SUPABASE_URL}/rest/v1/dados_cache?chave=eq.{chave}',
            headers=h,
            json={'valor': valor, 'atualizado': datetime.utcnow().isoformat()},
            timeout=15
        )
        if r.ok and r.text.strip() not in ('', '[]', 'null'):
            return
        h2 = {**h, 'Prefer': 'return=minimal'}
        r2 = http.post(
            f'{SUPABASE_URL}/rest/v1/dados_cache',
            headers=h2,
            json={'chave': chave, 'valor': valor, 'atualizado': datetime.utcnow().isoformat()},
            timeout=15
        )
        if not r2.ok:
            print(f'[CACHE SET ERROR] {chave}: {r2.status_code} {r2.text[:200]}')
    except Exception as e:
        print(f'[CACHE SET] {chave}: {e}')

# Token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        expected_token = current_app.config.get('ACCESS_TOKEN', 'pgm-contenciosa-2026')
        if token != expected_token:
            return jsonify({'error': 'Token inválido'}), 401
        return f(*args, **kwargs)
    return decorated

# Routes
@bp.route('/')
def index():
    from flask import redirect, url_for
    try:
        token = current_app.config.get('ACCESS_TOKEN', 'pgm-contenciosa-2026')
        return redirect(url_for('main.painel', token=token))
    except Exception as e:
        print(f'[ERROR index] {e}')
        return redirect('/painel?token=pgm-contenciosa-2026')

@bp.route('/favicon.ico')
def favicon():
    from flask import send_from_directory
    return send_from_directory(os.path.join(current_app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@bp.route('/painel')
def painel():
    from flask import make_response
    resp = make_response(render_template('dashboard.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@bp.route('/api/dashboard')
@token_required
def get_dashboard():
    stats = cache_get('stats') or {'total': 0, 'cumpridos': 0, 'vencidos': 0, 'proximos': 0, 'taxa': 0}
    perf = cache_get('performance') or []
    proximos = cache_get('proximos') or []
    vencidos = cache_get('vencidos') or []
    cumpridos_lista = cache_get('cumpridos_lista') or []
    
    try:
        membros_raw = _sb_get('equipe', 'select=nome,ativo')
        if membros_raw and isinstance(membros_raw, list):
            cadastrados = set(
                m['nome'].strip().upper() for m in membros_raw
                if isinstance(m, dict) and m.get('nome') and m.get('ativo') is not False
            )
            if cadastrados:
                perf = [p for p in perf if p.get('responsavel', '').strip().upper() in cadastrados]
    except Exception as e:
        print(f'[WARN] filtro equipe falhou: {e}')
    
    return jsonify({
        'total': stats.get('total', 0),
        'cumpridos': stats.get('cumpridos', 0),
        'vencidos': len(vencidos),
        'proximos': len(proximos),
        'taxa': stats.get('taxa', 0),
        'performance': perf,
        'proximos_lista': proximos,
        'vencidos_lista': vencidos,
        'cumpridos_lista': cumpridos_lista,
        'filename': cache_get('filename') or ''
    })

@bp.route('/api/criticos')
@token_required
def get_criticos():
    from datetime import timezone, timedelta
    tz_ro = timezone(timedelta(hours=-4))
    hoje = datetime.now(tz_ro).date()
    
    todos_proximos = cache_get('proximos') or []
    todos_vencidos = cache_get('vencidos') or []
    
    proximos_atualizados = []
    vencidos_atualizados = []
    
    for p in todos_proximos:
        try:
            prazo_d = datetime.strptime(p['prazo'], '%d/%m/%Y').date()
            diff = (prazo_d - hoje).days
            entry = dict(p)
            entry['dias'] = abs(diff)
            if diff < 0:
                vencidos_atualizados.append(entry)
            elif diff <= 7:
                proximos_atualizados.append(entry)
        except Exception:
            proximos_atualizados.append(p)
    
    for v in todos_vencidos:
        try:
            prazo_d = datetime.strptime(v['prazo'], '%d/%m/%Y').date()
            diff = (prazo_d - hoje).days
            entry = dict(v)
            entry['dias'] = abs(diff)
            vencidos_atualizados.append(entry)
        except Exception:
            vencidos_atualizados.append(v)
    
    proximos_atualizados.sort(key=lambda x: x['dias'])
    vencidos_atualizados.sort(key=lambda x: x['dias'], reverse=True)
    
    f = request.args.get('responsavel', '').strip().upper()
    if f:
        proximos_atualizados = [p for p in proximos_atualizados if p.get('responsavel', '').upper() == f]
        vencidos_atualizados = [v for v in vencidos_atualizados if v.get('responsavel', '').upper() == f]
    
    return jsonify({'vencidos': vencidos_atualizados, 'proximos': proximos_atualizados})

@bp.route('/api/cumpridos')
@token_required
def get_cumpridos():
    lista = cache_get('cumpridos_lista') or []
    resp_filtro = request.args.get('responsavel', '').strip().upper()
    if resp_filtro:
        lista = [c for c in lista if c.get('responsavel', '').upper() == resp_filtro]
    return jsonify({'cumpridos': lista})

@bp.route('/api/equipe')
@token_required
def get_equipe():
    membros = _sb_get('equipe', 'select=id,nome,funcao,email,whatsapp,ativo&order=id.asc')
    return jsonify({'membros': membros if isinstance(membros, list) else []})

@bp.after_request
def security(response):
    response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response
