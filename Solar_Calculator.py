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

st.title("☀️ Advanced Solar Financial Calculator")
# st.image("logo.png", width=200) # Uncomment to display your logo

st.info(
    "**Note:** These calculations are benchmarked for a **1 Hectare, 1 MW** scale project. "
    "Adjust inputs to reflect your project's specifics."
)

st.markdown("---")
st.header("⚙️ Input Parameters")

# Use columns for a cleaner layout of input widgets
col1, col2 = st.columns(2)

with col1:
    capex = st.number_input("Capital Expenditure (CAPEX) ($)", min_value=0.0, value=1_000_000.0, step=50_000.0)
    annual_kwh = st.number_input("Total kWh Generated Annually (kWh)", min_value=0, value=1_500_000, step=100_000)
    maintenance_cost = st.number_input("Annual Maintenance Costs ($)", min_value=0.0, value=20_000.0, step=1_000.0)

with col2:
    contingency_percentage = st.slider("Contingency Budget (%)", min_value=0, max_value=25, value=10)
    price_per_kwh = st.number_input("Price per kWh ($)", min_value=0.00, value=0.17, step=0.01, format="%.2f")
    plant_lifetime = st.slider("Plant Lifetime (Years)", min_value=5, max_value=40, value=25)

# --- Calculation Trigger ---
if st.button("Calculate Financials", type="primary"):
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
        "contingency_amount": contingency_amount
    }

    # --- Scenario Analysis for Graphs ---
    price_scenarios = np.linspace(0.10, 0.25, 16) # Create 16 price points from $0.10 to $0.25
    scenario_data = []

    for price in price_scenarios:
        scenario_revenue = annual_kwh * price
        _, payback, _, scenario_irr = calculate_solar_financials(
            capex, contingency_amount, scenario_revenue, maintenance_cost, plant_lifetime
        )
        scenario_data.append({"Price per kWh": price, "IRR": scenario_irr, "Payback Period (Years)": payback})
    
    st.session_state['scenario_df'] = pd.DataFrame(scenario_data)

# --- Display Results (if they exist in session state) ---
if 'results' in st.session_state:
    results = st.session_state['results']
    st.markdown("---")
    st.header("📊 Financial Metrics")

    if results['roi'] != -1.0:
        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("Simple Payback Period", f"{results['simple_payback']:.2f} Years")
        res_col2.metric("Return on Investment (ROI)", f"{results['roi']:.2%}")
        res_col3.metric("Internal Rate of Return (IRR)", f"{results['irr']:.2%}")

        st.success(
            f"With an initial investment of **${results['initial_investment']:,.2f}** (including a "
            f"${results['contingency_amount']:,.2f} contingency), the project is projected "
            f"to pay for itself in approximately **{results['simple_payback']:.2f} years**."
        )
    else:
        st.error("The project is not profitable with the given inputs (Annual Revenue is less than or equal to Maintenance Costs).")

    # --- Display Graphs ---
    if 'scenario_df' in st.session_state:
        st.markdown("---")
        st.header("📈 Scenario Analysis vs. Price per kWh")
        scenario_df = st.session_state['scenario_df']

        st.subheader("IRR vs. Price per kWh")
        st.line_chart(scenario_df.set_index("Price per kWh")[['IRR']])

        st.subheader("Payback Period vs. Price per kWh")
        st.line_chart(scenario_df.set_index("Price per kWh")[['Payback Period (Years)']])

# --- Explanations Expander ---
with st.expander("What do these metrics mean?"):
    st.markdown("""
    - **Simple Payback Period:** The number of years it takes for the project's profits to equal the initial investment. A shorter payback period is generally better.
    - **Return on Investment (ROI):** Measures the total net profit of the project as a percentage of the initial investment. A higher ROI is better.
    - **Internal Rate of Return (IRR):** A more advanced metric representing the project's intrinsic annual rate of return. A project is considered viable if its IRR is higher than your company's required rate of return.
    """)
