"""
for description see the first ui.HTML statement. 
Potential developments; 
    boolean to only produce simulation index values (currently outputs both)
    averages of risk factors, if more columns with risk factor statistics appear
    facility to sort a different column other than the second - based on user input. 
    option to whether headers are included in input/output files
    PARKED
"""

import pandas as pd
import shiny
from shiny import ui, reactive, render  
import os
import tempfile

# Define the UI of the app
app_ui = ui.page_fluid(
    ui.h2("Critical Window App"),
    ui.HTML("This application requires 3 inputs; <br> 1/A .csv file with two columns; first should be an index and second the statistic of interest. <br> \
            2/the percentile of interest and <br> 3/the width of the critical window. <br> The app then calculates \
            the average of the critical window around that percentile. <br> \
            The user can use the sliders to modify the percentile or the width of the window. <br> \
            The user can also download the indices of the cw simulations in a csv file. <br><br>"),

    # File input, percentile and number of simulations sliders
    ui.input_file("file_input", "Upload File", accept=[".csv"]),
    ui.input_slider("percentile", "Choose Percentile (K)", min=0, max=1, value=0.5, step=0.001),
    ui.input_slider("cw_width", "Critical window width", min=0, max=0.1, value=0.002, step = 0.0005),
    
    # Button to download the filtered data
    ui.download_button("download_data", "Download Filtered Data"),

    # Text output to show file status and average statistic
    ui.output_text_verbatim("file_status"),
    ui.output_text_verbatim("avg_statistic")  # Display the average statistic
)

# Define the server logic of the app
def server(input, output, session):
    # Create a reactive value to store the file data
    file_data = reactive.Value(None)

    @reactive.Effect
    @reactive.event(input.file_input)
    def file_status():
        """Load the CSV file and store it as a reactive value."""
        file = input.file_input()
        if file:
            df = pd.read_csv(file[0]['datapath'])
            file_data.set(df)
            return "File loaded successfully."
        else:
            return "No file loaded."

    @reactive.Calc
    def filtered_data():
        """Process the data based on the selected percentile and Y."""
        df = file_data.get()
        if df is None:
            return None
        
        # Sort the dataframe by the 'statistic' column
        df_sorted = df.sort_values(by=df.columns[1])
        
        # Compute the target index based on the selected percentile
        n = len(df_sorted)
        target_idx = round(input.percentile() * n)
        
        # Get Y observations either side of the chosen percentile
        Y = round(input.cw_width() / 2 * n)
        start_idx = max(target_idx - Y, 0)
        end_idx = min(target_idx + Y + 1, n)
        
        return df_sorted.iloc[start_idx:end_idx]

    # Calculate the average of the statistic in the filtered data
    @output
    @render.text
    def avg_statistic():
        """Calculate and display the average of the 'statistic' column."""
        data = filtered_data()
        if data is not None and len(data) > 0:
            avg = data.iloc[:, 1].mean()  # Assuming 'statistic' is the second column
            return f"Average statistic in the window: {avg:.6f}"
        else:
            return "No data available to calculate average."

    @render.download(filename="filtered_data.csv")
    def download_data():
        """Generate and download the filtered data as a CSV file."""
        data = filtered_data()
        if data is not None:
            tmp_dir = tempfile.mkdtemp()
            tmp_file_path = os.path.join(tmp_dir, "filtered_data.csv")
            data.to_csv(tmp_file_path, index=False)
            return tmp_file_path

# Run the app
app = shiny.App(app_ui, server)
