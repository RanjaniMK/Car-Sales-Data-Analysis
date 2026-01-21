import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

st.title(" CAR SALES DATA ANALYSIS")

st.subheader("CSV FILE VIEWER")
st.write("Upload a file and view it's  contents")

#Upload a CSV file

uploaded_file=st.file_uploader("Car_sales.csv", type=["csv"])

if uploaded_file is not None:
    #Read and display data from the CSV file
    data=pd.read_csv(uploaded_file)
    st.title("Exploratory Data Analysis")
    st.write("DATA FROM THE UPLOADED CSV FILE:")
    st.write(data)

    #Adding basic statistics
    st.write("Basic Statistics")
    st.write(data.describe())


    #Multiple Histograms for Different Variables
    st.subheader("Histogram Visualization:")

    selected_column = st.selectbox("Select a column for the histogram", data.columns)

    # Create figure and axis objects
    fig, ax = plt.subplots(figsize=(8, 6))

    # Plot on the specific axis
    sns.histplot(data[selected_column], kde=True, ax=ax)

    # Set labels and title
    ax.set_title(f'Distribution of {selected_column}', fontsize=14, fontweight='bold')
    ax.set_xlabel(selected_column, fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.grid(True, alpha=0.3)

    # Pass the figure object to st.pyplot()
    st.pyplot(fig)

    # Close the figure to free memory
    plt.close(fig)

    #Display data shape
    st.subheader("Data Shape")
    st.write(f"The dataset has {data.shape[0]} rows and {data.shape[1]} columns.")

   

