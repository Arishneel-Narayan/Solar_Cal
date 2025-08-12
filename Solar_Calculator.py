import streamlit as st
import numpy as np
import numpy_financial as npf
import pandas as pd

# --- Financial Calculation Function (Refactored) ---
def calculate_solar_financials(capex, contingency_pct, annual_kwh, price_per_kwh, maintenance_cost, plant_lifetime):
    """
    Calculates all key financial metrics and returns them in a single dictionary.

    Args:
        capex (float): The total capital expenditure.
        contingency_pct (float): Contingency percentage.
        annual_kwh (float): Total kWh generated annually.
        price_per_kwh (float): The price per kWh.
        maintenance_cost (float): The operational and maintenance cost per year.
        plant_lifetime (int): The total operational lifetime of the plant in years.

    Returns:
        dict: A dictionary containing all calculated financial metrics.
    """
    # Perform all calculations within this function to ensure consistency
    contingency_amount = capex * (contingency_pct / 100.0)
    initial_investment = capex + contingency_amount
    annual_revenue = annual_kwh * price_per_kwh
    annual_profit = annual_revenue - maintenance_cost
    lifetime_profit = annual_profit * plant_lifetime
    lifetime_maintenance_cost = maintenance_cost * plant_lifetime

    # Initialize results with default/non-profitable values
    results = {
        "initial_investment": initial_investment,
        "contingency_amount": contingency_amount,
        "annual_revenue": annual_revenue,
        "maintenance_cost": maintenance_cost,
        "annual_profit": annual_profit,
        "lifetime_profit": lifetime_profit,
        "lifetime_maintenance_cost": lifetime_maintenance_cost,
        "simple_payback": float('inf'),
        "roi": -1.0,
        "irr": -1.0,
    }

    # If the project is profitable, calculate the main metrics
    if annual_profit > 0:
        results["simple_payback"] = initial_investment / annual_profit
        net_gain = lifetime_profit - initial_investment
        results["roi"] = net_gain / initial_investment if initial_investment > 0 else 0
        cash_flows = [-initial_investment] + [annual_profit] * plant_lifetime
        results["irr"] = npf.irr(cash_flows)
    
    return results

# --- Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="Solar Calculations")

# --- Display the logo as a banner ---
st.image("logo.png", use_container_width=True) # Displays your logo as a banner

st.title("Solar Calculations")


st.info(
    "**Note:** These calculations are benchmarked for a **1 Hectare, 1 MW** scale project. "
    "Adjust inputs to reflect your project's specifics."
)

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
    # Store the primary inputs in session state for later use in scenario analysis
    st.session_state['primary_inputs'] = {
        'capex_mil': capex_mil,
        'annual_kwh_mil': annual_kwh_mil,
        'maintenance_cost_k': maintenance_cost_k,
        'contingency_percentage': contingency_percentage,
        'price_per_kwh': price_per_kwh,
        'plant_lifetime': plant_lifetime
    }
    
    # Convert inputs from millions/thousands to base units
    capex = capex_mil * 1_000_000
    annual_kwh = annual_kwh_mil * 1_000_000
    maintenance_cost = maintenance_cost_k * 1_000
    
    # Call the refactored function to get a complete results dictionary
    results = calculate_solar_financials(
        capex, contingency_percentage, annual_kwh, price_per_kwh, maintenance_cost, plant_lifetime
    )
    st.session_state['results'] = results


