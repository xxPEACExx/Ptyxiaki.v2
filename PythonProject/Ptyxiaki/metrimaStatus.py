import os
import xml.etree.ElementTree as ET
from collections import Counter

def find_statuses_in_file(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        statuses = []

        for elem in root.iter():
            status_attr = elem.attrib.get('status')
            if status_attr:
                statuses.append(status_attr.strip())

        return statuses
    except ET.ParseError:
        print(f"⚠️ Σφάλμα στο parsing του αρχείου: {file_path}")
        return []
    except Exception as e:
        print(f"⚠️ Σφάλμα στο αρχείο {file_path}: {e}")
        return []

def find_statuses_in_folder(folder_path):
    all_statuses = []

    for root_dir, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.xml'):
                file_path = os.path.join(root_dir, file)
                print(f"Επεξεργασία αρχείου: {file_path}")
                statuses_in_file = find_statuses_in_file(file_path)
                if statuses_in_file:
                    print(f"  Βρέθηκαν statuses: {statuses_in_file}")
                all_statuses.extend(statuses_in_file)

    return Counter(all_statuses)

if __name__ == "__main__":
    folder = r"C:/WPI/Aposibiesmena/EP"
    statuses_count = find_statuses_in_folder(folder)

    if statuses_count:
        print("\n📊 Αποτελέσματα διαφορετικών status attributes:")
        for status, count in statuses_count.items():
            print(f"  - '{status}': {count} φορές")
    else:
        print("\n⚠️ Δεν βρέθηκαν attributes status σε κανένα αρχείο.")
