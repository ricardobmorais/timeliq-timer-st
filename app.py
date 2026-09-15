import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime, date
import io

st.set_page_config(page_title="Timeliq Timer", page_icon="⏱", layout="centered")

# ─────────────────────────────────────────
# CSS PERSONALIZADO
# ─────────────────────────────────────────
st.markdown("""
<style>
  /* Esconde o menu hamburger e footer do Streamlit */
  #MainMenu, footer, header {visibility: hidden;}
  
  /* Fundo da página */
  .stApp { background: #f4f5f7; }
  
  /* Container principal */
  .block-container { 
    max-width: 680px !important; 
    padding-top: 2rem !important;
  }
  
  /* Título */
  .timeliq-title {
    font-size: 22px;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 2px;
  }
  .timeliq-subtitle {
    font-size: 13px;
    color: #6b6b6b;
    margin-bottom: 20px;
  }
  
  /* Card branco */
  .card {
    background: #ffffff;
    border: 1px solid #e3e3e3;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
  }
  
  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    background: #f0f1f3;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-weight: 500;
    font-size: 14px;
    color: #555;
    padding: 8px 20px;
  }
  .stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #1a1a1a !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
  }
  
  /* Labels */
  .stTextInput label, .stSelectbox label, .stDateInput label {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #444 !important;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  
  /* Inputs */
  .stTextInput input, .stSelectbox select {
    border-radius: 8px !important;
    border: 1px solid #d4d4d4 !important;
    font-size: 14px !important;
    background: #fafafa !important;
  }
  .stTextInput input:focus {
    border-color: #1a73e8 !important;
    background: #fff !important;
  }
  
  /* Botão primário */
  .stButton > button[kind="primary"] {
    background: #1a73e8 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    width: 100% !important;
    padding: 12px !important;
  }
  
  /* Info box de duração */
  .stAlert {
    border-radius: 8px !important;
    font-size: 14px !important;
  }
  
  /* Tabela de registos */
  .registo-linha {
    display: flex;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;
    font-size: 13px;
    gap: 8px;
  }
  .registo-data { color: #555; min-width: 90px; }
  .registo-hora { color: #1a73e8; font-weight: 600; min-width: 60px; }
  .registo-duracao { color: #e8710a; font-weight: 600; min-width: 50px; }
  .registo-pat { color: #444; min-width: 65px; }
  .registo-cliente { color: #1a1a1a; font-weight: 500; min-width: 90px; }
  .registo-tipo { color: #555; min-width: 120px; }
  .registo-relatorio { color: #777; flex: 1; }
  
  /* Mes header */
  .mes-header {
    font-size: 13px;
    font-weight: 700;
    color: #1a73e8;
    margin: 16px 0 8px;
    text-transform: capitalize;
  }
  
  /* Duracao display */
  .duracao-display {
    text-align: center;
    font-size: 48px;
    font-weight: 700;
    color: #1a73e8;
    font-family: monospace;
    letter-spacing: 4px;
    padding: 16px 0;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# TIPOS
# ─────────────────────────────────────────
TIPOS = [
    "", "Demonstração", "Documentação", "Formação", "Férias",
    "Gestão Projecto", "Gestão Serviço", "Gestão Transição",
    "Instalações Cilnet", "Instalações Cliente", "Mail", "RMA",
    "Reunião Cilnet", "Reunião Cliente", "Tarefa"
]

MESES_PT = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
            "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

# ─────────────────────────────────────────
# BD
# ─────────────────────────────────────────
def get_conn():
    return psycopg2.connect(st.secrets["postgres"]["PG_CONN_STRING"])

@st.cache_resource
def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS timer_registos (
                    id SERIAL PRIMARY KEY,
                    nopat TEXT, cliente TEXT, projeto TEXT,
                    data DATE NOT NULL, hora TIME NOT NULL, horaf TIME NOT NULL,
                    tipo TEXT, relatorio TEXT,
                    kms TEXT DEFAULT '0', deslocacao TEXT DEFAULT '00:00',
                    criado_em TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()

init_db()

def listar_registos():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, nopat, cliente, projeto,
                       TO_CHAR(data,'DD/MM/YYYY') as data,
                       TO_CHAR(hora,'HH24:MI') as hora,
                       TO_CHAR(horaf,'HH24:MI') as horaf,
                       tipo, relatorio, kms, deslocacao
                FROM timer_registos ORDER BY data DESC, hora DESC
            """)
            return cur.fetchall()

