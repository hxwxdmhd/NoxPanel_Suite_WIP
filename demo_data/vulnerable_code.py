
# Vulnerable Python code example
import subprocess
import pickle
import os

def execute_command(user_input):
    # Security vulnerability: Command injection
    result = subprocess.run(user_input, shell=True, capture_output=True)
    return result.stdout

def load_data(file_path):
    # Security vulnerability: Pickle deserialization
    with open(file_path, 'rb') as f:
        data = pickle.load(f)  # Unsafe!
    return data

def get_secret():
    # Security vulnerability: Hardcoded credentials
    api_key = "sk-1234567890abcdef"
    return api_key

# Performance issue: Inefficient loop
def slow_function(data_list):
    result = []
    for i in range(len(data_list)):
        for j in range(len(data_list)):
            if data_list[i] == data_list[j] and i != j:
                result.append(data_list[i])
    return result
