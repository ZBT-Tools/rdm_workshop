import pandas as pd
import os
import math
import matplotlib.pyplot as plt
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv
import helper_functions as hf

# import & define 'Excel Filter input' Speicherort&Name
path_Excel = "./filters/Filter_BZ011.xlsx" #spezifisch fürs Testing, muss über Explorer oä auswählbar sein
# Daten einlesen aus Filter (setID, NAvg, Auswertemethode)
Excel_Filter = pd.ExcelFile(path_Excel)
# Set dataframes mit Filter
df_Excel_Filter_Columns = pd.read_excel(Excel_Filter, 'header')
df_Excel_Filter_Sets = pd.read_excel(Excel_Filter, 'filter')

# Teststand auswählen
testbench_list = ['BZ011', 'BZ016', 'BZ_3Gleiche']
testbench_name = 'BZ011' #spezifisch fürs Testing, muss über Dropdown Menu oä auswählbar sein

col_set_id, datetime_format = hf.testbench_formats(testbench_name)
# Könnte man auch direkt mehrere Daten auswählen, indem man einen Ordner
# auswählt und alle enthaltenen Dateien aneinanderfügt?! Leider haben die
# Daten vom BZ-Teststand keine Dateiendung und ich kann nicht überprüfen, dass nur die richtigen Daten verwendet werden. Es muss also ein Ordner sein, der nur die Daten vom Teststand enthält.
folder_path = "data/" #spezifisch fürs Testing, muss über Explorer oä auswählbar sein
file_names = [os.path.join(folder_path, files)
              for files in os.listdir(folder_path)]
df_of_Files = []
dtype_dic = {'Alarme':str, 'Kommentar':str, 'Set Kommentar':str}
for Files in file_names:
    df_of_Files.append(pd.read_csv(Files, sep='\t', encoding = "utf-8", decimal=",", dtype=dtype_dic, parse_dates=[0], date_format=datetime_format))
df_full_evn = pd.concat(df_of_Files, ignore_index=True)

load_dotenv()

mongodb_user = os.environ.get("MONGODB_USER")
mongodb_password = os.environ.get("MONGODB_PASS")
# MongoDB connection
mongo_uri = "mongodb://"+mongodb_user+":"+mongodb_password+"@172.16.134.8:27017/?directConnection=true&authSource=admin"
# mongo_uri = "mongodb://localhost:27017"
client = MongoClient(mongo_uri)

# Select database and collection
db = client["rdm_workshop"]
collection = db["BZ011_Rohdaten"]

# Fetch data from MongoDB
cursor = collection.find({})  # Empty filter `{}` fetches all documents

# Convert to DataFrame
df = pd.DataFrame(list(cursor))

# Drop MongoDB’s default `_id` column if not needed
if "_id" in df.columns:
    df_full = df.drop(columns=["_id"])

# df_full = df_full_evn

# Nach Zeit sortieren
df_sorted = df_full.sort_values(["Datum"])
#df_sorted = df_Rohdaten.sort_values(["Datum / Uhrzeit"]) #hier eventuell unnötig, wenn df_full funktioniert

# Erstelle Liste von Spalten für Troubleshooting, ohne Troubleshooting und zusätzlich zu löschenden Spalten
List_of_Col_to_drop = list(())
List_of_Col_Troubleshoot = list(())
List_of_Col_woTroubleshoot = list(())
for Col_Filter in range(len(df_Excel_Filter_Columns.columns)):
    # Liste mit allen zu löschenden Spalten (Gegenteil von für Excel-Datei später)
    if df_Excel_Filter_Columns.iloc[0, Col_Filter] != 1:
        List_of_Col_to_drop.append(df_Excel_Filter_Columns.columns[Col_Filter])
    # Liste mit allen nicht Troubleshoot-Spalten (Gegenteil von Troubleshoot)
    if df_Excel_Filter_Columns.iloc[0, Col_Filter] != 2 and Col_Filter > 0:
        List_of_Col_woTroubleshoot.append(df_Excel_Filter_Columns.columns[Col_Filter])
    else:
        List_of_Col_Troubleshoot.append(df_Excel_Filter_Columns.columns[Col_Filter])

# print(List_of_Col_to_drop)
print(List_of_Col_Troubleshoot)
# print(List_of_Col_woTroubleshoot)

# Dataframe nur mit Spalten für Troubleshooting + Datum&Uhrzeit
df_Troubleshoot = df_sorted.drop(columns=List_of_Col_woTroubleshoot, axis=1)

print(df_Troubleshoot.head())
# Erstelle Graphen von Spalten im Troubleshooting
fig, ax = plt.subplots()
for i in range(len(List_of_Col_Troubleshoot)):
    if i > 0:
        x=df_Troubleshoot.iloc[:,0]
        y=df_Troubleshoot.iloc[:,i]
        ax.scatter(x, y, label=df_Troubleshoot.columns[i])
ax.legend()
plt.xlabel(df_Troubleshoot.columns[0])
# Exportiere Graphen als png
fig.savefig('Troubleshoot_Graph.png')
# plt.show()

