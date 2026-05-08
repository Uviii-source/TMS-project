from nicegui import ui
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import math

# --- Constants & Data ---
CURVES = {
    "IEC Normal Inverse": {"A": 0.14, "B": 0.0, "c": 0.02},
    "IEC Very Inverse": {"A": 13.5, "B": 0.0, "c": 1.0},
    "IEC Extremely Inverse": {"A": 80.0, "B": 0.0, "c": 2.0},
    "IEC Long Time Inverse": {"A": 120.0, "B": 0.0, "c": 1.0},
    "ANSI Normal Inverse": {"A": 0.0086, "B": 0.0185, "c": 0.02},
    "ANSI Very Inverse": {"A": 19.61, "B": 0.491, "c": 2.0},
    "ANSI Extremely Inverse": {"A": 28.2, "B": 0.1217, "c": 2.0}
}

CABLE_DATA = {
    "Cu": {
        "rho": 0.0175,
        "reactance": 0.08,
        "iz": {
            1.5: 14.5, 2.5: 20, 4: 26, 6: 34, 10: 46, 16: 62, 25: 80, 35: 99, 
            50: 118, 70: 149, 95: 179, 120: 206, 150: 235, 185: 268, 240: 313
        }
    },
    "Al": {
        "rho": 0.028,
        "reactance": 0.08,
        "iz": {
            2.5: 15.5, 4: 20, 6: 26, 10: 35, 16: 48, 25: 62, 35: 77, 50: 92, 
            70: 116, 95: 140, 120: 161, 150: 184, 185: 210, 240: 245
        }
    }
}

