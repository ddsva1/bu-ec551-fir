import csv

# Define the filename and the header columns
filename = input("name of csv file? (omit .csv) ")
filename = "csv-params/"+filename+".csv"
headers = ["values"]

print(f"Creating/Opening '{filename}' to save inputs...")

# Open the file in write mode ('w'). 'newline=""' prevents blank row issues.
with open(filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    
    # Write the column headers first
    writer.writerow(headers)

    #add parameters here - also, need to add the error checking for values
    #change to add to dict then csv?
    window = input("Enter Window of Observation - how many of the last inputs? Min 1: ")
    period = input("Enter period of time in ns between sampled inputs: ")
    max_inputs = input("Enter maximum amount of time in ns that program should run for: ")
    
    # Write the gathered inputs as a single row
    #potentially change to reading from/iterating through array instead of just listing out all rows
    writer.writerow([window])
    writer.writerow([period])
    writer.writerow([max_inputs])
    print("Data saved successfully.")

print(f"\nAll done! Data has been successfully written to {filename}.")