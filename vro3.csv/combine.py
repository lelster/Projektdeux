import pandas as pd
import os
from glob import glob

input_dir = "hourly_output2"
output_file = "2025-05-01_combined.csv.gz"
date_prefix = "05-01-2025"

# Dateien suchen
hourly_files = sorted(glob(os.path.join(input_dir, f"{date_prefix}_*.csv.gz")))

if not hourly_files:
    raise FileNotFoundError(f"❌ Keine Dateien gefunden für {date_prefix} in '{input_dir}'")

# Zusammenfügen
df_list = [pd.read_csv(f) for f in hourly_files]
combined = pd.concat(df_list, ignore_index=True)

# Exportieren
combined.to_csv(output_file, index=False, compression="gzip")
print(f"✅ {len(hourly_files)} Dateien zusammengefügt → {output_file} ({len(combined):,} Zeilen)")
