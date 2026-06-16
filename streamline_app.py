import streamlit as st
import time
import pandas as pd
import json
import streamlit.components.v1 as components

# --- 1. CONFIGURAZIONE ISTANZE KNAPSACK ---
TRIAL_INSTANCE = {
    "name": "Istanza di Prova",
    "capacity": 100,
    "optimal_value": 150,
    "v": [40, 60, 50, 90],
    "w": [30, 50, 40, 50]
}

INSTANCES = [
    {
        "name": "Istanza 1",
        "capacity": 1500,
        "optimal_value": 328,
        "v": [37, 72, 106, 32, 45, 71, 23, 44, 85, 62],
        "w": [50, 820, 700, 46, 220, 530, 107, 180, 435, 360]
    },
    {
        "name": "Istanza 2",
        "capacity": 1900,
        "optimal_value": 1615,
        "v": [500, 350, 505, 505, 640, 435, 465, 50, 220, 170],
        "w": [750, 406, 564, 595, 803, 489, 641, 177, 330, 252]
    },
    {
        "name": "Istanza 3",
        "capacity": 1300,
        "optimal_value": 1371,
        "v": [201, 84, 113, 303, 227, 251, 129, 147, 86, 127, 144, 167],
        "w": [192, 80, 106, 288, 212, 240, 121, 140, 82, 120, 137, 160]
    }
]

# --- 2. INIZIALIZZAZIONE SESSION STATE ---
if 'app_start_time' not in st.session_state:
    st.session_state.app_start_time = time.time()
if 'phase' not in st.session_state:
    st.session_state.phase = 'welcome'
if 'participant_id' not in st.session_state:
    st.session_state.participant_id = ""

# Stati per Knapsack Trial
if 'trial_selections' not in st.session_state:
    st.session_state.trial_selections = set()
if 'trial_error_msg' not in st.session_state:
    st.session_state.trial_error_msg = None
if 'trial_error_time' not in st.session_state:
    st.session_state.trial_error_time = 0

# Stati per Knapsack Reale
if 'current_instance' not in st.session_state:
    st.session_state.current_instance = 0
if 'start_time' not in st.session_state:
    st.session_state.start_time = 0
if 'metrics' not in st.session_state:
    st.session_state.metrics = []
if 'current_selections' not in st.session_state:
    st.session_state.current_selections = set()
if 'iterazioni' not in st.session_state:
    st.session_state.iterazioni = 0
if 'error_msg' not in st.session_state:
    st.session_state.error_msg = None
if 'error_time' not in st.session_state:
    st.session_state.error_time = 0

# Start time NASA Task
if 'nasa_start_time' not in st.session_state:
    st.session_state.nasa_start_time = 0

# --- 3. FUNZIONI DI SUPPORTO KNAPSACK ---

def toggle_trial_item(idx):
    if idx in st.session_state.trial_selections:
        st.session_state.trial_selections.remove(idx)
        st.session_state.trial_error_msg = None 
    else:
        tot_w = sum(TRIAL_INSTANCE['w'][i] for i in st.session_state.trial_selections)
        if tot_w + TRIAL_INSTANCE['w'][idx] <= TRIAL_INSTANCE['capacity']:
            st.session_state.trial_selections.add(idx)
            st.session_state.trial_error_msg = None 
        else:
            st.session_state.trial_error_msg = "L'aggiunta di questo item viola il vincolo di peso consentito."
            st.session_state.trial_error_time = time.time()

def get_current_totals():
    inst = INSTANCES[st.session_state.current_instance]
    tot_v = sum(inst['v'][i] for i in st.session_state.current_selections)
    tot_w = sum(inst['w'][i] for i in st.session_state.current_selections)
    return tot_v, tot_w

def toggle_item(idx):
    if idx in st.session_state.current_selections:
        st.session_state.current_selections.remove(idx)
        st.session_state.error_msg = None 
        st.session_state.iterazioni += 1 
    else:
        inst = INSTANCES[st.session_state.current_instance]
        _, tot_w = get_current_totals()
        if tot_w + inst['w'][idx] <= inst['capacity']:
            st.session_state.current_selections.add(idx)
            st.session_state.error_msg = None 
            st.session_state.iterazioni += 1 
        else:
            st.session_state.error_msg = "L'aggiunta di questo item viola il vincolo di peso consentito."
            st.session_state.error_time = time.time()

def finish_kp_instance():
    end_time = time.time()
    time_spent = end_time - st.session_state.start_time
    tot_v, tot_w = get_current_totals()
    inst = INSTANCES[st.session_state.current_instance]
    economic_performance = tot_v / inst["optimal_value"]
    
    start_rel = st.session_state.start_time - st.session_state.app_start_time
    end_rel = end_time - st.session_state.app_start_time
    
    st.session_state.metrics.append({
        "Istanza": inst["name"],
        "Valore_Ottenuto": tot_v,
        "Valore_Ottimale": inst["optimal_value"],
        "Economic_Performance": round(economic_performance, 4),
        "Tempo_Speso_sec": round(time_spent, 2),
        "Iterazioni_Effort": st.session_state.iterazioni,
        "Start_s": round(start_rel, 2),
        "End_s": round(end_rel, 2)
    })
    
    st.session_state.error_msg = None
    st.session_state.phase = 'kp_interstitial'

def next_kp_instance():
    st.session_state.current_instance += 1
    st.session_state.current_selections = set()
    st.session_state.iterazioni = 0
    st.session_state.error_msg = None
    
    if st.session_state.current_instance < len(INSTANCES):
        st.session_state.phase = 'kp_task'
        st.session_state.start_time = time.time()
    else:
        st.session_state.phase = 'nasa_task'
        st.session_state.nasa_start_time = time.time()

def start_real_experiment():
    st.session_state.phase = 'kp_task'
    st.session_state.current_instance = 0
    st.session_state.start_time = time.time()

