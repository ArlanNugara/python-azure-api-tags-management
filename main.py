import sys
from definitions.azure.initialize import start_azure_process

print("Initializing the code..")

if sys.argv[1] == "Azure":
    start_azure_process(sys.argv[1], sys.argv[2], sys.argv[3])
elif sys.argv[1] == "AzureChina":
    start_azure_process(sys.argv[1], sys.argv[2], sys.argv[3])
else:
    print("No Match found. Please provide either 'Azure' or 'AzureChina' as argument")
    sys.exit(1)