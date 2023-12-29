## ENAE380 Final Project: HAB Float Prediction Application
## Akemi Takeuchi
## UID: 117550054
## Section: 0105

from urllib.request import urlretrieve
import pandas as pd
import datetime
from datetime import datetime, timedelta
import simplekml
import os
import PySimpleGUI as sg

## =========================================== GUI =========================================== ##
def generate_gui():
    """
    Generates a simple GUI for the user to input all data necessary for a float predict.
    Also has a log feature to communicate errors and status for ease of use.

    ### Parameters
    none

    ### Returns
    none
    """
    # Variable (int) to keep track of the total number of predicts
    count = 0

    # Defines the layout of the GUI, line by line
    layout = [
        [sg.Text('This tool will generate a CSV Google Earth Pro KML file for High-Altitude Ballooning (HAB) float profile predictions.', font=(sg.DEFAULT_FONT[0], sg.DEFAULT_FONT[1], 'bold'))],
        [sg.Text('Hover over the text to see valid input ranges.')],
        [sg.Text('Date of launch (MM/DD/YYYY): ', tooltip='Enter the date between 8 hours before and 6 days 23 hours after current date.'), sg.InputText(key='MM', size=(2, 1), enable_events=True, justification='center'), sg.Text("/"), sg.InputText(key='DD', size=(2, 1), enable_events=True, justification='center'), sg.Text("/"), sg.InputText(key='YYYY', size=(4, 1), enable_events=True, justification='center')],
        [sg.Text('Time of launch (HH:MM, UTC): ', tooltip ='Enter a time between 00:00 and 24:00 and within a range of 8 hours before\nand 6 days 23 hours after current time.'), sg.InputText(key='HH', size=(2, 1), enable_events=True, justification='center'), sg.Text(":"), sg.InputText(key='mm', size=(2, 1), enable_events=True, justification='center')],
        [sg.Text('Launch Location Latitude:', tooltip='Accepts values between -90 and 90 in decimal.'), sg.InputText(key='latitude', size = (12,1), enable_events=True)],
        [sg.Text('Launch Location Longitude:', tooltip='Accepts values between -180 and 180 in decimal.'), sg.InputText(key='longitude', size = (12,1), enable_events=True)],
        [sg.Text('Launch Location Altitude (m):', tooltip='Accepts values between -430 and 8848 m.'), sg.InputText(key='altitude', size = (12,1), enable_events=True)],
        [sg.Text('Ascent rate (m/s):', tooltip ='Enter a value between 1.5 m/s and 100 m/s.'), sg.InputText(key = 'ascent_rate', size = (6,1), enable_events=True)],
        [sg.Text('Float Altitude (m):', tooltip='Must be greater than launch location altitude.'), sg.InputText(key='float_alt', size = (12,1), enable_events=True)],
        [sg.Text('Float length (minutes):', tooltip = 'Enter a value no longer than 24 hours.'), sg.InputText(key='float_time', size = (6,1), enable_events=True)],
        [sg.Text('Log Console:', font=(sg.DEFAULT_FONT[0], sg.DEFAULT_FONT[1], 'bold'))],
        [sg.Multiline(size=(60,8), expand_x=True, expand_y=True, write_only = True, key = "error_console")],
        [sg.Button('Submit'), sg.Button('Cancel')],
        [sg.Button('Download CSV', disabled = True), sg.Button('Download KML', disabled = True)]
    ]

    # Open a window for the GUI using the defined layout
    window = sg.Window('HAB Float Predictor', layout)

    # For as long as the window is open and the user does not close it out (by closing it out or pressing the "Cancel" button)
    while True:
        event, values = window.read() # Constantly reads the window for values (user inputs) or events
    
        ## -- Handles all events that could occur in the GUI -- ##
        # Event 1: Clicking the "Cancel" button will close the window
        if event in (sg.WIN_CLOSED, 'Cancel'):
            break
        # Event 2: Any inputs into month, day, year, hour, minute, or float time should all be digits
        elif event in ('MM', 'DD', 'YYYY', 'HH', 'mm', 'float_time'):
            # For the month, day, hour, minute entries, mask the value if it gets longer than 2.
            if len(values[event]) > 2 and event in ('MM', 'DD','HH', 'mm'):
                window[event].update(values[event][:2])
            # For the year entry, mask the value if it gets longer than 4
            elif len(values[event]) > 4 and event == 'YYYY':
                window[event].update(values[event][:4])
            # Only allows digits for all specified input boxes.
            window[event].update(''.join(filter(str.isdigit, values[event])))
        
        # Event 3: Any inputs into latitude, longitude, altitude, ascent rate, or float altitude should all be float values
        elif event in ('latitude', 'longitude', 'altitude', 'ascent_rate', 'float_alt'):
            window[event].update(''.join(filter(lambda x: x.isdigit() or x == '.' or x == '-', values[event]))) # Allows for "." and "-" in the entry

        # Event 4: Clicking the "Submit" button will calculate the predict
        elif event == 'Submit':
            # Get values from input fields and store them in variables
            date = str(values['YYYY'][:4]) + '-' + str(values['MM'][:2]) + '-' + str(values['DD'][:2])
            time = [values['HH'][:2], values['mm'][:2]]
            long = values['longitude']
            lat = values['latitude']
            alt = values['altitude']
            ascent_rate = values['ascent_rate']
            burst_altitude = values['float_alt']  # Retrieving the 'float_alt' value
            float_time = values['float_time']

            # Store all the values into an array for function inputs
            input_data = [date, time, long, lat, alt, ascent_rate, burst_altitude, float_time]
            #print(input_data)

            # Perform error handling: returns an empty string "" if no errors, returns string with error messages if there are errors
            errors = error(input_data)
            if errors == "": # No errors
                predict_profile, success = flight_predict_data(input_data) # Get predict data, returns pandas dataframe and success status (bool)
                if success == False: # Flight predict failed
                    window['error_console'].update("Data retrival error. Please try again with sensible values.")
                elif success == True: # Flght predict success
                    count += 1 # The predict number increases
                    window['error_console'].update(f"Successful data retrival of predict {str(count)}!") 
                    window['Download CSV'].update(disabled = False) # Enable the download of CSV
                    window['Download KML'].update(disabled = False) # Enable the download of KML
            else: # If there are errors
                window['error_console'].update(errors) # Print all errors to the conole
                window['Download CSV'].update(disabled = True) # Disable the download of CSV
                window['Download KML'].update(disabled = True) # Disable the download of KML
        
        # Event 5: Clicking the "Download CSV" button will generate the CSV data of the flight predict
        elif event == 'Download CSV':
            folder_path = sg.popup_get_folder('Select a folder') # Let the user pick a file path
            if folder_path: # If the user picks a file path
                window['error_console'].update(f"Downloaded CSV for float predict {str(count)}.") # Print to the console with status update
                generate_csv(predict_profile, folder_path, count) # Generate the csv
            else: # If the user does not pick a file path
                sg.popup("Please select a folder.")

        # Event 6: Clicking the "Download KML" button will generate the KML of the flight predict, same in operation to CSV function
        elif event == 'Download KML':
            folder_path = sg.popup_get_folder('Select a folder') 
            if folder_path:
                #print(str(folder_path))
                window['error_console'].update(f"Downloaded KML for float predict {str(count)}.")   
                generate_kml(predict_profile, folder_path, count)
            else:
                sg.popup("Please select a folder.")
    
    # when the user closes out of the window
    window.close()

