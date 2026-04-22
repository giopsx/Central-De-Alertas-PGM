"""Rotas HTTP - PGM Porto Velho - Subprocuradoria Contenciosa."""
from flask import Blueprint, render_template, request, jsonify, current_app
from functools import wraps
import os, json, requests as http
from datetime import datetime, date, timedelta

bp = Blueprint('main', __name__)

# Configurações do Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://vmbzykywtgzyxmoxogel.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZtYnp5a3l3dGd6eXhtb3hvZ2VsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjM3NjAyMywiZXhwIjoyMDkxOTUyMDIzfQ.fJlvsVIPLkIg5IXNx1uYfqa5pDj1B8DbRQIUiiTpcEo')

def _sb_headers():
    return {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Content-Type': 'application/json', 'Prefer': 'return=representation'}

def _sb_get(table, params=''):
    try:
        r = http.get(f'{SUPABASE_URL}/rest/v1/{table}?{params}', headers=_sb_headers(), timeout=10)
        return r.json() if r.ok else []
    except: return []

def cache_set(chave, valor):
    try:
        h = _sb_headers()
        h['Prefer'] = 'resolution=merge-duplicates,return=minimal'
        http.post(f'{SUPABASE_URL}/rest/v1/dados_cache', headers=h, json={'chave': chave, 'valor': valor, 'atualizado': datetime.utcnow().isoformat()}, timeout=10)
    except: pass

def cache_get(chave):
    try:
        rows = _sb_get('dados_cache', f'chave=eq.{chave}&select=valor')
        return rows[0].get('valor') if rows else None
    except: pass
    return None

# --- PROCESSAMENTO DINÂMICO ---
def _processar_dados(lista_mestra):
    hoje = date.today()
    venc, prox, cumpridos = [], [], []
    perf = {}
    
    for p in lista_mestra:
        dt = date.fromisoformat(p['data_iso'])
        resp = p['responsavel']
        if resp not in perf: perf[resp] = {'responsavel':resp, 'total':0, 'cumpridos':0, 'criticos':0}
        perf[resp]['total'] += 1
        
        if p.get('cumprido', False):
            perf[resp]['cumpridos'] += 1
            cumpridos.append(p)
            continue
            
        diff = (dt - hoje).days
        p['dias'] = diff
        if diff < 0:
            perf[resp]['criticos'] += 1
            venc.append(p)
        elif diff <= 7:
            prox.append(p)
            
    perf_list = []
    for r in perf.values():
        r['taxa'] = round(r['cumpridos']/r['total']*100, 1) if r['total'] > 0 else 0
        perf_list.append(r)
        
    return {
        'stats': {'total': len(lista_mestra), 'vencidos': len(venc), 'proximos': len(prox), 'cumpridos': len(cumpridos), 'taxa': round(len(cumpridos)/len(lista_mestra)*100, 1) if lista_mestra else 0, 'ultima_atualizacao': hoje.strftime('%d/%m/%Y')},
        'performance': sorted(perf_list, key=lambda x: x['taxa'], reverse=True),
        'proximos': sorted(prox, key=lambda x: x['dias']),
        'vencidos': sorted(venc, key=lambda x: x['dias'], reverse=True)
    }

@bp.route('/api/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    import openpyxl
    wb = openpyxl.load_workbook(file, data_only=True)
    ws = wb.active # Tenta a aba ativa para ser mais flexível
    lista = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[1] or not row[4]: continue
        lista.append({
            'processo': str(row[4]).strip(), 'parte': str(row[5] or '')[:60], 'responsavel': str(row[2] or '').upper(),
            'prazo': row[1].strftime('%d/%m/%Y'), 'data_iso': row[1].date().isoformat(), 'vara': str(row[6] or ''),
            'cumprido': str(row[13]).strip().upper() in ('SIM', 'PARCIAL')
        })
    cache_set('lista_mestra', lista)
    return jsonify({'success': True})

@bp.route('/api/dashboard')
def get_dashboard():
    lista = cache_get('lista_mestra')
    if not lista: return jsonify({'sem_dados': True})
    return jsonify(_processar_dados(lista))

@bp.route('/api/criticos')
def get_criticos():
    lista = cache_get('lista_mestra')
    res = _processar_dados(lista or [])
    return jsonify({'vencidos': res['vencidos'], 'proximos': res['proximos']})

@bp.route('/painel')
def painel(): return render_template('dashboard.html')

@bp.route('/')
def index(): return render_template('dashboard.html')

@bp.route('/api/equipe', methods=['GET', 'POST'])
def equipe_api():
    if request.method == 'GET': return jsonify({'membros': _sb_get('equipe', 'order=id.asc')})
    data = request.get_json()
    try:
        r = http.post(f'{SUPABASE_URL}/rest/v1/equipe', headers=_sb_headers(), json=data, timeout=10)
        return jsonify({'success': True, 'membro': r.json()})
    except: return jsonify({'success': False}), 500
