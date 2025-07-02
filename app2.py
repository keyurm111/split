# app.py
import streamlit as st
import pandas as pd
import os
import zipfile
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------------
# FUNCTIONS
# -------------------------------

def split_csv_to_batches(df, batch_size=10):
    total_batches = (len(df) + batch_size - 1) // batch_size
    batch_dfs = []

    for i in range(total_batches):
        batch_df = df.iloc[i*batch_size : (i+1)*batch_size]
        batch_dfs.append(batch_df)

    return batch_dfs

def save_batches_to_csv_zip(batch_dfs, zip_name='batches.zip'):
    os.makedirs('batches', exist_ok=True)
    batch_files = []

    for idx, batch_df in enumerate(batch_dfs):
        batch_file = f'batches/batch_{idx+1}.csv'
        batch_df.to_csv(batch_file, index=False)
        batch_files.append(batch_file)

    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for file in batch_files:
            zipf.write(file)

    for file in batch_files:
        os.remove(file)
    os.rmdir('batches')

    return zip_name

def save_batches_to_excel(batch_dfs, excel_name='batches.xlsx'):
    with pd.ExcelWriter(excel_name, engine='openpyxl') as writer:
        for idx, batch_df in enumerate(batch_dfs):
            sheet_name = f'Batch_{idx+1}'
            batch_df.to_excel(writer, sheet_name=sheet_name, index=False)
    return excel_name

def upload_batches_to_google_sheets(batch_dfs, spreadsheet_name):
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("your_gs_creds.json", scope)
    client = gspread.authorize(creds)

    # Create new spreadsheet
    sh = client.create(spreadsheet_name)
    for idx, batch_df in enumerate(batch_dfs):
        sheet_name = f'Batch_{idx+1}'
        worksheet = sh.add_worksheet(title=sheet_name, rows=batch_df.shape[0]+1, cols=batch_df.shape[1])
        worksheet.update([batch_df.columns.values.tolist()] + batch_df.values.tolist())

    # Delete default empty sheet if needed
    sh.del_worksheet(sh.sheet1)

    return f"https://docs.google.com/spreadsheets/d/{sh.id}"

# -------------------------------
# STREAMLIT UI
# -------------------------------

st.set_page_config(page_title="CSV Batch Splitter", layout="centered")
st.title("📊 CSV Batch Splitter")

st.write("Upload any CSV file, split it into batches, and choose your output option!")

uploaded_file = st.file_uploader("🔼 Upload your CSV file here", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("✅ **File uploaded!** Preview:")
    st.dataframe(df.head())

    batch_size = st.number_input("Select batch size:", min_value=1, value=10, step=1)

    output_option = st.selectbox(
        "Choose output option:",
        ["ZIP of CSV batches", "One Excel file (multiple sheets)", "Upload to Google Sheets"]
    )

    if st.button("🚀 Split & Process"):
        batch_dfs = split_csv_to_batches(df, batch_size)

        if output_option == "ZIP of CSV batches":
            zip_file = save_batches_to_csv_zip(batch_dfs)
            with open(zip_file, 'rb') as f:
                st.download_button(
                    label="📥 Download ZIP",
                    data=f,
                    file_name=zip_file,
                    mime='application/zip'
                )
            os.remove(zip_file)
            st.success("✅ ZIP ready!")

        elif output_option == "One Excel file (multiple sheets)":
            excel_file = save_batches_to_excel(batch_dfs)
            with open(excel_file, 'rb') as f:
                st.download_button(
                    label="📥 Download Excel",
                    data=f,
                    file_name=excel_file,
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            os.remove(excel_file)
            st.success("✅ Excel ready!")

        elif output_option == "Upload to Google Sheets":
            spreadsheet_name = st.text_input("Enter Google Sheets name:", value="My Batches Spreadsheet")
            if spreadsheet_name and st.button("Upload to Google Sheets"):
                url = upload_batches_to_google_sheets(batch_dfs, spreadsheet_name)
                st.success(f"✅ Uploaded! [View your Google Sheet here]({url})")

else:
    st.info("Please upload a CSV file to get started.")