## ================================ ERROR HANDLING =========================================== ##
def error(data):
    """
    Error handling for all user inputs to make sure that they are within defined ranges.

    ### Parameters
    data (arr): [date (str), time (arr, [str, str]), long (str), lat (str), alt (str), ascent_rate (str), burst_altitude (str), float_time (str)]

    ### Returns
    error_message (str): Error message to be displayed in the console. Returns empty string when there are no errors.
    """
    # Create the error message based on the helper functions that determine if all values are valid
    error_message = date_error(data[0], data[1]) + long_error(data[2]) + lat_error(data[3]) + alt_error(data[4]) + ascent_rate_error(data[5]) + float_alt_error(data[6], data[4]) + float_time_error(data[7]) # Initialize error string

    return error_message

#### HELPER FUNCTIONS FOR INPUTS THAT REQUIRE ERROR MESSAGES -----------------------------------
def date_error(date, time):
    """
    Error handling for date and time when time is unable to be resolved (ie. HH >= 24) or when the time is out of range of prediction software.
    ### Parameters: date (str), time(arr: [str, str])
    ### Returns: message (str)
    """
    message = "" # Initialize error message
    date = date + 'T' + time[0] + ':' + time[1] # Format time
    format_string = "%Y-%m-%dT%H:%M" # Define the formatting of the time string
    # Handles errors
    try:
        input_time = datetime.strptime(date, format_string) # Resolve the string input to a datetime module
    except Exception: # If there is an error
        append = "ERROR: Check time to ensure that all inputs are valid."
        message = message + append + '\n'
    else: 
        # Calculate maimum and minimum times based on the current time
        current = datetime.now()
        min_time = current - timedelta(hours=8) # 8 hours into the past
        max_time = current + timedelta(days = 6, hours = 23) # 6 days and 23 hours into the future
    
        # Checks whether the launch time is within prediction range (past = 8 hours before current time, future = 6 days 23 hours after current time)
        if not(min_time < input_time < max_time):
            append = "Time not within prediction time range.\nPlease input a time between 8 hours prior or 6 days and 23 hours after current time."
            message = message + append + '\n'
    return message

