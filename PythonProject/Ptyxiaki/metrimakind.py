import os
import xml.etree.ElementTree as ET
from collections import Counter

def find_kinds_in_file(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        kinds = []

        for elem in root.iter():
            # elem.tag μπορεί να είναι '{namespace}kind' ή απλά 'kind'
            # Θα πάρουμε το τοπικό όνομα του tag χωρίς το namespace
            if elem.tag.split('}')[-1] == 'kind' and elem.text:
                kinds.append(elem.text.strip())

        return kinds
    except ET.ParseError:
        print(f"⚠️ Σφάλμα στο parsing του αρχείου: {file_path}")
        return []
    except Exception as e:
        print(f"⚠️ Σφάλμα στο αρχείο {file_path}: {e}")
        return []

def find_kinds_in_folder(folder_path):
    all_kinds = []

    for root_dir, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.xml'):
                file_path = os.path.join(root_dir, file)
                print(f"Επεξεργασία αρχείου: {file_path}")  # Debug εκτύπωση
                kinds_in_file = find_kinds_in_file(file_path)
                if kinds_in_file:
                    print(f"  Βρέθηκαν kinds: {kinds_in_file}")  # Debug εκτύπωση
                all_kinds.extend(kinds_in_file)

    return Counter(all_kinds)

if __name__ == "__main__":
    folder = r"C:/WPI/Aposibiesmena/EP"
    kinds_count = find_kinds_in_folder(folder)

    if kinds_count:
        print("\n📊 Αποτελέσματα διαφορετικών <kind>:")
        for kind, count in kinds_count.items():
            print(f"  - '{kind}': {count} φορές")
    else:
        print("\n⚠️ Δεν βρέθηκαν στοιχεία <kind> σε κανένα αρχείο.")
