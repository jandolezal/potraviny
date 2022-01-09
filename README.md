# Potraviny na pranýři

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/jandolezal/potraviny/HEAD)
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/jandolezal/potraviny/main/foodpillory/foodpillory.py)


Modul `facilities.py` pro stažení seznamu uzavřených provozoven z webu [Potraviny na pranýři](https://www.potravinynapranyri.cz/) ve formátu .csv.

GitHub akce skrapuje seznam aktuálních případů každý den (soubor `data/actual.csv`). Archivní seznam (`data/archive.csv`) se (zatím) nemění.

Repozitář obsahuje také .ipynb notebooky pro seznámení se s datasetem (oba spojené seznamy) a minimální Streamlit [aplikaci](https://share.streamlit.io/jandolezal/potraviny/main/foodpillory/foodpillory.py), která prezentuje několik statistik.

## Použití

```bash
# Prepare virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt

# Scrape the actual dataset
python3 -m foodpillory.facilities

# Scrape the archive dataset
python3 -m foodpillory.facilities --archive --output archive.csv

# Run Streamlit app
streamlit run foodpillory/foodpillory.py
```