def lat_error(float_val):
    """
    Error handling for latitude values when it is unable to be resolved to a float value or when it is out of range
    ### Parameters: float_val (str)
    ### Returns: message (str)
    """
    message = ""
    try: # Try resolving the latitude value to a float
        float(float_val)
    except Exception: # If there is an error, return an error message
        append = "ERROR: Float value cannot be read in launch location latitude." 
        message = message + append + '\n'
        return message
    else: # If there is no error, continue to check that the latitude is within [-90, 90]
        if not(-90 <= float(float_val) <= 90):
            append = "Launch location latitude value is not within range. Please input a value between -90 and 90."
            message = message + append + '\n'
            return message
        else:
            return message

# For concision, comments will not be repeated unless drastically new commands are called
def long_error(float_val):
    """
    Error handling for longitude values when it is unable to be resolved to a float value or when it is out of range [-180, 180]
    ### Parameters: float_val (str)
    ### Returns: message (str)
    """
    message = ""
    try:
        float(float_val)
    except Exception:
        append = "ERROR: Float value cannot be read in launch location longitude." 
        message = message + append + '\n'
        return message
    else:
        if not(-180 <= float(float_val) <= 180):
            append = "Launch location longitude value is not within range. Please input a value between -180 and 180."
            message = message + append + '\n'
            return message
        else:
            return message

def alt_error(float_val):
    """
    Error handling for altitude values when it is unable to be resolved to a float value or when it is out of range [-430, 8848]
    ### Parameters: float_val (str)
    ### Returns: message (str)
    """
    message = ""
    try:
        float(float_val)
    except Exception:
        append = "ERROR: Float value cannot be read in launch location altitude." 
        message = message + append + '\n'
        return message
    else:
        if not(-430 <= float(float_val) <= 8848):
            append = "Launch location altitude value is not within range. Please input a value between -430 m and 8848 m."
            message = message + append + '\n'
            return message
        else:
            return message