# --- Display Results (if they exist in session state) ---
if 'results' in st.session_state:
    results = st.session_state['results']
    st.markdown("---")
    st.header("📊 Key Financial Metrics")

    if results['roi'] != -1.0:
        res_col1, res_col2, res_col3 = st.columns(3)
        # Reordered to show ROI first
        res_col1.metric("Return on Investment (ROI)", f"{results['roi']:.2%}")
        res_col2.metric("Simple Payback Period", f"{results['simple_payback']:.2f} Years")
        res_col3.metric("Internal Rate of Return (IRR)", f"{results['irr']:.2%}")

        st.success(
            f"With an initial investment of **{results['initial_investment']:,.2f} FJD** (including a "
            f"{results['contingency_amount']:,.2f} FJD contingency), the project is projected "
            f"to pay for itself in approximately **{results['simple_payback']:.2f} years**."
        )
        
        st.markdown("---")
        st.header("💰 Financials Breakdown")
        ann_col1, ann_col2, ann_col3, ann_col4, ann_col5 = st.columns(5)
        ann_col1.metric("Annual Revenue", f"{results['annual_revenue']:,.2f} FJD")
        ann_col2.metric("Annual Maintenance", f"{results['maintenance_cost']:,.2f} FJD")
        ann_col3.metric("Annual Profit", f"{results['annual_profit']:,.2f} FJD")
        ann_col4.metric("Lifetime Profit", f"{results['lifetime_profit']:,.2f} FJD")
        ann_col5.metric("Lifetime Maintenance", f"{results['lifetime_maintenance_cost']:,.2f} FJD")


    else:
        st.error("The project is not profitable with the given inputs (Annual Revenue is less than or equal to Maintenance Costs).")

    # --- Interactive Scenario Analysis Section ---
    st.markdown("---")
    st.header("📈 Interactive Scenario Analysis")
    
    inputs = st.session_state['primary_inputs']
    
    # Create two columns for the interactive section: Controls on left, Graphs on right
    control_col, graph_col = st.columns([1, 2])

    with control_col:
        st.subheader("Scenario Controls")
        
        scenario_capex_mil = st.slider(
            "Adjust CAPEX (Million FJD)",
            min_value=1.0, max_value=3.0, value=inputs['capex_mil'], step=0.1, key="scenario_capex"
        )
        
        scenario_maintenance_k = st.slider(
            "Adjust Annual Maintenance (k FJD)",
            min_value=10.0, max_value=100.0, value=inputs['maintenance_cost_k'], step=5.0, key="scenario_maint"
        )

        scenario_contingency_pct = st.slider(
            "Adjust Contingency (%)",
            min_value=0, max_value=25, value=inputs['contingency_percentage'], key="scenario_contingency"
        )
        
        show_irr = st.checkbox("Show IRR Sensitivity Graph")
        
    with graph_col:
        # Convert scenario inputs to base units
        scenario_capex = scenario_capex_mil * 1_000_000
        scenario_maintenance = scenario_maintenance_k * 1_000
        
        # Define the constant price range for the x-axis
        price_scenarios = np.linspace(0.10, 0.40, 31)
        
        # Prepare data for graphs
        graph_data = []
        for price in price_scenarios:
            scenario_results = calculate_solar_financials(
                scenario_capex, 
                scenario_contingency_pct, 
                inputs['annual_kwh_mil'] * 1_000_000, 
                price, 
                scenario_maintenance, 
                inputs['plant_lifetime']
            )
            graph_data.append({
                "Price per kWh (FJD)": price, 
                "IRR": scenario_results['irr'], 
                "Payback Period (Years)": scenario_results['simple_payback']
            })
        
        graph_df = pd.DataFrame(graph_data)

        # Display the Payback Period graph by default
        st.subheader("Payback Period vs. Price per kWh")
        st.line_chart(graph_df.set_index("Price per kWh (FJD)")[['Payback Period (Years)']])

        # Display the IRR graph only if the checkbox is ticked
        if show_irr:
            st.subheader("IRR vs. Price per kWh")
            st.line_chart(graph_df.set_index("Price per kWh (FJD)")[['IRR']])


# --- Explanations Expander ---
with st.expander("What do these metrics mean?"):
    st.markdown("""
    - **Simple Payback Period:** The number of years it takes for the project's profits to equal the initial investment. A shorter payback period is generally better.
    - **Return on Investment (ROI):** Measures the total net profit of the project as a percentage of the initial investment. A higher ROI is better.
    - **Internal Rate of Return (IRR):** A more advanced metric representing the project's intrinsic annual rate of return. A project is considered viable if its IRR is higher than your company's required rate of return.
    """)
