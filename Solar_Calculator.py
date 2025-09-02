import streamlit as st
import numpy as np
import numpy_financial as npf
import pandas as pd

# --- Core Calculation Functions ---

def calculate_scaled_cost(base_cost, base_scale, new_scale, scaling_factor):
    """
    Applies the Cost-to-Capacity formula to estimate costs for different project sizes.
    Used for both CAPEX and Maintenance costs, incorporating economies of scale.
    
    Formula: New Cost = Base Cost * (New Scale / Base Scale) ^ Scaling Factor
    """
    if base_scale <= 0:
        st.error("Base scale must be greater than zero for scaling calculations.")
        return 0
    return base_cost * (new_scale / base_scale) ** scaling_factor

def calculate_solar_financials(capex, contingency_pct, annual_kwh, price_per_kwh, maintenance_cost, plant_lifetime):
    """
    Calculates all key financial metrics and returns them in a single dictionary.
    """
    # --- Perform all calculations to ensure consistency ---
    contingency_amount = capex * (contingency_pct / 100.0)
    initial_investment = capex + contingency_amount
    annual_revenue = annual_kwh * price_per_kwh
    annual_profit = annual_revenue - maintenance_cost
    lifetime_profit = annual_profit * plant_lifetime
    lifetime_maintenance_cost = maintenance_cost * plant_lifetime

    # --- Initialize results with default/non-profitable values ---
    results = {
        "initial_investment": initial_investment,
        "contingency_amount": contingency_amount,
        "annual_revenue": annual_revenue,
        "maintenance_cost": maintenance_cost,
        "annual_profit": annual_profit,
        "lifetime_profit": lifetime_profit,
        "lifetime_maintenance_cost": lifetime_maintenance_cost,
        "simple_payback": float('inf'), # Represents an infinite payback period
        "roi": -1.0,
        "irr": -1.0, # Using -1 as a flag for non-profitable
    }

    # --- If the project is profitable, calculate the main metrics ---
    if annual_profit > 0 and initial_investment > 0:
        results["simple_payback"] = initial_investment / annual_profit
        net_gain = lifetime_profit - initial_investment
        results["roi"] = net_gain / initial_investment
        # Cash flow: initial investment is negative, followed by positive annual profits
        cash_flows = [-initial_investment] + [annual_profit] * plant_lifetime
        results["irr"] = npf.irr(cash_flows)
    
    return results

# --- Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="Solar Farm Business Calculator")

