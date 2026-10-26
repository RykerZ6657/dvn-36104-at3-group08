"""Preprocess Epoch AI model affiliations for the Geography dashboard."""

import pandas as pd


def flatten_attributions(csv_path: str):
    original = pd.read_csv(csv_path, low_memory=False)
    original['csv_row'] = original.index + 2  # header in row 1
    original['year'] = pd.to_datetime(original['Publication date'], errors='coerce').dt.year
    models = original[original['year'].between(2015, 2025)].copy()
    country_rows, org_rows = [], []
    for _, r in models.iterrows():
        country_list = [v.strip() for v in str(r['Country (of organization)']).split(',') if v.strip() and v.strip().lower() != 'nan']
        org_list = [v.strip() for v in str(r['Organization']).split(',') if v.strip() and v.strip().lower() != 'nan']
        base = {'Model':r['Model'], 'Year':int(r['year']), 'CSV row':int(r['csv_row'])}
        for country in dict.fromkeys(country_list):
            country_rows.append({**base, 'Country':country})
        # Epoch fields list institutions and countries in parallel in multi-affiliation rows.
        # Exclude misaligned rows from institution-country pair breakdown rather than guess.
        if len(org_list) == len(country_list):
            for org, country in set(zip(org_list, country_list)):
                org_rows.append({**base,'Country':country,'Organisation':org})
    return models, pd.DataFrame(country_rows), pd.DataFrame(org_rows)