# --- FUNZIONI DI SUPPORTO UI ---
def _render_single_item(i, v_list, w_list, selections, max_w, max_v, key_prefix, on_click_func):
    val = v_list[i]
    peso = w_list[i]
    is_selected = i in selections
    
    size_px = int((peso / max_w) * 100) + 60
    blue_intensity = int((val / max_v) * 255)
    
    if is_selected:
        bg_color = "#4CAF50" 
        text_color = "white"
    else:
        bg_color = f"rgb({255 - blue_intensity}, {255 - blue_intensity}, 255)"
        text_color = "black" if blue_intensity < 100 else "white"

    square_html = f"""
    <div style="
        width: {size_px}px; height: {size_px}px; 
        background-color: {bg_color}; 
        border: 2px solid {'#000' if is_selected else '#333'};
        border-radius: 5px; display: flex; flex-direction: column;
        align-items: center; justify-content: center; 
        margin: 0 auto 10px auto; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
        <span style="color: {text_color}; font-family: Arial; font-weight: bold; font-size: 14px;">V: {val}</span>
        <span style="color: {text_color}; font-family: Arial; font-size: 12px;">W: {peso}</span>
    </div>
    """
    st.markdown(square_html, unsafe_allow_html=True)
    
    btn_label = "Rimuovi" if is_selected else "Aggiungi"
    st.button(btn_label, key=f"{key_prefix}_{i}", 
              on_click=on_click_func, args=(i,), use_container_width=True)

def render_items_two_rows(v_list, w_list, selections, max_w, max_v, key_prefix, on_click_func):
    n = len(v_list)
    mid = (n + 1) // 2
    
    cols1 = st.columns(mid)
    for i in range(mid):
        with cols1[i]:
            _render_single_item(i, v_list, w_list, selections, max_w, max_v, key_prefix, on_click_func)
            
    st.write("") 
    
    cols2 = st.columns(n - mid)
    for i in range(mid, n):
        with cols2[i - mid]:
            _render_single_item(i, v_list, w_list, selections, max_w, max_v, key_prefix, on_click_func)

def render_copy_button(text_to_copy, button_label="📋 Copia"):
    safe_text = json.dumps(text_to_copy)
    html_code = f"""
    <script>
    function copyText() {{
        const text = {safe_text};
        navigator.clipboard.writeText(text).then(function() {{
            const btn = document.getElementById('btn');
            btn.innerText = '✅ Copiato!';
            btn.style.backgroundColor = '#4CAF50';
            btn.style.color = 'white';
            setTimeout(() => {{
                btn.innerText = '{button_label}';
                btn.style.backgroundColor = '#f0f2f6';
                btn.style.color = '#31333F';
            }}, 2000);
        }}).catch(function(err) {{
            const el = document.createElement('textarea');
            el.value = text;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
            
            const btn = document.getElementById('btn');
            btn.innerText = '✅ Copiato!';
            btn.style.backgroundColor = '#4CAF50';
            btn.style.color = 'white';
            setTimeout(() => {{
                btn.innerText = '{button_label}';
                btn.style.backgroundColor = '#f0f2f6';
                btn.style.color = '#31333F';
            }}, 2000);
        }});
    }}
    </script>
    <button id="btn" onclick="copyText()" style="
        width: 100%; 
        padding: 10px; 
        border-radius: 8px; 
        border: 1px solid #c4c4c4; 
        background: #f0f2f6; 
        cursor: pointer; 
        font-weight: bold; 
        color: #31333F; 
        font-family: sans-serif;
        transition: 0.2s;">
        {button_label}
    </button>
    """
    components.html(html_code, height=60)


# --- 4. INTERFACCIA UTENTE PRINCIPALE ---
st.set_page_config(page_title="Esperimento Decision-Making", layout="wide")

# ==========================================
# FASE 0: WELCOME & ID INPUT
# ==========================================
if st.session_state.phase == 'welcome':
    st.title("Benvenuto/a all'Esperimento")
    st.markdown("""
    Grazie per la tua partecipazione. Questo esperimento prevede diverse tipologie di task decisionali e questionari di autovalutazione:
    1. **Task di Ottimizzazione** (3 istanze a tempo limitato).
    2. **Task di Sopravvivenza e Prioritizzazione** (singolo scenario).
    3. **Valutazioni Soggettive** (questionari finali di percezione).
    
    **Istruzioni importanti per la raccolta dati:**
    Durante l'esecuzione di entrambi i task rileveremo i tuoi dati fisiologici. Per garantire un'acquisizione pulita ed evitare artefatti sui segnali, ti preghiamo di:
    * Mantenere una postura comoda ma **statica**.
    * Limitare al minimo i movimenti del corpo, in particolare della testa.
    * Mantenere il braccio non dominante fermo e rilassato sul tavolo.
    """)
    
    st.divider()
    
    user_id = st.text_input("Inserisci il tuo ID Partecipante (fornito dal ricercatore):", key="id_input")
    
    if st.button("Procedi", type="primary"):
        if user_id.strip() == "":
            st.error("È necessario inserire un ID valido per procedere.")
        else:
            st.session_state.participant_id = user_id.strip()
            st.session_state.phase = 'kp_instructions'
            st.rerun()

# ==========================================
# FASE 1: ISTRUZIONI E PROVA KNAPSACK
# ==========================================
elif st.session_state.phase == 'kp_instructions':
    st.title("Fase 1: Ottimizzazione del Valore")
    st.markdown("""
    Il tuo obiettivo è massimizzare il valore economico totale degli oggetti selezionati, assicurandoti che il loro peso combinato non superi la capacità massima consentita dello zaino.
    
    Affronterai **3 istanze sperimentali**, per ciascuna avrai a disposizione un massimo di **4 minuti**.
    
    ---
    ### 🛠️ Fai una prova (Senza limiti di tempo)
    Qui sotto trovi un'istanza semplificata per capire il meccanismo. Prova ad aggiungere e rimuovere gli elementi. Questa prova non salva alcun dato e non fa partire il timer.
    
    **Nota bene:** Durante questa fase di prova (così come nell'esperimento reale) è possibile copiare i valori e lo stato dello zaino in qualsiasi momento, utilizzando l'apposito riquadro dedicato in basso.
    """)
    
    # Render dell'istanza di prova
    tot_v_trial = sum(TRIAL_INSTANCE['v'][i] for i in st.session_state.trial_selections)
    tot_w_trial = sum(TRIAL_INSTANCE['w'][i] for i in st.session_state.trial_selections)
    
    st.markdown(f"**Valore Attuale: {tot_v_trial}** | **Peso: {tot_w_trial}/{TRIAL_INSTANCE['capacity']}**")
    
    max_w_t = max(TRIAL_INSTANCE['w'])
    max_v_t = max(TRIAL_INSTANCE['v'])
    
    render_items_two_rows(TRIAL_INSTANCE['v'], TRIAL_INSTANCE['w'], st.session_state.trial_selections, 
                          max_w_t, max_v_t, "btn_trial", toggle_trial_item)

    if st.session_state.trial_error_msg:
        if time.time() - st.session_state.trial_error_time < 3:
            st.error(st.session_state.trial_error_msg)
        else:
            st.session_state.trial_error_msg = None

    st.divider()

    # --- BOTTONE COPIA STATO PROVA ---
    copy_text_trial = f"Task: Ottimizzazione Valore (Prova)\n"
    copy_text_trial += f"Capacità Massima: {TRIAL_INSTANCE['capacity']}\n"
    copy_text_trial += f"Valore Attuale Raggiunto: {tot_v_trial} | Peso Attuale: {tot_w_trial}\n\n"
    copy_text_trial += "Elenco di TUTTI gli elementi disponibili in questa prova:\n"
    for j in range(len(TRIAL_INSTANCE['v'])):
        status = "[INSERITO]" if j in st.session_state.trial_selections else "[ NON inserito ]"
        copy_text_trial += f"- Item {j+1}: Valore = {TRIAL_INSTANCE['v'][j]}, Peso = {TRIAL_INSTANCE['w'][j]} -> Stato: {status}\n"
    
    render_copy_button(copy_text_trial, "📋 Copia stato della prova (per AI/Appunti)")
    # -----------------------------------------------

    st.markdown("Quando ti senti pronto/a e in una posizione rilassata, avvia l'esperimento reale (partirà il timer della prima istanza).")
    st.button("Avvia Esperimento (Timer 4 minuti)", type="primary", on_click=start_real_experiment, use_container_width=True)