# --- Custom CSS for Notion-style banner ---
st.markdown(
    """
    <style>
    /* This CSS targets the first image element on the page to style it as a banner */
    div[data-testid="stImage"]:first-of-type {
        border-radius: 10px;
        height: 20vh; /* Banner height is 20% of the viewport height */
        overflow: hidden; /* Ensures the image respects the border-radius */
        margin-bottom: 2rem; /* Adds some space below the banner */
    }
    
    div[data-testid="stImage"]:first-of-type img {
        object-fit: cover; /* Ensures the image covers the area without distortion */
        object-position: center; /* Centers the image within the frame */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Display the logo as a banner ---
# Replace the URL with your logo's path or link. Using a placeholder for demonstration.
st.image(
    "https://placehold.co/1600x400/333652/E9E8E8?text=Solar+Farm+Business+Calculator", 
    use_container_width=True
)

st.title("☀️ Solar Farm Business Calculator")
st.markdown("An advanced tool for financial modeling and scenario analysis of solar farm projects.")
st.markdown("---")


# --- NEW: Business Discussion Tools Section ---
st.header("🚀 Business Discussion Tools")
st.info("Use these tools for high-level planning and to quickly answer key questions from stakeholders.")

# Define base assumptions for quick calculations
BASE_MW = 1.0
BASE_CAPEX_MIL = 1.0
BASE_KWH_PER_MW_MIL = 1.5
BASE_MAINT_K = 30.0
HECTARES_PER_MW = 1.0

tab1, tab2 = st.tabs([
    "Scenario 1: From Investment & Land", 
    "Scenario 2: From Plant Size (MW)"
])

# --- Tab 1: Calculate from Investment and Land ---
with tab1:
    st.subheader("What can I get with my investment and land?")
    
    col1, col2 = st.columns(2)
    with col1:
        bus_investment_mil = st.number_input("Available Investment (Million FJD)", min_value=0.1, value=2.0, step=0.1, key="bus_invest")
        bus_land_hectares = st.number_input("Available Land (Hectares)", min_value=0.1, value=3.0, step=0.1, key="bus_land")
    
    with col2:
        bus_price_per_kwh = st.number_input("Expected Price per kWh (FJD)", min_value=0.01, value=0.17, step=0.01, format="%.2f", key="bus_price")
        bus_plant_lifetime = st.slider("Plant Lifetime (Years)", min_value=5, max_value=40, value=25, key="bus_life")
    
    st.markdown("###### Economies of Scale Assumptions")
    scale_col1, scale_col2 = st.columns(2)
    with scale_col1:
        capex_scaling_factor = st.slider("CAPEX Scaling Factor (n)", min_value=0.4, max_value=1.0, value=0.7, step=0.05,
                                         help="Represents capex savings on larger projects. Lower = greater savings. Typical for solar: 0.6-0.8", key="bus_capex_scale")
    with scale_col2:
        maint_scaling_factor = st.slider("Maintenance Scaling Factor (n)", min_value=0.5, max_value=1.0, value=0.85, step=0.05,
                                         help="Represents maintenance savings on larger projects. Lower = greater savings. Typical: 0.8-0.95", key="bus_maint_scale")

    if st.button("Analyze Investment & Land Scenario", type="primary"):
        # Determine max MW from each constraint
        mw_from_land = bus_land_hectares / HECTARES_PER_MW
        # Inverse of scaling formula to find MW from CAPEX
        mw_from_capex = BASE_MW * (bus_investment_mil / BASE_CAPEX_MIL) ** (1 / capex_scaling_factor)

        # The real constraint is the minimum of the two
        final_mw = min(mw_from_land, mw_from_capex)
        constraint = "Land Area" if final_mw == mw_from_land else "Investment"

        # Calculate final parameters based on the constrained MW
        final_capex_mil = calculate_scaled_cost(BASE_CAPEX_MIL, BASE_MW, final_mw, capex_scaling_factor)
        final_annual_kwh = final_mw * BASE_KWH_PER_MW_MIL * 1_000_000
        final_maintenance_cost = calculate_scaled_cost(BASE_MAINT_K * 1000, BASE_MW, final_mw, maint_scaling_factor)
        
        # We use the *actual available investment* for financial calculations if investment is the constraint
        capex_for_calc = bus_investment_mil * 1_000_000 if constraint == "Investment" else final_capex_mil * 1_000_000

        # Get financial results
        bus_results = calculate_solar_financials(
            capex=capex_for_calc,
            contingency_pct=0, # Assuming the investment is all-in for this tool
            annual_kwh=final_annual_kwh,
            price_per_kwh=bus_price_per_kwh,
            maintenance_cost=final_maintenance_cost,
            plant_lifetime=bus_plant_lifetime
        )

        st.markdown("---")
        st.subheader("Scenario Results")
        st.warning(f"This project is primarily constrained by **{constraint}**.")
        
        # Display output
        out_col1, out_col2, out_col3 = st.columns(3)
        out_col1.metric("Buildable Plant Size", f"{final_mw:.2f} MW")
        out_col2.metric("Estimated CAPEX", f"{final_capex_mil:.2f}M FJD")
        out_col3.metric("Annual Output", f"{final_annual_kwh / 1_000_000:.2f}M kWh")
        
        out_col4, out_col5, out_col6 = st.columns(3)
        out_col4.metric("Annual Revenue", f"{bus_results['annual_revenue']/1_000_000:.2f}M FJD")
        out_col5.metric("ROI", f"{bus_results['roi']:.2%}")
        out_col6.metric("Payback Period", f"{bus_results['simple_payback']:.2f} Years" if bus_results['roi']!=-1 else "N/A")

# --- Tab 2: Calculate from Desired Plant Size ---
with tab2:
    st.subheader("How much will it cost and what is the return?")
    
    col3, col4 = st.columns(2)
    with col3:
        bus_desired_mw = st.number_input("Desired Plant Size (MW)", min_value=0.1, value=1.0, step=0.1, key="bus_mw")
    with col4:
        bus_price_per_kwh_2 = st.number_input("Expected Price per kWh (FJD)", min_value=0.01, value=0.17, step=0.01, format="%.2f", key="bus_price_2")
    
    bus_plant_lifetime_2 = st.slider("Plant Lifetime (Years)", min_value=5, max_value=40, value=25, key="bus_life_2")
    
    st.markdown("###### Economies of Scale Assumptions")
    scale_col3, scale_col4 = st.columns(2)
    with scale_col3:
        capex_scaling_factor_2 = st.slider("CAPEX Scaling Factor (n)", min_value=0.4, max_value=1.0, value=0.7, step=0.05, key="bus_capex_scale_2")
    with scale_col4:
        maint_scaling_factor_2 = st.slider("Maintenance Scaling Factor (n)", min_value=0.5, max_value=1.0, value=0.85, step=0.05, key="bus_maint_scale_2")

    if st.button("Analyze Plant Size Scenario", type="primary"):
        # Calculate parameters from desired MW
        req_land = bus_desired_mw * HECTARES_PER_MW
        req_capex_mil = calculate_scaled_cost(BASE_CAPEX_MIL, BASE_MW, bus_desired_mw, capex_scaling_factor_2)
        req_annual_kwh = bus_desired_mw * BASE_KWH_PER_MW_MIL * 1_000_000
        req_maintenance_cost = calculate_scaled_cost(BASE_MAINT_K * 1000, BASE_MW, bus_desired_mw, maint_scaling_factor_2)
        
        bus_results_2 = calculate_solar_financials(
            capex=req_capex_mil * 1_000_000,
            contingency_pct=10, # Add a default 10% contingency for this estimate
            annual_kwh=req_annual_kwh,
            price_per_kwh=bus_price_per_kwh_2,
            maintenance_cost=req_maintenance_cost,
            plant_lifetime=bus_plant_lifetime_2
        )

        st.markdown("---")
        st.subheader("Scenario Results")
        
        # Display output
        out_col7, out_col8, out_col9 = st.columns(3)
        out_col7.metric("Required Land", f"{req_land:.2f} Hectares")
        out_col8.metric("Estimated CAPEX", f"{req_capex_mil:.2f}M FJD")
        out_col9.metric("Total Investment (w/ 10% Contingency)", f"{bus_results_2['initial_investment']/1_000_000:.2f}M FJD")

        out_col10, out_col11, out_col12 = st.columns(3)
        out_col10.metric("Annual Revenue", f"{bus_results_2['annual_revenue']/1_000_000:.2f}M FJD")
        out_col11.metric("ROI", f"{bus_results_2['roi']:.2%}")
        out_col12.metric("Payback Period", f"{bus_results_2['simple_payback']:.2f} Years" if bus_results_2['roi']!=-1 else "N/A")


# --- Detailed Financial Model Section ---
st.markdown("---")
with st.expander("🔬 Detailed Financial Model", expanded=False):
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
        plant_lifetime = st.slider("Plant Lifetime (Years)", min_value=5, max_value=40, value=25, key="detail_lifetime")

    # --- Calculation Trigger ---
    if st.button("Calculate Detailed Financials", type="primary"):
        st.session_state['primary_inputs'] = {
            'capex_mil': capex_mil, 'annual_kwh_mil': annual_kwh_mil, 'maintenance_cost_k': maintenance_cost_k,
            'contingency_percentage': contingency_percentage, 'price_per_kwh': price_per_kwh, 'plant_lifetime': plant_lifetime
        }
        
        results = calculate_solar_financials(
            capex_mil * 1_000_000, contingency_percentage, annual_kwh_mil * 1_000_000, price_per_kwh, maintenance_cost_k * 1_000, plant_lifetime
        )
        st.session_state['results'] = results

    # --- Display Results (if they exist in session state) ---
    if 'results' in st.session_state:
        results = st.session_state['results']
        st.markdown("---")
        st.header("📊 Key Financial Metrics")

        if results['roi'] != -1.0:
            res_col1, res_col2, res_col3 = st.columns(3)
            res_col1.metric("Return on Investment (ROI)", f"{results['roi']:.2%}")
            res_col2.metric("Simple Payback Period", f"{results['simple_payback']:.2f} Years")
            res_col3.metric("Internal Rate of Return (IRR)", f"{results['irr']:.2%}")

            st.success(
                f"With an initial investment of **{results['initial_investment']:,.2f} FJD** (including a "
                f"{results['contingency_amount']:,.2f} FJD contingency), the project is projected "
                f"to pay for itself in approximately **{results['simple_payback']:.2f} years**."
            )
            
            st.header("💰 Financials Breakdown")
            
            # Row 1 for Annual figures
            ann_row1_col1, ann_row1_col2, ann_row1_col3 = st.columns(3)
            ann_row1_col1.metric("Annual Revenue", f"{results['annual_revenue']:,.2f} FJD")
            ann_row1_col2.metric("Annual Maintenance", f"{results['maintenance_cost']:,.2f} FJD")
            ann_row1_col3.metric("Annual Profit", f"{results['annual_profit']:,.2f} FJD")

            # Row 2 for Lifetime figures
            ann_row2_col1, ann_row2_col2, _ = st.columns(3) # Use a spacer column
            ann_row2_col1.metric("Lifetime Profit", f"{results['lifetime_profit']:,.2f} FJD")
            ann_row2_col2.metric("Lifetime Maintenance", f"{results['lifetime_maintenance_cost']:,.2f} FJD")

        else:
            st.error("The project is not profitable with the given inputs (Annual Revenue does not exceed Maintenance Costs).")

# --- Interactive Scenario Analysis Section ---
if 'results' in st.session_state:
    st.markdown("---")
    st.header("📈 Interactive Scenario Analysis")
    
    inputs = st.session_state['primary_inputs']
    
    control_col, graph_col = st.columns([1, 2])
    with control_col:
        st.subheader("Scenario Controls")
        scenario_capex_mil = st.slider("Adjust CAPEX (Million FJD)", 1.0, 3.0, inputs['capex_mil'], 0.1, key="scenario_capex")
        scenario_maintenance_k = st.slider("Adjust Annual Maintenance (k FJD)", 10.0, 100.0, inputs['maintenance_cost_k'], 5.0, key="scenario_maint")
        scenario_contingency_pct = st.slider("Adjust Contingency (%)", 0, 25, inputs['contingency_percentage'], key="scenario_contingency")
        show_irr = st.checkbox("Show IRR Sensitivity Graph", value=True)
        
    with graph_col:
        price_scenarios = np.linspace(0.10, 0.40, 31)
        graph_data = []
        for price in price_scenarios:
            scenario_results = calculate_solar_financials(
                scenario_capex_mil * 1_000_000, scenario_contingency_pct, inputs['annual_kwh_mil'] * 1_000_000, 
                price, scenario_maintenance_k * 1_000, inputs['plant_lifetime']
            )
            graph_data.append({
                "Price per kWh (FJD)": price, 
                "IRR": scenario_results['irr'], 
                "Payback Period (Years)": scenario_results['simple_payback']
            })
        
        graph_df = pd.DataFrame(graph_data).round(2)
        
        st.subheader("Payback Period vs. Price per kWh")
        st.line_chart(graph_df.set_index("Price per kWh (FJD)")[['Payback Period (Years)']], use_container_width=True)

        if show_irr:
            st.subheader("IRR vs. Price per kWh")
            st.line_chart(graph_df.set_index("Price per kWh (FJD)")[['IRR']], use_container_width=True)

# --- Explanations Expander ---
with st.expander("What do these metrics mean?"):
    st.markdown("""
    - **Return on Investment (ROI):** Measures the total net profit of the project as a percentage of the initial investment. A higher ROI is better.
    - **Simple Payback Period:** The number of years it takes for the project's profits to equal the initial investment. A shorter payback period is generally better.
    - **Internal Rate of Return (IRR):** A more advanced metric representing the project's intrinsic annual rate of return. A project is considered viable if its IRR is higher than your company's required rate of return.
    - **Economies of Scale (Scaling Factor 'n'):** This principle states that larger projects are often cheaper per unit. A scaling factor of 1.0 means cost scales linearly (no savings). A factor of 0.7 means a 10x increase in size only costs 10^0.7 = ~5x as much.
    """)

