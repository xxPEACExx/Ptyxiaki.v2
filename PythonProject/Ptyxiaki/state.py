import traceback

lang_mapping = {
    'EN': 1,  # English (γλώσσα)
    'FR': 2,  # France
    'DE': 3,  # Germany
    'IT': 4,  # Italy
    'AL': 5,  # Albania
    'GR': 6,  # Greece
    'ES': 7,  # Spain
    'PT': 8,  # Portugal
    'NL': 9,  # Netherlands
    'BE': 10, # Belgium
    'LU': 11, # Luxembourg
    'AT': 12, # Austria
    'CH': 13, # Switzerland
    'SE': 14, # Sweden
    'NO': 15, # Norway
    'FI': 16, # Finland
    'DK': 17, # Denmark
    'IE': 18, # Ireland
    'IS': 19, # Iceland
    'PL': 20, # Poland
    'CZ': 21, # Czech Republic
    'SK': 22, # Slovakia
    'HU': 23, # Hungary
    'RO': 24, # Romania
    'BG': 25, # Bulgaria
    'HR': 26, # Croatia
    'SI': 27, # Slovenia
    'BA': 28, # Bosnia and Herzegovina
    'RS': 29, # Serbia
    'MK': 30, # North Macedonia
    'TR': 31, # Turkey
    'RU': 32, # Russia
    'UA': 33, # Ukraine
    'BY': 34, # Belarus
    'MD': 35, # Moldova
    'CY': 36, # Cyprus
    'MT': 37, # Malta
    'LT': 38, # Lithuania
    'LV': 39, # Latvia
    'EE': 40, # Estonia
    'AD': 41, # Andorra
    'AM': 42, # Armenia
    'AZ': 43, # Azerbaijan
    'GE': 44, # Georgia
    'LI': 45, # Liechtenstein
    'MC': 46, # Monaco
    'SM': 47, # San Marino
    'VA': 48, # Vatican City
    'AL': 49, # Albania (επαναλαμβάνεται, μπορείς να αλλάξεις)
    'ME': 50, # Montenegro
    'DZ': 51, # Algeria
    'EG': 52, # Egypt
    'MA': 53, # Morocco
    'TN': 54, # Tunisia
    'LY': 55, # Libya
    'ZA': 56, # South Africa
    'NG': 57, # Nigeria
    'KE': 58, # Kenya
    'UG': 59, # Uganda
    'TZ': 60, # Tanzania
    'GH': 61, # Ghana
    'SN': 62, # Senegal
    'CI': 63, # Ivory Coast
    'ZW': 64, # Zimbabwe
    'ZM': 65, # Zambia
    'BW': 66, # Botswana
    'NA': 67, # Namibia
    'AO': 68, # Angola
    'CM': 69, # Cameroon
    'ET': 70, # Ethiopia
    'SD': 71, # Sudan
    'SS': 72, # South Sudan
    'GA': 73, # Gabon
    'CG': 74, # Republic of the Congo
    'CD': 75, # Democratic Republic of the Congo
    'BJ': 76, # Benin
    'BF': 77, # Burkina Faso
    'ML': 78, # Mali
    'MR': 79, # Mauritania
    'TG': 80, # Togo
    'LR': 81, # Liberia
    'SL': 82, # Sierra Leone
    'CV': 83, # Cape Verde
    'KM': 84, # Comoros
    'MG': 85, # Madagascar
    'MU': 86, # Mauritius
    'SC': 87, # Seychelles
    'ZW': 88, # Zimbabwe (επαναλαμβάνεται)
    'DJ': 89, # Djibouti
    'ER': 90, # Eritrea
    'LS': 91, # Lesotho
    'SZ': 92, # Eswatini
    'MW': 93, # Malawi
    'RW': 94, # Rwanda
    'BI': 95, # Burundi
    'TD': 96, # Chad
    'NE': 97, # Niger
    'CF': 98, # Central African Republic
    'GN': 99, # Guinea
    'GW': 100,# Guinea-Bissau

    # Προσθήκη κωδικών που αφορούν διπλώματα (jurisdiction codes)
    'EP': 101,  # European Patent
    'US': 102,  # United States
    'JP': 103,  # Japan
    'CN': 104,  # China
    'KR': 105,  # South Korea
    'WO': 106,  # WIPO (PCT)
    'GB': 107,  # United Kingdom
    'CA': 108,  # Canada
    'AU': 109,  # Australia
    # Μπορείς να προσθέσεις κι άλλους αν χρειαστεί
}


# def initialize_state(cursor, db):
#     for lang, cid in lang_mapping.items():
#         cursor.execute("SELECT COUNT(*) FROM state WHERE CID = %s", (cid,))
#         if cursor.fetchone()[0] == 0:
#             cursor.execute("INSERT INTO state (CID, country_name) VALUES (%s, %s)", (cid, lang))
#     db.commit()
def log_error(message):
    with open("errors.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")

def initialize_state(cursor, db):
    for lang, cid in lang_mapping.items():
        try:
            cursor.execute("SELECT COUNT(*) FROM state WHERE CID = %s", (cid,))
            if cursor.fetchone()[0] == 0:
                try:
                    cursor.execute("INSERT INTO state (CID, country_name) VALUES (%s, %s)", (cid, lang))
                except Exception as insert_err:
                    log_error(f"[INSERT_ERROR] CID: {cid}, lang: {lang}, error: {insert_err}")
                    continue
        except Exception as select_err:
            log_error(f"[SELECT_ERROR] CID: {cid}, lang: {lang}, error: {select_err}")
            continue
    try:
        db.commit()
    except Exception as commit_err:
        db.rollback()
        log_error(f"[COMMIT_ERROR] initialize_state commit failed: {commit_err}")