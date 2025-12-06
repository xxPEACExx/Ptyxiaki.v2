import os
import xml.etree.ElementTree as ET
from collections import Counter

def find_load_source_attrs_in_file(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        sources = []

        for elem in root.iter():
            # Αν το attribute 'load-source' υπάρχει στο στοιχείο, το προσθέτουμε
            load_source = elem.attrib.get('load-source')
            if load_source:
                sources.append(load_source.strip())

        return sources
    except ET.ParseError:
        print(f"⚠️ Σφάλμα στο parsing του αρχείου: {file_path}")
        return []
    except Exception as e:
        print(f"⚠️ Σφάλμα στο αρχείο {file_path}: {e}")
        return []

def find_load_source_attrs_in_folder(folder_path):
    all_sources = []

    for root_dir, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.xml'):
                file_path = os.path.join(root_dir, file)
                print(f"Επεξεργασία αρχείου: {file_path}")
                sources_in_file = find_load_source_attrs_in_file(file_path)
                if sources_in_file:
                    print(f"  Βρέθηκαν load-source attributes: {sources_in_file}")
                all_sources.extend(sources_in_file)

    return Counter(all_sources)

if __name__ == "__main__":
    folder = r"C:/WPI/Aposibiesmena/EP"
    sources_count = find_load_source_attrs_in_folder(folder)

    if sources_count:
        print("\n📊 Αποτελέσματα διαφορετικών load-source attributes:")
        for source, count in sources_count.items():
            print(f"  - '{source}': {count} φορές")
    else:
        print("\n⚠️ Δεν βρέθηκαν load-source attributes σε κανένα αρχείο.")
