import os
import xml.etree.ElementTree as ET
from collections import Counter

def find_formats_in_file(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        formats = []

        for elem in root.iter():
            format_attr = elem.attrib.get('format')
            if format_attr:
                formats.append(format_attr.strip())

        return formats
    except ET.ParseError:
        print(f"⚠️ Σφάλμα στο parsing του αρχείου: {file_path}")
        return []
    except Exception as e:
        print(f"⚠️ Σφάλμα στο αρχείο {file_path}: {e}")
        return []

def find_formats_in_folder(folder_path):
    all_formats = []

    for root_dir, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.xml'):
                file_path = os.path.join(root_dir, file)
                print(f"Επεξεργασία αρχείου: {file_path}")
                formats_in_file = find_formats_in_file(file_path)
                if formats_in_file:
                    print(f"  Βρέθηκαν formats: {formats_in_file}")
                all_formats.extend(formats_in_file)

    return Counter(all_formats)

if __name__ == "__main__":
    folder = r"C:/WPI/Aposibiesmena/EP"
    formats_count = find_formats_in_folder(folder)

    if formats_count:
        print("\n📊 Αποτελέσματα διαφορετικών format:")
        for fmt, count in formats_count.items():
            print(f"  - '{fmt}': {count} φορές")
    else:
        print("\n⚠️ Δεν βρέθηκαν attributes format σε κανένα αρχείο.")
