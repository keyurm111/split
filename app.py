# app.py
import streamlit as st
import pandas as pd
import os
import zipfile

# -------------------------------
# FUNCTIONS
# -------------------------------

def split_csv_to_batches(df, batch_size=10):
    total_batches = (len(df) + batch_size - 1) // batch_size
    batch_files = []

    # Create a temp folder for batches
    os.makedirs('batches', exist_ok=True)

    for i in range(total_batches):
        batch_df = df.iloc[i*batch_size : (i+1)*batch_size]
        batch_file = f'batches/batch_{i+1}.csv'
        batch_df.to_csv(batch_file, index=False)
        batch_files.append(batch_file)

    return batch_files

def create_zip(batch_files, zip_name='batches.zip'):
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for file in batch_files:
            zipf.write(file)
    return zip_name

# -------------------------------
# STREAMLIT UI
# -------------------------------

st.set_page_config(page_title="CSV Batch Splitter", layout="centered")
st.title("📊 CSV Batch Splitter")

st.write("Upload any CSV file, split it into batches, and download them all at once!")

uploaded_file = st.file_uploader("🔼 Upload your CSV file here", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("✅ **File uploaded!** Preview:")
    st.dataframe(df.head())

    batch_size = st.number_input("Select batch size:", min_value=1, value=10, step=1)

    if st.button("🚀 Split & Download"):
        with st.spinner("Processing..."):
            batch_files = split_csv_to_batches(df, batch_size)
            zip_file = create_zip(batch_files)

            with open(zip_file, 'rb') as f:
                st.download_button(
                    label="📥 Download ZIP of Batches",
                    data=f,
                    file_name='batches.zip',
                    mime='application/zip'
                )

        # Clean up batches folder after creating ZIP
        for file in batch_files:
            os.remove(file)
        os.rmdir('batches')
        os.remove(zip_file)

        st.success("✅ Done! Your batches ZIP is ready.")

else:
    st.info("Please upload a CSV file to get started.")
