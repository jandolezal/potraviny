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

    text = bars.mark_text(
        align='left', baseline='middle', dx=3
    ).encode(text='pocet:Q')

    return bars + text


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

    text = bars.mark_text(
        align='left', baseline='middle', dx=3
    ).encode(text='pocet:Q')

    return bars + text


def load_offenses_perc(data):
    offenses = data['zjistene_skutecnosti'].str.get_dummies()
    offenses_freq = offenses.mean()
    df = pd.DataFrame((offenses_freq.sort_values(ascending=False) * 100).round(1))
    df = df.reset_index()
    df.columns = ['Co se zanedbalo', 'Jak často (%)']
    df['Jak často (%)'] = (
        df['Jak často (%)'].astype(str).str.replace('.', ',', regex=False) + ' %'
    )
    df.index = np.arange(1, len(df) + 1)
    return df


st.title('Uzavřené provozovny v roce 2021')

st.markdown('Jak se loni zavíraly hospody nebo obchody, odkud jídlo nechcete?')
st.markdown(
    'Zdrojem dat je webová aplikace [Potraviny na pranýři](https://www.potravinynapranyri.cz/), která shrnuje výsledky šetření Státní zemědělské a potravinářeské inspekce.'
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


# Load data only for year 2021
last_year = load_year(data, 2021)


# Categories of closed businesses
st.subheader('Jaké podniky se zavírají')
business_types_count = load_business_types_count(last_year)
c2 = plot_business_types(business_types_count)
st.altair_chart(c2, use_container_width=True)


# Percentage of offences accross closed establishments
st.subheader('Co se zanedbalo')
st.markdown('Na jednom místě se může sejít více pochybení.')

sorted_offenses_perc = load_offenses_perc(last_year)
num_offenses = st.slider('Vyber kolik pochybení ukázat', 1, sorted_offenses_perc.shape[0], 5)
sorted_offenses_perc = sorted_offenses_perc[:num_offenses]

st.table(sorted_offenses_perc)

st.markdown('Stránka se nevěnuje celkovému počtu provozoven, které šlo v daném roce navštívit...a zavřít.')
st.markdown(
    "Stránka jen tak pro nic za nic, původně inspirována skvělou přednáškou [Built in Super Heroes](https://www.youtube.com/watch?v=lyDLAutA88s), kde David Beazley pracuje jen s použitím standardní knihovny Pythonu s podobným (ale mnohem větším) datasetem, a také blogem Vicky Boykis [Doing small, fun projects](https://vickiboykis.com/2021/10/10/doing-small-fun-projects/)."
)