# --- Styling ---
ui.add_head_html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Lora:ital,wght@0,400;0,600;1,400&display=swap');
    body { font-family: 'Inter', sans-serif; background-color: #f1f5f9; }
    .abb-header { background-color: #FF0000; height: 4px; width: 100%; position: fixed; top: 0; left: 0; z-index: 1000; }
    .nav-button { justify-content: flex-start; text-align: left; width: 100%; letter-spacing: 0.3px; font-weight: 500; height: 44px; border-radius: 8px; margin-bottom: 4px; text-transform: none !important; }
    .nav-button-active { background-color: rgba(255, 0, 0, 0.05) !important; color: #FF0000 !important; font-weight: 700; }
    .nav-label { font-size: 0.85rem; }
    .nav-standard { font-size: 0.7rem; font-weight: 700; opacity: 0.6; }
    .result-card { border-left: 4px solid #FF0000; background-color: white; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .input-sidebar { background-color: #f8fafc; border-right: 1px solid #e2e8f0; }
    .metric-value { color: #FF0000; font-size: 1.5rem; font-weight: bold; }

    /* Math rendering - pure CSS, no external libraries */
    .formula-block {
        background: white;
        border-left: 4px solid #dde3ed;
        border-radius: 4px;
        padding: 1.1rem 2rem;
        margin: 0.3rem 0 1rem 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        overflow-x: auto;
    }
    .math-row {
        display: flex;
        align-items: center;
        justify-content: center;
        flex-wrap: wrap;
        gap: 0.3em;
        font-family: 'Lora', 'Georgia', 'Times New Roman', serif;
        font-size: 1.18em;
        color: #1e293b;
        line-height: 2.5;
    }
    .math-eq { color: #64748b; margin: 0 0.15em; }
    .math-result { color: #DC2626; font-weight: 700; font-size: 1.05em; }
    .math-unit { font-family: 'Inter', sans-serif; font-style: normal; font-size: 0.88em; color: #475569; margin-left: 0.1em; }
    .mfrac {
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        vertical-align: middle;
        margin: 0 0.2em;
        line-height: 1.2;
    }
    .mnum { border-bottom: 1.5px solid #1e293b; padding: 0.05em 0.35em; text-align: center; font-size: 0.9em; }
    .mden { padding: 0.05em 0.35em; text-align: center; font-size: 0.9em; }
    .step-label {
        font-weight: 700;
        color: #334155;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 0.25rem;
    }
</style>
<div class="abb-header"></div>
""")

# --- State Management ---
class AppState:
    def __init__(self):
        self.current_tool = "transformer"

        self.calc_triggered = False
        
        # Transformer Inputs
        self.t_s_nom = 1000
        self.t_u_nom = 10.5
        self.t_ct_primary = 100
        self.t_ct_secondary = 5
        self.t_k_ots = 1.2
        self.t_k_szp = 1.3
        self.t_k_v = 0.95
        self.t_k_per = 1.4
        self.t_i_kz_min = 800.0
        self.t_curve_type = "IEC Normal Inverse"
        self.t_i_sc = 2000.0
        self.t_t_op = 0.5
        self.t_manual_start = False
        self.t_manual_val = 1.0
        self.t_method = "Methodic 1"
        self.t_time_mode = "Inverse Time (TMS)"
        self.t_t_sz_def = 0.5  # Defined time delay
        
        # Transformer Methodic 2 coefficients
        self.t_m2_k_n_load = 1.2
        self.t_m2_k_n_ats = 1.1
        self.t_m2_k_szp = 4.0
        self.t_m2_k_n_sel = 1.1

        # Generator Inputs
        self.g_i_nom_g = 2000.0
        self.g_k_ots_g = 1.2
        self.g_k_v_g = 0.935
        self.g_i_max_mtz_ol = 1500.0
        self.g_k_tt = 400.0
        self.g_i_kz_min_g = 5000.0
        self.g_curve_type_g = "IEC Extremely Inverse"
        self.g_t_mtz_ol = 0.5
        self.g_delta_t = 0.3

        # Selectivity Inputs
        self.s_ds_name = "Q1 (Feeder)"
        self.s_ds_curve = "IEC Normal Inverse"
        self.s_ds_pickup = 200.0
        self.s_ds_tms = 0.1
        self.s_us_name = "Q0 (Main)"
        self.s_us_curve = "IEC Very Inverse"
        self.s_us_pickup = 400.0
        self.s_us_tms = 0.2
        self.s_i_min_fault = 600.0
        self.s_i_max_fault = 5000.0
        self.s_delta_t_req = 0.3

        # Cable Inputs
        self.c_p_load = 50.0
        self.c_u_nom = 400
        self.c_cos_phi = 0.85
        self.c_length = 100.0
        self.c_material = "Cu"
        self.c_du_max = 5.0

        # SC Generator Inputs
        self.sc_s_n = 100.0
        self.sc_u_rG = 11.0
        self.sc_cos_phi_G = 0.85
        self.sc_x_d_pu = 0.14
        self.sc_r_a_pu = 0.003
        self.sc_u_n = 11.0
        self.sc_freq = 50
        self.sc_c_max = 1.10
        self.sc_fault_loc = ["Generator Terminals (LV Bus)"]
        self.sc_fault_types = ["3-phase (I\"k3)", "2-phase (I\"k2)"]
        self.sc_t_k = 1.0
        # Transformer
        self.sc_s_T = 100.0
        self.sc_u_T_lv = 11.0
        self.sc_u_T_hv = 110.0
        self.sc_u_k_pct = 10.0
        self.sc_p_k_kw = 200.0

        # Earthing Inputs
        self.e_u_sys = 110.0
        self.e_if_sym = 10000.0
        self.e_tf = 0.5
        self.e_xr = 10.0
        self.e_sf = 0.6
        self.e_rho = 100.0
        self.e_rho_s = 2500.0
        self.e_hs = 0.1
        self.e_h = 0.5
        self.e_a = 3600.0
        self.e_lx = 60.0
        self.e_ly = 60.0
        self.e_lc = 600.0
        self.e_lr = 0.0
        self.e_nx = 7
        self.e_ny = 7
        self.e_d_cond = 0.01
        self.e_body_weight = 50
        self.e_ts = 0.5
        self.e_cond_mat = "Copper (soft-drawn)"

        # Incomer Inputs (ANSI 67)
        self.inc_i_rab_own_max = 320.0
        self.inc_i_rab_neighbor_max = 320.0
        self.inc_i_sz_sv = 1200.0
        self.inc_t_sz_sv = 0.5
        self.inc_i_k_min = 2000.0
        self.inc_k_szp = 2.8
        self.inc_k_ots = 1.2
        self.inc_k_v = 0.935
        self.inc_k_otv = 1.5
        self.inc_k_tok = 1.0
        self.inc_delta_t = 0.3
        self.inc_method = "Methodic 1"
        self.inc_time_mode = "Defined Time"
        
        # Incomer Methodic 2 coefficients
        self.inc_m2_k_n_load = 1.2
        self.inc_m2_k_n_ats = 1.1
        self.inc_m2_k_szp = 4.0
        self.inc_m2_k_n_sel = 1.1
        
        # Incomer Inverse Time parameters
        self.inc_curve_type = "IEC Normal Inverse"
        self.inc_i_sc = 2000.0
        self.inc_t_op = 0.5

state = AppState()

# --- Utility Functions ---
def reset_calc():
    state.calc_triggered = False
    content.refresh()

def trigger_calc():
    state.calc_triggered = True
    content.refresh()

def frac(num, den):
    """HTML fraction using CSS flex — renders identically to LaTeX fractions."""
    return f'<span class="mfrac"><span class="mnum">{num}</span><span class="mden">{den}</span></span>'

def math_step(label, lhs, rhs, result, unit=""):
    """Render a labeled calculation step as: LHS = RHS = RESULT unit (pure HTML/CSS)."""
    with ui.column().classes('w-full mb-1'):
        ui.label(label).classes('step-label')
        ui.html(f'''<div class="formula-block"><div class="math-row">
            <span style="font-style:italic;">{lhs}</span>
            <span class="math-eq">=</span>
            {rhs}
            <span class="math-eq">=</span>
            <span class="math-result">{result}</span>
            <span class="math-unit">{unit}</span>
        </div></div>''')

# --- Module: Transformer Protection (ANSI 51) ---
def transformer_protection_page():
    with ui.row().classes('w-full no-wrap'):
        # Sidebar-like input panel
        with ui.column().classes('w-80 p-4 input-sidebar min-h-screen'):
            ui.label('METHODOLOGY').classes('text-xs font-bold text-slate-400 mb-2')
            ui.select(["Methodic 1", "Methodic 2"], 
                      value=state.t_method, 
                      on_change=lambda e: (setattr(state, 't_method', e.value), content.refresh())).classes('w-full mb-4')

            ui.label('TIME MODE').classes('text-xs font-bold text-slate-400 mb-2')
            ui.select(["Defined Time", "Inverse Time (TMS)"], 
                      value=state.t_time_mode, 
                      on_change=lambda e: (setattr(state, 't_time_mode', e.value), content.refresh())).classes('w-full mb-4')

            ui.label('TRANSFORMER DATA').classes('text-xs font-bold text-slate-400 mb-2')
            ui.number('S_nom (kVA)', value=state.t_s_nom, on_change=lambda e: setattr(state, 't_s_nom', e.value)).classes('w-full')
            ui.number('U_nom (kV)', value=state.t_u_nom, on_change=lambda e: setattr(state, 't_u_nom', e.value)).classes('w-full')
            
            ui.label('CT PARAMETERS').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.number('CT Primary (A)', value=state.t_ct_primary, on_change=lambda e: setattr(state, 't_ct_primary', e.value)).classes('w-full')
            ui.select([5, 1], label='CT Secondary (A)', value=state.t_ct_secondary, on_change=lambda e: setattr(state, 't_ct_secondary', e.value)).classes('w-full')
            
            ui.label('COEFFICIENTS').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.number('K_v', value=state.t_k_v, step=0.01, on_change=lambda e: setattr(state, 't_k_v', e.value)).classes('w-full')
            ui.number('K_per', value=state.t_k_per, step=0.1, on_change=lambda e: setattr(state, 't_k_per', e.value)).classes('w-full')

            if state.t_method == "Methodic 1":
                ui.number('K_ots', value=state.t_k_ots, step=0.1, on_change=lambda e: setattr(state, 't_k_ots', e.value)).classes('w-full')
                ui.number('K_szp', value=state.t_k_szp, step=0.1, on_change=lambda e: setattr(state, 't_k_szp', e.value)).classes('w-full')
            else:
                ui.number('k_n (Load)', value=state.t_m2_k_n_load, step=0.1, on_change=lambda e: setattr(state, 't_m2_k_n_load', e.value)).classes('w-full')
                ui.number('k_n (ATS)', value=state.t_m2_k_n_ats, step=0.1, on_change=lambda e: setattr(state, 't_m2_k_n_ats', e.value)).classes('w-full')
                ui.number('k_szp (ATS)', value=state.t_m2_k_szp, step=0.1, on_change=lambda e: setattr(state, 't_m2_k_szp', e.value)).classes('w-full')
            
            ui.label('SENSITIVITY').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.number('Min SC Current (A)', value=state.t_i_kz_min, step=50, on_change=lambda e: setattr(state, 't_i_kz_min', e.value)).classes('w-full')
            
            if state.t_time_mode == "Inverse Time (TMS)":
                ui.label('TIME DELAY (TMS)').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
                ui.select(list(CURVES.keys()), label='Curve Type', value=state.t_curve_type, on_change=lambda e: setattr(state, 't_curve_type', e.value)).classes('w-full')
                ui.number('I_sc (A)', value=state.t_i_sc, step=100, on_change=lambda e: setattr(state, 't_i_sc', e.value)).classes('w-full')
                ui.number('Req. Time (s)', value=state.t_t_op, step=0.1, on_change=lambda e: setattr(state, 't_t_op', e.value)).classes('w-full')
            else:
                ui.label('TIME DELAY (DEFINED)').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
                ui.number('Time Delay (s)', value=state.t_t_sz_def, step=0.1, on_change=lambda e: setattr(state, 't_t_sz_def', e.value)).classes('w-full')
            
            ui.checkbox('Manual Start Value', value=state.t_manual_start, on_change=lambda e: setattr(state, 't_manual_start', e.value)).classes('mt-4')
            if state.t_manual_start:
                ui.number('Manual Value (x In)', value=state.t_manual_val, step=0.01, on_change=lambda e: setattr(state, 't_manual_val', e.value)).classes('w-full')

            ui.button('CALCULATE', on_click=trigger_calc).classes('w-full mt-6 bg-red-600 text-white font-bold')

        # Main content area
        with ui.column().classes('flex-grow p-8'):
            ui.label('Transformer Protection Settings (ANSI 51)').classes('text-2xl font-bold text-slate-800 mb-6')
            
            if state.calc_triggered:
                # Common Calculations
                i_nom = state.t_s_nom / (1.732 * state.t_u_nom)
                i_rab_max = i_nom * state.t_k_per
                
                if state.t_method == "Methodic 1":
                    i_szp = (state.t_k_ots * state.t_k_szp / state.t_k_v) * i_rab_max
                    threshold = 1.5
                else:
                    i_szp1 = (state.t_m2_k_n_load / state.t_k_v) * i_rab_max
                    i_szp2 = (state.t_m2_k_n_ats / state.t_k_v) * (i_rab_max) # Simplified
                    i_szp = max(i_szp1, i_szp2)
                    threshold = 1.2
                
                set_value = i_szp / state.t_ct_primary
                
                if state.t_manual_start:
                    final_set_value = state.t_manual_val
                    i_pickup_actual = final_set_value * state.t_ct_primary
                else:
                    final_set_value = set_value
                    i_pickup_actual = i_szp
                
                k_s = state.t_i_kz_min / i_pickup_actual
                
                tms_calc = None
                if state.t_time_mode == "Inverse Time (TMS)":
                    if state.t_i_sc > i_pickup_actual:
                        c = CURVES[state.t_curve_type]
                        i_rel = state.t_i_sc / i_pickup_actual
                        denominator = (c["A"] / ((i_rel ** c["c"]) - 1)) + c["B"]
                        tms_calc = state.t_t_op / denominator

                with ui.column().classes('w-full gap-4'):
                    # Results Summary Metrics
                    with ui.row().classes('w-full justify-between gap-4'):
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('I_nom').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{i_nom:.2f} A').classes('metric-value')
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('Start Value').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{final_set_value:.3f} x In').classes('metric-value')
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('Sensitivity Ks').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{k_s:.2f}').classes('metric-value')
                        
                        if state.t_time_mode == "Inverse Time (TMS)":
                            with ui.card().classes('flex-grow result-card'):
                                ui.label('TMS').classes('text-xs font-bold text-slate-400')
                                ui.label(f'{tms_calc:.3f}' if tms_calc else 'N/A').classes('metric-value')
                        else:
                            with ui.card().classes('flex-grow result-card'):
                                ui.label('Time Delay').classes('text-xs font-bold text-slate-400')
                                ui.label(f'{state.t_t_sz_def:.2f} s').classes('metric-value')

                    # Detailed Steps
                    with ui.expansion('Step-by-Step Calculations', icon='calculate').classes('w-full bg-white border').props('value=True'):
                        with ui.column().classes('w-full p-4'):
                            math_step('1. Nominal Current',
                                     'I<sub>nom</sub>',
                                     frac(f'{state.t_s_nom}', f'&radic;3 &middot; {state.t_u_nom}'),
                                     f'{i_nom:.2f}', 'A')

                            math_step('2. Max Operating Current',
                                     'I<sub>rab.max</sub>',
                                     f'{i_nom:.2f} &middot; K<sub>per</sub> = {i_nom:.2f} &middot; {state.t_k_per}',
                                     f'{i_rab_max:.2f}', 'A')

                            if state.t_method == "Methodic 1":
                                math_step('3. Protection Pickup Current',
                                         'I<sub>szp</sub>',
                                         frac(f'K<sub>ots</sub> &middot; K<sub>szp</sub>', 'K<sub>v</sub>') +
                                         f' &middot; I<sub>rab.max</sub> = ' +
                                         frac(f'{state.t_k_ots} &middot; {state.t_k_szp}', f'{state.t_k_v}') +
                                         f' &middot; {i_rab_max:.2f}',
                                         f'{i_szp:.2f}', 'A')
                            else:
                                math_step('3. Condition 1 (Load)',
                                         'I<sub>szp(1)</sub>',
                                         frac('k<sub>n</sub>', 'k<sub>v</sub>') + f' &middot; I<sub>rab.max</sub> = ' +
                                         frac(f'{state.t_m2_k_n_load}', f'{state.t_k_v}') + f' &middot; {i_rab_max:.2f}',
                                         f'{i_szp1:.2f}', 'A')
                                math_step('4. Condition 2 (Self-start)',
                                         'I<sub>szp(2)</sub>',
                                         frac('k<sub>n</sub>', 'k<sub>v</sub>') + f' &middot; I<sub>rab.max</sub> = ' +
                                         frac(f'{state.t_m2_k_n_ats}', f'{state.t_k_v}') + f' &middot; {i_rab_max:.2f}',
                                         f'{i_szp2:.2f}', 'A')
                                math_step('5. Final Pickup Current',
                                         'I<sub>szp</sub>',
                                         f'max({i_szp1:.2f}, {i_szp2:.2f})',
                                         f'{i_szp:.2f}', 'A')

                            math_step('Relay Start Value',
                                     'Start value',
                                     frac('I<sub>szp</sub>', 'CT<sub>primary</sub>') +
                                     f' = ' + frac(f'{i_szp:.2f}', f'{state.t_ct_primary}'),
                                     f'{set_value:.3f}', '&times; I<sub>n</sub>')

                    with ui.expansion('Sensitivity Check', icon='security').classes('w-full bg-white border'):
                        with ui.column().classes('w-full p-4'):
                            math_step('Sensitivity Coefficient',
                                     'K<sub>s</sub>',
                                     frac('I<sub>kz.min</sub>', 'I<sub>pickup</sub>') +
                                     f' = ' + frac(f'{state.t_i_kz_min:.0f}', f'{i_pickup_actual:.2f}'),
                                     f'{k_s:.2f}')
                        if k_s >= threshold:
                            ui.label(f'✅ Sensitivity confirmed (Ks ≥ {threshold})').classes('text-green-600 font-bold')
                        else:
                            ui.label(f'❌ Sensitivity insufficient (Ks < {threshold})').classes('text-red-600 font-bold')

                    if tms_calc and state.t_time_mode == "Inverse Time (TMS)":
                        with ui.expansion('Time Delay Analysis', icon='timer').classes('w-full bg-white border'):
                            ui.label(f'TMS = {tms_calc:.3f}').classes('font-bold')
                            ui.label('Expected operation time at multiples of pickup:').classes('text-slate-600 mt-2')
                            
                            def calc_time(m):
                                c = CURVES[state.t_curve_type]
                                if m <= 1: return None
                                return (c["A"] / (m**c["c"] - 1) + c["B"]) * tms_calc
                            
                            with ui.row().classes('w-full gap-4 mt-2'):
                                for mult in [3, 5, 8]:
                                    t = calc_time(mult)
                                    with ui.column().classes('items-center border p-2 rounded w-24'):
                                        ui.label(f'{mult}x').classes('text-xs font-bold')
                                        ui.label(f'{t:.2f}s' if t else 'N/A').classes('text-red-600')
            else:
                with ui.column().classes('w-full items-center justify-center p-20 border-2 border-dashed rounded-xl'):
                    ui.icon('analytics', size='64px').classes('text-slate-300')
                    ui.label('Enter data and click Calculate to see results').classes('text-slate-400 mt-4')

# --- Module: Generator Protection (ANSI 67) ---
def generator_protection_page():
    with ui.row().classes('w-full no-wrap'):
        with ui.column().classes('w-80 p-4 input-sidebar min-h-screen'):
            ui.label('GENERATOR DATA').classes('text-xs font-bold text-slate-400 mb-2')
            ui.number('I_nom.g (A)', value=state.g_i_nom_g, on_change=lambda e: setattr(state, 'g_i_nom_g', e.value)).classes('w-full')
            ui.number('K_ots', value=state.g_k_ots_g, step=0.1, on_change=lambda e: setattr(state, 'g_k_ots_g', e.value)).classes('w-full')
            ui.number('K_v', value=state.g_k_v_g, step=0.005, on_change=lambda e: setattr(state, 'g_k_v_g', e.value)).classes('w-full')
            
            ui.label('COORDINATION').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.number('Max I_mtz Feeder (A)', value=state.g_i_max_mtz_ol, on_change=lambda e: setattr(state, 'g_i_max_mtz_ol', e.value)).classes('w-full')
            ui.number('CT Ratio (k_TT)', value=state.g_k_tt, step=10, on_change=lambda e: setattr(state, 'g_k_tt', e.value)).classes('w-full')
            
            ui.label('SENSITIVITY & TIME').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.number('Min 2-ph SC (A)', value=state.g_i_kz_min_g, on_change=lambda e: setattr(state, 'g_i_kz_min_g', e.value)).classes('w-full')
            ui.select(list(CURVES.keys()), label='Curve Type', value=state.g_curve_type_g, on_change=lambda e: setattr(state, 'g_curve_type_g', e.value)).classes('w-full')
            ui.number('Feeder Time (s)', value=state.g_t_mtz_ol, step=0.1, on_change=lambda e: setattr(state, 'g_t_mtz_ol', e.value)).classes('w-full')
            ui.number('Delta T (s)', value=state.g_delta_t, step=0.1, on_change=lambda e: setattr(state, 'g_delta_t', e.value)).classes('w-full')

            ui.button('CALCULATE', on_click=trigger_calc).classes('w-full mt-6 bg-red-600 text-white font-bold')

        with ui.column().classes('flex-grow p-8'):
            ui.label('Generator Directional Protection (ANSI 67)').classes('text-2xl font-bold text-slate-800 mb-6')
            
            if state.calc_triggered:
                i_perv_sz1 = (state.g_k_ots_g / state.g_k_v_g) * state.g_i_nom_g
                i_perv_sz2 = state.g_k_ots_g * state.g_i_max_mtz_ol
                i_perv_sz = max(i_perv_sz1, i_perv_sz2)
                i_s = i_perv_sz / state.g_k_tt
                k_s_g = state.g_i_kz_min_g / i_perv_sz if i_perv_sz > 0 else 0
                t_d_i = state.g_t_mtz_ol + state.g_delta_t
                
                tms_g = None
                if state.g_i_kz_min_g > i_perv_sz:
                    c = CURVES[state.g_curve_type_g]
                    i_rel_g = state.g_i_kz_min_g / i_perv_sz
                    denominator_g = (c["A"] / ((i_rel_g ** c["c"]) - 1)) + c["B"]
                    tms_g = t_d_i / denominator_g

                with ui.column().classes('w-full gap-4'):
                    with ui.row().classes('w-full justify-between gap-4'):
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('I_pickup (Primary)').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{i_perv_sz:.2f} A').classes('metric-value')
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('I_pickup (Secondary)').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{i_s:.3f} A').classes('metric-value')
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('Sensitivity Ks').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{k_s_g:.2f}').classes('metric-value')
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('TMS').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{tms_g:.3f}' if tms_g else 'N/A').classes('metric-value')

                    with ui.expansion('Calculation Logic', icon='menu_book').classes('w-full bg-white border'):
                        with ui.column().classes('w-full p-4'):
                            math_step('1. Sensitivity Condition 1',
                                     'I<sub>perv.sz1</sub>',
                                     frac('K<sub>ots</sub>', 'K<sub>v</sub>') +
                                     f' &middot; I<sub>nom</sub> = ' +
                                     frac(f'{state.g_k_ots_g}', f'{state.g_k_v_g}') +
                                     f' &middot; {state.g_i_nom_g:.0f}',
                                     f'{i_perv_sz1:.2f}', 'A')

                            math_step('2. Sensitivity Condition 2',
                                     'I<sub>perv.sz2</sub>',
                                     f'K<sub>ots</sub> &middot; I<sub>mtz.max</sub> = {state.g_k_ots_g} &middot; {state.g_i_max_mtz_ol:.0f}',
                                     f'{i_perv_sz2:.2f}', 'A')

                            math_step('3. Final Pickup Current',
                                     'I<sub>perv.sz</sub>',
                                     f'max({i_perv_sz1:.2f}, {i_perv_sz2:.2f})',
                                     f'{i_perv_sz:.2f}', 'A')

                            math_step('4. Secondary Pickup',
                                     'I<sub>s</sub>',
                                     frac('I<sub>perv.sz</sub>', 'k<sub>TT</sub>') +
                                     f' = ' + frac(f'{i_perv_sz:.2f}', f'{state.g_k_tt:.0f}'),
                                     f'{i_s:.3f}', 'A')
            else:
                with ui.column().classes('w-full items-center justify-center p-20 border-2 border-dashed rounded-xl'):
                    ui.icon('electric_bolt', size='64px').classes('text-slate-300')
                    ui.label('Enter data and click Calculate to see results').classes('text-slate-400 mt-4')

# --- Module: Selectivity Analysis ---
def selectivity_page():
    with ui.row().classes('w-full no-wrap'):
        with ui.column().classes('w-80 p-4 input-sidebar min-h-screen'):
            ui.label('DOWNSTREAM (DS)').classes('text-xs font-bold text-slate-400 mb-2')
            ui.input('Name', value=state.s_ds_name, on_change=lambda e: setattr(state, 's_ds_name', e.value)).classes('w-full')
            ui.select(list(CURVES.keys()), label='Curve', value=state.s_ds_curve, on_change=lambda e: setattr(state, 's_ds_curve', e.value)).classes('w-full')
            ui.number('Pickup (A)', value=state.s_ds_pickup, on_change=lambda e: setattr(state, 's_ds_pickup', e.value)).classes('w-full')
            ui.number('TMS', value=state.s_ds_tms, step=0.01, on_change=lambda e: setattr(state, 's_ds_tms', e.value)).classes('w-full')
            
            ui.label('UPSTREAM (US)').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.input('Name', value=state.s_us_name, on_change=lambda e: setattr(state, 's_us_name', e.value)).classes('w-full')
            ui.select(list(CURVES.keys()), label='Curve', value=state.s_us_curve, on_change=lambda e: setattr(state, 's_us_curve', e.value)).classes('w-full')
            ui.number('Pickup (A)', value=state.s_us_pickup, on_change=lambda e: setattr(state, 's_us_pickup', e.value)).classes('w-full')
            ui.number('TMS', value=state.s_us_tms, step=0.01, on_change=lambda e: setattr(state, 's_us_tms', e.value)).classes('w-full')
            
            ui.label('ANALYSIS RANGE').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.number('Min Fault (A)', value=state.s_i_min_fault, on_change=lambda e: setattr(state, 's_i_min_fault', e.value)).classes('w-full')
            ui.number('Max Fault (A)', value=state.s_i_max_fault, on_change=lambda e: setattr(state, 's_i_max_fault', e.value)).classes('w-full')
            ui.number('Req. Delta T (s)', value=state.s_delta_t_req, step=0.05, on_change=lambda e: setattr(state, 's_delta_t_req', e.value)).classes('w-full')

            ui.button('CALCULATE', on_click=trigger_calc).classes('w-full mt-6 bg-red-600 text-white font-bold')

        with ui.column().classes('flex-grow p-8'):
            ui.label('Protection Selectivity Analysis').classes('text-2xl font-bold text-slate-800 mb-6')
            
            if state.calc_triggered:
                currents = np.logspace(np.log10(min(state.s_ds_pickup, state.s_us_pickup) * 1.1), np.log10(state.s_i_max_fault), 100)
                
                def get_time(current, pickup, tms, curve_name):
                    c = CURVES[curve_name]
                    multiple = current / pickup
                    if multiple <= 1.001: return 100
                    return (c["A"] / (multiple**c["c"] - 1) + c["B"]) * tms

                ds_times = [get_time(i, state.s_ds_pickup, state.s_ds_tms, state.s_ds_curve) for i in currents]
                us_times = [get_time(i, state.s_us_pickup, state.s_us_tms, state.s_us_curve) for i in currents]

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=currents, y=ds_times, name=state.s_ds_name, line=dict(color='#3b82f6', width=3)))
                fig.add_trace(go.Scatter(x=currents, y=us_times, name=state.s_us_name, line=dict(color='#ef4444', width=3)))

                fig.update_xaxes(type="log", title_text="Current (A)", gridcolor='#e2e8f0')
                fig.update_yaxes(type="log", title_text="Time (s)", gridcolor='#e2e8f0', range=[np.log10(0.01), np.log10(100)])
                fig.update_layout(
                    margin=dict(l=20, r=20, t=40, b=20),
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                ui.plotly(fig).classes('w-full h-96')

                with ui.row().classes('w-full gap-4 mt-6'):
                    test_currents = [state.s_i_min_fault, (state.s_i_min_fault + state.s_i_max_fault)/2, state.s_i_max_fault]
                    for curr in test_currents:
                        t_ds = get_time(curr, state.s_ds_pickup, state.s_ds_tms, state.s_ds_curve)
                        t_us = get_time(curr, state.s_us_pickup, state.s_us_tms, state.s_us_curve)
                        margin = t_us - t_ds
                        with ui.card().classes('flex-grow result-card'):
                            ui.label(f'At {curr:.0f} A').classes('text-xs font-bold text-slate-400')
                            ui.label(f'Δt = {margin:.2f} s').classes('metric-value')
                            if margin >= state.s_delta_t_req:
                                ui.label('SELECTIVE').classes('text-green-600 text-[10px] font-bold')
                            else:
                                ui.label('NON-SELECTIVE').classes('text-red-600 text-[10px] font-bold')
            else:
                with ui.column().classes('w-full items-center justify-center p-20 border-2 border-dashed rounded-xl'):
                    ui.icon('legend_toggle', size='64px').classes('text-slate-300')
                    ui.label('Enter parameters to generate coordination map').classes('text-slate-400 mt-4')

# --- Module: Cable Selection ---
def cable_page():
    with ui.row().classes('w-full no-wrap'):
        with ui.column().classes('w-80 p-4 input-sidebar min-h-screen'):
            ui.label('LOAD PARAMETERS').classes('text-xs font-bold text-slate-400 mb-2')
            ui.number('P_load (kW)', value=state.c_p_load, on_change=lambda e: setattr(state, 'c_p_load', e.value)).classes('w-full')
            ui.number('U_nom (V)', value=state.c_u_nom, on_change=lambda e: setattr(state, 'c_u_nom', e.value)).classes('w-full')
            ui.number('cos φ', value=state.c_cos_phi, step=0.01, min_value=0.5, max_value=1.0, on_change=lambda e: setattr(state, 'c_cos_phi', e.value)).classes('w-full')
            
            ui.label('LINE PARAMETERS').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.number('Length (m)', value=state.c_length, on_change=lambda e: setattr(state, 'c_length', e.value)).classes('w-full')
            ui.radio(['Cu', 'Al'], value=state.c_material, on_change=lambda e: setattr(state, 'c_material', e.value)).props('inline').classes('mt-2')
            ui.number('Max ΔU (%)', value=state.c_du_max, step=0.5, on_change=lambda e: setattr(state, 'c_du_max', e.value)).classes('w-full mt-2')

            ui.button('CALCULATE', on_click=trigger_calc).classes('w-full mt-6 bg-red-600 text-white font-bold')

        with ui.column().classes('flex-grow p-8'):
            ui.label('Cable Selection & Voltage Drop').classes('text-2xl font-bold text-slate-800 mb-6')
            
            if state.calc_triggered:
                i_load = (state.c_p_load * 1000) / (math.sqrt(3) * state.c_u_nom * state.c_cos_phi)
                
                available_sections = sorted(CABLE_DATA[state.c_material]["iz"].keys())
                selected_section = None
                for s in available_sections:
                    if CABLE_DATA[state.c_material]["iz"][s] >= i_load:
                        selected_section = s
                        break
                
                if selected_section:
                    rho = CABLE_DATA[state.c_material]["rho"]
                    x_react = CABLE_DATA[state.c_material]["reactance"]
                    sin_phi = math.sqrt(1 - state.c_cos_phi**2)
                    
                    while True:
                        delta_u = math.sqrt(3) * i_load * ((rho/selected_section * state.c_cos_phi) + (x_react/1000 * sin_phi)) * state.c_length
                        delta_u_pct = (delta_u / state.c_u_nom) * 100
                        
                        if delta_u_pct <= state.c_du_max:
                            break
                        
                        idx = available_sections.index(selected_section)
                        if idx + 1 < len(available_sections):
                            selected_section = available_sections[idx + 1]
                        else:
                            break

                    with ui.row().classes('w-full gap-4'):
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('Design Current').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{i_load:.2f} A').classes('metric-value')
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('Selected Section').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{selected_section} mm²').classes('metric-value')
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('Voltage Drop ΔU').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{delta_u_pct:.2f} %').classes('metric-value')

                    with ui.expansion('Calculation Details', icon='info').classes('w-full bg-white border mt-6'):
                        with ui.column().classes('w-full p-4'):
                            math_step('1. Load Current', 
                                     'I', 
                                     f'\\frac{{{state.c_p_load} \\cdot 1000}}{{\\sqrt{{3}} \\cdot {state.c_u_nom} \\cdot {state.c_cos_phi}}}', 
                                     f'{i_load:.2f}', 'A')
                            
                            ui.label(f'Permissible Current (Iz): {CABLE_DATA[state.c_material]["iz"][selected_section]} A for {selected_section} mm²').classes('mb-4 text-slate-600')

                            math_step('2. Voltage Drop', 
                                     '\\Delta U\\%', 
                                     f'\\frac{{\\Delta U}}{{{state.c_u_nom}}} \\cdot 100', 
                                     f'{delta_u_pct:.2f}', '%')
                            
                            if delta_u_pct <= state.c_du_max:
                                ui.label('✅ Meets voltage drop requirements').classes('text-green-600 font-bold')
                            else:
                                ui.label('❌ Fails voltage drop requirements').classes('text-red-600 font-bold')
                else:
                    ui.label('Current too high for available cable sizes').classes('text-red-600')
            else:
                with ui.column().classes('w-full items-center justify-center p-20 border-2 border-dashed rounded-xl'):
                    ui.icon('power', size='64px').classes('text-slate-300')
                    ui.label('Enter load parameters to select cable').classes('text-slate-400 mt-4')

# --- Module: SC Generator (IEC 60909) ---
def sc_generator_page():
    with ui.row().classes('w-full no-wrap'):
        with ui.column().classes('w-80 p-4 input-sidebar min-h-screen'):
            ui.label('GENERATOR DATA').classes('text-xs font-bold text-slate-400 mb-2')
            ui.number('S_n (MVA)', value=state.sc_s_n, on_change=lambda e: setattr(state, 'sc_s_n', e.value)).classes('w-full')
            ui.number('U_rG (kV)', value=state.sc_u_rG, on_change=lambda e: setattr(state, 'sc_u_rG', e.value)).classes('w-full')
            ui.number('x\"d (p.u.)', value=state.sc_x_d_pu, step=0.01, format="%.4f", on_change=lambda e: setattr(state, 'sc_x_d_pu', e.value)).classes('w-full')
            
            ui.label('NETWORK').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.number('U_n (kV)', value=state.sc_u_n, on_change=lambda e: setattr(state, 'sc_u_n', e.value)).classes('w-full')
            ui.select([50, 60], label='Freq (Hz)', value=state.sc_freq, on_change=lambda e: setattr(state, 'sc_freq', e.value)).classes('w-full')
            
            ui.label('FAULT PARAMETERS').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.select(["Generator Terminals (LV Bus)", "HV Bus (after transformer)"], multiple=True, label='Locations', value=state.sc_fault_loc, on_change=lambda e: setattr(state, 'sc_fault_loc', e.value)).classes('w-full')
            ui.number('Fault Duration T_k (s)', value=state.sc_t_k, step=0.05, on_change=lambda e: setattr(state, 'sc_t_k', e.value)).classes('w-full')

            if "HV Bus (after transformer)" in state.sc_fault_loc:
                ui.label('TRANSFORMER DATA').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
                ui.number('S_T (MVA)', value=state.sc_s_T, on_change=lambda e: setattr(state, 'sc_s_T', e.value)).classes('w-full')
                ui.number('U_T_HV (kV)', value=state.sc_u_T_hv, on_change=lambda e: setattr(state, 'sc_u_T_hv', e.value)).classes('w-full')
                ui.number('u_k (%)', value=state.sc_u_k_pct, on_change=lambda e: setattr(state, 'sc_u_k_pct', e.value)).classes('w-full')

            ui.button('CALCULATE', on_click=trigger_calc).classes('w-full mt-6 bg-red-600 text-white font-bold')

        with ui.column().classes('flex-grow p-8'):
            ui.label('Short-Circuit Calculation (IEC 60909)').classes('text-2xl font-bold text-slate-800 mb-6')
            
            if state.calc_triggered:
                # Calculations
                sin_phi_G = math.sqrt(max(1 - state.sc_cos_phi_G**2, 0))
                z_base = (state.sc_u_rG ** 2) / state.sc_s_n
                x_d_ohm = state.sc_x_d_pu * z_base
                r_a_ohm = state.sc_r_a_pu * z_base
                
                denom_KG = 1 + state.sc_x_d_pu * sin_phi_G
                K_G = (state.sc_u_n / state.sc_u_rG) * (state.sc_c_max / denom_KG)
                
                r_GK = K_G * r_a_ohm
                x_GK = K_G * x_d_ohm
                z_GK = math.sqrt(r_GK**2 + x_GK**2)
                
                def peak_factor(r, x):
                    rX = r / x if x > 0 else 0
                    return 1.02 + 0.98 * math.exp(-3 * rX)

                results = []
                if "Generator Terminals (LV Bus)" in state.sc_fault_loc:
                    kap = peak_factor(r_GK, x_GK)
                    ik3 = (state.sc_c_max * state.sc_u_rG * 1e3) / (math.sqrt(3) * z_GK) / 1e3
                    ip = kap * math.sqrt(2) * ik3
                    results.append({"loc": "LV Bus", "ik3": ik3, "ip": ip, "kap": kap})
                
                if "HV Bus (after transformer)" in state.sc_fault_loc:
                    z_T_base_hv = (state.sc_u_T_hv**2) / state.sc_s_T
                    z_T_hv = (state.sc_u_k_pct / 100) * z_T_base_hv
                    r_T_pu = (state.sc_p_k_kw * 1e3) / (state.sc_s_T * 1e6)
                    r_T_hv = r_T_pu * z_T_base_hv
                    x_T_hv = math.sqrt(max(z_T_hv**2 - r_T_hv**2, 0))
                    
                    n_ratio = state.sc_u_T_hv / state.sc_u_T_lv
                    r_tot_hv = r_GK * n_ratio**2 + r_T_hv
                    x_tot_hv = x_GK * n_ratio**2 + x_T_hv
                    z_tot_hv = math.sqrt(r_tot_hv**2 + x_tot_hv**2)
                    
                    kap_hv = peak_factor(r_tot_hv, x_tot_hv)
                    ik3_hv = (state.sc_c_max * state.sc_u_T_hv * 1e3) / (math.sqrt(3) * z_tot_hv) / 1e3
                    ip_hv = kap_hv * math.sqrt(2) * ik3_hv
                    results.append({"loc": f"HV Bus ({state.sc_u_T_hv}kV)", "ik3": ik3_hv, "ip": ip_hv, "kap": kap_hv})

                with ui.row().classes('w-full gap-4'):
                    for res in results:
                        with ui.card().classes('flex-grow result-card'):
                            ui.label(res["loc"]).classes('text-xs font-bold text-slate-400')
                            ui.label(f'I\"k3 = {res["ik3"]:.3f} kA').classes('metric-value')
                            ui.label(f'ip = {res["ip"]:.3f} kA (κ={res["kap"]:.2f})').classes('text-xs text-slate-600')

                with ui.expansion('Impedance Derivation', icon='hub').classes('w-full bg-white border mt-6'):
                    with ui.column().classes('w-full p-4'):
                        math_step('1. Generator Base Impedance', 
                                 'Z_{base}', 
                                 f'\\frac{{U_{{rG}}^2}}{{S_n}}', 
                                 f'{z_base:.4f}', '\\Omega')
                        
                        math_step('2. Correction Factor', 
                                 'K_G', 
                                 f'\\frac{{U_n}}{{U_{{rG}}}} \\cdot \\frac{{C_{{max}}}}{{1 + x\"_d \\cdot \\sin\\phi_G}}', 
                                 f'{K_G:.4f}')
                        
                        math_step('3. Corrected Reactance', 
                                 'X_{GK}', 
                                 'K_G \\cdot X\"_d', 
                                 f'{x_GK:.4f}', '\\Omega')
                        
                        math_step('4. SC Current (3-phase)', 
                                 'I\"_{k3}', 
                                 '\\frac{C_{max} \\cdot U_{rG}}{\\sqrt{3} \\cdot Z_{GK}}', 
                                 f'{ik3:.3f}', 'kA')
            else:
                with ui.column().classes('w-full items-center justify-center p-20 border-2 border-dashed rounded-xl'):
                    ui.icon('settings_input_component', size='64px').classes('text-slate-300')
                    ui.label('Enter system data to calculate SC currents').classes('text-slate-400 mt-4')

# --- Module: Earthing (IEEE 80) ---
def earthing_page():
    with ui.row().classes('w-full no-wrap'):
        with ui.column().classes('w-80 p-4 input-sidebar min-h-screen'):
            ui.label('FAULT PARAMETERS').classes('text-xs font-bold text-slate-400 mb-2')
            ui.number('If (A)', value=state.e_if_sym, on_change=lambda e: setattr(state, 'e_if_sym', e.value)).classes('w-full')
            ui.number('tf (s)', value=state.e_tf, step=0.05, on_change=lambda e: setattr(state, 'e_tf', e.value)).classes('w-full')
            ui.number('X/R', value=state.e_xr, on_change=lambda e: setattr(state, 'e_xr', e.value)).classes('w-full')
            ui.number('Sf', value=state.e_sf, step=0.01, on_change=lambda e: setattr(state, 'e_sf', e.value)).classes('w-full')
            
            ui.label('GRID GEOMETRY').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.number('Area (m²)', value=state.e_a, on_change=lambda e: setattr(state, 'e_a', e.value)).classes('w-full')
            ui.number('Burial h (m)', value=state.e_h, step=0.05, on_change=lambda e: setattr(state, 'e_h', e.value)).classes('w-full')
            ui.number('Length Lc (m)', value=state.e_lc, on_change=lambda e: setattr(state, 'e_lc', e.value)).classes('w-full')
            ui.number('nx', value=state.e_nx, step=1, on_change=lambda e: setattr(state, 'e_nx', e.value)).classes('w-full')
            ui.number('ny', value=state.e_ny, step=1, on_change=lambda e: setattr(state, 'e_ny', e.value)).classes('w-full')
            
            ui.label('SOIL DATA').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.number('ρ (Ohm.m)', value=state.e_rho, on_change=lambda e: setattr(state, 'e_rho', e.value)).classes('w-full')
            ui.number('ρ_s (Ohm.m)', value=state.e_rho_s, on_change=lambda e: setattr(state, 'e_rho_s', e.value)).classes('w-full')

            ui.button('CALCULATE', on_click=trigger_calc).classes('w-full mt-6 bg-red-600 text-white font-bold')

        with ui.column().classes('flex-grow p-8'):
            ui.label('Substation Earthing Safety (IEEE 80)').classes('text-2xl font-bold text-slate-800 mb-6')
            
            if state.calc_triggered:
                # Core IEEE 80 Logic
                ta_dc = state.e_xr / (2 * math.pi * 50)
                df = math.sqrt(1 + (ta_dc / state.e_tf) * (1 - math.exp(-2 * state.e_tf / ta_dc))) if state.e_tf > 0 else 1.0
                ig_sym = state.e_sf * state.e_if_sym
                ig_max = df * ig_sym
                
                lt = state.e_lc + state.e_lr # Simplified for brevity in this port
                rg = state.e_rho * (1/lt + (1/math.sqrt(20*state.e_a)) * (1 + 1/(1 + state.e_h * math.sqrt(20/state.e_a))))
                gpr = ig_max * rg
                
                cs = 1 - (0.09*(1 - state.e_rho/state.e_rho_s))/(2*state.e_hs + 0.09) if state.e_hs > 0 else 1.0
                ib = (0.116 if state.e_body_weight == 50 else 0.157) / math.sqrt(state.e_ts)
                e_touch_tol = (1000 + 1.5 * cs * state.e_rho_s) * ib
                e_step_tol = (1000 + 6.0 * cs * state.e_rho_s) * ib
                
                dx = state.e_lx / (state.e_nx - 1) if state.e_nx > 1 else state.e_lx
                dy = state.e_ly / (state.e_ny - 1) if state.e_ny > 1 else state.e_ly
                d_avg = (dx + dy) / 2.0
                n_geom = math.sqrt(state.e_nx * state.e_ny)
                ki = 0.644 + 0.148 * n_geom
                kh = math.sqrt(1 + state.e_h / 1.0)
                
                # Simplified Km calculation for port
                km = (1/(2*math.pi)) * (math.log(d_avg**2 / (16*state.e_h*state.e_d_cond)) + math.log((d_avg + 2*state.e_h)**2 / (8*d_avg*state.e_d_cond)) - state.e_h/(4*state.e_d_cond) + (1/kh)*math.log(8/(math.pi*(2*n_geom-1))))
                em = state.e_rho * ig_max * km * ki / state.e_lc
                
                touch_ok = em <= e_touch_tol

                with ui.row().classes('w-full gap-4'):
                    with ui.card().classes('flex-grow result-card'):
                        ui.label('Ground Resistance Rg').classes('text-xs font-bold text-slate-400')
                        ui.label(f'{rg:.4f} Ω').classes('metric-value')
                    with ui.card().classes('flex-grow result-card'):
                        ui.label('GPR').classes('text-xs font-bold text-slate-400')
                        ui.label(f'{gpr:.0f} V').classes('metric-value')
                    with ui.card().classes('flex-grow result-card'):
                        ui.label('Mesh Voltage Em').classes('text-xs font-bold text-slate-400')
                        ui.label(f'{em:.1f} V').classes('metric-value')
                    with ui.card().classes('flex-grow result-card'):
                        ui.label('Status').classes('text-xs font-bold text-slate-400')
                        ui.label('PASS' if touch_ok else 'FAIL').classes(f'metric-value {"text-green-600" if touch_ok else "text-red-600"}')

                with ui.expansion('Safety Verification Details', icon='verified_user').classes('w-full bg-white border mt-6'):
                    with ui.column().classes('w-full p-4'):
                        math_step('1. Body Current Limit', 
                                 'I_b', 
                                 f'\\frac{{0.116}}{{\\sqrt{{t_s}}}}', 
                                 f'{ib:.3f}', 'A')
                        
                        math_step('2. Allowable Touch Voltage', 
                                 'E_{touch.tol}', 
                                 '(1000 + 1.5 \\cdot C_s \\cdot \\rho_s) \\cdot I_b', 
                                 f'{e_touch_tol:.1f}', 'V')
                        
                        math_step('3. Actual Mesh Voltage', 
                                 'E_m', 
                                 '\\frac{\\rho \\cdot I_G \\cdot K_m \\cdot K_i}{L_c}', 
                                 f'{em:.1f}', 'V')

                        if touch_ok:
                            ui.label('✅ Safety criteria met for touch voltage.').classes('text-green-600 font-bold mt-2')
                        else:
                            ui.label('❌ Safety criteria NOT met. Increase grid density.').classes('text-red-600 font-bold mt-2')
                    
                with ui.expansion('Impedance & Currents', icon='bolt').classes('w-full bg-white border mt-2'):
                    with ui.column().classes('w-full p-4'):
                        math_step('Grid Resistance', 
                                 'R_g', 
                                 '\\rho \\left[ \\frac{1}{L_T} + \\frac{1}{\\sqrt{20A}} \\left( 1 + \\frac{1}{1+h\\sqrt{20/A}} \\right) \\right]', 
                                 f'{rg:.4f}', '\\Omega')
                        
                        math_step('Decrement Factor', 
                                 'D_f', 
                                 '\\sqrt{1 + \\frac{T_a}{t_f}(1 - e^{-2t_f/T_a})}', 
                                 f'{df:.3f}')
            else:
                with ui.column().classes('w-full items-center justify-center p-20 border-2 border-dashed rounded-xl'):
                    ui.icon('public', size='64px').classes('text-slate-300')
                    ui.label('Enter grid and soil data for safety analysis').classes('text-slate-400 mt-4')

# --- Module: Incomer Protection (ANSI 67) ---
def incomer_protection_page():
    with ui.row().classes('w-full no-wrap'):
        # Sidebar for inputs
        with ui.column().classes('w-80 p-4 input-sidebar min-h-screen'):
            ui.label('METHODOLOGY').classes('text-xs font-bold text-slate-400 mb-2')
            ui.select(["Methodic 1", "Methodic 2"], 
                      value=state.inc_method, 
                      on_change=lambda e: (setattr(state, 'inc_method', e.value), content.refresh())).classes('w-full mb-4')

            ui.label('TIME MODE').classes('text-xs font-bold text-slate-400 mb-2')
            ui.select(["Defined Time", "Inverse Time (TMS)"], 
                      value=state.inc_time_mode, 
                      on_change=lambda e: (setattr(state, 'inc_time_mode', e.value), content.refresh())).classes('w-full mb-4')

            ui.label('LOAD DATA').classes('text-xs font-bold text-slate-400 mb-2')
            ui.number('I_rab.own.max (A)', value=state.inc_i_rab_own_max, on_change=lambda e: setattr(state, 'inc_i_rab_own_max', e.value)).classes('w-full')
            ui.number('I_rab.neighbor.max (A)', value=state.inc_i_rab_neighbor_max, on_change=lambda e: setattr(state, 'inc_i_rab_neighbor_max', e.value)).classes('w-full')
            
            ui.label('COORDINATION (SV)').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.number('I_sz.SV (A)', value=state.inc_i_sz_sv, on_change=lambda e: setattr(state, 'inc_i_sz_sv', e.value)).classes('w-full')
            ui.number('t_sz.SV (s)', value=state.inc_t_sz_sv, step=0.1, on_change=lambda e: setattr(state, 'inc_t_sz_sv', e.value)).classes('w-full')
            
            if state.inc_time_mode == "Defined Time":
                ui.label('TIME PARAMETERS').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
                ui.number('Delta t (s)', value=state.inc_delta_t, step=0.05, on_change=lambda e: setattr(state, 'inc_delta_t', e.value)).classes('w-full mt-2')

            ui.label('FAULT & COEFFICIENTS').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
            ui.number('Min SC (I_k.min) (A)', value=state.inc_i_k_min, on_change=lambda e: setattr(state, 'inc_i_k_min', e.value)).classes('w-full')
            ui.number('K_v', value=state.inc_k_v, step=0.005, on_change=lambda e: setattr(state, 'inc_k_v', e.value)).classes('w-full')

            if state.inc_method == "Methodic 1":
                ui.number('K_szp', value=state.inc_k_szp, step=0.1, on_change=lambda e: setattr(state, 'inc_k_szp', e.value)).classes('w-full')
                ui.number('K_ots', value=state.inc_k_ots, step=0.05, on_change=lambda e: setattr(state, 'inc_k_ots', e.value)).classes('w-full')
                ui.number('K\'_otv', value=state.inc_k_otv, step=0.1, on_change=lambda e: setattr(state, 'inc_k_otv', e.value)).classes('w-full')
                ui.number('K_tok', value=state.inc_k_tok, step=0.1, on_change=lambda e: setattr(state, 'inc_k_tok', e.value)).classes('w-full')
            else:
                ui.label('MTZ COEFFICIENTS').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
                ui.number('k_n (Load)', value=state.inc_m2_k_n_load, step=0.1, on_change=lambda e: setattr(state, 'inc_m2_k_n_load', e.value)).classes('w-full')
                ui.number('k_n (ATS)', value=state.inc_m2_k_n_ats, step=0.1, on_change=lambda e: setattr(state, 'inc_m2_k_n_ats', e.value)).classes('w-full')
                ui.number('k_szp (ATS)', value=state.inc_m2_k_szp, step=0.1, on_change=lambda e: setattr(state, 'inc_m2_k_szp', e.value)).classes('w-full')
                ui.number('k_n (Selectivity)', value=state.inc_m2_k_n_sel, step=0.1, on_change=lambda e: setattr(state, 'inc_m2_k_n_sel', e.value)).classes('w-full')
            
            if state.inc_time_mode == "Inverse Time (TMS)":
                ui.label('INVERSE TIME (TMS)').classes('text-xs font-bold text-slate-400 mt-4 mb-2')
                ui.select(list(CURVES.keys()), label='Curve Type', value=state.inc_curve_type, on_change=lambda e: setattr(state, 'inc_curve_type', e.value)).classes('w-full')
                ui.number('I_sc (A)', value=state.inc_i_sc, step=100, on_change=lambda e: setattr(state, 'inc_i_sc', e.value)).classes('w-full')
                ui.number('Req. Time (s)', value=state.inc_t_op, step=0.1, on_change=lambda e: setattr(state, 'inc_t_op', e.value)).classes('w-full')

            ui.button('CALCULATE', on_click=trigger_calc).classes('w-full mt-6 bg-red-600 text-white font-bold')

        # Main content area
        with ui.column().classes('flex-grow p-8'):
            ui.label(f'Incomer Protection Settings (ANSI 67)').classes('text-2xl font-bold text-slate-800 mb-6')
            
            if state.calc_triggered:
                tms_inc = None
                if state.inc_method == "Methodic 1":
                    # M1 Calculations
                    i_sz_bb1 = (state.inc_k_ots / state.inc_k_v) * (state.inc_k_szp * state.inc_i_rab_neighbor_max + state.inc_k_otv * state.inc_i_rab_own_max)
                    i_sz_bb2 = (state.inc_k_ots / state.inc_k_tok) * (state.inc_i_sz_sv + state.inc_i_rab_own_max)
                    i_sz_bb = max(i_sz_bb1, i_sz_bb2)
                    threshold = 1.5
                else:
                    # M2 Calculations
                    i_sz_bb1 = (state.inc_m2_k_n_load / state.inc_k_v) * state.inc_i_rab_own_max
                    i_sz_bb2 = (state.inc_m2_k_n_ats / state.inc_k_v) * (state.inc_i_rab_own_max + state.inc_m2_k_szp * state.inc_i_rab_neighbor_max)
                    i_sz_bb3 = state.inc_m2_k_n_sel * state.inc_i_sz_sv
                    i_sz_bb = max(i_sz_bb1, i_sz_bb2, i_sz_bb3)
                    threshold = 1.2
                
                t_sz_bb = state.inc_t_sz_sv + state.inc_delta_t
                
                # Time Mode Logic
                if state.inc_time_mode == "Inverse Time (TMS)":
                    if state.inc_i_sc > i_sz_bb:
                        c = CURVES[state.inc_curve_type]
                        i_rel = state.inc_i_sc / i_sz_bb
                        denominator = (c["A"] / ((i_rel ** c["c"]) - 1)) + c["B"]
                        tms_inc = state.inc_t_op / denominator
                
                k_s_inc = (math.sqrt(3)/2 * state.inc_i_k_min) / i_sz_bb if i_sz_bb > 0 else 0

                with ui.column().classes('w-full gap-4'):
                    # Metrics Row
                    with ui.row().classes('w-full justify-between gap-4'):
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('I_pickup (Incomer)').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{i_sz_bb:.1f} A').classes('metric-value')
                        
                        if state.inc_time_mode == "Inverse Time (TMS)":
                            with ui.card().classes('flex-grow result-card'):
                                ui.label('Calculated TMS').classes('text-xs font-bold text-slate-400')
                                ui.label(f'{tms_inc:.3f}' if tms_inc else 'N/A').classes('metric-value')
                        else:
                            with ui.card().classes('flex-grow result-card'):
                                ui.label('Time Delay (t_sz)').classes('text-xs font-bold text-slate-400')
                                ui.label(f'{t_sz_bb:.2f} s').classes('metric-value')
                        
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('Sensitivity Ks').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{k_s_inc:.2f}').classes('metric-value')
                        with ui.card().classes('flex-grow result-card'):
                            ui.label('Min Ks Req.').classes('text-xs font-bold text-slate-400')
                            ui.label(f'{threshold}').classes('metric-value text-slate-600')

                    # Detailed Steps
                    with ui.expansion('Step-by-Step Calculations', icon='calculate').classes('w-full bg-white border').props('value=True'):
                        with ui.column().classes('w-full p-4'):
                            if state.inc_method == "Methodic 1":
                                math_step('1. Condition 1 (ATS Overload)',
                                         'I<sub>sz.BB(1)</sub>',
                                         frac('K<sub>ots</sub>', 'K<sub>v</sub>') + f' &middot; (K<sub>szp</sub> &middot; I<sub>rab.neighbor.max</sub> + K\'<sub>otv</sub> &middot; I<sub>rab.own.max</sub>) = ' +
                                         frac(f'{state.inc_k_ots}', f'{state.inc_k_v}') + f' &middot; ({state.inc_k_szp} &middot; {state.inc_i_rab_neighbor_max} + {state.inc_k_otv} &middot; {state.inc_i_rab_own_max})',
                                         f'{i_sz_bb1:.1f}', 'A')
                                math_step('2. Condition 2 (Selectivity with SV)',
                                         'I<sub>sz.BB(2)</sub>',
                                         frac('K<sub>ots</sub>', 'K<sub>tok</sub>') + f' &middot; (I<sub>sz.SV</sub> + I<sub>rab.own.max</sub>) = ' +
                                         frac(f'{state.inc_k_ots}', f'{state.inc_k_tok}') + f' &middot; ({state.inc_i_sz_sv} + {state.inc_i_rab_own_max})',
                                         f'{i_sz_bb2:.1f}', 'A')
                                math_step('3. Final Pickup Current',
                                         'I<sub>sz.BB</sub>',
                                         f'max({i_sz_bb1:.1f}, {i_sz_bb2:.1f})',
                                         f'{i_sz_bb:.1f}', 'A')
                            else:
                                math_step('1. Condition 1 (Load)',
                                         'I<sub>sz.BB(1)</sub>',
                                         frac('k<sub>n</sub>', 'k<sub>v</sub>') + f' &middot; I<sub>rab.max</sub> = ' +
                                         frac(f'{state.inc_m2_k_n_load}', f'{state.inc_k_v}') + f' &middot; {state.inc_i_rab_own_max}',
                                         f'{i_sz_bb1:.1f}', 'A')
                                math_step('2. Condition 2 (Self-start with ATS)',
                                         'I<sub>sz.BB(2)</sub>',
                                         frac('k<sub>n</sub>', 'k<sub>v</sub>') + f' &middot; (I<sub>rab.max.1</sub> + k<sub>szp</sub> &middot; I<sub>rab.max.2</sub>) = ' +
                                         frac(f'{state.inc_m2_k_n_ats}', f'{state.inc_k_v}') + f' &middot; ({state.inc_i_rab_own_max} + {state.inc_m2_k_szp} &middot; {state.inc_i_rab_neighbor_max})',
                                         f'{i_sz_bb2:.1f}', 'A')
                                math_step('3. Condition 3 (Selectivity with SV)',
                                         'I<sub>sz.BB(3)</sub>',
                                         f'k<sub>n</sub> &middot; I<sub>max.MTZ.SV</sub> = {state.inc_m2_k_n_sel} &middot; {state.inc_i_sz_sv}',
                                         f'{i_sz_bb3:.1f}', 'A')
                                math_step('4. Final Pickup Current',
                                         'I<sub>sz.BB</sub>',
                                         f'max({i_sz_bb1:.1f}, {i_sz_bb2:.1f}, {i_sz_bb3:.1f})',
                                         f'{i_sz_bb:.1f}', 'A')

                            if state.inc_time_mode == "Inverse Time (TMS)":
                                if tms_inc:
                                    math_step('5. Time Multiplier Setting',
                                             'TMS',
                                             frac('t<sub>op</sub>', f'(A / ((I<sub>sc</sub>/I<sub>pickup</sub>)<sup>c</sup> - 1)) + B'),
                                             f'{tms_inc:.3f}')
                            else:
                                math_step(f'4. Time Delay',
                                         't<sub>sz.BB</sub>',
                                         f't<sub>sz.SV</sub> + &Delta;t = {state.inc_t_sz_sv} + {state.inc_delta_t}',
                                         f'{t_sz_bb:.2f}', 's')

                    # Sensitivity Check
                    with ui.expansion('Sensitivity Analysis', icon='security').classes('w-full bg-white border'):
                        with ui.column().classes('w-full p-4'):
                            math_step('Sensitivity Coefficient',
                                     'K<sub>s</sub>',
                                     frac('&radic;3/2 &middot; I<sub>k.min</sub>', 'I<sub>sz.BB</sub>') + f' = ' +
                                     frac(f'0.866 &middot; {state.inc_i_k_min}', f'{i_sz_bb:.1f}'),
                                     f'{k_s_inc:.2f}')
                            
                            if k_s_inc >= threshold:
                                ui.label(f'✅ Sensitivity confirmed (Ks ≥ {threshold})').classes('text-green-600 font-bold')
                            else:
                                ui.label(f'❌ Sensitivity insufficient (Ks < {threshold})').classes('text-red-600 font-bold')
            else:
                with ui.column().classes('w-full items-center justify-center p-20 border-2 border-dashed rounded-xl'):
                    ui.icon('bolt', size='64px').classes('text-slate-300')
                    ui.label('Enter load and coordination data then click Calculate').classes('text-slate-400 mt-4')


# --- Main Layout ---
@ui.refreshable
def content():
    if state.current_tool == "transformer":
        transformer_protection_page()
    elif state.current_tool == "generator":
        generator_protection_page()
    elif state.current_tool == "selectivity":
        selectivity_page()
    elif state.current_tool == "cable":
        cable_page()
    elif state.current_tool == "sc_generator":
        sc_generator_page()
    elif state.current_tool == "earthing":
        earthing_page()
    elif state.current_tool == "incomer":
        incomer_protection_page()

    else:
        with ui.column().classes('w-full items-center p-20'):
            ui.label(f'{state.current_tool} Module').classes('text-3xl font-bold text-slate-300')
            ui.label('Module implementation in progress...').classes('text-slate-400')

with ui.header(elevated=True).style('background-color: white; color: #333;').classes('items-center px-4'):
    ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=black')
    ui.label('ENGINEERING TOOLS').classes('font-bold text-lg tracking-widest')
    ui.space()
    ui.label('v2.0 (NiceGUI)').classes('text-xs text-slate-400')

with ui.left_drawer(value=True, bordered=True).classes('bg-white w-72') as left_drawer:
    with ui.column().classes('w-full p-4 items-center'):
        ui.icon('bolt', size='48px').classes('text-red-600')
        ui.label('RELAY CALCULATOR').classes('font-bold text-slate-800 tracking-tighter')
    
    ui.separator()
    ui.label('PROTECTION MODULES').classes('text-[10px] font-bold text-slate-400 p-4 pb-0 tracking-widest')
    
    def set_tool(tool_id):
        state.current_tool = tool_id
        reset_calc()

    modules = [
        ("transformer", "Transformer", "(ANSI 51)", "transformer"),
        ("generator", "Generator", "(ANSI 67)", "power"),
        ("selectivity", "Selectivity", "ANALYSIS", "analytics"),
        ("cable", "Cable Sizing", "IEC/BS", "electrical_services"),
        ("sc_generator", "SC Generator", "(IEC 60909)", "settings_input_component"),
        ("earthing", "Earthing", "(IEEE 80)", "public"),
        ("incomer", "Incomer", "(ANSI 67)", "vpn_key")
    ]
    
    for tool_id, name, standard, icon in modules:
        is_active = state.current_tool == tool_id
        with ui.button(on_click=lambda t=tool_id: set_tool(t)) \
            .props('flat') \
            .classes('nav-button px-4') \
            .classes('nav-button-active' if is_active else 'text-slate-600'):
            with ui.row().classes('w-full items-center justify-between no-wrap'):
                with ui.row().classes('items-center gap-3 no-wrap'):
                    ui.icon(icon, size='20px')
                    ui.label(name).classes('nav-label')
                ui.label(standard).classes('nav-standard')


content()

ui.run(title='Engineering Tool', port=8080, dark=False)
