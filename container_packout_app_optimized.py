import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Optimized Container Packout Tool", layout="wide")
st.title("📦 Optimized Container Packout Tool")

st.markdown("""
Upload your Excel order file and this tool will:
- Combine SKUs to maximize pallet space
- Keep fuel and non-fuel on separate pallets
- Apply stacking rules (fuels can be double stacked)
- Determine if the optimized load fits in a 20' or 40' container
""")

uploaded_file = st.file_uploader("Upload your Order Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    expected_cols = ["Part Number", "Description", "Case Qty Ordered", "Pallet Weight (lbs)", "Is Fuel (Double Stackable)"]
    if not all(col in df.columns for col in expected_cols):
        st.error("Excel file is missing required columns. Please use the correct template.")
    else:
        df["Cases per Pallet"] = None

        for idx in df.index:
            excel_row = idx + 5  # Adjust for Excel indexing
            if 7 <= excel_row <= 159:
                df.at[idx, "Cases per Pallet"] = 77.42
            elif 161 <= excel_row <= 166:
                df.at[idx, "Cases per Pallet"] = 18
            elif 167 <= excel_row <= 179:
                df.at[idx, "Cases per Pallet"] = 26
            elif 181 <= excel_row <= 366:
                df.at[idx, "Cases per Pallet"] = pd.to_numeric(df.at[idx, "Cases per Pallet"], errors="coerce")

        df["Case Qty Ordered"] = pd.to_numeric(df["Case Qty Ordered"], errors="coerce")
        df["Pallet Weight (lbs)"] = pd.to_numeric(df["Pallet Weight (lbs)"], errors="coerce")
        df = df.dropna(subset=["Case Qty Ordered", "Cases per Pallet", "Pallet Weight (lbs)"])

        # Create list of individual cases with type separation
        cases = []
        for _, row in df.iterrows():
            case_weight = row["Pallet Weight (lbs)"] / row["Cases per Pallet"]
            for _ in range(int(row["Case Qty Ordered"])):
                cases.append({
                    "Part Number": row["Part Number"],
                    "Weight": case_weight,
                    "Is Fuel": row["Is Fuel (Double Stackable)"] == "Yes"
                })

        # Define max constraints
        MAX_CASES_PER_PALLET = 77.42
        MAX_PALLET_WEIGHT = 1800

        # Separate fuel and non-fuel cases
        fuel_cases = [c for c in cases if c["Is Fuel"]]
        nonfuel_cases = [c for c in cases if not c["Is Fuel"]]

        def pack_cases(case_list):
            pallets = []
            current = []
            count = 0
            weight = 0
            for case in case_list:
                if count + 1 > MAX_CASES_PER_PALLET or weight + case["Weight"] > MAX_PALLET_WEIGHT:
                    pallets.append(current)
                    current = []
                    count = 0
                    weight = 0
                current.append(case)
                count += 1
                weight += case["Weight"]
            if current:
                pallets.append(current)
            return pallets

        fuel_pallets = pack_cases(fuel_cases)
        nonfuel_pallets = pack_cases(nonfuel_cases)
        all_pallets = fuel_pallets + nonfuel_pallets

        fuel_weight = sum(sum(c["Weight"] for c in p) for p in fuel_pallets)
        total_weight = fuel_weight + sum(sum(c["Weight"] for c in p) for p in nonfuel_pallets)

        result_data = [
            {
                "Container": "20' Single Stack",
                "Max Pallets": 10,
                "Total Pallets": len(all_pallets),
                "Total Weight": total_weight,
                "Fits": "Yes" if len(all_pallets) <= 10 else "No"
            },
            {
                "Container": "20' Double Stack (Fuels Only)",
                "Max Pallets": 20,
                "Total Pallets": len(fuel_pallets),
                "Total Weight": fuel_weight,
                "Fits": "Yes" if len(fuel_pallets) <= 20 else "No"
            },
            {
                "Container": "40' Single Stack",
                "Max Pallets": 20,
                "Max Weight": 42800,
                "Total Pallets": len(all_pallets),
                "Total Weight": total_weight,
                "Fits": "Yes" if len(all_pallets) <= 20 and total_weight <= 42800 else "No"
            },
            {
                "Container": "40' Double Stack (Fuels Only)",
                "Max Pallets": 40,
                "Max Weight": 42800,
                "Total Pallets": len(fuel_pallets),
                "Total Weight": fuel_weight,
                "Fits": "Yes" if len(fuel_pallets) <= 40 and fuel_weight <= 42800 else "No"
            }
        ]

        st.subheader("📊 Optimized Container Fit Summary")
        st.dataframe(pd.DataFrame(result_data))

        st.subheader("📦 Total Pallets Built")
        st.write(f"Total Pallets: {len(all_pallets)}")
        st.write(f"Fuel Pallets: {len(fuel_pallets)} | Non-Fuel Pallets: {len(nonfuel_pallets)}")

else:
    st.info("Please upload an Excel file to begin.")
