import os
import subprocess
import csv
import re

print("Processing test datasets...")

# Set path so you can run the script from any directory
baseDirectory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "datasets")

# Create or open the CSV file to record the results
with open(baseDirectory + '/results.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Group', 'Model 1', 'Model 2', 'Model 3', 'Global'])

    # Iterate through all folders and their files in the test datasets directory
    for folder in os.listdir(baseDirectory):
        groundTruth = 1 if 'mw' in folder else 0
        folderPath = os.path.join(baseDirectory, folder)
        totalFiles = 0
        correctPredictions = [0, 0, 0, 0]
        if os.path.isdir(folderPath):
            for file in os.listdir(folderPath):
                filePath = os.path.join(folderPath, file)
                if os.path.isfile(filePath):
                    curlCMD = [
                        'curl',
                        '-s',
                        '-XPOST',
                        '--data-binary', f'@{filePath}',
                        'http://127.0.0.1:8080/',
                        '-H', 'Content-Type: application/octet-stream'
                    ]
                    # Run the cURL command and capture the JSON response
                    response = subprocess.run(curlCMD, stdout=subprocess.PIPE)
                    response = response.stdout.decode('utf-8')
                    # Extract the prediction from the JSON response
                    globalPrediction = re.search(r'"malware":\s*(\d)', response)
                    if globalPrediction:
                        globalPrediction = int(globalPrediction.group(1))
                        if globalPrediction == groundTruth:
                            correctPredictions[-1] += 1
                        totalFiles += 1

                    # Extract the individual predictions from the JSON response
                    predictions = re.findall(r'"predictions":\s*\[(\d),\s*(\d),\s*(\d)\]', response)
                    if predictions:
                        predictions = predictions[0]
                        for i in range(len(predictions)):
                            if int(predictions[i]) == groundTruth:
                                correctPredictions[i] += 1
                
            for i in range(len(correctPredictions)):
                try:
                    correctPredictions[i] = "{:.2f}".format(correctPredictions[i] / totalFiles * 100)
                except ZeroDivisionError:
                    correctPredictions[i] = "0%"
            
            print(f"Group: {folder}, Model 1: {correctPredictions[0]}, Model 2: {correctPredictions[1]}, Model 3: {correctPredictions[2]}, Global: {correctPredictions[3]}")
            writer.writerow([folder, correctPredictions[0], correctPredictions[1], correctPredictions[2], correctPredictions[3]])
            
print("Finished processing test datasets.")