def ascent_rate_error(float_val):
    """
    Error handling for ascent rate values when it is unable to be resolved to a float value or when it is out of range (< 1.5)
    ### Parameters: float_val (str)
    ### Returns: message (str)
    """
    message = ""
    try: # Try resolving the latitude value to a float
        float(float_val)
    except Exception: # If there is an error, return an error message
        append = "ERROR: Decimal value cannot be read in ascent rate." 
        message = message + append + '\n'
        return message
    else: # If there is no error, continue to check that the latitude is within [-90, 90]
        if not(1.5 <= float(float_val) <= 100):
            append = "Ascent rate value is not within range. Please input a value between 1.5 and 100 m/s."
            message = message + append + '\n'
            return message
        else:
            return message

def float_alt_error(float_val, alt_val):
    """
    Error handling for float altitude values when it is unable to be resolved to a float value or when it is less than launch altitude or greater than 60000 m
    ### Parameters: float_val (str), alt_val (str)
    ### Returns: message (str)
    """
    message = ""
    try:
        float(float_val)
    except Exception: 
        append = "ERROR: Decimal value cannot be read in float altitude." 
        message = message + append + '\n'
        return message
    else:
        if not(float(float_val) <= 60000):
            append = "Float altitude value is not within range. Please input a value less than or equal to 60000 m."
            message = message + append + '\n'
        
        # Ensure that the altitude value can be converted to a float value, then compare the values. If not, return error message.
        if alt_error(alt_val) == "":
            if not(float(alt_val) < float(float_val)):
                append = "Launch altitude is higher than float altitude. Float altitude must be greater than launch altitude."
                message = message + append + '\n'
        else:
            append = "Unable to check float altitude. Check to make sure altitude is correct."
            message = message + append + '\n'
            return message
        return message

def float_time_error(float_val):
    """
    Error handling for float duration values when it is unable to be resolved to a float value or if it is greater than 24 hours
    ### Parameters: float_val (str)
    ### Returns: message (str)
    """
    message = ""
    try:
        int(float_val)
    except Exception:
        append = "ERROR: Int value cannot be read in float length." 
        message = message + append + '\n'
        return message
    else:
        if not(float(float_val) <= 1440):
            append = "Floar length is not within range. Please input a value less than 24 hours."
            message = message + append + '\n'
            return message
        else:
            return message