# Berechnung des Avg - c=alle x Werte / lv=nur letzte x Werte
df_avg = df_sorted.iloc[:0,:].copy()
LastRow = -1
Temp_LastRow_Alt = -1
List_Temp = list()
List_avg = list()
for row_Daten_SetID in range(len(df_sorted)):
    for row_Filter in range(len(df_Excel_Filter_Sets)):
        current_col_set_id = df_sorted.iloc[row_Daten_SetID, col_set_id]
        if df_sorted.iloc[row_Daten_SetID, col_set_id] == df_Excel_Filter_Sets.iloc[row_Filter, 0]:
            NAvg = df_Excel_Filter_Sets.iloc[row_Filter, 1]
            # cyclic: alle NAvg Werte wird der Mittelwert berechnet
            if df_Excel_Filter_Sets.iloc[row_Filter, 2] == 'c':
                if row_Daten_SetID > Temp_LastRow_Alt:
                    LastRow = row_Daten_SetID+NAvg-1
                    if LastRow < len(df_sorted):
                        if df_sorted.iloc[row_Daten_SetID, col_set_id] == df_sorted.iloc[LastRow, col_set_id]:
                            #liste erstellen mit Werte aus erster row
                            List_Temp = df_sorted.iloc[[row_Daten_SetID]].values.flatten().tolist()
                            for row_Mittelwert in range(row_Daten_SetID+1, LastRow+1):
                                for Col_Mittelwert in range(len(df_sorted.columns)):
                                    #wenn Nummernwert, dann addieren (alles außer erster Spalte)
                                    if type(List_Temp[Col_Mittelwert]) is int or type(List_Temp[Col_Mittelwert]) is float:
                                        List_Temp[Col_Mittelwert] = math.fsum([List_Temp[Col_Mittelwert], df_sorted.iloc[row_Mittelwert, Col_Mittelwert]])
                            #als letztes, wenn Nummernwert, dann durch NAvg
                            for Col_Mittelwert in range(len(df_sorted.columns)):
                                if type(List_Temp[Col_Mittelwert]) is int or type(List_Temp[Col_Mittelwert]) is float:
                                    List_Temp[Col_Mittelwert] = List_Temp[Col_Mittelwert]/NAvg
                            # Mittelwerte anhängen
                            List_avg.append(List_Temp)
                            Temp_LastRow_Alt = LastRow
            #last value: nur die letzten NAvg Werte werten gemittelt
            if df_Excel_Filter_Sets.iloc[row_Filter, 2] == 'lv':
                if row_Daten_SetID > Temp_LastRow_Alt:
                    LastRow = row_Daten_SetID+NAvg-1
                    if LastRow+1 < len(df_sorted):
                        if df_sorted.iloc[LastRow, col_set_id] != df_sorted.iloc[LastRow + 1, col_set_id] and df_sorted.iloc[row_Daten_SetID, col_set_id] == df_sorted.iloc[LastRow, col_set_id]:
                            #gleicher Kram wie oben
                            # liste erstellen mit Werte aus erster row
                            List_Temp = df_sorted.iloc[[row_Daten_SetID]].values.flatten().tolist()
                            for row_Mittelwert in range(row_Daten_SetID+1, LastRow+1):
                                for Col_Mittelwert in range(len(df_sorted.columns)):
                                    # wenn Nummernwert, dann addieren (alles außer erster Spalte)
                                    if type(List_Temp[Col_Mittelwert]) is int or type(List_Temp[Col_Mittelwert]) is float:
                                        List_Temp[Col_Mittelwert] = math.fsum([List_Temp[Col_Mittelwert], df_sorted.iloc[row_Mittelwert, Col_Mittelwert]])
                            # als letztes, wenn Nummernwert, dann durch NAvg
                            for Col_Mittelwert in range(len(df_sorted.columns)):
                                if type(List_Temp[Col_Mittelwert]) is int or type(List_Temp[Col_Mittelwert]) is float:
                                    List_Temp[Col_Mittelwert] = List_Temp[Col_Mittelwert] / NAvg
                            # Mittelwerte anhängen
                            List_avg.append(List_Temp)
                            Temp_LastRow_Alt = LastRow
                    elif LastRow +1 == len(df_sorted) and df_sorted.iloc[row_Daten_SetID, col_set_id] == df_sorted.iloc[LastRow, col_set_id]: #properties of len() => lastRow is actual last row of file
                        row_Daten_SetID = LastRow - NAvg + 1
                        #gleicher Kram wie oben
                        # liste erstellen mit Werte aus erster row
                        List_Temp = df_sorted.iloc[[row_Daten_SetID]].values.flatten().tolist()
                        for row_Mittelwert in range(row_Daten_SetID, LastRow):
                            for Col_Mittelwert in range(len(df_sorted.columns)):
                                # wenn Nummernwert, dann addieren (alles außer erster Spalte)
                                if type(List_Temp[Col_Mittelwert]) is int or type(List_Temp[Col_Mittelwert]) is float:
                                    List_Temp[Col_Mittelwert] = math.fsum([List_Temp[Col_Mittelwert], df_sorted.iloc[row_Mittelwert, Col_Mittelwert]])
                        # als letztes, wenn Nummernwert, dann durch NAvg
                        for Col_Mittelwert in range(len(df_sorted.columns)):
                            if type(List_Temp[Col_Mittelwert]) is int or type(List_Temp[Col_Mittelwert]) is float:
                                List_Temp[Col_Mittelwert] = List_Temp[Col_Mittelwert] / NAvg
                        # Mittelwerte anhängen
                        List_avg.append(List_Temp)
                        Temp_LastRow_Alt = LastRow
df_avg = pd.DataFrame(List_avg, columns = df_sorted.columns)

# Lösche spalten in SetIDs und Speicher unter output
df_Output = df_avg.drop(columns=List_of_Col_to_drop, axis=1)

# Daten speichern als txt & define output_Daten Speicherort&Name
output_Daten = r"output.txt" #spezifisch fürs Testing, muss über Explorer oä auswählbar sein
#sinnvoll auf MongoDB zu speichern? Oder nur auf dem Mitarbeiter PC?!
df_Output.to_csv(output_Daten, sep='\t', encoding="ISO-8859-1", index=False, header=True, decimal=",")