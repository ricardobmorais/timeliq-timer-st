import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="Timeliq Timer", page_icon="⏱", layout="centered")

# ─────────────────────────────────────────
# TEMA
# ─────────────────────────────────────────
if 'tema' not in st.session_state:
    st.session_state.tema = 'claro'

def toggle_tema():
    st.session_state.tema = 'escuro' if st.session_state.tema == 'claro' else 'claro'

dark = st.session_state.tema == 'escuro'

# Cores por tema
if dark:
    bg = "#1a1a2e"
    card_bg = "#16213e"
    card_border = "#0f3460"
    text = "#e0e0e0"
    text_sub = "#9a9ab0"
    text_label = "#8888aa"
    input_bg = "#0f3460"
    input_border = "#1a5276"
    input_focus = "#3498db"
    tab_bg = "#0f3460"
    tab_active = "#1a5276"
    tab_text = "#9a9ab0"
    tab_active_text = "#ffffff"
    btn_bg = "#2980b9"
    btn_hover = "#3498db"
    divider = "#0f3460"
    mes_color = "#3498db"
    dur_color = "#e67e22"
    hora_color = "#3498db"
    info_bg = "#0f3460"
    info_border = "#1a5276"
    toggle_icon = "☀️"
    toggle_label = "Modo claro"
else:
    bg = "#f4f5f7"
    card_bg = "#ffffff"
    card_border = "#e3e3e3"
    text = "#1a1a1a"
    text_sub = "#6b6b6b"
    text_label = "#444444"
    input_bg = "#fafafa"
    input_border = "#d4d4d4"
    input_focus = "#1a73e8"
    tab_bg = "#f0f1f3"
    tab_active = "#ffffff"
    tab_text = "#555555"
    tab_active_text = "#1a1a1a"
    btn_bg = "#1a73e8"
    btn_hover = "#1557b0"
    divider = "#eeeeee"
    mes_color = "#1a73e8"
    dur_color = "#e8710a"
    hora_color = "#1a73e8"
    info_bg = "#e8f0fe"
    info_border = "#1a73e8"
    toggle_icon = "🌙"
    toggle_label = "Modo escuro"

