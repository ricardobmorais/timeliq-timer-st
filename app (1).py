import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime, date, timedelta
import io

st.set_page_config(page_title="Timeliq Timer", page_icon="⏱", layout="wide")

# ─────────────────────────────────────────
# LIGAÇÃO À BASE DE DADOS
# ─────────────────────────────────────────
def get_conn():
    conn_str = st.secrets["postgres"]["PG_CONN_STRING"]
    return psycopg2.connect(conn_str)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS timer_registos (
                    id SERIAL PRIMARY KEY,
                    nopat TEXT,
                    cliente TEXT,
                    projeto TEXT,
                    data DATE NOT NULL,
                    hora TIME NOT NULL,
                    horaf TIME NOT NULL,
                    tipo TEXT,
                    relatorio TEXT,
                    kms TEXT DEFAULT '0',
                    deslocacao TEXT DEFAULT '00:00',
                    criado_em TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()

# ─────────────────────────────────────────
# TIPOS DE TAREFA
# ─────────────────────────────────────────
TIPOS = [
    "", "Demonstração", "Documentação", "Formação", "Férias",
    "Gestão Projecto", "Gestão Serviço", "Gestão Transição",
    "Instalações Cilnet", "Instalações Cliente", "Mail", "RMA",
    "Reunião Cilnet", "Reunião Cliente", "Tarefa"
]

# ─────────────────────────────────────────
# FUNÇÕES DE DADOS
# ─────────────────────────────────────────
def listar_registos():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, nopat, cliente, projeto, 
                       TO_CHAR(data, 'DD/MM/YYYY') as data,
                       TO_CHAR(hora, 'HH24:MI') as hora,
                       TO_CHAR(horaf, 'HH24:MI') as horaf,
                       tipo, relatorio, kms, deslocacao
                FROM timer_registos
                ORDER BY data DESC, hora DESC
            """)
            return cur.fetchall()

def inserir_registo(nopat, cliente, projeto, data, hora, horaf, tipo, relatorio, kms, deslocacao):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO timer_registos 
                (nopat, cliente, projeto, data, hora, horaf, tipo, relatorio, kms, deslocacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (nopat, cliente, projeto, data, hora, horaf, tipo, relatorio, kms, deslocacao))
            conn.commit()

def apagar_registo(rid):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM timer_registos WHERE id = %s", (rid,))
            conn.commit()

def atualizar_registo(rid, nopat, cliente, projeto, data, hora, horaf, tipo, relatorio, kms, deslocacao):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE timer_registos SET
                nopat=%s, cliente=%s, projeto=%s, data=%s, hora=%s,
                horaf=%s, tipo=%s, relatorio=%s, kms=%s, deslocacao=%s
                WHERE id = %s
            """, (nopat, cliente, projeto, data, hora, horaf, tipo, relatorio, kms, deslocacao, rid))
            conn.commit()

def listar_clientes():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT cliente FROM timer_registos WHERE cliente IS NOT NULL AND cliente != '' ORDER BY cliente")
            return [r[0] for r in cur.fetchall()]

