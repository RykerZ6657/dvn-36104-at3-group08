"""Section: Geography. Placeholder until the owner opens a pull request."""

from pathlib import Path
import streamlit as st
import plotly.express as px
from scripts.geography_processing import flatten_attributions

OI_BLUE = '#0072B2'
DATA_PATH = Path(__file__).resolve().parents[1] / 'data' / 'raw' / 'notable_ai_models.csv'

@st.cache_data
def load_geography_data(csv_path: str):
    return flatten_attributions(csv_path)


def render() -> None:
    st.header('Geography: where are the leading AI organisations based?')
    st.caption('Source: Epoch AI, Notable AI Models; publication years 2015–2025.')
    if not DATA_PATH.exists():
        st.error(f'Missing dataset: {DATA_PATH}. Place notable_ai_models.csv in the data/ directory.'); st.stop()
    models, country_model, org_model = load_geography_data(str(DATA_PATH))
    if country_model.empty:
        st.error('No valid country records in the selected years.'); st.stop()

    left, right = st.columns([3,2])
    with left:
        year_start, year_end = st.slider('Publication year range', min_value=2015, max_value=2025, value=(2015,2025), step=1)
    with right:
        display_n = st.selectbox('Number of countries in ranking', [5,10,15,20], index=1)
    cm = country_model[country_model['Year'].between(year_start,year_end)]
    om = org_model[org_model['Year'].between(year_start,year_end)]
    m = models[models['year'].between(year_start,year_end)]

    country_counts = cm.groupby('Country',as_index=False).agg(Models=('CSV row','nunique')).sort_values(['Models','Country'],ascending=[False,True])
    leader = country_counts.iloc[0]
    a,b,c = st.columns(3)
    a.metric('Distinct notable models',f'{len(m):,}')
    b.metric('Countries represented',f'{len(country_counts):,}')
    c.metric('Leading country',leader['Country'])

    st.markdown('### 1 · Countries ranked by notable-model participation')
    st.caption('Each model counts once for each participating country. Collaborations may be counted in more than one country.')
    top = country_counts.head(display_n).sort_values('Models')
    fig = px.bar(top,x='Models',y='Country',orientation='h',text='Models',custom_data=['Country'], color_discrete_sequence=[OI_BLUE], title='Notable AI model participation by country')
    fig.update_layout(height=max(330,len(top)*37+110),margin=dict(l=10,r=35,t=55,b=15),xaxis_title='Notable models (count)',yaxis_title='Country')
    fig.update_traces(textposition='outside',cliponaxis=False)
    st.plotly_chart(fig,width='stretch')
    st.markdown(f'**What this shows:** {leader["Country"]} has the highest number of country-affiliated notable model records ({int(leader["Models"]):,}) in {year_start}–{year_end}. This indicates where recorded development participation is concentrated, not a direct measure of model capability.')

    st.markdown('### 2 · Organisations contributing to a country')
    options = country_counts['Country'].tolist()
    selected = st.selectbox('Select a country', options)
    chosen = om[om['Country'].eq(selected)]
    organisation_counts = (chosen.groupby('Organisation',as_index=False).agg(Models=('CSV row','nunique'))
                           .sort_values(['Models','Organisation'],ascending=[False,True]).head(12))
    if organisation_counts.empty:
        st.info('No unambiguous institution-country mappings for this selection.')
    else:
        fig2=px.bar(organisation_counts.sort_values('Models'),x='Models',y='Organisation',orientation='h',text='Models',color_discrete_sequence=[OI_BLUE],title=f'Notable model contributions by organisation — {selected}')
        fig2.update_layout(height=max(350,len(organisation_counts)*32+100),margin=dict(l=10,r=35,t=55,b=15),xaxis_title='Notable models (count)',yaxis_title='Organisation')
        fig2.update_traces(textposition='outside',cliponaxis=False)
        st.plotly_chart(fig2,width='stretch')
        top_org = organisation_counts.iloc[0]
        st.markdown(f'**What this shows:** {top_org["Organisation"]} is the largest identifiable organisation contributor for {selected} in {year_start}–{year_end}, with {int(top_org["Models"]):,} notable model records. This is a contribution count, not a capability ranking.')
        st.caption('Collaborative models are credited to each participating institution. Institution counts are not additive.')

    st.markdown('### 3 · Trace a displayed number back to the CSV')
    if selected in country_counts['Country'].values:
        count = int(country_counts.set_index('Country').loc[selected,'Models'])
        st.write(f'**{selected}: {count} distinct models** in {year_start}–{year_end}. This counts unique CSV records in which {selected} appears as an affiliated country.')
        evidence = cm[cm['Country'].eq(selected)][['CSV row','Year','Model','Country']].sort_values(['Year','CSV row'],ascending=[False,True])
        st.dataframe(evidence,width='stretch',hide_index=True)
        st.caption('CSV row is the original 1-indexed spreadsheet row including the header. Open that row in data/raw/notable_ai_models.csv to verify Model, Publication date and Country (of organization).')
        st.download_button('Download evidence rows as CSV',evidence.to_csv(index=False).encode('utf-8'),file_name='geography_evidence.csv',mime='text/csv')

    with st.expander('Methodology, limitations and citation'):
        st.markdown('''**Source:** Epoch AI, *Data on AI models*, https://epoch.ai/data/ai-models, provided snapshot of 21 October 2026.\n\n**Filter:** Publication date in calendar years 2015–2025 (inclusive). **Unit:** one record in the Notable AI Models CSV. **Country counts:** split comma-separated country affiliations, trim whitespace, de-duplicate country assignments per model. **Institution chart:** pair comma-separated organisations and countries by position when both lists have equal length; count each model once per organisation-country pair. Mismatched or missing pairs are excluded from the institution chart, not imputed.\n\n**Limitations:** Country is recorded organisational affiliation, not necessarily where model training took place. Collaboration leads to multi-country credit and non-additive country counts. Organisation aliases (e.g. Google/Google DeepMind) have not been merged. Notable model counts do not directly measure AI capability, quality or compute. The 2025 year may reflect source coverage and reporting bias.''')
