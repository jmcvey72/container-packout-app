# container_packout_app.py
import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Container Packout Tool", layout="wide")
st.title("📦 Container Packout Optimization Tool")

st.markdown("""
Upload your Excel order file and this tool will:
- Calculate total pallets and weight
- Apply stacking rules (fuels can be double stacked)
- Determine if it fits in a 20' or 40' container
""")

uploaded_file = st.file_uploader("Upload your Order Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Ensure expected columns exist
    expected_cols = ["Part Number", "Description", "Case Qty Ordered", "Cases per Pallet", "Pallet Weight (lbs)", "Is Fuel (Double Stackable)"]
    if not all(col in df.columns for col in expected_cols):
        st.error("Excel file missing required columns. Please use the provided template.")
    else:
        # Calculate pallets required and total pallet weight
        df["Pallets Required"] = (df["Case Qty Ordered"] / df["Cases per Pallet"]).apply(lambda x: math.ceil(x) if pd.notnull(x) else 0)
        df["Total Pallet Weight"] = df["Pallets Required"] * df["Pallet Weight (lbs)"]

        # Total pallet counts by type
        fuel_df = df[df["Is Fuel (Double Stackable)"] == "Yes"]
        nonfuel_df = df[df["Is Fuel (Double Stackable)"] != "Yes"]

        fuel_pallets = fuel_df["Pallets Required"].sum()
        nonfuel_pallets = nonfuel_df["Pallets Required"].sum()
        total_weight = df["Total Pallet Weight"].sum()

        # Container logic
        result_data = []

        result_data.append({
            "Container": "20' Single Stack",
            "Max Pallets": 10,
            "Max Weight": None,
            "Fuel Pallets": fuel_pallets,
            "Non-Fuel Pallets": nonfuel_pallets,
            "Total Pallets": fuel_pallets + nonfuel_pallets,
            "Total Weight": total_weight,
            "Fits": "Yes" if (fuel_pallets + nonfuel_pallets) <= 10 else "No"
        })

        result_data.append({
            "Container": "20' Double Stack (Fuels Only)",
            "Max Pallets": 20,
            "Max Weight": None,
            "Fuel Pallets": fuel_pallets,
            "Non-Fuel Pallets": 0,
            "Total Pallets": fuel_pallets,
            "Total Weight": fuel_df["Total Pallet Weight"].sum(),
            "Fits": "Yes" if fuel_pallets <= 20 else "No"
        })

        result_data.append({
            "Container": "40' Single Stack",
            "Max Pallets": 20,
            "Max Weight": 42800,
            "Fuel Pallets": fuel_pallets,
            "Non-Fuel Pallets": nonfuel_pallets,
            "Total Pallets": fuel_pallets + nonfuel_pallets,
            "Total Weight": total_weight,
            "Fits": "Yes" if (fuel_pallets + nonfuel_pallets) <= 20 and total_weight <= 42800 else "No"
        })

        result_data.append({
            "Container": "40' Double Stack (Fuels Only)",
            "Max Pallets": 40,
            "Max Weight": 42800,
            "Fuel Pallets": fuel_pallets,
            "Non-Fuel Pallets": 0,
            "Total Pallets": fuel_pallets,
            "Total Weight": fuel_df["Total Pallet Weight"].sum(),
            "Fits": "Yes" if fuel_pallets <= 40 and fuel_df["Total Pallet Weight"].sum() <= 42800 else "No"
        })

        st.subheader("📊 Container Fit Summary")
        st.dataframe(pd.DataFrame(result_data))

        st.subheader("🔍 Order Breakdown")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Detailed Order Report", data=csv, file_name="order_packout_summary.csv", mime="text/csv")
else:
    st.info("Please upload an Excel file to begin.")