## =========================================== GENERATING FLOAT FLIGHT PREDICT DATAFRAME =========================================== ##
def flight_predict_data(data):
    """
    Retrieves flight prediction data based on user input.

    ### Parameters
    data (list): Contains input data for flight prediction.

    ### Returns
    flight_profile (pandas DataFrame): DataFrame containing flight prediction data.
    success (bool): Indicates the success of data retrieval.
    """

    # Define each of the variables from the input data
    date = data[0]
    time = data[1]
    long = data[2]
    lat = data[3]
    alt = data[4]
    ascent_rate = data[5]
    burst_altitude = data[6]
    float_time = data[7]

    # Further parsing of variables
    splitdate = date.split("-")
    stop_time = f"{splitdate[0]}-{splitdate[1]}-{int(splitdate[2])+1}" # Parse into datetime modulus and accomodate longer floats
    lat = round(float(lat), 4)
    long = round(float(long)%360, 4)
    burst_altitude = round(int(burst_altitude), -2)
    descent_rate = 9 # Descent rate is always assumed to be -9 m/s

    # Construct URL for API call
    url = f"https://api.v2.sondehub.org/tawhiri?profile=float_profile&pred_type=single&launch_datetime={date}T{time[0]}%3A{time[1]}%3A00Z&launch_latitude={lat}&launch_longitude={long}&launch_altitude={alt}&ascent_rate={ascent_rate}&float_altitude={burst_altitude}&stop_datetime={stop_time}T{time[0]}%3A{time[1]}%3A00Z&format=csv"

    # Download CSV data from the API using the constructed URL
    filename = "temporary.csv"
    try:
        urlretrieve(url, filename)
    except Exception:
        # Return empty DataFrame and False if data retrieval fails
        empty = pd.DataFrame()
        return empty, False

    df = pd.read_csv(filename)
    #print(df.head())
    float_time = round(int(float_time) / 20) * 20 # Rounds to the nearest interval of 20 minutes
    begin_float = ""
    append_index = 0
    # Find the time at which the float begins by finding the repeat altitude
    index = df[df['altitude'].eq(df['altitude'].shift())].index[0]
    begin_float= df.loc[index, 'datetime']

    # Convert the time that the float begins at and add the desired float time
    datetime_string = begin_float
    format_string = "%Y-%m-%dT%H:%M:%S.%fZ"
    parsed_datetime = datetime.strptime(datetime_string, format_string)
    time_interval = timedelta(minutes=float_time)

    # Calculate the end of float time
    end_float_time = parsed_datetime + time_interval
    rounded_end_float = end_float_time + timedelta(seconds=round(end_float_time.microsecond / 1e6))
    rounded_end_float = rounded_end_float.replace(microsecond=0)
    end_float_formatted = end_float_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-1] + 'Z' # Format datetime for end of float time

    # All variables for creating the link for the API
    term_date = rounded_end_float.date()
    term_time = str(rounded_end_float.time()).split(":")
    term_lat = ""
    term_long = ""
    term_alt = ""
    term_ascent = 1
    term_burst_alt = ""
    term_descent = descent_rate

    # Collect location data of the balloon once it has reached the end of its float and set variables accordingly so that they can be used to generate the API URL
    for index, value in df['datetime'].items():
        if end_float_formatted == value:
            term_lat = str(round(df.loc[index, 'latitude'], 4))
            term_long = str(round(df.loc[index, 'longitude'], 4)%360)
            term_alt = str(df.loc[index, 'altitude'])
            term_burst_alt = str(float(df.loc[index, 'altitude']) + 0.01) # We can simulate immediate termination by increasing altitude by 0.01 meters
            append_index = index
            break

    # Generate the termination flight profile data frame
    term_filename = "temporary_term.csv"
    term_url = f"https://api.v2.sondehub.org/tawhiri?profile=standard_profile&pred_type=single&launch_datetime={term_date}T{term_time[0]}%3A{term_time[1]}%3A{term_time[2]}Z&launch_latitude={term_lat}&launch_longitude={term_long}&launch_altitude={term_alt}&ascent_rate={term_ascent}&burst_altitude={term_burst_alt}&descent_rate={term_descent}&format=csv"
    urlretrieve(term_url, term_filename)
    descent_profile = pd.read_csv(term_filename)

    # Generate the flight predict csv
    ascend_float_profile = df.iloc[0:append_index+1]
    flight_profile = pd.concat([ascend_float_profile, descent_profile], ignore_index=True)

    # Delete temporary files
    os.remove(filename)
    os.remove(term_filename)
    
    return flight_profile, True

## =========================================== GENERATE THE CSV FILE =========================================== ##
def generate_csv(read_df, save_location, count):
    """
    Generates a CSV file from a DataFrame and saves it to the specified location.

    ### Parameters
    read_df (pandas DataFrame): DataFrame to be saved as a CSV.
    save_location (str): Path to the directory where the CSV file will be saved.
    count (int): Number to be included in the filename for identification purposes.
    ### Returns
    None
    """
    # Define the filename for the CSV based on the count and save location
    flight_predict = rf"{save_location}\flight_predict{count}.csv"
    # Save the DataFrame as a CSV file without index and with headers
    read_df.to_csv(flight_predict, index = False, header = True)