st.markdown(f"""
<style>
  #MainMenu, footer, header {{visibility: hidden;}}
  .stApp {{ background: {bg} !important; }}
  .block-container {{ max-width: 700px !important; padding-top: 1.5rem !important; }}

  /* Texto geral */
  .stApp, .stApp p, .stApp label, .stApp div {{color: {text};}}

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {{
    background: {tab_bg} !important;
    border-radius: 10px; padding: 4px; gap: 4px;
  }}
  .stTabs [data-baseweb="tab"] {{
    border-radius: 8px; font-weight: 500; font-size: 14px;
    color: {tab_text} !important; padding: 8px 20px;
  }}
  .stTabs [aria-selected="true"] {{
    background: {tab_active} !important;
    color: {tab_active_text} !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
  }}

  /* Labels */
  .stTextInput label, .stSelectbox label, .stDateInput label,
  .stFileUploader label {{
    font-size: 12px !important; font-weight: 600 !important;
    color: {text_label} !important;
    text-transform: uppercase; letter-spacing: 0.3px;
  }}

  /* Inputs */
  .stTextInput input {{
    border-radius: 8px !important; border: 1px solid {input_border} !important;
    font-size: 14px !important; background: {input_bg} !important;
    color: {text} !important;
  }}
  .stTextInput input:focus {{
    border-color: {input_focus} !important; background: {card_bg} !important;
  }}

  /* Selectbox */
  .stSelectbox > div > div {{
    border-radius: 8px !important; border: 1px solid {input_border} !important;
    background: {input_bg} !important; color: {text} !important;
  }}

  /* Date input */
  .stDateInput > div > div {{
    border-radius: 8px !important; border: 1px solid {input_border} !important;
    background: {input_bg} !important; color: {text} !important;
  }}

  /* Botão primário */
  .stButton > button[kind="primary"] {{
    background: {btn_bg} !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; font-size: 14px !important;
    width: 100% !important; padding: 12px !important;
  }}
  .stButton > button[kind="primary"]:hover {{
    background: {btn_hover} !important;
  }}

  /* Botão secundário */
  .stButton > button[kind="secondary"] {{
    border-radius: 8px !important; border: 1px solid {input_border} !important;
    background: {input_bg} !important; color: {text} !important;
    font-size: 13px !important;
  }}

  /* Download button */
  .stDownloadButton > button {{
    border-radius: 8px !important; border: 1px solid {input_border} !important;
    background: {input_bg} !important; color: {text} !important;
  }}

  /* Expander */
  .streamlit-expanderHeader {{
    background: {card_bg} !important; border-radius: 8px !important;
    border: 1px solid {card_border} !important; color: {text} !important;
    font-weight: 600 !important;
  }}
  .streamlit-expanderContent {{
    background: {card_bg} !important; border: 1px solid {card_border} !important;
    border-top: none !important;
  }}

  /* Info/success/error */
  .stAlert {{
    border-radius: 8px !important; background: {info_bg} !important;
    border-left: 4px solid {info_border} !important; color: {text} !important;
  }}

  /* Métrica */
  .stMetric {{color: {text} !important;}}
  .stMetric label {{color: {text_sub} !important;}}

  /* Dataframe */
  .stDataFrame {{border-radius: 8px !important;}}

  /* Divider */
  hr {{border-color: {divider} !important;}}

  /* Caption */
  .stCaption, caption {{color: {text_sub} !important;}}

  /* Toggle button estilo */
  .tema-btn {{
    position: fixed; top: 14px; right: 60px; z-index: 999;
    background: {card_bg}; border: 1px solid {card_border};
    border-radius: 20px; padding: 4px 12px;
    font-size: 12px; cursor: pointer; color: {text};
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
  }}

  /* Duração display cronómetro */
  .duracao-display {{
    text-align: center; font-size: 52px; font-weight: 700;
    color: {hora_color}; font-family: monospace;
    letter-spacing: 4px; padding: 12px 0;
    background: {card_bg}; border-radius: 12px;
    border: 1px solid {card_border}; margin: 8px 0;
  }}

  /* Info duracao */
  .dur-info {{
    text-align: center; padding: 10px;
    background: {info_bg}; border-radius: 8px;
    border: 1px solid {info_border};
    font-size: 15px; font-weight: 600; color: {dur_color};
    margin: 8px 0;
  }}

  /* Linha registo */
  .reg-data {{color: {text_sub}; font-size: 12px;}}
  .reg-hora {{color: {hora_color}; font-weight: 700; font-size: 13px;}}
  .reg-dur {{color: {dur_color}; font-weight: 700; font-size: 13px;}}
  .reg-main {{color: {text}; font-size: 13px;}}
  .reg-sub {{color: {text_sub}; font-size: 12px;}}
  .mes-titulo {{
    color: {mes_color}; font-weight: 700; font-size: 13px;
    padding: 6px 0; text-transform: capitalize;
  }}
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
    sql = f"SELECT DISTINCT {campo} FROM timer_registos WHERE {campo} IS NOT NULL AND {campo}!=''"
    vals = []
    for k, v in filtros.items():
        if v:
            sql += f" AND {k}=%s"
            vals.append(v)
    sql += f" ORDER BY {campo}"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, vals)
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
col_title, col_tema = st.columns([5, 1])
with col_title:
    st.markdown(f"<h2 style='margin:0;color:{text}'>⏱ Timeliq Timer</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{text_sub};margin:0 0 12px;font-size:13px'>Contabilizador de tempos de tarefa</p>", unsafe_allow_html=True)
with col_tema:
    st.button(f"{toggle_icon}", on_click=toggle_tema, help=toggle_label, use_container_width=True)

# ─────────────────────────────────────────
# TABS
# ─────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📝 Registar", "📋 Registos", "📊 Métricas"])

# ═══════════════════════════════
# TAB 1 — REGISTAR
# ═══════════════════════════════
with tab1:
    if 'cron_inicio' not in st.session_state:
        st.session_state.cron_inicio = None

    col_s, col_e = st.columns(2)
    with col_s:
        if st.button("▶ Start", use_container_width=True,
                     disabled=st.session_state.cron_inicio is not None):
            st.session_state.cron_inicio = datetime.now()
            st.rerun()
    with col_e:
        if st.button("⏹ Stop", use_container_width=True,
                     disabled=st.session_state.cron_inicio is None):
            fim = datetime.now()
            st.session_state.hora_auto = st.session_state.cron_inicio.strftime("%H:%M")
            st.session_state.horaf_auto = fim.strftime("%H:%M")
            st.session_state.data_auto = st.session_state.cron_inicio.date()
            st.session_state.cron_inicio = None
            st.rerun()

    if st.session_state.cron_inicio:
        elapsed = datetime.now() - st.session_state.cron_inicio
        h, rem = divmod(int(elapsed.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        st.markdown(f'<div class="duracao-display">{h:02d}:{m:02d}:{s:02d}</div>',
                    unsafe_allow_html=True)
        st.rerun()

    st.divider()

    clientes = listar_opcoes('cliente')
    c1, c2 = st.columns(2)
    with c1:
        cliente_sel = st.selectbox("Cliente / Atividade Interna", [""] + clientes, key="f_cli")
        cliente_novo = st.text_input("Novo cliente", key="f_cli_novo",
                                      label_visibility="collapsed", placeholder="Escreve novo cliente...")
        cliente = cliente_novo.strip() or cliente_sel

    projetos = listar_opcoes('projeto', {'cliente': cliente})
    with c2:
        proj_sel = st.selectbox("Projeto", [""] + projetos, key="f_proj")
        proj_novo = st.text_input("Novo projeto", key="f_proj_novo",
                                   label_visibility="collapsed", placeholder="Escreve novo projeto...")
        projeto = proj_novo.strip() or proj_sel

    pats = listar_opcoes('nopat', {'cliente': cliente, 'projeto': projeto})
    c3, c4 = st.columns(2)
    with c3:
        pat_sel = st.selectbox("Nº PAT", [""] + pats, key="f_pat")
        pat_novo = st.text_input("Novo PAT", key="f_pat_novo",
                                  label_visibility="collapsed", placeholder="Escreve novo PAT...")
        nopat = pat_novo.strip() or pat_sel
    with c4:
        tipo = st.selectbox("Tipo", TIPOS, key="f_tipo")

    relatorio = st.text_input("Relatório", placeholder="descrição da tarefa", key="f_rel")

    c5, c6, c7 = st.columns(3)
    with c5:
        data = st.date_input("Data", value=st.session_state.get('data_auto', date.today()),
                              format="DD/MM/YYYY", key="f_data")
    with c6:
        hora = st.text_input("Hora início", value=st.session_state.get('hora_auto','09:00'),
                              key="f_hora", placeholder="09:00")
    with c7:
        horaf = st.text_input("Hora fim", value=st.session_state.get('horaf_auto','10:00'),
                               key="f_horaf", placeholder="10:00")

    c8, c9 = st.columns(2)
    with c8:
        kms = st.text_input("Km / Deslocação", value="0", key="f_kms")
    with c9:
        deslocacao = st.text_input("Tempo de Deslocação (HH:MM)", value="00:00", key="f_desloc")

    dur = calcular_duracao(hora, horaf)
    st.markdown(f'<div class="dur-info">⏱ Duração: {dur}</div>', unsafe_allow_html=True)

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
    st.markdown(f"<p style='font-weight:600;font-size:13px;color:{text}'>📥 Importar CSV</p>",
                unsafe_allow_html=True)
    f = st.file_uploader("", type=["csv"], label_visibility="collapsed", key="f_import")
    if f:
        if st.button("Importar", key="btn_imp"):
            txt = f.read().decode('windows-1252', errors='replace')
            add, skip = importar_csv(txt)
            st.success(f"✅ {add} importado(s), {skip} já existiam.")
            st.rerun()

# ═══════════════════════════════
# TAB 2 — REGISTOS
# ═══════════════════════════════
with tab2:
    with st.expander("📤 Exportar CSV para PHC"):
        ce1, ce2 = st.columns(2)
        with ce1:
            ei = st.date_input("De", value=date.today().replace(day=1),
                                format="DD/MM/YYYY", key="ei")
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
        meses = {}
        for r in registos:
            chave = r['data'][3:]
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
                # Cabeçalho
                cols_h = st.columns([1, 0.7, 0.7, 0.6, 0.7, 1.1, 1.2, 2, 0.3, 0.3])
                for h, lbl in zip(cols_h, ["Data","Início","Fim","Dur.","PAT","Cliente","Tipo","Relatório","",""] ):
                    h.markdown(f"<span style='font-size:11px;font-weight:700;color:{text_sub};text-transform:uppercase'>{lbl}</span>",
                               unsafe_allow_html=True)
                st.divider()
                for r in info['regs']:
                    dur = calcular_duracao(r['hora'], r['horaf'])
                    c = st.columns([1, 0.7, 0.7, 0.6, 0.7, 1.1, 1.2, 2, 0.3, 0.3])
                    c[0].markdown(f"<span class='reg-data'>{r['data']}</span>", unsafe_allow_html=True)
                    c[1].markdown(f"<span class='reg-hora'>{r['hora']}</span>", unsafe_allow_html=True)
                    c[2].markdown(f"<span class='reg-hora'>{r['horaf']}</span>", unsafe_allow_html=True)
                    c[3].markdown(f"<span class='reg-dur'>{dur}</span>", unsafe_allow_html=True)
                    c[4].markdown(f"<span class='reg-sub'>{r['nopat'] or ''}</span>", unsafe_allow_html=True)
                    c[5].markdown(f"<span class='reg-main'>{r['cliente'] or ''}</span>", unsafe_allow_html=True)
                    c[6].markdown(f"<span class='reg-sub'>{r['tipo'] or ''}</span>", unsafe_allow_html=True)
                    c[7].markdown(f"<span class='reg-sub'>{r['relatorio'] or ''}</span>", unsafe_allow_html=True)
                    if c[8].button("✏️", key=f"e{r['id']}"):
                        st.session_state['edit_id'] = r['id']
                        st.session_state['edit_r'] = dict(r)
                    if c[9].button("🗑", key=f"d{r['id']}"):
                        apagar_registo(r['id'])
                        st.rerun()

        if 'edit_id' in st.session_state:
            r = st.session_state['edit_r']
            st.divider()
            st.markdown(f"<p style='font-weight:700;color:{text}'>✏️ Editar registo</p>",
                        unsafe_allow_html=True)
            with st.form("edit_form"):
                ea, eb = st.columns(2)
                with ea:
                    ec = st.text_input("Cliente", value=r.get('cliente',''))
                    ep = st.text_input("Projeto", value=r.get('projeto',''))
                    en = st.text_input("Nº PAT", value=r.get('nopat',''))
                with eb:
                    et_idx = TIPOS.index(r.get('tipo','')) if r.get('tipo','') in TIPOS else 0
                    et = st.selectbox("Tipo", TIPOS, index=et_idx)
                    er_txt = st.text_input("Relatório", value=r.get('relatorio',''))
                    ek = st.text_input("Km", value=r.get('kms','0'))
                ed1, ed2, ed3 = st.columns(3)
                with ed1:
                    p = r['data'].split('/')
                    ed = st.date_input("Data", value=date(int(p[2]),int(p[1]),int(p[0])),
                                       format="DD/MM/YYYY")
                with ed2:
                    eh = st.text_input("Hora início", value=r.get('hora',''))
                with ed3:
                    ehf = st.text_input("Hora fim", value=r.get('horaf',''))
                edk = st.text_input("Deslocação", value=r.get('deslocacao','00:00'))
                fa, fb = st.columns(2)
                with fa:
                    if st.form_submit_button("💾 Atualizar", type="primary", use_container_width=True):
                        with get_conn() as conn:
                            with conn.cursor() as cur:
                                cur.execute("""UPDATE timer_registos SET
                                    nopat=%s,cliente=%s,projeto=%s,data=%s,hora=%s,
                                    horaf=%s,tipo=%s,relatorio=%s,kms=%s,deslocacao=%s
                                    WHERE id=%s""",
                                    (en,ec,ep,ed,eh,ehf,et,er_txt,ek,edk,st.session_state['edit_id']))
                                conn.commit()
                        del st.session_state['edit_id'], st.session_state['edit_r']
                        st.rerun()
                with fb:
                    if st.form_submit_button("✕ Cancelar", use_container_width=True):
                        del st.session_state['edit_id'], st.session_state['edit_r']
                        st.rerun()

# ═══════════════════════════════
# TAB 3 — MÉTRICAS
# ═══════════════════════════════
with tab3:
    mc1, mc2 = st.columns(2)
    with mc1:
        mi = st.date_input("De", value=date.today().replace(day=1),
                            format="DD/MM/YYYY", key="mi")
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
                st.markdown(f"<p style='font-weight:700;color:{text}'>Por Cliente</p>", unsafe_allow_html=True)
                pc = df.groupby('cliente')['minutos'].sum().reset_index().sort_values('minutos', ascending=False)
                pc['Horas'] = pc['minutos'].apply(lambda m: f"{int(m)//60:02d}h{int(m)%60:02d}m")
                pc['%'] = (pc['minutos']/pc['minutos'].sum()*100).round(1).astype(str)+'%'
                st.dataframe(pc[['cliente','Horas','%']].rename(columns={'cliente':'Cliente'}),
                             use_container_width=True, hide_index=True)
            with col_b:
                st.markdown(f"<p style='font-weight:700;color:{text}'>Por Tipo</p>", unsafe_allow_html=True)
                pt = df.groupby('tipo')['minutos'].sum().reset_index().sort_values('minutos', ascending=False)
                pt['Horas'] = pt['minutos'].apply(lambda m: f"{int(m)//60:02d}h{int(m)%60:02d}m")
                pt['%'] = (pt['minutos']/pt['minutos'].sum()*100).round(1).astype(str)+'%'
                st.dataframe(pt[['tipo','Horas','%']].rename(columns={'tipo':'Tipo'}),
                             use_container_width=True, hide_index=True)
