import streamlit as st
import numpy as np
# Using numpy_financial is safer for compatibility across different environments
# as it was separated from the main numpy library for a time.
# To install: pip install numpy-financial
import numpy_financial as npf

# --- Financial Calculation Function ---
def calculate_solar_financials(capex, contingency_amount, annual_profit, plant_lifetime):
    """
    Calculates key financial metrics for a capital project like a solar farm.

    Args:
        capex (float): The total capital expenditure.
        contingency_amount (float): A budget reserve for unforeseen upfront costs.
        annual_profit (float): The expected net profit generated each year.
        plant_lifetime (int): The total operational lifetime of the plant in years.

    Returns:
        tuple: A tuple containing the initial investment, payback period, ROI, and IRR.
    """
    if annual_profit <= 0:
        return (0, float('inf'), -1.0, -1.0)

    # 1. Calculate the total initial investment
    initial_investment = capex + contingency_amount

    # 2. Simple Payback Period
    simple_payback = initial_investment / annual_profit if annual_profit > 0 else float('inf')

    # 3. Return on Investment (ROI)
    total_profit = annual_profit * plant_lifetime
    net_gain = total_profit - initial_investment
    roi = net_gain / initial_investment if initial_investment > 0 else 0

    # 4. Internal Rate of Return (IRR)
    # Create the cash flow stream: negative investment followed by positive annual profits
    cash_flows = [-initial_investment] + [annual_profit] * plant_lifetime
    # Use the numpy_financial library to calculate IRR
    irr = npf.irr(cash_flows)

    return initial_investment, simple_payback, roi, irr

# --- Streamlit App Layout ---

# Set the page configuration
st.set_page_config(layout="centered", page_title="Solar Financial Calculator")

# --- Main Panel for Title and Inputs ---
st.title("☀️ Solar Farm Financial Calculator")

# --- Placeholder for Company Logo ---
# To add your logo, create an 'assets' folder, place 'logo.png' inside,
# and uncomment the line below.
st.image("logo.png", width=200)

st.info(
    "**Note:** These calculations are benchmarked for a **1 Hectare, 1 MW** scale project. "
    "Please adjust the input values to reflect the specifics of your project."
)

st.markdown("---")
st.header("⚙️ Input Parameters")

# Use columns for a cleaner layout of input widgets
col1, col2 = st.columns(2)

with col1:
    capex = st.number_input(
        "Capital Expenditure (CAPEX) ($)",
        min_value=0.0,
        value=1_000_000.0,
        step=50_000.0,
        help="Total upfront cost of building the solar farm (panels, inverters, land, labor)."
    )
    annual_profit = st.number_input(
        "Annual Net Profit ($)",
        min_value=0.0,
        value=150_000.0,
        step=10_000.0,
        help="Expected profit each year after all operational costs (Opex) are paid."
    )

with col2:
    contingency_percentage = st.slider(
        "Contingency Budget (%)",
        min_value=0,
        max_value=25,
        value=10,
        help="Extra budget for unforeseen costs as a percentage of CAPEX."
    )
    plant_lifetime = st.slider(
        "Plant Lifetime (Years)",
        min_value=5,
        max_value=40,
        value=25,
        help="The expected operational lifetime of the solar farm."
    )

# Calculate the contingency amount from the percentage
contingency_amount = capex * (contingency_percentage / 100.0)


# --- Calculation and Display ---
initial_investment, simple_payback, roi, irr = calculate_solar_financials(
    capex, contingency_amount, annual_profit, plant_lifetime
)

st.markdown("---")
st.header("📊 Financial Metrics")

if annual_profit > 0:
    # Display results using st.metric for a nice visual presentation
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric(
        label="Simple Payback Period",
        value=f"{simple_payback:.2f} Years"
    )
    res_col2.metric(
        label="Return on Investment (ROI)",
        value=f"{roi:.2%}"
    )
    res_col3.metric(
        label="Internal Rate of Return (IRR)",
        value=f"{irr:.2%}"
    )

    # Provide a summary of the investment
    st.success(
        f"With an initial investment of **${initial_investment:,.2f}** (including a "
        f"${contingency_amount:,.2f} contingency), the project is projected "
        f"to pay for itself in approximately **{simple_payback:.2f} years** and deliver an IRR of **{irr:.2%}**."
    )
else:
    st.error("Annual profit must be greater than zero to calculate financial metrics.")


# --- Explanations Expander ---
with st.expander("What do these metrics mean?"):
    st.markdown("""
    - **Simple Payback Period:** The number of years it takes for the project's profits to equal the initial investment. A shorter payback period is generally better. This calculation does *not* account for the time value of money.

    - **Return on Investment (ROI):** Measures the total net profit of the project as a percentage of the initial investment. It tells you how much money you made relative to how much you spent. A higher ROI is better.

    - **Internal Rate of Return (IRR):** A more advanced metric that represents the project's intrinsic annual rate of return. It's the discount rate at which the Net Present Value (NPV) of all cash flows becomes zero. **A project is considered financially viable if its IRR is higher than your company's required rate of return or cost of capital.**
    """)