# ==========================================
# FASE 2: ESECUZIONE KNAPSACK REALE
# ==========================================
elif st.session_state.phase == 'kp_task':
    inst = INSTANCES[st.session_state.current_instance]
    tot_v, tot_w = get_current_totals()
    
    elapsed_time = time.time() - st.session_state.start_time
    time_remaining = max(240 - int(elapsed_time), 0)
    
    if time_remaining <= 0:
        st.warning("Tempo scaduto per questa istanza!")
        finish_kp_instance()
        st.rerun()

    col_title, col_timer = st.columns([3, 1])
    with col_title:
        st.title(f"{inst['name']}")
    with col_timer:
        st.metric("Tempo Rimanente", f"{time_remaining} s")
        st.progress(time_remaining / 240.0)

    # --- INIEZIONE JS PER MODAL KNAPSACK NELLA FINESTRA GENITORE ---
    modal_js = f"""
    <script>
    const parentDoc = window.parent.document;
    const flagId = 'kp-alert-shown-{st.session_state.current_instance}';
    const intervalId = 'kp-interval-{st.session_state.current_instance}';

    if (!parentDoc.getElementById(intervalId)) {{
        const marker = parentDoc.createElement('div');
        marker.id = intervalId;
        marker.style.display = 'none';
        parentDoc.body.appendChild(marker);

        const startTime = {st.session_state.start_time};
        const timer = setInterval(() => {{
            const now = new Date().getTime() / 1000;
            const remaining = Math.floor(240 - (now - startTime));
            
            if (remaining <= 60 && remaining > 0 && !parentDoc.getElementById(flagId)) {{
                
                const flag = parentDoc.createElement('div');
                flag.id = flagId;
                flag.style.display = 'none';
                parentDoc.body.appendChild(flag);

                const overlay = parentDoc.createElement('div');
                overlay.id = 'modal-overlay-{st.session_state.current_instance}';
                overlay.style.cssText = "position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.7); z-index:9999999; display:flex; align-items:center; justify-content:center; font-family: sans-serif;";
                
                const modal = parentDoc.createElement('div');
                modal.style.cssText = "background:white; padding:40px; border-radius:12px; text-align:center; box-shadow:0 10px 30px rgba(0,0,0,0.5); max-width: 450px; position: relative; border-top: 6px solid #ff4b4b;";
                
                modal.innerHTML = `
                    <span onclick="this.parentElement.parentElement.remove()" style="position:absolute; top:10px; right:20px; font-size:30px; cursor:pointer; font-weight:bold; color:#888;">&times;</span>
                    <h2 style="color:#cc0000; margin-top:0; font-size: 28px;">⚠️ Attenzione!</h2>
                    <p style="font-size:18px; color:#333; line-height: 1.6;">Manca 1 minuto o meno alla scadenza.<br><br>Ti suggeriamo di inviare la tua soluzione al più presto.</p>
                    <button onclick="this.parentElement.parentElement.remove()" style="margin-top:20px; padding:12px 25px; background:#ff4b4b; color:white; border:none; border-radius:8px; cursor:pointer; font-size:18px; font-weight:bold;">Chiudi e Continua</button>
                `;
                
                overlay.appendChild(modal);
                parentDoc.body.appendChild(overlay);
                
                clearInterval(timer);
            }}
        }}, 1000);
    }}
    </script>
    """
    components.html(modal_js, height=0, width=0)
    # ----------------------------------------------------------------

    st.markdown(f"### Valore: **{tot_v}** | Peso: **{tot_w}/{inst['capacity']}**")
    st.divider()

    max_w = max(inst['w'])
    max_v = max(inst['v'])
    
    render_items_two_rows(inst['v'], inst['w'], st.session_state.current_selections, 
                          max_w, max_v, f"btn_{st.session_state.current_instance}", toggle_item)

    if st.session_state.error_msg:
        if time.time() - st.session_state.error_time < 3:
            st.error(st.session_state.error_msg)
        else:
            st.session_state.error_msg = None

    st.divider()

    # --- BOTTONE COPIA STATO REALE ---
    copy_text = f"Task: Ottimizzazione Valore ({inst['name']})\n"
    copy_text += f"Capacità Massima: {inst['capacity']}\n"
    copy_text += f"Valore Attuale Raggiunto: {tot_v} | Peso Attuale: {tot_w}\n\n"
    copy_text += "Elenco di TUTTI gli elementi disponibili in questa istanza:\n"
    for j in range(len(inst['v'])):
        status = "[INSERITO]" if j in st.session_state.current_selections else "[ NON inserito ]"
        copy_text += f"- Item {j+1}: Valore = {inst['v'][j]}, Peso = {inst['w'][j]} -> Stato: {status}\n"
    
    render_copy_button(copy_text, "📋 Copia stato attuale dello zaino (per AI/Appunti)")
    # -----------------------------------------------

    st.button("Invia Soluzione", on_click=finish_kp_instance, type="primary")
    time.sleep(1)
    st.rerun()

# ==========================================
# FASE 3: KNAPSACK INTERSTITIAL
# ==========================================
elif st.session_state.phase == 'kp_interstitial':
    st.title("Istanza Completata")
    st.info("Dati della prova registrati con successo.")
    
    if (st.session_state.current_instance + 1) < len(INSTANCES):
        st.markdown(f"Procedi con la **{INSTANCES[st.session_state.current_instance + 1]['name']}**.")
        st.button("Inizia Prossima Istanza", on_click=next_kp_instance, type="primary")
    else:
        st.markdown("Hai completato la prima fase dell'esperimento. Clicca per procedere al task finale.")
        st.button("Procedi al Task NASA", on_click=next_kp_instance, type="primary")

