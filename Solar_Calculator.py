import streamlit as st
import numpy as np
import numpy_financial as npf
import pandas as pd

# --- Financial Calculation Function ---
def calculate_solar_financials(capex, contingency_amount, annual_revenue, maintenance_cost, plant_lifetime):
    """
    Calculates key financial metrics for a capital project.

    Args:
        capex (float): The total capital expenditure.
        contingency_amount (float): A budget reserve for unforeseen upfront costs.
        annual_revenue (float): The total revenue generated each year.
        maintenance_cost (float): The operational and maintenance cost per year.
        plant_lifetime (int): The total operational lifetime of the plant in years.

    Returns:
        tuple: A tuple containing the initial investment, payback period, ROI, and IRR.
    """
    annual_profit = annual_revenue - maintenance_cost
    if annual_profit <= 0:
        return (0, float('inf'), -1.0, -1.0)

    initial_investment = capex + contingency_amount
    simple_payback = initial_investment / annual_profit if annual_profit > 0 else float('inf')
    total_profit = annual_profit * plant_lifetime
    net_gain = total_profit - initial_investment
    roi = net_gain / initial_investment if initial_investment > 0 else 0
    cash_flows = [-initial_investment] + [annual_profit] * plant_lifetime
    irr = npf.irr(cash_flows)

    return initial_investment, simple_payback, roi, irr

# --- Streamlit App Layout ---
st.set_page_config(layout="centered", page_title="Solar Financial Calculator")

st.title("☀️ Scenario Solar Financial Calculator")
st.image("logo.png", width=500) # Uncomment to display your logo



st.markdown("---")
st.header("⚙️ Input Parameters")

# Use columns for a cleaner layout of input widgets
col1, col2 = st.columns(2)

with col1:
    capex_mil = st.number_input("Capital Expenditure (CAPEX) (Million FJD)", min_value=0.0, value=1.0, step=0.1)
    annual_kwh_mil = st.number_input("Total Energy Generated Annually (Million kWh)", min_value=0.0, value=1.5, step=0.1)
    maintenance_cost_k = st.number_input("Annual Maintenance Costs (k FJD)", min_value=0.0, value=30.0, step=1.0)

with col2:
    contingency_percentage = st.slider("Contingency Budget (%)", min_value=0, max_value=25, value=10)
    price_per_kwh = st.number_input("Price per kWh (FJD)", min_value=0.00, value=0.17, step=0.01, format="%.2f")
    plant_lifetime = st.slider("Plant Lifetime (Years)", min_value=5, max_value=40, value=25)

# --- Calculation Trigger ---
if st.button("Calculate Financials", type="primary"):
    # Convert inputs from millions/thousands to base units
    capex = capex_mil * 1_000_000
    annual_kwh = annual_kwh_mil * 1_000_000
    maintenance_cost = maintenance_cost_k * 1_000
    
    # Calculate main scenario
    contingency_amount = capex * (contingency_percentage / 100.0)
    annual_revenue = annual_kwh * price_per_kwh
    
    initial_investment, simple_payback, roi, irr = calculate_solar_financials(
        capex, contingency_amount, annual_revenue, maintenance_cost, plant_lifetime
    )
    # Store results in session state to persist them
    st.session_state['results'] = {
        "initial_investment": initial_investment,
        "simple_payback": simple_payback,
        "roi": roi,
        "irr": irr,
        "contingency_amount": contingency_amount,
        "annual_revenue": annual_revenue,
        "maintenance_cost": maintenance_cost
    }

    # --- Scenario Analysis for Graphs ---
    price_scenarios = np.linspace(0.10, 0.30, 21) # Create 21 price points from $0.10 to $0.30
    scenario_data = []

    for price in price_scenarios:
        scenario_revenue = annual_kwh * price
        _, payback, _, scenario_irr = calculate_solar_financials(
            capex, contingency_amount, scenario_revenue, maintenance_cost, plant_lifetime
        )
        scenario_data.append({"Price per kWh (FJD)": price, "IRR": scenario_irr, "Payback Period (Years)": payback})
    
    st.session_state['scenario_df'] = pd.DataFrame(scenario_data)

# --- Display Results (if they exist in session state) ---
if 'results' in st.session_state:
    results = st.session_state['results']
    st.markdown("---")
    st.header("📊 Key Financial Metrics")

    if results['roi'] != -1.0:
        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("Simple Payback Period", f"{results['simple_payback']:.2f} Years")
        res_col2.metric("Return on Investment (ROI)", f"{results['roi']:.2%}")
        res_col3.metric("Internal Rate of Return (IRR)", f"{results['irr']:.2%}")

        st.success(
            f"With an initial investment of **{results['initial_investment']:,.2f} FJD** (including a "
            f"{results['contingency_amount']:,.2f} FJD contingency), the project is projected "
            f"to pay for itself in approximately **{results['simple_payback']:.2f} years**."
        )
        
        st.markdown("---")
        st.header("💰 Annual Financials Breakdown")
        ann_col1, ann_col2, ann_col3 = st.columns(3)
        ann_col1.metric("Annual Revenue", f"{results['annual_revenue']:,.2f} FJD")
        ann_col2.metric("Annual Maintenance", f"{results['maintenance_cost']:,.2f} FJD")
        ann_col3.metric("Annual Profit", f"{(results['annual_revenue'] - results['maintenance_cost']):,.2f} FJD")

    else:
        st.error("The project is not profitable with the given inputs (Annual Revenue is less than or equal to Maintenance Costs).")

    # --- Display Graphs ---
    if 'scenario_df' in st.session_state:
        st.markdown("---")
        st.header("📈 Scenario Analysis vs. Price per kWh")
        scenario_df = st.session_state['scenario_df']

        st.subheader("IRR vs. Price per kWh")
        st.line_chart(scenario_df.set_index("Price per kWh (FJD)")[['IRR']])

        st.subheader("Payback Period vs. Price per kWh")
        st.line_chart(scenario_df.set_index("Price per kWh (FJD)")[['Payback Period (Years)']])
