import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import math

# ABB Style Configuration
st.set_page_config(page_title="Engineering Tool", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* Red Accent Header */
    .abb-header {
        background-color: #FF0000;
        height: 4px;
        width: 100%;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 1000;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #F2F2F2 !important;
        border-right: 1px solid #E6E6E6;
    }
    
    /* Button Styling */
    .stButton>button {
        border-radius: 2px !important;
        border: 1px solid #333333 !important;
        color: #333333 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        border-color: #FF0000 !important;
        color: #FF0000 !important;
        background-color: rgba(255, 0, 0, 0.05) !important;
    }
    
    /* Primary Action Button (ABB Style) */
    div[data-testid="stFormSubmitButton"] button, 
    button[kind="primary"] {
        background-color: #FF0000 !important;
        color: white !important;
        border: none !important;
    }
    
    div[data-testid="stFormSubmitButton"] button:hover,
    button[kind="primary"]:hover {
        background-color: #CC0000 !important;
        color: white !important;
    }
    
    /* Card/Expander Styling */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border-top: 1px solid #EEEEEE !important;
        border-bottom: 1px solid #EEEEEE !important;
        font-size: 1.1rem !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #FF0000 !important;
    }
</style>
<div class="abb-header"></div>
""", unsafe_allow_html=True)
import plotly.graph_objects as go
import pandas as pd

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
        "rho": 0.0175,  # Ohm*mm^2/m
        "reactance": 0.08, # Ohm/km
        "iz": { # Section: Permissible current (A) in air
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

if 'current_tool' not in st.session_state:
    st.session_state.current_tool = "МТЗ Трансформатора (ANSI 51)"

if 'calc_triggered' not in st.session_state:
    st.session_state.calc_triggered = False

def reset_calc():
    st.session_state.calc_triggered = False

st.markdown("<h3 style='text-align: center; color: #333333; margin-bottom: 25px;'>ENGINEERING TOOL</h3>", unsafe_allow_html=True)
col1, col2, col3, col4, col5, col6 = st.columns(6)
if col1.button("TRANSFORMER PROTECTION (ANSI 51)", use_container_width=True):
    st.session_state.current_tool = "МТЗ Трансформатора (ANSI 51)"
    reset_calc()
if col2.button("GENERATOR PROTECTION (ANSI 67)", use_container_width=True):
    st.session_state.current_tool = "МТЗ Генератора (ANSI 67)"
    reset_calc()
if col3.button("📊 SELECTIVITY", use_container_width=True):
    st.session_state.current_tool = "Проверка селективности"
    reset_calc()
if col4.button("🔌 CABLE", use_container_width=True):
    st.session_state.current_tool = "Выбор сечения кабеля"
    reset_calc()
if col5.button("⚡ SC GENERATOR (IEC 60909)", use_container_width=True):
    st.session_state.current_tool = "SC Generator (IEC 60909)"
    reset_calc()
if col6.button("🌍 EARTHING (IEEE 80)", use_container_width=True):
    st.session_state.current_tool = "Earthing (IEEE 80)"
    reset_calc()

st.markdown("---")
tool = st.session_state.current_tool

if tool == "МТЗ Трансформатора (ANSI 51)":
    st.title("⚡ Расчет уставок защиты трансформатора")
    
    # Боковая панель - Исходные данные
    st.sidebar.header("Исходные данные трансформатора")
    s_nom = st.sidebar.number_input("Мощность трансформатора (кВА)", value=1000)
    u_nom = st.sidebar.number_input("Напряжение ВН (кВ)", value=10.5)
    
    st.sidebar.header("Параметры ТТ (Трансформатора тока)")
    ct_primary = st.sidebar.number_input("Первичный ток ТТ (А)", value=100)
    ct_secondary = st.sidebar.selectbox("Вторичный ток ТТ (А)", [5, 1])
    
    st.sidebar.header("Коэффициенты для МТЗ (ANSI 51)")
    k_ots = st.sidebar.number_input("Коэффициент отстройки (Kотс)", value=1.2, step=0.1)
    k_szp = st.sidebar.number_input("Коэффициент самозапуска (Kсзп)", value=1.3, step=0.1)
    k_v = st.sidebar.number_input("Коэффициент возврата (Kв)", value=0.95, step=0.01)
    k_per = st.sidebar.number_input("Коэффициент перегрузки (Kпер)", value=1.4, step=0.1)
    
    st.sidebar.header("Проверка чувствительности")
    i_kz_min = st.sidebar.number_input("Мин. ток КЗ (I^{(2)}_{КЗ.мин}, А)", value=800.0, step=50.0)
    
    st.sidebar.header("Параметры для расчета TMS (Выдержка времени)")
    curve_type = st.sidebar.selectbox("Тип характеристики", list(CURVES.keys()))
    i_sc = st.sidebar.number_input("Ток КЗ для согласования (I_sc, А)", value=2000.0, step=100.0)
    t_op = st.sidebar.number_input("Требуемое время срабатывания (t_op, с)", value=0.5, step=0.1)
    
    # Расчет
    i_nom = s_nom / (1.732 * u_nom)
    i_rab_max = i_nom * k_per
    i_szp = (k_ots * k_szp / k_v) * i_rab_max
    set_value = i_szp / ct_primary
    
    st.sidebar.header("Ручная корректировка уставки")
    manual_start_value = st.sidebar.checkbox("Изменить Start value вручную", value=False)
    if manual_start_value:
        final_set_value = st.sidebar.number_input("Пользовательское значение Start value (x I_n)", value=float(set_value), step=0.01)
        i_pickup_actual = final_set_value * ct_primary
    else:
        final_set_value = set_value
        i_pickup_actual = i_szp
    
    k_s = i_kz_min / i_pickup_actual
    
    if i_sc > i_pickup_actual:
        A_const = CURVES[curve_type]["A"]
        B_const = CURVES[curve_type]["B"]
        c_const = CURVES[curve_type]["c"]
        i_rel = i_sc / i_pickup_actual
        denominator = (A_const / ((i_rel ** c_const) - 1)) + B_const
        tms_calc = t_op / denominator
    else:
        tms_calc = None
    
    # Кнопка запуска расчета
    if st.button("🚀 Выполнить расчет", type="primary", use_container_width=True):
        st.session_state.calc_triggered = True

    # Вывод
    if st.session_state.calc_triggered:
        with st.expander("Пошаговый расчет токов трансформатора", expanded=False):
            st.subheader("1. Определение номинального тока")
            st.latex(r"I_{nom} = \frac{S_{nom}}{\sqrt{3} \cdot U_{nom}}")
            st.success(f"I_nom = {i_nom:.2f} А")
            st.subheader("2. Расчет максимального рабочего тока")
            st.latex(r"I_{rab.max} = I_{nom} \cdot K_{per}")
            st.info(f"I_{{rab.max}} = {i_rab_max:.2f} А")
            st.subheader("3. Расчет тока срабатывания защиты (МТЗ)")
            st.latex(r"I_{szp} = \frac{K_{ots} \cdot K_{szp}}{K_{v}} \cdot I_{rab.max}")
            st.success(f"I_{{szp}} = {i_szp:.2f} А")
        
        st.header("Результаты расчета уставок")
        with st.expander("Уставка PHLPTOC для терминала ABB REF615", expanded=True):
            if manual_start_value:
                st.info(f"Расчетное значение: {set_value:.3f} x I_n")
                st.warning(f"Принятое вручную Start value = {final_set_value:.3f} x I_n")
                st.markdown(f"Фактический первичный ток срабатывания $I_{{pickup\\_actual}} = {i_pickup_actual:.2f}$ А")
            else:
                st.latex(r"Start\ value = \frac{I_{szp}}{I_{1nom.TT}}")
                st.warning(f"Start value = {final_set_value:.3f} x I_n")
        
        with st.expander("Проверка чувствительности защиты", expanded=True):
            st.latex(r"K_s = \frac{I^{(2)}_{K3.min}}{I_{szp\_actual}}")
            st.info(f"Коэффициент чувствительности K_s = {k_s:.2f}")
            if k_s >= 1.5:
                st.success("✅ Условие выполняется: $K_s \\geq 1.5$. Чувствительность обеспечена.")
            else:
                st.error("❌ Условие не выполняется: $K_s < 1.5$.")
                st.warning("Внимание: Защита должна выполняться с блокировкой по минимальному напряжению.")
        
        with st.expander("Расчет уставки выдержки времени (TMS / k)", expanded=True):
            st.markdown(f"Выбрана кривая: **{curve_type}**")
            if tms_calc is not None:
                st.success(f"Требуемое значение TMS = {tms_calc:.3f}")
                st.markdown("---")
                st.markdown("**Ожидаемое время срабатывания защиты при различных кратностях тока:**")
                def calc_time(multiple):
                    A = CURVES[curve_type]["A"]; B = CURVES[curve_type]["B"]; c = CURVES[curve_type]["c"]
                    if multiple <= 1: return None
                    return (A / (multiple**c - 1) + B) * tms_calc
                col1, col2, col3 = st.columns(3)
                t_3x = calc_time(3); col1.metric("При 3 × I>", f"{t_3x:.2f} с" if t_3x else "Н/Д")
                t_5x = calc_time(5); col2.metric("При 5 × I>", f"{t_5x:.2f} с" if t_5x else "Н/Д")
                t_8x = calc_time(8); col3.metric("При 8 × I>", f"{t_8x:.2f} с" if t_8x else "Н/Д")
            else:
                st.error("Ошибка: Ток КЗ должен быть больше тока срабатывания защиты!")

elif tool == "МТЗ Генератора (ANSI 67)":
    st.title("⚡ Расчет направленной МТЗ генератора (ANSI 67)")
    st.sidebar.header("Исходные данные генератора")
    i_nom_g = st.sidebar.number_input("Номинальный ток генератора (I_ном.г, А)", value=2000.0, step=100.0)
    k_ots_g = st.sidebar.number_input("Коэффициент отстройки (k_отс)", value=1.2, step=0.1)
    k_v_g = st.sidebar.number_input("Коэффициент возврата (k_в)", value=0.935, step=0.005)
    i_max_mtz_ol = st.sidebar.number_input("Макс. уставка МТЗ секц. выключателя (А)", value=1500.0, step=100.0)
    k_tt = st.sidebar.number_input("Коэффициент трансформации ТТ (k_ТТ)", value=400.0, step=10.0)
    i_kz_min_g = st.sidebar.number_input("Ток мин. двухфазного КЗ (А)", value=5000.0, step=100.0)
    curve_type_g = st.sidebar.selectbox("Тип характеристики", list(CURVES.keys()), index=2)
    t_mtz_ol = st.sidebar.number_input("Время МТЗ фидера (с)", value=0.5, step=0.1)
    delta_t = st.sidebar.number_input("Ступень селективности (Δt, с)", value=0.3, step=0.1)
    
    i_perv_sz1 = (k_ots_g / k_v_g) * i_nom_g
    i_perv_sz2 = k_ots_g * i_max_mtz_ol
    i_perv_sz = max(i_perv_sz1, i_perv_sz2)
    i_s = i_perv_sz / k_tt
    k_s_g = i_kz_min_g / i_perv_sz if i_perv_sz > 0 else 0
    t_d_i = t_mtz_ol + delta_t
    
    if i_kz_min_g > i_perv_sz:
        A_const_g = CURVES[curve_type_g]["A"]; B_const_g = CURVES[curve_type_g]["B"]; c_const_g = CURVES[curve_type_g]["c"]
        i_rel_g = i_kz_min_g / i_perv_sz
        denominator_g = (A_const_g / ((i_rel_g ** c_const_g) - 1)) + B_const_g
        tms_g = t_d_i / denominator_g
    else:
        tms_g = None
        
    # Кнопка запуска расчета
    if st.button("🚀 Выполнить расчет", type="primary", key="gen_calc_btn", use_container_width=True):
        st.session_state.calc_triggered = True

    if st.session_state.calc_triggered:
        with st.expander("Пошаговый расчет тока срабатывания", expanded=True):
            st.latex(r"I_{perv.sz} = \max(I_{perv.sz1}, I_{perv.sz2})")
            st.success(f"I_perv.sz = {i_perv_sz:.2f} А")
        with st.expander("Вторичный ток и проверка чувствительности", expanded=True):
            st.warning(f"I_s = {i_s:.3f} А")
            st.info(f"Коэффициент чувствительности K_s = {k_s_g:.2f}")
        with st.expander("Расчет уставки выдержки времени (TMS)", expanded=True):
            if tms_g is not None:
                st.success(f"Требуемое значение TMS = {tms_g:.3f}")
                st.markdown("---")
                st.markdown("**Ожидаемое время срабатывания защиты при различных кратностях тока:**")
                def calc_time_g(multiple):
                    A = CURVES[curve_type_g]["A"]; B = CURVES[curve_type_g]["B"]; c = CURVES[curve_type_g]["c"]
                    if multiple <= 1: return None
                    return (A / (multiple**c - 1) + B) * tms_g
                col1, col2, col3 = st.columns(3)
                t_3x_g = calc_time_g(3); col1.metric("При 3 × I>", f"{t_3x_g:.2f} с" if t_3x_g else "Н/Д")
                t_5x_g = calc_time_g(5); col2.metric("При 5 × I>", f"{t_5x_g:.2f} с" if t_5x_g else "Н/Д")
                t_8x_g = calc_time_g(8); col3.metric("При 8 × I>", f"{t_8x_g:.2f} с" if t_8x_g else "Н/Д")
            else:
                st.error("Ошибка расчета TMS!")

elif tool == "Проверка селективности":
    st.title("📊 Проверка селективности защит")
    
    col_ds, col_us = st.columns(2)
    
    with col_ds:
        st.header("Нижестоящая защита (Downstream)")
        ds_name = st.text_input("Название", value="Q1 (Фидер)")
        ds_curve = st.selectbox("Характеристика", list(CURVES.keys()), key="ds_curve")
        ds_pickup = st.number_input("Ток срабатывания (А)", value=200.0, step=10.0, key="ds_pickup")
        ds_tms = st.number_input("Уставка TMS", value=0.1, step=0.01, format="%.3f", key="ds_tms")
        
    with col_us:
        st.header("Вышестоящая защита (Upstream)")
        us_name = st.text_input("Название", value="Q0 (Ввод)")
        us_curve = st.selectbox("Характеристика", list(CURVES.keys()), key="us_curve")
        us_pickup = st.number_input("Ток срабатывания (А)", value=400.0, step=10.0, key="us_pickup")
        us_tms = st.number_input("Уставка TMS", value=0.2, step=0.01, format="%.3f", key="us_tms")

    st.sidebar.header("Параметры анализа")
    i_min_fault = st.sidebar.number_input("Мин. ток КЗ для анализа (А)", value=float(min(ds_pickup, us_pickup) * 1.5), step=100.0)
    i_max_fault = st.sidebar.number_input("Макс. ток КЗ для анализа (А)", value=5000.0, step=500.0)
    delta_t_req = st.sidebar.number_input("Требуемая ступень селективности (с)", value=0.3, step=0.05)

    if st.button("🚀 Выполнить расчет", type="primary", key="sel_calc_btn", use_container_width=True):
        st.session_state.calc_triggered = True

    if st.session_state.calc_triggered:
        # Генерация данных для графиков
        currents = np.logspace(np.log10(min(ds_pickup, us_pickup) * 1.1), np.log10(i_max_fault), 100)
        
        def get_time(current, pickup, tms, curve_name):
            A = CURVES[curve_name]["A"]; B = CURVES[curve_name]["B"]; c = CURVES[curve_name]["c"]
            multiple = current / pickup
            if multiple <= 1.001: return 100 # Очень большое время
            return (A / (multiple**c - 1) + B) * tms

        ds_times = [get_time(i, ds_pickup, ds_tms, ds_curve) for i in currents]
        us_times = [get_time(i, us_pickup, us_tms, us_curve) for i in currents]

        # Построение графика
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=currents, y=ds_times, name=ds_name, line=dict(color='blue', width=3)))
        fig.add_trace(go.Scatter(x=currents, y=us_times, name=us_name, line=dict(color='red', width=3)))

        fig.update_xaxes(type="log", title_text="Ток (А)", gridcolor='lightgrey')
        fig.update_yaxes(type="log", title_text="Время (с)", gridcolor='lightgrey', range=[np.log10(0.01), np.log10(100)])
        fig.update_layout(
            title="Карта селективности (Логарифмический масштаб)",
            hovermode="x unified",
            template="plotly_white",
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)

        # Анализ селективности
        st.header("Анализ координации")
        
        # Проверка при конкретных токах
        test_currents = [i_min_fault, (i_min_fault + i_max_fault)/2, i_max_fault]
        cols = st.columns(len(test_currents))
        
        for i, curr in enumerate(test_currents):
            t_ds = get_time(curr, ds_pickup, ds_tms, ds_curve)
            t_us = get_time(curr, us_pickup, us_tms, us_curve)
            margin = t_us - t_ds
            
            with cols[i]:
                st.metric(f"При {curr:.0f} А", f"Δt = {margin:.2f} с")
                if margin >= delta_t_req:
                    st.success("✅ Селективно")
                else:
                    st.error("❌ Неселективно")

        if all((get_time(i, us_pickup, us_tms, us_curve) - get_time(i, ds_pickup, ds_tms, ds_curve)) >= delta_t_req for i in currents):
            st.success(f"✅ Полная селективность обеспечена во всем диапазоне с запасом не менее {delta_t_req} с.")
        else:
            st.warning("⚠️ Внимание: В некоторых режимах селективность может быть нарушена.")

elif tool == "Выбор сечения кабеля":
    st.title("🔌 Выбор сечения кабеля и расчет падения напряжения")
    
    st.sidebar.header("Параметры нагрузки")
    p_load = st.sidebar.number_input("Мощность нагрузки (кВт)", value=50.0, step=1.0)
    u_nom_c = st.sidebar.number_input("Напряжение сети (В)", value=400, step=10)
    cos_phi = st.sidebar.number_input("Коэффициент мощности (cos φ)", value=0.85, min_value=0.5, max_value=1.0, step=0.01)
    
    st.sidebar.header("Параметры линии")
    length = st.sidebar.number_input("Длина линии (м)", value=100.0, step=10.0)
    material = st.sidebar.radio("Материал жил", ["Cu", "Al"])
    du_max = st.sidebar.number_input("Доп. падение напряжения (%)", value=5.0, step=0.5)
    
    # Расчет тока
    i_load = (p_load * 1000) / (math.sqrt(3) * u_nom_c * cos_phi)
    
    # Кнопка запуска расчета
    if st.button("🚀 Выполнить расчет", type="primary", key="cable_calc_btn", use_container_width=True):
        st.session_state.calc_triggered = True
        
    if st.session_state.calc_triggered:
        st.header("Результаты выбора кабеля")
        
        # 1. Выбор по току
        available_sections = sorted(CABLE_DATA[material]["iz"].keys())
        selected_section = None
        for s in available_sections:
            if CABLE_DATA[material]["iz"][s] >= i_load:
                selected_section = s
                break
        
        if selected_section is None:
            st.error("Ошибка: Ток нагрузки превышает возможности самого большого сечения в базе!")
        else:
            # 2. Проверка по падению напряжения
            rho = CABLE_DATA[material]["rho"]
            x_react = CABLE_DATA[material]["reactance"]
            sin_phi = math.sqrt(1 - cos_phi**2)
            
            while True:
                r_line = (rho / selected_section) * (length / 1000) * 1000 # Ohm
                x_line = (x_react) * (length / 1000) # Ohm
                
                delta_u = math.sqrt(3) * i_load * ( (rho/selected_section * cos_phi) + (x_react/1000 * sin_phi) ) * length
                delta_u_pct = (delta_u / u_nom_c) * 100
                
                if delta_u_pct <= du_max:
                    break
                
                # Ищем следующее сечение
                idx = available_sections.index(selected_section)
                if idx + 1 < len(available_sections):
                    selected_section = available_sections[idx + 1]
                else:
                    st.warning(f"Даже максимальное сечение {selected_section} мм² не удовлетворяет условию по падению напряжения.")
                    break
            
            # Вывод результатов
            col1, col2, col3 = st.columns(3)
            col1.metric("Расчетный ток", f"{i_load:.2f} А")
            col2.metric("Рекомендованное сечение", f"{selected_section} мм²")
            col3.metric("Падение напряжения", f"{delta_u_pct:.2f} %")
            
            st.markdown("---")
            
            with st.expander("Подробности расчета", expanded=True):
                st.subheader("1. Расчет тока нагрузки")
                st.latex(r"I = \frac{P \cdot 1000}{\sqrt{3} \cdot U \cdot \cos \phi}")
                st.info(f"I = {i_load:.2f} А")
                
                st.subheader("2. Выбор сечения по нагреву")
                st.write(f"Минимальное сечение для тока {i_load:.2f} А: **{selected_section} мм²**")
                st.write(f"Допустимый ток выбранного кабеля: **{CABLE_DATA[material]['iz'][selected_section]} А**")
                
                st.subheader("3. Проверка падения напряжения")
                st.latex(r"\Delta U\% = \frac{\sqrt{3} \cdot I \cdot (R \cdot \cos \phi + X \cdot \sin \phi) \cdot L}{U_{nom}} \cdot 100")
                if delta_u_pct <= du_max:
                    st.success(f"✅ Условие выполнено: {delta_u_pct:.2f}% ≤ {du_max}%")
                else:
                    st.error(f"❌ Условие не выполнено: {delta_u_pct:.2f}% > {du_max}%")
            
            # Таблица доступных сечений
            st.subheader("Таблица допустимых токов (в воздухе)")
            df_iz = pd.DataFrame({
                "Сечение (мм²)": list(CABLE_DATA[material]["iz"].keys()),
                "Ток Iz (А)": list(CABLE_DATA[material]["iz"].values())
            })
            st.dataframe(df_iz, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────
# SC GENERATOR — IEC 60909
# ─────────────────────────────────────────────────────────────────
elif tool == "SC Generator (IEC 60909)":
    st.title("⚡ Short-Circuit Current Calculation — IEC 60909")
    st.caption("IEC 60909-0:2016 | Initial symmetrical short-circuit current from a synchronous generator")

    # ── Sidebar inputs ──────────────────────────────────────────
    st.sidebar.header("Generator Data")
    s_n    = st.sidebar.number_input("Rated Power S_n (MVA)", value=100.0, step=1.0, min_value=0.1)
    u_rG   = st.sidebar.number_input("Rated Voltage U_rG (kV)", value=11.0, step=0.1, min_value=0.1)
    cos_phi_G = st.sidebar.number_input("Rated Power Factor cos φ", value=0.85, min_value=0.1, max_value=1.0, step=0.01)
    x_d_pu = st.sidebar.number_input("Subtransient Reactance X\"d (p.u.)", value=0.14, step=0.01, min_value=0.001, format="%.4f")
    r_a_pu = st.sidebar.number_input("Armature Resistance R_a (p.u.)", value=0.003, step=0.001, min_value=0.0, format="%.4f")

    st.sidebar.header("Network & Fault Parameters")
    u_n   = st.sidebar.number_input("Nominal System Voltage U_n (kV)", value=11.0, step=0.1, min_value=0.1)
    freq  = st.sidebar.selectbox("System Frequency (Hz)", [50, 60])
    c_mode = st.sidebar.radio("Voltage Factor c", ["Auto (IEC table)", "Manual"])
    if c_mode == "Auto (IEC table)":
        c_max = 1.10
        c_min = 0.95 if u_n <= 1.0 else 1.00
        st.sidebar.info(f"c_max = {c_max} | c_min = {c_min}")
    else:
        c_max = st.sidebar.number_input("c_max", value=1.10, step=0.01)
        c_min = st.sidebar.number_input("c_min", value=1.00, step=0.01)

    fault_locations = st.sidebar.multiselect(
        "Fault Location(s)",
        ["Generator Terminals (LV Bus)", "HV Bus (after step-up transformer)"],
        default=["Generator Terminals (LV Bus)"]
    )
    fault_types = st.sidebar.multiselect(
        "Fault Type(s)",
        ["3-phase (I\"k3)", "2-phase (I\"k2)", "1-phase (I\"k1)"],
        default=["3-phase (I\"k3)", "2-phase (I\"k2)"]
    )

    # Step-up transformer
    need_trafo = "HV Bus (after step-up transformer)" in fault_locations
    if need_trafo:
        st.sidebar.header("Step-Up Transformer Data")
        s_T     = st.sidebar.number_input("Transformer Rating S_T (MVA)", value=100.0, step=1.0, min_value=0.1)
        u_T_lv  = st.sidebar.number_input("LV Voltage U_T_LV (kV)", value=11.0, step=0.1, min_value=0.1)
        u_T_hv  = st.sidebar.number_input("HV Voltage U_T_HV (kV)", value=110.0, step=1.0, min_value=0.1)
        u_k_pct = st.sidebar.number_input("Short-Circuit Voltage u_k (%)", value=10.0, step=0.1, min_value=0.1)
        p_k_kw  = st.sidebar.number_input("Short-Circuit Losses P_k (kW)", value=200.0, step=10.0, min_value=0.0)
    else:
        s_T = u_T_lv = u_T_hv = u_k_pct = p_k_kw = None

    # Zero-sequence (optional, for 1-phase fault)
    need_z0 = "1-phase (I\"k1)" in fault_types
    has_z0 = False
    z0_r = z0_x = 0.0
    if need_z0:
        st.sidebar.header("Zero-Sequence Impedance Z0 (Optional)")
        st.sidebar.caption("Leave both at 0 to skip single-phase calculation.")
        z0_r = st.sidebar.number_input("R0 (Ω)", value=0.0, step=0.01, format="%.4f")
        z0_x = st.sidebar.number_input("X0 (Ω)", value=0.0, step=0.01, format="%.4f")
        has_z0 = (z0_r != 0.0 or z0_x != 0.0)

    st.sidebar.header("Thermal Calculation")
    t_k = st.sidebar.number_input("Fault Duration T_k (s)", value=1.0, step=0.05, min_value=0.01)

    if st.button("🚀 Calculate Short-Circuit Currents", type="primary", key="sc_iec_btn", use_container_width=True):
        st.session_state.calc_triggered = True

    if st.session_state.calc_triggered:
        if not fault_locations:
            st.error("Please select at least one fault location in the sidebar.")
            st.stop()

        # ── Core calculations ────────────────────────────────────
        sin_phi_G = math.sqrt(max(1 - cos_phi_G**2, 0))
        omega     = 2 * math.pi * freq

        # Generator base impedance  [Ω]
        z_base   = (u_rG ** 2) / s_n           # kV² / MVA = Ω
        x_d_ohm  = x_d_pu * z_base
        r_a_ohm  = r_a_pu * z_base

        # Correction factor K_G  (IEC 60909-0 §4.6.3, Eq. 18)
        denom_KG = 1 + x_d_pu * sin_phi_G
        K_G = (u_n / u_rG) * (c_max / denom_KG)

        # Corrected generator impedance  [Ω]
        r_GK = K_G * r_a_ohm
        x_GK = K_G * x_d_ohm
        z_GK = math.sqrt(r_GK**2 + x_GK**2)

        # ── Helper: peak factor & thermal ───────────────────────
        def peak_factor(r, x):
            rX = r / x if x > 0 else 0
            return 1.02 + 0.98 * math.exp(-3 * rX)

        def thermal_factor(kappa, r, x, tk):
            """Returns m (DC heat factor). n=1 assumed. IEC 60909-0 §4.5."""
            tau_dc = x / (omega * r) if r > 0 else 1e6
            if tau_dc < 1e5 and tk > 0:
                m = kappa**2 * (tau_dc / (2 * tk)) * (1 - math.exp(-2 * tk / tau_dc))
            else:
                m = kappa**2  # conservative
            return m

        # ── Results container ────────────────────────────────────
        results = {}

        # ── A: Generator Terminals ───────────────────────────────
        if "Generator Terminals (LV Bus)" in fault_locations:
            kap_G   = peak_factor(r_GK, x_GK)
            ik3_G   = (c_max * u_rG * 1e3) / (math.sqrt(3) * z_GK) / 1e3   # kA
            ik2_G   = (math.sqrt(3) / 2) * ik3_G
            ip_G    = kap_G * math.sqrt(2) * ik3_G
            m_G     = thermal_factor(kap_G, r_GK, x_GK, t_k)
            ith_G   = ik3_G * math.sqrt(m_G + 1)

            if need_z0 and has_z0:
                z_seq_r = 2 * r_GK + z0_r
                z_seq_x = 2 * x_GK + z0_x
                z_seq   = math.sqrt(z_seq_r**2 + z_seq_x**2)
                ik1_G   = (math.sqrt(3) * c_max * u_rG * 1e3) / z_seq / 1e3
            else:
                ik1_G   = None

            results["gen"] = dict(label="Generator Terminals", u_n=u_rG,
                                  kap=kap_G, ik3=ik3_G, ik2=ik2_G,
                                  ip=ip_G, ik1=ik1_G, ith=ith_G, m=m_G)

        # ── B: HV Bus ────────────────────────────────────────────
        if need_trafo:
            # Transformer impedance referred to HV  [Ω]
            z_T_base_hv = (u_T_hv**2) / s_T
            z_T_hv      = (u_k_pct / 100) * z_T_base_hv
            r_T_pu      = (p_k_kw * 1e3) / (s_T * 1e6)
            r_T_hv      = r_T_pu * z_T_base_hv
            x_T_hv      = math.sqrt(max(z_T_hv**2 - r_T_hv**2, 0))

            # Generator impedance referred to HV via turns ratio
            n_ratio  = u_T_hv / u_T_lv
            r_GK_hv  = r_GK * n_ratio**2
            x_GK_hv  = x_GK * n_ratio**2

            # Total
            r_tot_hv = r_GK_hv + r_T_hv
            x_tot_hv = x_GK_hv + x_T_hv
            z_tot_hv = math.sqrt(r_tot_hv**2 + x_tot_hv**2)

            kap_HV  = peak_factor(r_tot_hv, x_tot_hv)
            ik3_HV  = (c_max * u_T_hv * 1e3) / (math.sqrt(3) * z_tot_hv) / 1e3
            ik2_HV  = (math.sqrt(3) / 2) * ik3_HV
            ip_HV   = kap_HV * math.sqrt(2) * ik3_HV
            m_HV    = thermal_factor(kap_HV, r_tot_hv, x_tot_hv, t_k)
            ith_HV  = ik3_HV * math.sqrt(m_HV + 1)

            if need_z0 and has_z0:
                z_seq_r_hv = 2 * r_tot_hv + z0_r * n_ratio**2
                z_seq_x_hv = 2 * x_tot_hv + z0_x * n_ratio**2
                z_seq_hv   = math.sqrt(z_seq_r_hv**2 + z_seq_x_hv**2)
                ik1_HV     = (math.sqrt(3) * c_max * u_T_hv * 1e3) / z_seq_hv / 1e3
            else:
                ik1_HV     = None

            results["hv"] = dict(label=f"HV Bus ({u_T_hv} kV)", u_n=u_T_hv,
                                 kap=kap_HV, ik3=ik3_HV, ik2=ik2_HV,
                                 ip=ip_HV, ik1=ik1_HV, ith=ith_HV, m=m_HV,
                                 r_T=r_T_hv, x_T=x_T_hv, z_T=z_T_hv,
                                 r_tot=r_tot_hv, x_tot=x_tot_hv, z_tot=z_tot_hv)

        # ── Step-by-step impedance derivation ───────────────────
        with st.expander("Step 1 — Generator Impedance & K_G Correction", expanded=True):
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Base Impedance")
                st.latex(r"Z_{base} = \frac{U_{rG}^2}{S_n}")
                st.info(f"Z_base = {u_rG}² / {s_n} = **{z_base:.4f} Ω**")
                st.subheader("Subtransient Impedance (Ω)")
                st.latex(r"X''_d = x''_d \cdot Z_{base}, \quad R_a = r_a \cdot Z_{base}")
                st.info(f"X\"d = {x_d_pu} × {z_base:.4f} = **{x_d_ohm:.4f} Ω**")
                st.info(f"R_a  = {r_a_pu} × {z_base:.4f} = **{r_a_ohm:.4f} Ω**")
            with col_b:
                st.subheader("Correction Factor K_G  (IEC 60909-0 Eq. 18)")
                st.latex(r"K_G = \frac{U_n}{U_{rG}} \cdot \frac{c_{max}}{1 + x''_d \cdot \sin\varphi_G}")
                st.success(f"sin φ_G = {sin_phi_G:.4f}")
                st.success(f"K_G = ({u_n}/{u_rG}) × {c_max} / {denom_KG:.4f} = **{K_G:.4f}**")
                st.subheader("Corrected Generator Impedance")
                st.latex(r"Z_{GK} = K_G \cdot Z_G")
                st.warning(f"R_GK = {r_GK:.4f} Ω | X_GK = {x_GK:.4f} Ω | Z_GK = **{z_GK:.4f} Ω**")

        if need_trafo and "hv" in results:
            hv = results["hv"]
            with st.expander("Step 2 — Step-Up Transformer Impedance (HV side)", expanded=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.subheader("Transformer Z_T")
                    st.latex(r"Z_T = \frac{u_k\%}{100} \cdot \frac{U_{T,HV}^2}{S_T}")
                    st.info(f"Z_T = {u_k_pct/100} × {u_T_hv}²/{s_T} = **{hv['z_T']:.4f} Ω**")
                    st.info(f"R_T = **{hv['r_T']:.4f} Ω** | X_T = **{hv['x_T']:.4f} Ω**")
                with col_b:
                    st.subheader("Total Impedance at HV Bus")
                    st.latex(r"Z_{tot} = Z_{GK,HV} + Z_T")
                    st.warning(f"n = {u_T_hv}/{u_T_lv} = {u_T_hv/u_T_lv:.4f}")
                    st.warning(f"R_tot = **{hv['r_tot']:.4f} Ω** | X_tot = **{hv['x_tot']:.4f} Ω** | Z_tot = **{hv['z_tot']:.4f} Ω**")

        # ── Results per fault location ───────────────────────────
        st.header("Short-Circuit Current Results")
        loc_cols = st.columns(len(results))

        for col_idx, (key, r) in enumerate(results.items()):
            with loc_cols[col_idx]:
                st.subheader(f"📍 {r['label']}")
                st.markdown(f"*U_n = {r['u_n']} kV | κ = {r['kap']:.3f}*")

                show_3ph = "3-phase (I\"k3)" in fault_types
                show_2ph = "2-phase (I\"k2)" in fault_types
                show_1ph = "1-phase (I\"k1)" in fault_types

                if show_3ph:
                    st.metric("I\"k3 — 3-phase SC", f"{r['ik3']:.3f} kA")
                if show_2ph:
                    st.metric("I\"k2 — Line-to-line SC", f"{r['ik2']:.3f} kA")
                if show_1ph:
                    if r['ik1'] is not None:
                        st.metric("I\"k1 — Single-phase SC", f"{r['ik1']:.3f} kA")
                    else:
                        st.info("I\"k1 skipped — Z0 not provided")

                st.metric("ip — Peak current", f"{r['ip']:.3f} kA")
                st.metric("Ith — Thermal equiv. (Tk=" + f"{t_k}s)", f"{r['ith']:.3f} kA")

        # ── Formula summary expander ─────────────────────────────
        with st.expander("Formula Reference — IEC 60909-0", expanded=False):
            st.markdown("**3-phase initial SC current:**")
            st.latex(r"I''_{k3} = \frac{c \cdot U_n}{\sqrt{3} \cdot Z_{GK}}")
            st.markdown("**2-phase SC current:**")
            st.latex(r"I''_{k2} = \frac{\sqrt{3}}{2} \cdot I''_{k3}")
            st.markdown("**1-phase SC current (Z0 required):**")
            st.latex(r"I''_{k1} = \frac{\sqrt{3} \cdot c \cdot U_n}{Z_1 + Z_2 + Z_0}")
            st.markdown("**Peak current:**")
            st.latex(r"i_p = \kappa \cdot \sqrt{2} \cdot I''_{k3}, \quad \kappa = 1.02 + 0.98\,e^{-3R/X}")
            st.markdown("**Thermal equivalent current:**")
            st.latex(r"I_{th} = I''_{k3} \cdot \sqrt{m + n}, \quad n=1")
            st.latex(r"m = \kappa^2 \cdot \frac{\tau_{DC}}{2T_k} \cdot \left(1 - e^{-2T_k/\tau_{DC}}\right), \quad \tau_{DC}=\frac{X}{\omega R}")

# ─────────────────────────────────────────────────────────────────
# EARTHING (GROUNDING) — IEEE Std 80-2013
# ─────────────────────────────────────────────────────────────────
elif tool == "Earthing (IEEE 80)":
    st.title("🌍 Substation Earthing Design — IEEE Std 80-2013")
    st.caption("IEEE Guide for Safety in AC Substation Grounding | Steps per Chapter 15 methodology")

    # ── Sidebar ─────────────────────────────────────────────────
    st.sidebar.header("System Fault Parameters")
    u_sys      = st.sidebar.number_input("System Voltage (kV)", value=110.0, step=1.0, min_value=0.1)
    If_sym     = st.sidebar.number_input("Symmetrical Fault Current If (A)", value=10000.0, step=100.0, min_value=1.0,
                                          help="Rms value of symmetrical ground fault current (3I0)")
    tf         = st.sidebar.number_input("Fault Duration tf (s)", value=0.5, step=0.05, min_value=0.01)
    X_R        = st.sidebar.number_input("System X/R Ratio", value=10.0, step=0.5, min_value=0.1)
    Sf         = st.sidebar.number_input("Fault Current Division Factor Sf", value=0.6, step=0.01,
                                          min_value=0.01, max_value=1.0,
                                          help="Sf = Ig / If — fraction of fault current flowing into earth grid")

    st.sidebar.header("Soil & Grid Geometry")
    rho_e      = st.sidebar.number_input("Soil Resistivity rho (Ohm.m)", value=100.0, step=5.0, min_value=1.0)
    rho_s_e    = st.sidebar.number_input("Surface Layer Resistivity rho_s (Ohm.m)", value=2500.0, step=100.0, min_value=1.0)
    hs_e       = st.sidebar.number_input("Surface Layer Thickness hs (m)", value=0.1, step=0.01, min_value=0.0)
    h_e        = st.sidebar.number_input("Grid Burial Depth h (m)", value=0.5, step=0.05, min_value=0.01)
    A_e        = st.sidebar.number_input("Grid Area A (m2)", value=3600.0, step=100.0, min_value=1.0)
    Lx_e       = st.sidebar.number_input("Grid Length Lx (m)", value=60.0, step=1.0, min_value=1.0)
    Ly_e       = st.sidebar.number_input("Grid Width Ly (m)", value=60.0, step=1.0, min_value=1.0)
    Lc_e       = st.sidebar.number_input("Total Conductor Length Lc (m)", value=600.0, step=10.0, min_value=1.0)
    Lr_e       = st.sidebar.number_input("Total Rod Length Lr (m)", value=0.0, step=1.0, min_value=0.0)
    nx_e       = st.sidebar.number_input("Parallel Conductors X (nx)", value=7, step=1, min_value=1)
    ny_e       = st.sidebar.number_input("Parallel Conductors Y (ny)", value=7, step=1, min_value=1)
    d_cond_e   = st.sidebar.number_input("Conductor Diameter d (m)", value=0.01, step=0.001, min_value=0.001, format="%.3f")

    st.sidebar.header("Body Safety Parameters")
    body_weight_e = st.sidebar.selectbox("Body Weight (kg)", [50, 70], index=0)
    ts_e          = st.sidebar.number_input("Shock Duration ts (s)", value=0.5, step=0.05, min_value=0.01)

    st.sidebar.header("Conductor Material")
    cond_mat_e = st.sidebar.selectbox("Material", ["Copper (soft-drawn)", "Copper (hard-drawn)", "Steel (galv.)"])
    KF_MAP_E   = {"Copper (soft-drawn)": 7.06, "Copper (hard-drawn)": 7.06, "Steel (galv.)": 15.95}
    Kf_e       = KF_MAP_E[cond_mat_e]
    Ta_e       = st.sidebar.number_input("Ambient Temperature Ta (C)", value=40.0, step=1.0)

    if st.button("Calculate Earthing System", type="primary", key="earth_btn", use_container_width=True):
        st.session_state.calc_triggered = True

    if st.session_state.calc_triggered:

        # STEP 1: Decrement Factor
        Ta_dc_e = X_R / (2 * math.pi * 50)
        if Ta_dc_e > 0 and tf > 0:
            Df_e = math.sqrt(1 + (Ta_dc_e / tf) * (1 - math.exp(-2 * tf / Ta_dc_e)))
        else:
            Df_e = 1.0

        Ig_e = Sf * If_sym
        IG_e = Df_e * Ig_e

        with st.expander("Step 1 — Fault Current & Maximum Grid Current (IEEE 80 Eq. 68-70)", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.subheader("DC Time Constant")
                st.latex(r"\tau_{DC} = \frac{X/R}{2\pi f}")
                st.info(f"t_DC = {X_R}/(2p x 50) = **{Ta_dc_e:.4f} s**")
            with c2:
                st.subheader("Decrement Factor Df (Eq. 79)")
                st.latex(r"D_f = \sqrt{1 + \frac{\tau_{DC}}{t_f}\left(1-e^{-2t_f/\tau_{DC}}\right)}")
                st.success(f"Df = **{Df_e:.4f}**")
            with c3:
                st.subheader("Grid Currents (Eq. 69-70)")
                st.latex(r"I_g = S_f \times I_f")
                st.latex(r"I_G = D_f \times I_g")
                st.warning(f"Ig (symmetrical) = **{Ig_e:.1f} A**")
                st.error(f"IG (maximum) = **{IG_e:.1f} A**")

        # STEP 2: Conductor Sizing
        A_kcmil_e = (If_sym / 1000) * math.sqrt(tf) * Kf_e
        A_mm2_e   = A_kcmil_e * 0.5067

        with st.expander("Step 2 — Conductor Sizing (IEEE 80 Table 1)", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Minimum Cross-Section")
                st.latex(r"A_{kcmil} = \frac{I_f}{1000}\sqrt{t_f} \cdot K_f")
                st.info(f"Kf ({cond_mat_e}) = {Kf_e}")
                st.warning(f"A = **{A_kcmil_e:.2f} kcmil = {A_mm2_e:.1f} mm2**")
            with c2:
                st.subheader("Recommendation")
                st.markdown(f"- Fault current: **{If_sym:.0f} A**")
                st.markdown(f"- Duration: **{tf} s**")
                st.markdown(f"- Ambient: **{Ta_e} °C**")
                st.success(f"Use conductor >= **{math.ceil(A_mm2_e)} mm2**")

        # STEP 3: Ground Resistance
        Lt_e = Lc_e + (1.55 + 1.22*(Lr_e / math.sqrt(Lx_e**2 + Ly_e**2)))*Lr_e if Lr_e > 0 else Lc_e
        Rg_e = rho_e * (1/Lt_e + (1/math.sqrt(20*A_e)) * (1 + 1/(1 + h_e*math.sqrt(20/A_e))))

        with st.expander("Step 3 — Ground Resistance Rg (IEEE 80 Eq. 53 - Sverak)", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Sverak Formula")
                st.latex(r"R_g = \rho\left[\frac{1}{L_t}+\frac{1}{\sqrt{20A}}\left(1+\frac{1}{1+h\sqrt{20/A}}\right)\right]")
                st.info(f"rho={rho_e} Ohm.m | Lt={Lt_e:.1f} m | A={A_e} m2 | h={h_e} m")
            with c2:
                st.metric("Ground Resistance Rg", f"{Rg_e:.4f} Ohm")

        # STEP 4: GPR
        GPR_e = IG_e * Rg_e

        with st.expander("Step 4 — Ground Potential Rise GPR", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.latex(r"GPR = I_G \times R_g")
                st.info(f"IG={IG_e:.1f} A | Rg={Rg_e:.4f} Ohm")
            with c2:
                st.metric("GPR", f"{GPR_e:.1f} V", f"{GPR_e/1000:.3f} kV")

        # STEP 5: Tolerable Voltages
        Cs_e = 1 - (0.09*(1 - rho_e/rho_s_e))/(2*hs_e + 0.09) if hs_e > 0 else 1.0
        Cs_e = max(0.0, min(1.0, Cs_e))
        Ib_e = (0.116 if body_weight_e == 50 else 0.157) / math.sqrt(ts_e)
        Etouch_e = (1000 + 1.5 * Cs_e * rho_s_e) * Ib_e
        Estep_e  = (1000 + 6.0 * Cs_e * rho_s_e) * Ib_e

        with st.expander("Step 5 — Tolerable Touch & Step Voltages (IEEE 80 Eq. 29-32)", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.subheader("Reflection Factor Cs")
                st.latex(r"C_s = 1 - \frac{0.09(1-\rho/\rho_s)}{2h_s + 0.09}")
                st.success(f"Cs = **{Cs_e:.4f}**")
            with c2:
                st.subheader("Body Current Ib")
                st.latex(r"I_b = \frac{0.116}{\sqrt{t_s}}\,(50\,kg)")
                st.info(f"Ib = **{Ib_e:.4f} A**")
            with c3:
                st.subheader("Tolerable Voltages")
                st.latex(r"E_{touch} = (1000+1.5C_s\rho_s)I_b")
                st.latex(r"E_{step}  = (1000+6C_s\rho_s)I_b")
                st.warning(f"Etouch = **{Etouch_e:.1f} V**")
                st.warning(f"Estep  = **{Estep_e:.1f} V**")

        # STEP 6: Mesh & Step Voltages
        Dx_e = Lx_e / (nx_e - 1) if nx_e > 1 else Lx_e
        Dy_e = Ly_e / (ny_e - 1) if ny_e > 1 else Ly_e
        D_e  = (Dx_e + Dy_e) / 2.0
        n_e  = math.sqrt(nx_e * ny_e)
        Kh_e = math.sqrt(1 + h_e / 1.0)
        try:
            km_t1 = math.log(D_e**2 / (16*h_e*d_cond_e))
            km_t2 = math.log((D_e + 2*h_e)**2 / (8*D_e*d_cond_e))
            km_t3 = h_e / (4*d_cond_e)
            km_t4 = (1/Kh_e) * math.log(8 / (math.pi*(2*n_e - 1)))
            Km_e  = (1/(2*math.pi)) * (km_t1 + km_t2 - km_t3 + km_t4)
        except (ValueError, ZeroDivisionError):
            Km_e = 0.5
        try:
            Ks_e = (1/math.pi) * (1/(2*h_e) + 1/(D_e+h_e) + (1/D_e)*(1 - 0.5**(n_e-2)))
        except ZeroDivisionError:
            Ks_e = 0.1
        Ki_e  = 0.644 + 0.148 * n_e
        Lm_e  = Lc_e + 1.55*Lr_e if Lr_e > 0 else Lc_e
        Ls_e  = 0.75*Lc_e + 0.85*Lr_e if Lr_e > 0 else 0.75*Lc_e
        Em_e  = rho_e * IG_e * Km_e * Ki_e / Lm_e if Lm_e > 0 else 0
        Es_e  = rho_e * IG_e * Ks_e * Ki_e / Ls_e if Ls_e > 0 else 0

        with st.expander("Step 6 — Mesh & Step Voltages (IEEE 80 Eq. 80-94)", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Geometric Factors")
                st.markdown(f"- Avg mesh spacing D = **{D_e:.2f} m**")
                st.markdown(f"- n (geometric mean) = **{n_e:.2f}**")
                st.markdown(f"- Km = **{Km_e:.4f}** | Ks = **{Ks_e:.4f}** | Ki = **{Ki_e:.4f}**")
                st.markdown(f"- Lm = **{Lm_e:.1f} m** | Ls = **{Ls_e:.1f} m**")
            with c2:
                st.subheader("Voltages")
                st.latex(r"E_m = \frac{\rho \cdot I_G \cdot K_m \cdot K_i}{L_m}")
                st.latex(r"E_s = \frac{\rho \cdot I_G \cdot K_s \cdot K_i}{L_s}")
                st.error(f"Em = **{Em_e:.1f} V**")
                st.error(f"Es = **{Es_e:.1f} V**")

        # STEP 7: Safety Summary
        touch_ok_e = Em_e <= Etouch_e
        step_ok_e  = Es_e <= Estep_e

        st.header("Safety Verification Summary")
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Max Grid Current IG", f"{IG_e:.0f} A")
        mc2.metric("Ground Resistance Rg", f"{Rg_e:.4f} Ohm")
        mc3.metric("GPR", f"{GPR_e:.0f} V")
        mc4.metric("Min Conductor", f">= {math.ceil(A_mm2_e)} mm2")
        st.markdown("---")

        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown("### Touch Voltage Check")
            if touch_ok_e:
                st.success(f"PASS — Em ({Em_e:.1f} V) <= Etouch ({Etouch_e:.1f} V)")
            else:
                st.error(f"FAIL — Em ({Em_e:.1f} V) > Etouch ({Etouch_e:.1f} V)")
                st.warning("Action: Increase conductor density or add surface layer.")
        with rc2:
            st.markdown("### Step Voltage Check")
            if step_ok_e:
                st.success(f"PASS — Es ({Es_e:.1f} V) <= Estep ({Estep_e:.1f} V)")
            else:
                st.error(f"FAIL — Es ({Es_e:.1f} V) > Estep ({Estep_e:.1f} V)")
                st.warning("Action: Increase burial depth or surface layer thickness.")

        with st.expander("Full Results Table", expanded=False):
            df_res = pd.DataFrame({
                "Parameter": ["If (symmetrical)","DC Time Constant","Decrement Factor Df",
                               "Ig (symmetrical grid)","IG (maximum grid)","Ground Resistance Rg",
                               "GPR","Reflection Factor Cs","Etouch allowable","Estep allowable",
                               "Em (mesh voltage)","Es (step voltage)","Min Conductor Size"],
                "Value": [f"{If_sym:.0f} A", f"{Ta_dc_e:.4f} s", f"{Df_e:.4f}",
                          f"{Ig_e:.1f} A", f"{IG_e:.1f} A", f"{Rg_e:.4f} Ohm",
                          f"{GPR_e:.1f} V", f"{Cs_e:.4f}", f"{Etouch_e:.1f} V",
                          f"{Estep_e:.1f} V", f"{Em_e:.1f} V", f"{Es_e:.1f} V",
                          f">= {math.ceil(A_mm2_e)} mm2"],
                "Status": ["—","—","—","—","—","—","—","—","—","—",
                           "PASS" if touch_ok_e else "FAIL",
                           "PASS" if step_ok_e  else "FAIL","—"],
            })
            st.dataframe(df_res, use_container_width=True, hide_index=True)

        with st.expander("Formula Reference — IEEE Std 80-2013", expanded=False):
            st.markdown("**Fault Current Division (Eq. 68-70):**")
            st.latex(r"S_f = \frac{I_g}{3I_0}\;;\quad I_g = S_f \cdot I_f\;;\quad I_G = D_f \cdot I_g")
            st.markdown("**Decrement Factor (Eq. 79):**")
            st.latex(r"D_f = \sqrt{1 + \frac{\tau_{DC}}{t_f}\left(1 - e^{-2t_f/\tau_{DC}}\right)}")
            st.markdown("**Ground Resistance — Sverak (Eq. 53):**")
            st.latex(r"R_g = \rho\left[\frac{1}{L_t}+\frac{1}{\sqrt{20A}}\left(1+\frac{1}{1+h\sqrt{20/A}}\right)\right]")
            st.markdown("**Tolerable Touch & Step Voltages (Eq. 29-32):**")
            st.latex(r"E_{touch50} = (1000 + 1.5\,C_s\rho_s)\frac{0.116}{\sqrt{t_s}}")
            st.latex(r"E_{step50}  = (1000 + 6\,C_s\rho_s)\frac{0.116}{\sqrt{t_s}}")
            st.markdown("**Mesh & Step Voltages (Eq. 80-94):**")
            st.markdown("**Mesh & Step Voltages (Eq. 80-94):**")

            st.latex(r"E_m = \frac{\rho \cdot I_G \cdot K_m \cdot K_i}{L_m}\;;\quad E_s = \frac{\rho \cdot I_G \cdot K_s \cdot K_i}{L_s}")
            st.latex(r"E_m = \frac{\rho \cdot I_G \cdot K_m \cdot K_i}{L_m}\;;\quad E_s = \frac{\rho \cdot I_G \cdot K_s \cdot K_i}{L_s}")
