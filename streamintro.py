import streamlit as st
import pandas as pd

st.title('Hello Wilders, welcome to my application!')

st.write("I enjoy to discover stremalit possibilities")

df = pd.read_csv("https://raw.githubusercontent.com/murpi/wilddata/master/quests/cars.csv")
