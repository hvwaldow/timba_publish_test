from pathlib import Path
import os
import pickle
import gzip

bigfile = Path("TiMBA/data/input/03_Serialization/WorldDataContent.pkl")
smallfile = Path("./smallworld.pkl")
print(f'Current size of {bigfile}: {os.stat(bigfile).st_size / 2**20:.2f} MiB')

# Laden
with bigfile.open('rb') as f:
    data = pickle.load(f)

# Gegzipped dumpen
with gzip.open(smallfile,'wb') as f:
    pickle.dump(data, f)
print(f'Current size of {smallfile}: {os.stat(smallfile).st_size / 2**20:.2f} MiB')
print(f'compression ratio: {os.stat(bigfile).st_size / os.stat(smallfile).st_size:.0f}')

# Wieder laden
with gzip.open(smallfile,'rb') as f:
    data_reloaded = pickle.load(f)
print(f'Attribute des gepickelten Objekts:\n {dir(data_reloaded)}')
