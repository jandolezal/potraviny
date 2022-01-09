import datetime

import altair as alt
import pandas as pd
import numpy as np
import streamlit as st


@st.cache
def load_data():
    actual = pd.read_csv(
        'data/actual.csv',
        index_col='id',
        dtype={'id': int, 'ico': str, 'druh': 'category'},
        parse_dates=['datum_zverejneni', 'datum_uzavreni', 'datum_uvolneni_zakazu'],
    )
    archive = pd.read_csv(
        'data/archive.csv',
        index_col='id',
        dtype={'id': int, 'ico': str, 'druh': 'category'},
        parse_dates=['datum_zverejneni', 'datum_uzavreni', 'datum_uvolneni_zakazu'],
    )
    combined = actual.append(archive)
    return combined


def load_closed_count_by_year(data):
    closed_by_year = (
        pd.DataFrame(data.groupby(data['datum_uzavreni'].dt.year)['referencni_cislo'].count())
    ).reset_index()  # Altair does not work with index
    closed_by_year.columns = ['rok_uzavreni', 'pocet']
    return closed_by_year


def load_year(data, year):
    return data[
        (data['datum_uzavreni'] >= datetime.datetime(year, 1, 1))
        & (data['datum_uzavreni'] <= datetime.datetime(year, 12, 31))
    ]


def plot_closed_count_by_year(closed_by_year):
    bars = (
        alt.Chart(closed_by_year)
        .mark_bar(color='#ff4b4b')
        .encode(
            alt.Y('rok_uzavreni:N', title='Rok uzavření'),
            alt.X('pocet:Q', title='Počet případů'),
        )
        .properties(title='Počty uzavření v jednotlivých letech')
    )

    text = bars.mark_text(align='left', baseline='middle', dx=3).encode(text='pocet:Q')

    return bars + text


def load_closed_for_good(df):
    closed_for_good = df[df['stav_uzavreni'] == 'Uzavřeno'].groupby(df['datum_uzavreni'].dt.year)['referencni_cislo'].count().reset_index()
    closed_for_good.columns = ['rok_uzavreni', 'pocet']
    return closed_for_good


def plot_closed_for_good(df):
    bars = alt.Chart(df).mark_bar(color='#ff4b4b').encode(
        alt.Y('rok_uzavreni:N', title='Rok uzavření'),
        alt.X('pocet:Q', title='Počet'),
        ).properties(title='Počty stále uzavřených podniků')
    return bars


def load_business_types_count(data):
    business_types = data['druh'].value_counts().reset_index()
    business_types.columns = ['druh', 'pocet']
    return business_types


def plot_business_types(business_types):
    bars = (
        alt.Chart(business_types)
        .mark_bar(color='#ff4b4b')
        .encode(
            alt.Y('druh:N', sort='-x', title='Druh'),
            alt.X('pocet:Q', title='Počet'),
        )
        .properties(title=f'Druhy uzavřených podniků (celkem {business_types["pocet"].sum()})')
    )

    text = bars.mark_text(align='left', baseline='middle', dx=3).encode(text='pocet:Q')

    return bars + text


def load_offenses_perc(data):
    offenses = data['zjistene_skutecnosti'].str.get_dummies()
    offenses_freq = offenses.mean()
    df = pd.DataFrame((offenses_freq.sort_values(ascending=False) * 100).round(1))
    df = df.reset_index()
    df.columns = ['Co se zanedbalo', 'Jak často (%)']
    df['Jak často (%)'] = df['Jak často (%)'].astype(str).str.replace('.', ',', regex=False) + ' %'
    df.index = np.arange(1, len(df) + 1)
    return df



def load_offenses(data):
    offenses = data['zjistene_skutecnosti'].str.get_dummies()
    offenses_freq = offenses.mean()
    df = pd.DataFrame((offenses_freq.sort_values(ascending=False)))
    df = df.reset_index()
    df.columns = ['Co se zanedbalo', 'Podíl']
    df.index = np.arange(1, len(df) + 1)
    return df


