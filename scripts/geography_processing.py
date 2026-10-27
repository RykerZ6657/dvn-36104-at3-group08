"""Preprocess Epoch AI model affiliations for the Geography dashboard."""

import pandas as pd
from scripts.prepare_concentration import PARENT


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
                # Apply the same parent-company mapping as Concentration.
                parent_org = PARENT.get(org, org)
                org_rows.append({**base, 'Country': country, 'Organisation': parent_org})
    # One model can list multiple labs belonging to the same parent company.
    # De-duplicate after mapping, separately within each affiliated country.
    org_df = pd.DataFrame(org_rows, columns=['Model', 'Year', 'CSV row', 'Country', 'Organisation'])
    org_df = org_df.drop_duplicates(subset=['CSV row', 'Country', 'Organisation'])
    return models, pd.DataFrame(country_rows), org_df