# ==========================================
# FASE 4: ESECUZIONE NASA, STAI, TLX & RISULTATI
# ==========================================
elif st.session_state.phase == 'nasa_task':
    
    clean_metrics = []
    for m in st.session_state.metrics:
        clean_metrics.append({
            "Istanza": m["Istanza"],
            "Economic_Performance": float(m["Economic_Performance"]),
            "Tempo_Speso_sec": float(m["Tempo_Speso_sec"]),
            "Iterazioni_Effort": int(m["Iterazioni_Effort"]),
            "Start_s": float(m["Start_s"]),
            "End_s": float(m["End_s"])
        })
    metrics_list_json = json.dumps(clean_metrics)

    csv_headers = ["ID"]
    csv_values = [st.session_state.participant_id]
    for i, m in enumerate(clean_metrics):
        csv_headers.extend([f"KP_Ist{i+1}_Perf", f"KP_Ist{i+1}_Time_s", f"KP_Ist{i+1}_Iter", f"KP_Ist{i+1}_Start_s", f"KP_Ist{i+1}_End_s"])
        csv_values.extend([m['Economic_Performance'], m['Tempo_Speso_sec'], m['Iterazioni_Effort'], m['Start_s'], m['End_s']])
    
    df_metrics = pd.DataFrame(clean_metrics)
    kp_mean_perf = float(df_metrics['Economic_Performance'].mean()) if not df_metrics.empty else 0.0
    kp_tot_time = float(df_metrics['Tempo_Speso_sec'].sum()) if not df_metrics.empty else 0.0
    kp_tot_iter = int(df_metrics['Iterazioni_Effort'].sum()) if not df_metrics.empty else 0
    
    csv_headers.extend(["KP_Mean_Perf", "KP_Total_Time_s", "KP_Total_Iter"])
    csv_values.extend([kp_mean_perf, kp_tot_time, kp_tot_iter])
    
    headers_json = json.dumps(csv_headers)
    values_json = json.dumps(csv_values)
    
    nasa_start_rel = round(st.session_state.nasa_start_time - st.session_state.app_start_time, 2)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.0/Sortable.min.js"></script>
        <style>
            body {{ font-family: sans-serif; padding: 10px; color: #31333F; margin: 0; }}
            .task-header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef; margin-bottom: 20px; line-height: 1.6; }}
            .highlight-action {{ background-color: #ffeb3b; padding: 2px 6px; font-weight: bold; border-radius: 4px; }}
            .timer-box {{ background-color: #ffe6e6; color: #cc0000; padding: 12px; border-radius: 8px; text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 20px; }}
            
            /* Modal / Overlays */
            #timer-modal-overlay {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10000; align-items: center; justify-content: center; }}
            .timer-modal-content {{ background: white; padding: 40px; border-radius: 12px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5); max-width: 450px; position: relative; border-top: 6px solid #ff4b4b; }}
            .close-btn {{ position: absolute; top: 10px; right: 20px; font-size: 30px; cursor: pointer; color: #888; font-weight: bold; }}
            .close-btn:hover {{ color: #333; }}
            .modal-btn {{ margin-top: 20px; padding: 12px 25px; background: #ff4b4b; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 18px; font-weight: bold; }}

            /* NASA UI */
            #ranking-list {{ list-style-type: none; padding: 0; margin: 0; }}
            .sortable-item {{ background-color: #f0f2f6; padding: 12px 15px; margin-bottom: 8px; border-radius: 8px; cursor: grab; border: 1px solid #e0e0e0; display: flex; align-items: center; }}
            .badge {{ background-color: #0066cc; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; margin-right: 15px; font-weight: bold; font-size: 14px;}}
            .btn-submit {{ background-color: #ff4b4b; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 20px; font-weight: bold; }}
            .btn-copy-nasa {{ background-color: #e0e2e6; color: #31333F; border: 1px solid #c4c4c4; padding: 12px 24px; font-size: 14px; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 0px; margin-bottom: 20px; font-weight: bold; transition: 0.2s;}}
            .btn-copy-nasa:hover {{ background-color: #d0d2d6; }}
            .btn-download {{ background-color: #4CAF50; color: white; border: none; padding: 15px 30px; font-size: 18px; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 20px; font-weight: bold; text-align: center; display: block; text-decoration: none;}}
            .results-box {{ background-color: #f9f9f9; padding: 30px; border-radius: 8px; border: 1px solid #ddd; }}
            .kp-instance-card {{ background: #fff; padding: 10px 15px; border-left: 4px solid #0066cc; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}

            /* STAI e TLX UI */
            .quest-container {{ background: #fff; padding: 30px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 20px; }}
            .stai-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .stai-table th, .stai-table td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: center; }}
            .stai-table td:first-child {{ text-align: left; font-size: 16px; width: 40%; }}
            .stai-table tr:hover {{ background-color: #f9f9f9; }}
            
            /* Ingrandimento dei pallini STAI */
            .stai-table input[type="radio"] {{ transform: scale(2); cursor: pointer; }}
            
            .tlx-item {{ margin-bottom: 45px; }}
            .tlx-title {{ font-size: 20px; font-weight: bold; margin-bottom: 5px; color: #222; text-transform: uppercase; letter-spacing: 1px; }}
            .tlx-desc {{ font-size: 14px; color: #555; margin-bottom: 15px; font-weight: 500;}}
            .tlx-scale-container {{ display: flex; align-items: flex-end; justify-content: space-between; position: relative; }}
            .tlx-label {{ font-weight: bold; font-size: 16px; text-transform: uppercase; margin-top: 20px; }}
            
            /* Righello Custom fedele all'immagine */
            .ruler-wrapper {{
                flex-grow: 1;
                margin: 0 20px;
                position: relative;
                height: 40px;
            }}
            input[type=range].ruler {{
                -webkit-appearance: none; width: 100%; background: transparent; position: absolute; top: 0; left: 0; height: 100%; margin: 0;
                opacity: 0.3; /* Sbiadito all'inizio */
                transition: opacity 0.3s;
            }}
            input[type=range].ruler:focus {{ outline: none; }}
            
            /* Linea base e tacche verticali */
            input[type=range].ruler::-webkit-slider-runnable-track {{
                width: 100%; height: 40px; cursor: pointer;
                background:
                    linear-gradient(90deg, #000 2px, transparent 2px) 0 100% / 5% 50%, /* Tacche verticali */
                    linear-gradient(0deg, #000 2px, transparent 2px) 0 10px / 100% 2px; /* Linea orizzontale di base */
                background-repeat: repeat-x, no-repeat;
            }}
            
            /* Cursore invisibile/minimale che segna il punto scelto */
            input[type=range].ruler::-webkit-slider-thumb {{
                -webkit-appearance: none; height: 40px; width: 6px; background: #ff4b4b; cursor: pointer; border-radius: 2px;
                box-shadow: 0px 0px 5px rgba(255, 75, 75, 0.8);
            }}
            
            /* Stato attivo post-interazione */
            input[type=range].ruler.touched {{ opacity: 1; }}

        </style>
    </head>
    <body>

        <div id="nasa-task-container">
            <div class="task-header">
                <h1 style="margin-top: 0;">🚀 NASA Survival Task</h1>
                <p>Sei un membro di un equipaggio spaziale originariamente programmato per incontrarsi con una nave madre sulla superficie illuminata della luna. A causa di problemi meccanici, tuttavia, la tua nave è stata costretta ad atterrare in un punto a circa 320 km dal punto di incontro. Durante l'atterraggio di fortuna, gran parte dell'equipaggiamento a bordo è andato distrutto e, poiché la sopravvivenza dipende dal raggiungimento della nave madre, devono essere scelti gli articoli più critici a disposizione per affrontare il viaggio di 320 km.</p>
                <p>Di seguito sono elencati i 15 oggetti rimasti intatti e non danneggiati dopo l'atterraggio. Il tuo compito è ordinarli in base alla loro importanza nel permettere al tuo equipaggio di raggiungere il punto di incontro.</p>
                <p style="font-size: 16px; border-left: 4px solid #ff4b4b; padding-left: 10px;">
                    <span class="highlight-action">Usa il mouse per trascinare e riordinare gli elementi nell'elenco.</span> Posiziona in alto (numero 1) l'oggetto più importante, al numero 2 il secondo più importante, e così via, fino al numero 15 per quello meno importante.
                </p>
            </div>
            <button id="copy-nasa-btn" class="btn-copy-nasa" onclick="copyNasaState()">📋 COPIA ISTRUZIONI E RANKING ATTUALE</button>
            <div id="timer" class="timer-box">Tempo Rimanente: 15:00</div>

            <div id="timer-modal-overlay">
                <div class="timer-modal-content">
                    <span class="close-btn" onclick="document.getElementById('timer-modal-overlay').style.display='none'">&times;</span>
                    <h2 style="color: #cc0000; margin-top: 0; font-size: 28px;">⚠️ Attenzione!</h2>
                    <p style="font-size: 18px; color: #333; line-height: 1.6;">Manca 1 minuto o meno alla scadenza!<br><br>Ti suggeriamo di inviare la tua soluzione al più presto.</p>
                    <button class="modal-btn" onclick="document.getElementById('timer-modal-overlay').style.display='none'">Chiudi e Continua</button>
                </div>
            </div>

            <ul id="ranking-list">
                <li class="sortable-item" data-name="Scatola di fiammiferi"><div class="badge"></div><span class="item-text">Scatola di fiammiferi</span></li>
                <li class="sortable-item" data-name="Cibo concentrato"><div class="badge"></div><span class="item-text">Cibo concentrato</span></li>
                <li class="sortable-item" data-name="15 metri di corda di nylon"><div class="badge"></div><span class="item-text">15 metri di corda di nylon</span></li>
                <li class="sortable-item" data-name="Seta di paracadute"><div class="badge"></div><span class="item-text">Seta di paracadute</span></li>
                <li class="sortable-item" data-name="Unità di riscaldamento portatile"><div class="badge"></div><span class="item-text">Unità di riscaldamento portatile</span></li>
                <li class="sortable-item" data-name="Due pistole calibro .45"><div class="badge"></div><span class="item-text">Due pistole calibro .45</span></li>
                <li class="sortable-item" data-name="Una cassa di latte disidratato"><div class="badge"></div><span class="item-text">Una cassa di latte disidratato</span></li>
                <li class="sortable-item" data-name="Due serbatoi di ossigeno da 45 kg"><div class="badge"></div><span class="item-text">Due serbatoi di ossigeno da 45 kg</span></li>
                <li class="sortable-item" data-name="Mappa stellare"><div class="badge"></div><span class="item-text">Mappa stellare</span></li>
                <li class="sortable-item" data-name="Zattera di salvataggio autogonfiabile"><div class="badge"></div><span class="item-text">Zattera di salvataggio autogonfiabile</span></li>
                <li class="sortable-item" data-name="Bussola magnetica"><div class="badge"></div><span class="item-text">Bussola magnetica</span></li>
                <li class="sortable-item" data-name="20 litri d'acqua"><div class="badge"></div><span class="item-text">20 litri d'acqua</span></li>
                <li class="sortable-item" data-name="Razzi di segnalazione luminosa"><div class="badge"></div><span class="item-text">Razzi di segnalazione luminosa</span></li>
                <li class="sortable-item" data-name="Kit di pronto soccorso con aghi da iniezione"><div class="badge"></div><span class="item-text">Kit di pronto soccorso con aghi da iniezione</span></li>
                <li class="sortable-item" data-name="Ricetrasmettitore FM a energia solare"><div class="badge"></div><span class="item-text">Ricetrasmettitore FM a energia solare</span></li>
            </ul>
            <button class="btn-submit" onclick="finishNasaTask()">PROCEDI AI QUESTIONARI</button>
        </div>

        <div id="stai-container" class="quest-container" style="display:none;">
            <h1 style="color:#0066cc; margin-top:0;">Questionario di Autovalutazione</h1>
            <p><strong>Istruzioni:</strong> Leggi ogni affermazione e scegli la risposta appropriata per indicare come ti senti in questo momento, cioè <em>proprio adesso</em>. Non ci sono risposte giuste o sbagliate. Non dedicare troppo tempo a nessuna singola affermazione, ma dai la risposta che sembra descrivere meglio i tuoi sentimenti attuali.</p>
            <table class="stai-table">
                <thead>
                    <tr>
                        <th>Affermazione</th>
                        <th>1 = Per nulla</th>
                        <th>2 = Un po'</th>
                        <th>3 = Abbastanza</th>
                        <th>4 = Moltissimo</th>
                    </tr>
                </thead>
                <tbody id="stai-body">
                    </tbody>
            </table>
            <button class="btn-submit" onclick="submitStai()" style="background-color: #0066cc;">AVANTI</button>
        </div>

        <div id="tlx-container" class="quest-container" style="display:none;">
            <h1 style="color:#0066cc; margin-top:0;">RATING SHEET</h1>
            <p style="margin-bottom: 40px; font-size: 16px;">Valuta il compito appena concluso selezionando il punto appropriato sulle scale qui sotto (ogni tacca vale 5 punti). <strong>È obbligatorio indicare un valore per ognuna delle scale.</strong></p>
            
            <div class="tlx-item">
                <div class="tlx-title">MENTAL DEMAND</div>
                <div class="tlx-desc">Quanta attività mentale e percettiva è stata richiesta (es. pensare, decidere, calcolare, ricordare, guardare, cercare, ecc.)? Il compito è stato facile o impegnativo, semplice o complesso, severo o indulgente?</div>
                <div class="tlx-scale-container">
                    <span class="tlx-label">Low</span>
                    <div class="ruler-wrapper"><input type="range" class="ruler" id="tlx_0" min="0" max="100" step="5" value="50" oninput="markTlx(0)"></div>
                    <span class="tlx-label">High</span>
                </div>
            </div>
            
            <div class="tlx-item">
                <div class="tlx-title">TEMPORAL DEMAND</div>
                <div class="tlx-desc">Quanta pressione temporale hai avvertito a causa del ritmo o della frequenza con cui si sono presentati i compiti o gli elementi del compito? Il ritmo è stato lento e tranquillo oppure rapido e frenetico?</div>
                <div class="tlx-scale-container">
                    <span class="tlx-label">Low</span>
                    <div class="ruler-wrapper"><input type="range" class="ruler" id="tlx_1" min="0" max="100" step="5" value="50" oninput="markTlx(1)"></div>
                    <span class="tlx-label">High</span>
                </div>
            </div>
            
            <div class="tlx-item">
                <div class="tlx-title">PERFORMANCE</div>
                <div class="tlx-desc">Quanto ritieni di aver avuto successo nel raggiungere gli obiettivi del compito stabiliti dallo sperimentatore (o da te stesso)? Quanto sei stato soddisfatto della tua prestazione nel raggiungimento di questi obiettivi?</div>
                <div class="tlx-scale-container">
                    <span class="tlx-label" style="text-align:left;">Good</span>
                    <div class="ruler-wrapper"><input type="range" class="ruler" id="tlx_2" min="0" max="100" step="5" value="50" oninput="markTlx(2)"></div>
                    <span class="tlx-label" style="text-align:right;">Poor</span>
                </div>
            </div>
            
            <div class="tlx-item">
                <div class="tlx-title">EFFORT</div>
                <div class="tlx-desc">Quanto duramente hai dovuto lavorare (mentalmente e fisicamente) per raggiungere il tuo livello di prestazione?</div>
                <div class="tlx-scale-container">
                    <span class="tlx-label">Low</span>
                    <div class="ruler-wrapper"><input type="range" class="ruler" id="tlx_3" min="0" max="100" step="5" value="50" oninput="markTlx(3)"></div>
                    <span class="tlx-label">High</span>
                </div>
            </div>
            
            <div class="tlx-item">
                <div class="tlx-title">FRUSTRATION LEVEL</div>
                <div class="tlx-desc">Quanto ti sei sentito insicuro, scoraggiato, irritato, stressato e infastidito, piuttosto che sicuro, gratificato, contento, rilassato e soddisfatto durante lo svolgimento del compito?</div>
                <div class="tlx-scale-container">
                    <span class="tlx-label">Low</span>
                    <div class="ruler-wrapper"><input type="range" class="ruler" id="tlx_4" min="0" max="100" step="5" value="50" oninput="markTlx(4)"></div>
                    <span class="tlx-label">High</span>
                </div>
            </div>
            
            <button class="btn-submit" onclick="submitTlx()" style="background-color: #4CAF50; margin-top: 40px;">COMPLETA ESPERIMENTO</button>
        </div>

        <div id="results-container" style="display:none;"></div>

        <script>
            const kp_metrics = {metrics_list_json};
            const kp_mean_perf = {kp_mean_perf};
            const kp_tot_time = {kp_tot_time};
            const kp_tot_iter = {kp_tot_iter};
            const nasa_start_rel = {nasa_start_rel};

            const expertRanking = {{
                "Due serbatoi di ossigeno da 45 kg": 1, "20 litri d'acqua": 2, "Mappa stellare": 3,
                "Cibo concentrato": 4, "Ricetrasmettitore FM a energia solare": 5, "15 metri di corda di nylon": 6,
                "Kit di pronto soccorso con aghi da iniezione": 7, "Seta di paracadute": 8, "Zattera di salvataggio autogonfiabile": 9,
                "Razzi di segnalazione luminosa": 10, "Due pistole calibro .45": 11, "Una cassa di latte disidratato": 12,
                "Unità di riscaldamento portatile": 13, "Bussola magnetica": 14, "Scatola di fiammiferi": 15
            }};
            
            const explanations = {{
                "Scatola di fiammiferi": "Inutile poiché non c'è ossigeno sulla luna.", "Cibo concentrato": "Soddisfa i requisiti energetici di base.", "15 metri di corda di nylon": "Utile per scalare scogliere, legare i feriti insieme, ecc.", "Seta di paracadute": "Protezione dai raggi solari.", "Unità di riscaldamento portatile": "Utile solo se sul lato oscuro della luna.", "Due pistole calibro .45": "Possibile fonte di autopropulsione.", "Una cassa di latte disidratato": "Duplica il cibo concentrato in una forma più ingombrante.", "Due serbatoi di ossigeno da 45 kg": "Necessità assoluta per il supporto vitale.", "Mappa stellare": "Mezzo più importante per determinare posizione e direzioni.", "Zattera di salvataggio autogonfiabile": "La bombola di CO2 è un possibile dispositivo di propulsione.", "Bussola magnetica": "Praticamente inutile poiché il campo magnetico sulla luna non è polarizzato.", "20 litri d'acqua": "Necessità assoluta per sostenere la vita.", "Razzi di segnalazione luminosa": "Possibile segnale di soccorso una volta abbastanza vicini alla nave madre per essere visti.", "Kit di pronto soccorso con aghi da iniezione": "Gli aghi da iniezione adatti all'apertura delle tute sono molto utili.", "Ricetrasmettitore FM a energia solare": "Utile solo se è possibile la trasmissione in linea di vista, con raggio di trasmissione limitato."
            }};

            // STAI Setup
            const staiStatements = [
                "Mi sento calmo/a", "Mi sento sicuro/a", "Sono teso/a", "Mi sento sotto pressione", "Mi sento tranquillo/a",
                "Mi sento turbato/a", "Sono attualmente preoccupato/a per possibili disgrazie", "Mi sento soddisfatto/a", "Mi sento spaventato/a", "Mi sento a mio agio",
                "Mi sento sicuro/a di me", "Mi sento nervoso/a", "Sono agitato/a", "Mi sento indeciso/a", "Sono rilassato/a",
                "Mi sento contento/a", "Sono preoccupato/a", "Mi sento confuso/a", "Mi sento disteso/a", "Mi sento bene"
            ];
            const invertedStai = [1, 2, 5, 8, 10, 11, 15, 16, 19, 20];
            
            const tbody = document.getElementById('stai-body');
            staiStatements.forEach((stmt, idx) => {{
                let i = idx + 1;
                let tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${{i}}. ${{stmt}}</td>
                    <td><input type="radio" name="stai_${{i}}" value="1"></td>
                    <td><input type="radio" name="stai_${{i}}" value="2"></td>
                    <td><input type="radio" name="stai_${{i}}" value="3"></td>
                    <td><input type="radio" name="stai_${{i}}" value="4"></td>
                `;
                tbody.appendChild(tr);
            }});

            // Tracker Variabili
            let movesCount = 0;
            let firstMoveTime = null;
            let lastMoveTime = null;
            const startTime = new Date().getTime(); 
            const durationLimit = 15 * 60 * 1000;
            let timerInterval;
            let alertShown = false;
            
            // Variabili Risultati Globali
            let totalTimeMs = 0;
            let nasa_dai = 0;
            let tableRowsHtml = ""; // Tabella NASA
            let stai_vals = [];
            let stai_total = 0;
            let stai_mean = 0;
            let tlx_vals = [];
            let tlx_total = 0;
            let tlx_mean = 0;

            // TLX tracker
            let tlxTouched = [false, false, false, false, false];

            function copyNasaState() {{
                let copyText = "Task: NASA Survival Task\\n";
                copyText += "Il partecipante deve ordinare 15 oggetti dal più importante (1) al meno importante (15).\\n\\n";
                copyText += "Ranking Attuale impostato dal partecipante:\\n";
                
                // Estrae l'ordine attuale dalla lista
                let items = document.querySelectorAll('.sortable-item');
                items.forEach((item, index) => {{
                    let itemName = item.getAttribute('data-name');
                    copyText += (index + 1) + ". " + itemName + "\\n";
                }});

                // API per copiare negli appunti
                navigator.clipboard.writeText(copyText).then(function() {{
                    const btn = document.getElementById('copy-nasa-btn');
                    btn.innerText = '✅ COPIATO!';
                    btn.style.backgroundColor = '#4CAF50';
                    btn.style.color = 'white';
                    setTimeout(() => {{
                        btn.innerText = '📋 COPIA ISTRUZIONI E RANKING ATTUALE';
                        btn.style.backgroundColor = '#e0e2e6';
                        btn.style.color = '#31333F';
                    }}, 2000);
                }}).catch(function(err) {{
                    // Fallback se le API clipboard sono bloccate dall'iframe di Streamlit
                    const el = document.createElement('textarea');
                    el.value = copyText;
                    document.body.appendChild(el);
                    el.select();
                    document.execCommand('copy');
                    document.body.removeChild(el);
                    
                    const btn = document.getElementById('copy-nasa-btn');
                    btn.innerText = '✅ COPIATO!';
                    btn.style.backgroundColor = '#4CAF50';
                    btn.style.color = 'white';
                    setTimeout(() => {{
                        btn.innerText = '📋 COPIA ISTRUZIONI E RANKING ATTUALE';
                        btn.style.backgroundColor = '#e0e2e6';
                        btn.style.color = '#31333F';
                    }}, 2000);
                }});
            }}
            function updateBadges() {{
                document.querySelectorAll('.sortable-item').forEach((item, index) => {{
                    item.querySelector('.badge').innerText = index + 1;
                }});
            }}
            updateBadges();

            const sortable = new Sortable(document.getElementById('ranking-list'), {{
                animation: 150,
                onEnd: function (evt) {{
                    if (evt.oldIndex !== evt.newIndex) {{
                        movesCount++;
                        const now = new Date().getTime();
                        if (!firstMoveTime) firstMoveTime = now;
                        lastMoveTime = now;
                        updateBadges();
                    }}
                }}
            }});

            timerInterval = setInterval(function() {{
                const timeLeft = durationLimit - (new Date().getTime() - startTime);
                if (timeLeft <= 60000 && !alertShown) {{
                    alertShown = true;
                    document.getElementById('timer-modal-overlay').style.display = 'flex';
                }}
                if (timeLeft <= 0) {{
                    document.getElementById('timer').innerText = "TEMPO SCADUTO!";
                    clearInterval(timerInterval);
                    finishNasaTask();
                }} else {{
                    const m = Math.floor((timeLeft % 3600000) / 60000);
                    const s = Math.floor((timeLeft % 60000) / 1000);
                    document.getElementById('timer').innerText = "Tempo Rimanente: " + (m<10?"0":"")+m + ":" + (s<10?"0":"")+s;
                }}
            }}, 1000);

            function finishNasaTask() {{
                clearInterval(timerInterval);
                totalTimeMs = new Date().getTime() - startTime;
                if (totalTimeMs > durationLimit) totalTimeMs = durationLimit;
                
                // Calcolo Tabella Finale NASA e DAI
                document.querySelectorAll('.sortable-item').forEach((item, index) => {{
                    const itemName = item.getAttribute('data-name');
                    const participantRank = index + 1;
                    const expertRank = expertRanking[itemName];
                    const explanation = explanations[itemName];
                    
                    nasa_dai += Math.abs(participantRank - expertRank);
                    
                    tableRowsHtml += "<tr>" +
                        "<td style='padding: 8px; border: 1px solid #ddd;'><strong>" + itemName + "</strong></td>" +
                        "<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>" + participantRank + "</td>" +
                        "<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>" + expertRank + "</td>" +
                        "<td style='padding: 8px; border: 1px solid #ddd; font-style: italic;'>" + explanation + "</td>" +
                    "</tr>";
                }});

                document.getElementById('nasa-task-container').style.display = 'none';
                document.getElementById('stai-container').style.display = 'block';
                window.scrollTo(0, 0);
            }}

            function submitStai() {{
                stai_total = 0;
                stai_vals = [];
                let allAnswered = true;
                
                for(let i=1; i<=20; i++) {{
                    let radio = document.querySelector(`input[name="stai_${{i}}"]:checked`);
                    if(!radio) {{ allAnswered = false; break; }}
                    
                    let val = parseInt(radio.value);
                    stai_vals.push(val); // Salvo risposta grezza per Export CSV
                    
                    if(invertedStai.includes(i)) {{
                        val = 5 - val; // Inversione di scala
                    }}
                    stai_total += val;
                }}

                if(!allAnswered) {{
                    alert("⚠️ Attenzione: è obbligatorio rispondere a tutte le 20 affermazioni prima di procedere.");
                    return;
                }}

                stai_mean = stai_total / 20.0;
                
                document.getElementById('stai-container').style.display = 'none';
                document.getElementById('tlx-container').style.display = 'block';
                window.scrollTo(0, 0);
            }}

            function markTlx(idx) {{
                tlxTouched[idx] = true;
                document.getElementById(`tlx_${{idx}}`).classList.add('touched');
            }}

            function submitTlx() {{
                let allTouched = tlxTouched.every(v => v === true);
                if(!allTouched) {{
                    alert("⚠️ Attenzione: è obbligatorio valutare tutte e 5 le dimensioni spostando i selettori.");
                    return;
                }}

                tlx_total = 0;
                tlx_vals = [];
                for(let i=0; i<5; i++) {{
                    let val = parseInt(document.getElementById(`tlx_${{i}}`).value);
                    tlx_vals.push(val);
                    tlx_total += val;
                }}
                tlx_mean = tlx_total / 5.0;

                document.getElementById('tlx-container').style.display = 'none';
                generateFinalResults();
            }}

            function generateFinalResults() {{
                let timePerMove = 0;
                if (movesCount > 0 && firstMoveTime && lastMoveTime) {{
                    timePerMove = ((lastMoveTime - firstMoveTime) / 1000) / movesCount;
                }}

                let totalTimeSec = totalTimeMs / 1000;
                let nasa_end_rel = nasa_start_rel + totalTimeSec;

                let finalHeaders = {headers_json};
                let finalValues = {values_json};
                
                // Add NASA metrics
                finalHeaders.push("NASA_DAI", "NASA_Total_Time_s", "NASA_Moves", "NASA_Time_Per_Move_s", "NASA_Start_s", "NASA_End_s");
                finalValues.push(nasa_dai, totalTimeSec.toFixed(2), movesCount, timePerMove.toFixed(2), nasa_start_rel.toFixed(2), nasa_end_rel.toFixed(2));

                // Add STAI raw individual values
                for(let i=1; i<=20; i++) {{
                    finalHeaders.push(`STAI_${{i}}`);
                    finalValues.push(stai_vals[i-1]);
                }}
                
                // Add STAI and TLX totals
                finalHeaders.push("STAI_Total", "STAI_Mean", "TLX_Mental", "TLX_Temporal", "TLX_Performance", "TLX_Effort", "TLX_Frustration", "TLX_Total", "TLX_Mean");
                finalValues.push(stai_total, stai_mean.toFixed(2), tlx_vals[0], tlx_vals[1], tlx_vals[2], tlx_vals[3], tlx_vals[4], tlx_total, tlx_mean.toFixed(2));

                const csvContent = finalHeaders.join(",") + "\\n" + finalValues.join(",");
                const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
                const url = URL.createObjectURL(blob);

                let kp_instances_html = "";
                kp_metrics.forEach(m => {{
                    kp_instances_html += `
                        <div class="kp-instance-card">
                            <strong>${{m.Istanza}}</strong><br>
                            Performance: ${{(m.Economic_Performance * 100).toFixed(2)}}% | Tempo: ${{m.Tempo_Speso_sec}}s | Click: ${{m.Iterazioni_Effort}}
                        </div>
                    `;
                }});

                // Display Original Results UI (Hidden Questionnaires)
                const resDiv = document.getElementById('results-container');
                resDiv.style.display = 'block';
                resDiv.innerHTML = `
                    <div class="results-box">
                        <h1 style="color:#4CAF50; text-align:center; font-size: 32px; margin-top: 0;">Esperimento Completato con Successo!</h1>
                        <p style="text-align:center; font-size: 18px;">Grazie per la collaborazione. Clicca il pulsante qui sotto per esportare i dati finali.</p>
                        <a href="${{url}}" download="Esperimento_{st.session_state.participant_id}_Completo.csv" class="btn-download">⬇️ SCARICA DATASET COMPLETO (CSV)</a>
                        <hr style="margin: 30px 0;">
                        
                        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                            
                            <div style="flex: 1; min-width: 300px; background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
                                <h3 style="margin-top:0; color:#0066cc;">📊 Task 1: Knapsack</h3>
                                ${{kp_instances_html}}
                                <div style="background: #e6f2ff; padding: 10px; margin-top: 15px; border-radius: 4px;">
                                    <strong>Media Globale (Senza Prova):</strong> ${{(kp_mean_perf * 100).toFixed(2)}}% <br>
                                    <strong>Tempo Totale (Senza Prova):</strong> ${{kp_tot_time.toFixed(1)}} s <br>
                                    <strong>Iterazioni Totali (Senza Prova):</strong> ${{kp_tot_iter}}
                                </div>
                                
                                <hr style="margin: 25px 0;">
                                
                                <h3 style="color:#cc0000;">🚀 Task 2: NASA Survival</h3>
                                <p><strong>Decision Adequacy Index (DAI):</strong> <span style="font-size:20px; font-weight:bold;">${{nasa_dai}}</span> / 112 <br><span style="font-size: 12px; color: #666;">(Più basso è meglio)</span></p>
                                <p><strong>Tempo Speso:</strong> ${{totalTimeSec.toFixed(1)}} s</p>
                                <p><strong>Mosse:</strong> ${{movesCount}}</p>
                            </div>
                            
                            <div style="flex: 2; min-width: 400px; background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
                                <h3 style="margin-top:0;">Spiegazione Ranking NASA</h3>
                                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                                    <tr style="background-color: #f2f2f2;">
                                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Oggetto</th>
                                        <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Tuo Rank</th>
                                        <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Rank Esperto</th>
                                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Spiegazione Ufficiale</th>
                                    </tr>
                                    ${{tableRowsHtml}}
                                </table>
                            </div>
                            
                        </div>
                    </div>
                `;
                
                window.scrollTo(0, 0);
            }}
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=1800, scrolling=True)
