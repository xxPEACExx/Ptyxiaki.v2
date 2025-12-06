import os
import xml.etree.ElementTree as ET
from collections import Counter

def find_schemes_in_file(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        schemes = []

        for elem in root.iter():
            scheme_attr = elem.attrib.get('scheme')
            if scheme_attr:
                schemes.append(scheme_attr.strip())

        return schemes
    except ET.ParseError:
        print(f"⚠️ Σφάλμα στο parsing του αρχείου: {file_path}")
        return []
    except Exception as e:
        print(f"⚠️ Σφάλμα στο αρχείο {file_path}: {e}")
        return []

def find_schemes_in_folder(folder_path):
    all_schemes = []

    for root_dir, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.xml'):
                file_path = os.path.join(root_dir, file)
                print(f"Επεξεργασία αρχείου: {file_path}")
                schemes_in_file = find_schemes_in_file(file_path)
                if schemes_in_file:
                    print(f"  Βρέθηκαν schemes: {schemes_in_file}")
                all_schemes.extend(schemes_in_file)

    return Counter(all_schemes)

if __name__ == "__main__":
    folder = r"C:/WPI/Aposibiesmena/EP"
    schemes_count = find_schemes_in_folder(folder)

    if schemes_count:
        print("\n📊 Αποτελέσματα διαφορετικών scheme:")
        for scheme, count in schemes_count.items():
            print(f"  - '{scheme}': {count} φορές")
    else:
        print("\n⚠️ Δεν βρέθηκαν attributes scheme σε κανένα αρχείο.")