## =========================================== GENERATE THE KML FILE =========================================== ##
def generate_kml(read_df, save_location, count): #accepts a dataframe
    """
    Generates a KML file based on flight prediction data and saves it to the specified location.

    ### Parameters
    - read_df (pandas DataFrame): DataFrame containing flight prediction data.
    - save_location (str): Path to the directory where the KML file will be saved.
    - count (int): Number to be included in the filename for identification purposes.

    ### Returns
    None
    """

    # Create a KML object
    kml = simplekml.Kml()
    folder = kml.newfolder(name = "flight predict path")

    # Create an array for all the path coordinates
    coordinates = []

    # Read all the data from the file and make a flight predict profile
    for index, row in read_df.iterrows():
        long = row['longitude']
        lat = row['latitude']
        alt = row['altitude']
        coordinates.append((long, lat, alt))

    # Create a LineString in the KML object using the extracted coordinates
    path = folder.newlinestring(name="Flight Path")
    path.altitudemode = simplekml.AltitudeMode.absolute  # Set altitude mode to absolute
    path.coords = coordinates  # Assign the list of coordinates to the LineString

    # Style the LineString (path) - width and color
    path.style.linestyle.width = 3
    path.style.linestyle.color = simplekml.Color.red

    # Create a MultiGeometry for lines relative to the ground
    multi_geom = folder.newmultigeometry(name="Ground projections")

    # Create LineStrings for each point connecting to the ground
    for coord in coordinates:
        point_line = multi_geom.newlinestring(name=f"Point Line - {coord}")
        point_line.coords = [(coord[0], coord[1], coord[2]), (coord[0], coord[1], 0)]  # Connect point to ground

        # Style and altitude
        point_line.style.linestyle.color = simplekml.Color.red  # Change line color (red)
        point_line.style.linestyle.width = 4  # Change line width
        point_line.altitudemode = simplekml.AltitudeMode.absolute  # Set altitude mode to absolute

    # Create a Polygon based on the path coordinates
    multi_geom2 = folder.newmultigeometry(name="Polygons to Ground")
    for i in range(len(coordinates) - 1):
        coord1 = coordinates[i]
        coord2 = coordinates[i + 1]

        point_area = multi_geom2.newpolygon(name=f"Polygon - {i+1}")
        point_area.outerboundaryis = [coord1, coord2, (coord2[0], coord2[1], 0), (coord1[0], coord1[1], 0)]

        # Style
        point_area.style.linestyle.color = simplekml.Color.changealphaint(150, simplekml.Color.white)  # Edge color
        point_area.style.polystyle.color = simplekml.Color.changealphaint(150, simplekml.Color.white)
        point_area.altitudemode = simplekml.AltitudeMode.absolute

    # Add points for begining of float and end of float
    # Find the point at which altitude stays the same and take the first point to find when the float begins
    incr_index = None
    for index in range(0, len(read_df['altitude'])-1):
        if read_df['altitude'][index + 1] == read_df['altitude'][index]:
            incr_index = index
            break
    
    # Find the point at which altitude decreases to find when termination occurs
    decr_index = None
    for index in range(0, len(read_df['altitude'])-1):
        if read_df['altitude'][index + 1] < read_df['altitude'][index]:
            decr_index = index
            break
    
    # Calculate the coordinates of the two points (long, lat, alt)
    begin_float = (read_df.loc[incr_index, 'longitude'], read_df.loc[incr_index, 'latitude'], read_df.loc[incr_index, 'altitude'])
    end_float = (read_df.loc[decr_index, 'longitude'], read_df.loc[decr_index, 'latitude'], read_df.loc[decr_index, 'altitude'])

    # Create the points in the KML file
    begin_float_point = kml.newpoint(name="Begin Float", coords=[begin_float])
    begin_float_point.altitudemode = simplekml.AltitudeMode.absolute
    end_float_point = kml.newpoint(name="End Float (Termination)", coords=[end_float])
    end_float_point.altitudemode = simplekml.AltitudeMode.absolute

    # Save the KML file
    kml_file = rf"{save_location}\flight_predict_path{count}.kml"
    kml.save(kml_file)

# Run the application
generate_gui()