def load_top_3_offenses_across_years(df, start, end):
    top_multiple_years = pd.DataFrame()
    for year in range(start, end + 1):
        last_year = load_year(df, year)
        last_year_problems = load_offenses(last_year)
        top_problems = last_year_problems.loc[last_year_problems['Co se zanedbalo'].isin(['Výskyt trusu hlodavců', 'Nečistoty na podlaze', 'Výrazně zanedbaný úklid']), :].copy()
        top_problems['Rok'] = year
        top_multiple_years = pd.concat([top_multiple_years, top_problems])
    top_multiple_years = top_multiple_years.reset_index(drop=True)
    return top_multiple_years


def plot_offenses_accross_years(df):
    lines = alt.Chart(df).mark_line().encode(
        alt.X('Rok:N', title='Rok uzavření'),
        alt.Y('Podíl:Q', axis=alt.Axis(format='%'), title='Četnost (%)'),
        color='Co se zanedbalo:N',
        ).properties(title='Tři nejčastější problémy během let')
    return lines


@st.cache
def convert_df_to_csv(df):
    return df.to_csv().encode('utf-8')


st.title('Uzavřené provozovny  🍔 🐀')

st.markdown('Jak se v minulých letech zavíraly hospody nebo obchody, odkud jídlo nechcete?')
st.markdown(
    'Zdrojem dat je webová aplikace [Potraviny na pranýři](https://www.potravinynapranyri.cz/), která shrnuje výsledky šetření Státní zemědělské a potravinářské inspekce.'
)


# Load one dataframe
# data_load_state = st.text('Načítám data...')
data = load_data()
# data_load_state.text('Načítám data...hotovo!')


# Count of closed facilities by year
st.subheader('Jak se zavíralo v minulosti')
closed_by_year = load_closed_count_by_year(data)
# st.write(closed_by_year)
c1 = plot_closed_count_by_year(closed_by_year)
st.altair_chart(c1, use_container_width=True)


# Establishements closed for good throughout the years
st.subheader('Kolik podniků již neotevřelo')
closed_for_good = load_closed_for_good(data)
c2 = plot_closed_for_good(closed_for_good)
st.altair_chart(c2, use_container_width=True)


# Top 3 offenses accross years
st.subheader('Největší lahůdky napříč roky')
top3_years = load_top_3_offenses_across_years(data, 2015, 2021)
c3 = plot_offenses_accross_years(top3_years)
st.altair_chart(c3, use_container_width=True)


# Show rest of the statistics just for single year
selected_year = st.selectbox(
    'Zvol rok, který tě zajímá',
    (2021, 2020, 2019, 2018, 2017, 2016, 2015),
    help='Dále zobrazí statistiky již jen pro vybraný rok',
    )
emojis = {2021: '🐀', 2020: '🐀', 2019: '🐀', 2018: '🐀', 2017: '🤮', 2016: '🤮', 2015: '🧹'}
emoji = emojis[selected_year]
# Load data only for selected year
last_year = load_year(data, selected_year)


# Categories of closed businesses
st.subheader('Jaké podniky se zavírají')
business_types_count = load_business_types_count(last_year)
c4 = plot_business_types(business_types_count)
st.altair_chart(c4, use_container_width=True)


# Percentage of offences accross closed establishments
st.subheader('Co se zanedbalo ' + emoji)
st.markdown('Na jednom místě se může sejít více pochybení.')

sorted_offenses_perc = load_offenses_perc(last_year)
num_offenses = st.slider('Vyber kolik pochybení ukázat', 1, sorted_offenses_perc.shape[0], 10)
sorted_offenses_perc = sorted_offenses_perc[:num_offenses]

st.table(sorted_offenses_perc)


# Provide a button to download dataset for selected year as .csv
csv = convert_df_to_csv(last_year)

st.download_button(
     label='Stáhnout data jako CSV',
     data=csv,
     file_name=f'foodpillory_{selected_year}.csv',
     mime='text/csv',
     help=f'Stáhne data pro rok {selected_year}'
 )

st.markdown('Stránka se nevěnuje celkovému počtu provozoven, které šlo v daném roce navštívit...a zavřít.')
st.markdown(
    "První výkop stránky jen tak pro nic za nic, původně inspirována skvělou přednáškou [Built in Super Heroes](https://www.youtube.com/watch?v=lyDLAutA88s), kde David Beazley pracuje jen s použitím standardní knihovny Pythonu s podobným (ale mnohem větším) datasetem, a také blogem Vicky Boykis [Doing small, fun projects](https://vickiboykis.com/2021/10/10/doing-small-fun-projects/)."
)
