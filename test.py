import ast

# Your input string
# Specify the file path
file_path = "stops.txt"

# Read the content from the file
with open(file_path, "r") as file:
    input_string = file.read()
coordinates = ast.literal_eval(input_string)

# Print the resulting list
print(coordinates)