def inserir_registo(nopat, cliente, projeto, data, hora, horaf, tipo, relatorio, kms, deslocacao):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO timer_registos (nopat,cliente,projeto,data,hora,horaf,tipo,relatorio,kms,deslocacao)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (nopat,cliente,projeto,data,hora,horaf,tipo,relatorio,kms,deslocacao))
            conn.commit()

def apagar_registo(rid):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM timer_registos WHERE id=%s", (rid,))
            conn.commit()

def listar_opcoes(campo, filtros={}):
    where = " AND ".join([f"{k}=%s" for k in filtros])
    sql = f"SELECT DISTINCT {campo} FROM timer_registos WHERE {campo} IS NOT NULL AND {campo}!='' "
    if where:
        sql += f" AND {where}"
    sql += f" ORDER BY {campo}"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, list(filtros.values()))
            return [r[0] for r in cur.fetchall()]

def calcular_duracao(h1, h2):
    try:
        t1 = datetime.strptime(h1, "%H:%M")
        t2 = datetime.strptime(h2, "%H:%M")
        m = int((t2-t1).total_seconds()/60)
        return f"{m//60:02d}:{m%60:02d}" if m > 0 else "00:00"
    except:
        return "00:00"

def exportar_csv_bytes(d1, d2):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT nopat, TO_CHAR(data,'DD/MM/YYYY') as data,
                       TO_CHAR(hora,'HH24:MI') as hora, TO_CHAR(horaf,'HH24:MI') as horaf,
                       deslocacao as deh, tipo, relatorio, kms
                FROM timer_registos WHERE data BETWEEN %s AND %s ORDER BY data,hora
            """, (d1,d2))
            rows = cur.fetchall()
    if not rows: return None
    linhas = ["nopat;data;hora;horaf;deh;tipo;relatorio;kms"]
    for r in rows:
        linhas.append(f"{r['nopat']};{r['data']};{r['hora']};{r['horaf']};{r['deh']};{r['tipo']};{r['relatorio']};{r['kms']}")
    return '\r\n'.join(linhas).encode('windows-1252', errors='replace')

def importar_csv(texto):
    linhas = texto.lstrip('\ufeff').replace('\r\n','\n').replace('\r','\n').split('\n')
    linhas = [l for l in linhas if l.strip()]
    if len(linhas) < 2: return 0, 0
    cab = [h.strip() for h in linhas[0].split(';')]
    add, skip = 0, 0
    for linha in linhas[1:]:
        vals = [v.strip() for v in linha.split(';')]
        r = dict(zip(cab, vals))
        if not r.get('data') or not r.get('hora'): continue
        try:
            p = r['data'].split('/')
            d = date(int(p[2]),int(p[1]),int(p[0]))
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM timer_registos WHERE nopat=%s AND data=%s AND hora=%s AND horaf=%s",
                                (r.get('nopat',''), d, r.get('hora',''), r.get('horaf','')))
                    if cur.fetchone(): skip += 1; continue
            inserir_registo(r.get('nopat',''),r.get('cliente',''),r.get('projeto',''),
                            d,r.get('hora',''),r.get('horaf',''),
                            r.get('tipo',''),r.get('relatorio',''),
                            r.get('kms','0'),r.get('deh','00:00'))
            add += 1
        except: continue
    return add, skip

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown('<div class="timeliq-title">⏱ Timeliq Timer</div>', unsafe_allow_html=True)
st.markdown('<div class="timeliq-subtitle">Contabilizador de tempos de tarefa</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Cronómetro / Manual", "📋 Registos", "📊 Métricas"])

# ═══════════════════════════════
# TAB 1 — REGISTAR
# ═══════════════════════════════
with tab1:
    # Cronómetro simples
    if 'cronometro_inicio' not in st.session_state:
        st.session_state.cronometro_inicio = None

    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("▶ Start", use_container_width=True, disabled=st.session_state.cronometro_inicio is not None):
            st.session_state.cronometro_inicio = datetime.now()
            st.rerun()
    with col_stop:
        if st.button("⏹ Stop", use_container_width=True, disabled=st.session_state.cronometro_inicio is None):
            fim = datetime.now()
            st.session_state.hora_auto = st.session_state.cronometro_inicio.strftime("%H:%M")
            st.session_state.horaf_auto = fim.strftime("%H:%M")
            st.session_state.data_auto = st.session_state.cronometro_inicio.date()
            st.session_state.cronometro_inicio = None
            st.rerun()

    if st.session_state.cronometro_inicio:
        elapsed = datetime.now() - st.session_state.cronometro_inicio
        h, rem = divmod(int(elapsed.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        st.markdown(f'<div class="duracao-display">{h:02d}:{m:02d}:{s:02d}</div>', unsafe_allow_html=True)
        st.rerun()

    st.divider()

    # Campos do registo
    clientes = listar_opcoes('cliente')
    c1, c2 = st.columns(2)
    with c1:
        cliente_sel = st.selectbox("Cliente / Atividade Interna", [""] + clientes, key="f_cliente")
        cliente_novo = st.text_input("Ou escreve novo cliente", key="f_cliente_novo", label_visibility="collapsed", placeholder="Novo cliente...")
        cliente = cliente_novo.strip() if cliente_novo.strip() else cliente_sel

    projetos = listar_opcoes('projeto', {'cliente': cliente} if cliente else {})
    with c2:
        projeto_sel = st.selectbox("Projeto", [""] + projetos, key="f_projeto")
        projeto_novo = st.text_input("Ou escreve novo projeto", key="f_projeto_novo", label_visibility="collapsed", placeholder="Novo projeto...")
        projeto = projeto_novo.strip() if projeto_novo.strip() else projeto_sel

    pats = listar_opcoes('nopat', {'cliente': cliente, 'projeto': projeto} if projeto else ({'cliente': cliente} if cliente else {}))
    c3, c4 = st.columns(2)
    with c3:
        pat_sel = st.selectbox("Nº PAT", [""] + pats, key="f_pat")
        pat_novo = st.text_input("Ou escreve novo PAT", key="f_pat_novo", label_visibility="collapsed", placeholder="Novo PAT...")
        nopat = pat_novo.strip() if pat_novo.strip() else pat_sel
    with c4:
        tipo = st.selectbox("Tipo", TIPOS, key="f_tipo")

    relatorio = st.text_input("Relatório", placeholder="descrição da tarefa", key="f_relatorio")

    c5, c6, c7 = st.columns(3)
    with c5:
        data = st.date_input("Data", value=st.session_state.get('data_auto', date.today()), format="DD/MM/YYYY", key="f_data")
    with c6:
        hora = st.text_input("Hora início", value=st.session_state.get('hora_auto','09:00'), key="f_hora", placeholder="09:00")
    with c7:
        horaf = st.text_input("Hora fim", value=st.session_state.get('horaf_auto','10:00'), key="f_horaf", placeholder="10:00")

    c8, c9 = st.columns(2)
    with c8:
        kms = st.text_input("Km / Deslocação", value="0", key="f_kms")
    with c9:
        deslocacao = st.text_input("Tempo de Deslocação (HH:MM)", value="00:00", key="f_deslocacao")

    dur = calcular_duracao(hora, horaf)
    st.info(f"⏱ Duração: **{dur}**")

    if st.button("💾 Gravar registo", type="primary", use_container_width=True):
        if not nopat:
            st.error("Indica o Nº PAT.")
        else:
            inserir_registo(nopat, cliente, projeto, data, hora, horaf, tipo, relatorio, kms, deslocacao)
            for k in ['hora_auto','horaf_auto','data_auto']:
                st.session_state.pop(k, None)
            st.success("✅ Gravado!")
            st.rerun()

    st.divider()
    st.markdown("**📥 Importar CSV**")
    f = st.file_uploader("", type=["csv"], label_visibility="collapsed")
    if f:
        if st.button("Importar", key="btn_import"):
            txt = f.read().decode('windows-1252', errors='replace')
            add, skip = importar_csv(txt)
            st.success(f"✅ {add} importado(s), {skip} já existiam.")
            st.rerun()

# ═══════════════════════════════
# TAB 2 — REGISTOS
# ═══════════════════════════════
with tab2:
    # Export
    with st.expander("📤 Exportar CSV para PHC"):
        ce1, ce2 = st.columns(2)
        with ce1:
            ei = st.date_input("De", value=date.today().replace(day=1), format="DD/MM/YYYY", key="ei")
        with ce2:
            ef = st.date_input("Até", value=date.today(), format="DD/MM/YYYY", key="ef")
        csv_b = exportar_csv_bytes(ei, ef)
        if csv_b:
            st.download_button("⬇️ Descarregar CSV", data=csv_b,
                file_name=f"tempos_{ei.strftime('%Y-%m-%d')}_a_{ef.strftime('%Y-%m-%d')}.csv",
                mime="text/csv")
        else:
            st.caption("Sem registos nesse período.")

    registos = listar_registos()
    if not registos:
        st.info("Ainda não há registos.")
    else:
        # Agrupa por mês
        meses = {}
        for r in registos:
            d = r['data']  # DD/MM/YYYY
            chave = d[3:]  # MM/YYYY
            num_mes = int(chave[:2])
            ano = chave[3:]
            label = f"{MESES_PT[num_mes-1]} de {ano}"
            if chave not in meses:
                meses[chave] = {'label': label, 'regs': []}
            meses[chave]['regs'].append(r)

        primeiro = True
        for chave, info in meses.items():
            with st.expander(f"📅 {info['label']} ({len(info['regs'])} registos)", expanded=primeiro):
                primeiro = False
                for r in info['regs']:
                    dur = calcular_duracao(r['hora'], r['horaf'])
                    c = st.columns([1.1, 0.7, 0.7, 0.6, 0.7, 1, 1.2, 2.2, 0.3, 0.3])
                    c[0].caption(r['data'])
                    c[1].markdown(f"**{r['hora']}**")
                    c[2].markdown(f"**{r['horaf']}**")
                    c[3].markdown(f"**{dur}**")
                    c[4].caption(r['nopat'] or '')
                    c[5].caption(r['cliente'] or '')
                    c[6].caption(r['tipo'] or '')
                    c[7].caption(r['relatorio'] or '')
                    if c[8].button("✏️", key=f"e{r['id']}"):
                        st.session_state['edit_id'] = r['id']
                        st.session_state['edit_r'] = dict(r)
                    if c[9].button("🗑", key=f"d{r['id']}"):
                        apagar_registo(r['id'])
                        st.rerun()

        if 'edit_id' in st.session_state:
            r = st.session_state['edit_r']
            st.divider()
            st.markdown("**✏️ Editar registo**")
            with st.form("edit_form"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    ec = st.text_input("Cliente", value=r.get('cliente',''))
                    ep = st.text_input("Projeto", value=r.get('projeto',''))
                    en = st.text_input("Nº PAT", value=r.get('nopat',''))
                with ec2:
                    et_idx = TIPOS.index(r.get('tipo','')) if r.get('tipo','') in TIPOS else 0
                    et = st.selectbox("Tipo", TIPOS, index=et_idx)
                    er = st.text_input("Relatório", value=r.get('relatorio',''))
                er2, er3, er4 = st.columns(3)
                with er2:
                    p = r['data'].split('/')
                    ed = st.date_input("Data", value=date(int(p[2]),int(p[1]),int(p[0])), format="DD/MM/YYYY")
                with er3:
                    eh = st.text_input("Hora início", value=r.get('hora',''))
                with er4:
                    ehf = st.text_input("Hora fim", value=r.get('horaf',''))
                ek = st.text_input("Km", value=r.get('kms','0'))
                edk = st.text_input("Deslocação", value=r.get('deslocacao','00:00'))
                ca, cb = st.columns(2)
                with ca:
                    if st.form_submit_button("💾 Atualizar", type="primary", use_container_width=True):
                        with get_conn() as conn:
                            with conn.cursor() as cur:
                                cur.execute("""UPDATE timer_registos SET
                                    nopat=%s,cliente=%s,projeto=%s,data=%s,hora=%s,
                                    horaf=%s,tipo=%s,relatorio=%s,kms=%s,deslocacao=%s
                                    WHERE id=%s""",
                                    (en,ec,ep,ed,eh,ehf,et,er,ek,edk,st.session_state['edit_id']))
                                conn.commit()
                        del st.session_state['edit_id'], st.session_state['edit_r']
                        st.rerun()
                with cb:
                    if st.form_submit_button("✕ Cancelar", use_container_width=True):
                        del st.session_state['edit_id'], st.session_state['edit_r']
                        st.rerun()

# ═══════════════════════════════
# TAB 3 — MÉTRICAS
# ═══════════════════════════════
with tab3:
    mc1, mc2 = st.columns(2)
    with mc1:
        mi = st.date_input("De", value=date.today().replace(day=1), format="DD/MM/YYYY", key="mi")
    with mc2:
        mf = st.date_input("Até", value=date.today(), format="DD/MM/YYYY", key="mf")

    if st.button("📊 Ver métricas", type="primary", use_container_width=True):
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT cliente, tipo,
                           SUM(EXTRACT(EPOCH FROM (horaf-hora))/60) as minutos
                    FROM timer_registos WHERE data BETWEEN %s AND %s
                    GROUP BY cliente, tipo ORDER BY minutos DESC
                """, (mi, mf))
                dados = cur.fetchall()

        if not dados:
            st.warning("Sem registos nesse período.")
        else:
            df = pd.DataFrame(dados)
            total = int(df['minutos'].sum())
            st.metric("Total geral", f"{total//60:02d}h{total%60:02d}m")

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Por Cliente**")
                pc = df.groupby('cliente')['minutos'].sum().reset_index().sort_values('minutos', ascending=False)
                pc['Horas'] = pc['minutos'].apply(lambda m: f"{int(m)//60:02d}h{int(m)%60:02d}m")
                pc['%'] = (pc['minutos']/pc['minutos'].sum()*100).round(1).astype(str)+'%'
                st.dataframe(pc[['cliente','Horas','%']].rename(columns={'cliente':'Cliente'}),
                             use_container_width=True, hide_index=True)
            with col_b:
                st.markdown("**Por Tipo**")
                pt = df.groupby('tipo')['minutos'].sum().reset_index().sort_values('minutos', ascending=False)
                pt['Horas'] = pt['minutos'].apply(lambda m: f"{int(m)//60:02d}h{int(m)%60:02d}m")
                pt['%'] = (pt['minutos']/pt['minutos'].sum()*100).round(1).astype(str)+'%'
                st.dataframe(pt[['tipo','Horas','%']].rename(columns={'tipo':'Tipo'}),
                             use_container_width=True, hide_index=True)