def listar_projetos(cliente=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            if cliente:
                cur.execute("SELECT DISTINCT projeto FROM timer_registos WHERE cliente=%s AND projeto IS NOT NULL AND projeto != '' ORDER BY projeto", (cliente,))
            else:
                cur.execute("SELECT DISTINCT projeto FROM timer_registos WHERE projeto IS NOT NULL AND projeto != '' ORDER BY projeto")
            return [r[0] for r in cur.fetchall()]

def listar_pats(cliente=None, projeto=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            if projeto:
                cur.execute("SELECT DISTINCT nopat FROM timer_registos WHERE projeto=%s AND nopat IS NOT NULL AND nopat != '' ORDER BY nopat", (projeto,))
            elif cliente:
                cur.execute("SELECT DISTINCT nopat FROM timer_registos WHERE cliente=%s AND nopat IS NOT NULL AND nopat != '' ORDER BY nopat", (cliente,))
            else:
                cur.execute("SELECT DISTINCT nopat FROM timer_registos WHERE nopat IS NOT NULL AND nopat != '' ORDER BY nopat")
            return [r[0] for r in cur.fetchall()]

def calcular_duracao(hora_str, horaf_str):
    try:
        h1 = datetime.strptime(hora_str, "%H:%M")
        h2 = datetime.strptime(horaf_str, "%H:%M")
        diff = int((h2 - h1).total_seconds() / 60)
        if diff > 0:
            return f"{diff // 60:02d}:{diff % 60:02d}"
    except:
        pass
    return "00:00"

# ─────────────────────────────────────────
# IMPORTAR CSV
# ─────────────────────────────────────────
def importar_csv(conteudo):
    linhas = conteudo.replace('\r\n', '\n').replace('\r', '\n').lstrip('\ufeff').split('\n')
    linhas = [l for l in linhas if l.strip()]
    if len(linhas) < 2:
        return 0, 0
    cabecalho = [h.strip() for h in linhas[0].split(';')]
    adicionados = 0
    ignorados = 0
    for linha in linhas[1:]:
        valores = [v.strip() for v in linha.split(';')]
        r = dict(zip(cabecalho, valores))
        if not r.get('data') or not r.get('hora'):
            continue
        try:
            # Converte data de DD/MM/YYYY para date
            partes = r['data'].split('/')
            data = date(int(partes[2]), int(partes[1]), int(partes[0]))
            hora = r.get('hora', '00:00')
            horaf = r.get('horaf', '00:00')
            # Verifica se já existe
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id FROM timer_registos 
                        WHERE nopat=%s AND data=%s AND hora=%s AND horaf=%s
                    """, (r.get('nopat',''), data, hora, horaf))
                    if cur.fetchone():
                        ignorados += 1
                        continue
            inserir_registo(
                r.get('nopat', ''), r.get('cliente', ''), r.get('projeto', ''),
                data, hora, horaf,
                r.get('tipo', ''), r.get('relatorio', ''),
                r.get('kms', '0'), r.get('deh', '00:00')
            )
            adicionados += 1
        except Exception as e:
            continue
    return adicionados, ignorados

# ─────────────────────────────────────────
# EXPORTAR CSV (Windows-1252 para PHC)
# ─────────────────────────────────────────
def exportar_csv(data_inicio, data_fim):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT nopat, TO_CHAR(data,'DD/MM/YYYY') as data,
                       TO_CHAR(hora,'HH24:MI') as hora,
                       TO_CHAR(horaf,'HH24:MI') as horaf,
                       deslocacao as deh, tipo, relatorio, kms
                FROM timer_registos
                WHERE data BETWEEN %s AND %s
                ORDER BY data, hora
            """, (data_inicio, data_fim))
            rows = cur.fetchall()
    if not rows:
        return None
    cabecalho = "nopat;data;hora;horaf;deh;tipo;relatorio;kms"
    linhas = [cabecalho]
    for r in rows:
        linhas.append(f"{r['nopat']};{r['data']};{r['hora']};{r['horaf']};{r['deh']};{r['tipo']};{r['relatorio']};{r['kms']}")
    conteudo = '\r\n'.join(linhas)
    return conteudo.encode('windows-1252', errors='replace')

# ─────────────────────────────────────────
# INICIALIZAÇÃO
# ─────────────────────────────────────────
init_db()

# ─────────────────────────────────────────
# INTERFACE
# ─────────────────────────────────────────
st.title("⏱ Timeliq Timer")
st.caption("Contabilizador de tempos de tarefa")

tab_registo, tab_lista, tab_metricas = st.tabs(["📝 Registar", "📋 Registos", "📊 Métricas"])

# ═══════════════════════════════════════════
# TAB 1 — REGISTAR
# ═══════════════════════════════════════════
with tab_registo:
    st.subheader("Novo registo")

    clientes = [""] + listar_clientes()
    col1, col2 = st.columns(2)
    with col1:
        cliente = st.selectbox("Cliente / Atividade Interna", clientes, key="reg_cliente")
        if st.text_input("Ou escreve novo cliente", key="reg_cliente_novo").strip():
            cliente = st.session_state.reg_cliente_novo.strip()

    projetos = [""] + listar_projetos(cliente if cliente else None)
    with col2:
        projeto = st.selectbox("Projeto", projetos, key="reg_projeto")
        if st.text_input("Ou escreve novo projeto", key="reg_projeto_novo").strip():
            projeto = st.session_state.reg_projeto_novo.strip()

    pats = [""] + listar_pats(cliente if cliente else None, projeto if projeto else None)
    col3, col4 = st.columns(2)
    with col3:
        nopat = st.selectbox("Nº PAT", pats, key="reg_pat")
        if st.text_input("Ou escreve novo PAT", key="reg_pat_novo").strip():
            nopat = st.session_state.reg_pat_novo.strip()
    with col4:
        tipo = st.selectbox("Tipo", TIPOS, key="reg_tipo")

    relatorio = st.text_input("Relatório", key="reg_relatorio")

    col5, col6, col7 = st.columns(3)
    with col5:
        data = st.date_input("Data", value=date.today(), format="DD/MM/YYYY", key="reg_data")
    with col6:
        hora = st.text_input("Hora início (HH:MM)", value="09:00", key="reg_hora")
    with col7:
        horaf = st.text_input("Hora fim (HH:MM)", value="10:00", key="reg_horaf")

    col8, col9 = st.columns(2)
    with col8:
        kms = st.text_input("Km / Deslocação", value="0", key="reg_kms")
    with col9:
        deslocacao = st.text_input("Tempo de Deslocação (HH:MM)", value="00:00", key="reg_deslocacao")

    # Mostra duração calculada
    duracao = calcular_duracao(hora, horaf)
    st.info(f"⏱ Duração: **{duracao}**")

    if st.button("💾 Gravar registo", type="primary", use_container_width=True):
        if not nopat:
            st.error("Indica o Nº PAT.")
        elif not hora or not horaf:
            st.error("Indica a hora de início e fim.")
        else:
            try:
                inserir_registo(nopat, cliente, projeto, data, hora, horaf, tipo, relatorio, kms, deslocacao)
                st.success("✅ Registo gravado!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao gravar: {e}")

    st.divider()

    # Importar CSV
    st.subheader("Importar CSV")
    ficheiro = st.file_uploader("Seleciona o ficheiro CSV", type=["csv"], key="importar_csv")
    if ficheiro and st.button("📥 Importar", key="btn_importar"):
        try:
            conteudo = ficheiro.read().decode('windows-1252', errors='replace')
            adicionados, ignorados = importar_csv(conteudo)
            st.success(f"✅ {adicionados} registo(s) importado(s). {ignorados} já existiam.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro na importação: {e}")

# ═══════════════════════════════════════════
# TAB 2 — LISTA DE REGISTOS
# ═══════════════════════════════════════════
with tab_lista:
    registos = listar_registos()

    # Exportar CSV
    with st.expander("📤 Exportar CSV para PHC"):
        col_ei, col_ef = st.columns(2)
        with col_ei:
            exp_inicio = st.date_input("De", value=date.today().replace(day=1), format="DD/MM/YYYY", key="exp_inicio")
        with col_ef:
            exp_fim = st.date_input("Até", value=date.today(), format="DD/MM/YYYY", key="exp_fim")
        if st.button("⬇️ Descarregar CSV", key="btn_export"):
            csv_bytes = exportar_csv(exp_inicio, exp_fim)
            if csv_bytes:
                nome = f"tempos_{exp_inicio.strftime('%Y-%m-%d')}_a_{exp_fim.strftime('%Y-%m-%d')}.csv"
                st.download_button("💾 Guardar ficheiro", data=csv_bytes, file_name=nome, mime="text/csv")
            else:
                st.warning("Sem registos nesse período.")

    if not registos:
        st.info("Ainda não há registos.")
    else:
        # Agrupar por mês
        meses = {}
        for r in registos:
            mes = r['data'][3:]  # MM/YYYY
            if mes not in meses:
                meses[mes] = []
            meses[mes].append(r)

        for mes, regs in meses.items():
            with st.expander(f"📅 {mes} ({len(regs)} registos)", expanded=(list(meses.keys())[0] == mes)):
                for r in regs:
                    duracao = calcular_duracao(r['hora'], r['horaf'])
                    col_d, col_i, col_f, col_dur, col_pat, col_cli, col_proj, col_tipo, col_rel, col_act = st.columns([1.2,0.8,0.8,0.8,0.9,1.2,1.2,1.3,2,0.4])
                    col_d.write(r['data'])
                    col_i.write(r['hora'])
                    col_f.write(r['horaf'])
                    col_dur.write(f"**{duracao}**")
                    col_pat.write(r['nopat'] or '')
                    col_cli.write(r['cliente'] or '')
                    col_proj.write(r['projeto'] or '')
                    col_tipo.write(r['tipo'] or '')
                    col_rel.write(r['relatorio'] or '')
                    with col_act:
                        if st.button("✏️", key=f"edit_{r['id']}", help="Editar"):
                            st.session_state['editar_id'] = r['id']
                            st.session_state['editar_dados'] = dict(r)
                        if st.button("🗑", key=f"del_{r['id']}", help="Apagar"):
                            apagar_registo(r['id'])
                            st.rerun()

        # Formulário de edição
        if 'editar_id' in st.session_state:
            r = st.session_state['editar_dados']
            st.divider()
            st.subheader("✏️ Editar registo")
            with st.form("form_editar"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_cliente = st.text_input("Cliente", value=r.get('cliente',''))
                    e_nopat = st.text_input("Nº PAT", value=r.get('nopat',''))
                    e_tipo = st.selectbox("Tipo", TIPOS, index=TIPOS.index(r.get('tipo','')) if r.get('tipo','') in TIPOS else 0)
                    e_kms = st.text_input("Km", value=r.get('kms','0'))
                with ec2:
                    e_projeto = st.text_input("Projeto", value=r.get('projeto',''))
                    e_relatorio = st.text_input("Relatório", value=r.get('relatorio',''))
                    e_deslocacao = st.text_input("Deslocação", value=r.get('deslocacao','00:00'))
                ec3, ec4, ec5 = st.columns(3)
                with ec3:
                    partes = r['data'].split('/')
                    e_data = st.date_input("Data", value=date(int(partes[2]), int(partes[1]), int(partes[0])), format="DD/MM/YYYY")
                with ec4:
                    e_hora = st.text_input("Hora início", value=r.get('hora',''))
                with ec5:
                    e_horaf = st.text_input("Hora fim", value=r.get('horaf',''))

                col_guardar, col_cancelar = st.columns(2)
                with col_guardar:
                    if st.form_submit_button("💾 Atualizar", type="primary", use_container_width=True):
                        atualizar_registo(st.session_state['editar_id'], e_nopat, e_cliente, e_projeto, e_data, e_hora, e_horaf, e_tipo, e_relatorio, e_kms, e_deslocacao)
                        del st.session_state['editar_id']
                        del st.session_state['editar_dados']
                        st.rerun()
                with col_cancelar:
                    if st.form_submit_button("✕ Cancelar", use_container_width=True):
                        del st.session_state['editar_id']
                        del st.session_state['editar_dados']
                        st.rerun()

# ═══════════════════════════════════════════
# TAB 3 — MÉTRICAS
# ═══════════════════════════════════════════
with tab_metricas:
    st.subheader("Métricas por período")
    mc1, mc2 = st.columns(2)
    with mc1:
        m_inicio = st.date_input("De", value=date.today().replace(day=1), format="DD/MM/YYYY", key="met_inicio")
    with mc2:
        m_fim = st.date_input("Até", value=date.today(), format="DD/MM/YYYY", key="met_fim")

    if st.button("📊 Ver métricas", type="primary"):
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT cliente, projeto, tipo,
                           SUM(EXTRACT(EPOCH FROM (horaf - hora))/60) as minutos
                    FROM timer_registos
                    WHERE data BETWEEN %s AND %s
                    GROUP BY cliente, projeto, tipo
                    ORDER BY minutos DESC
                """, (m_inicio, m_fim))
                dados = cur.fetchall()

        if not dados:
            st.warning("Sem registos nesse período.")
        else:
            df = pd.DataFrame(dados)
            df['horas'] = df['minutos'].apply(lambda m: f"{int(m)//60:02d}h{int(m)%60:02d}m")
            total = int(df['minutos'].sum())
            st.metric("Total", f"{total//60:02d}h{total%60:02d}m", f"{len(dados)} entradas")

            col_cli, col_tipo = st.columns(2)
            with col_cli:
                st.markdown("**Por Cliente**")
                por_cliente = df.groupby('cliente')['minutos'].sum().reset_index().sort_values('minutos', ascending=False)
                por_cliente['horas'] = por_cliente['minutos'].apply(lambda m: f"{int(m)//60:02d}h{int(m)%60:02d}m")
                por_cliente['%'] = (por_cliente['minutos'] / por_cliente['minutos'].sum() * 100).round(1).astype(str) + '%'
                st.dataframe(por_cliente[['cliente','horas','%']], use_container_width=True, hide_index=True)

            with col_tipo:
                st.markdown("**Por Tipo**")
                por_tipo = df.groupby('tipo')['minutos'].sum().reset_index().sort_values('minutos', ascending=False)
                por_tipo['horas'] = por_tipo['minutos'].apply(lambda m: f"{int(m)//60:02d}h{int(m)%60:02d}m")
                por_tipo['%'] = (por_tipo['minutos'] / por_tipo['minutos'].sum() * 100).round(1).astype(str) + '%'
                st.dataframe(por_tipo[['tipo','horas','%']], use_container_width=True, hide_index=True)
