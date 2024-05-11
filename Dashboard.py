import pandas as pd  # pip install pandas openpyxl
import plotly.express as px  # pip install plotly-express
import streamlit as st  # pip install streamlit
import json

# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="Sales Dashboard", 
                   page_icon=":bar_chart:", 
                   layout="wide"
)

#READ EXCEL FILE
df = pd.read_excel(
    io="Data.xlsx",
    engine="openpyxl",
    sheet_name="CS",
    skiprows=0,
    usecols="A:L",
    nrows=5781,
    )

#CREATING GEOJSON CONECTION
us_states = json.load(open("states.geojson", 'r'))
#----------------------------------

#UNDERSTANDING WHATS INSIDE GEOJSON
#type(us_states)
#us_states.keys()
#type(us_states["features"])
#us_states["features"][0].keys()
#us_states['features'][0]['properties']
#----------------------------------

#GETTING DATA FROM THE GEOJSON THAT WILL BE USED
state_id_map = {}
for feature in us_states['features']:
    feature["id"] = feature["properties"]["STATEFP"]
    state_id_map[feature["properties"]["NAME"]] = feature["id"]
#----------------------------------

#MANIPULATING Data.xlsx FILE
df=df.sort_values(("Date"), ascending=False) #SORTING DATA BY COLUMN "DATE"
df["Month"] = df["Date"].apply(lambda x: str(x.year) + "-" + str(x.month)) #ADDING "MONTH" COLUMN
df["Day"] = df["Date"].apply(lambda x: str(x.day)) #ADDING "DAY" COLUMN
df["Day"] = pd.to_numeric(df["Day"]) #CONVERTING "DAY" COLUMN TO NUMERIC VALUE
df["Customer Satisfaction Rating"] = df["Customer Satisfaction"].str.extract(r'\((\d+)\)') #GETTING NUMERIC VALUE FROM COLUMN "CUSTOMER SATISFACTION"
df["Customer Satisfaction Rating"] = pd.to_numeric(df["Customer Satisfaction Rating"]) #CONVERTING "DAY" COLUMN TO NUMERIC VALUE
df["id"] = df["State"].apply(lambda x: state_id_map[x]) #COPYING "ID" FROM THE GEOJSON TO THE EXCEL FILE
#-----------------------------------

#CREATING STREAMLIT PAGE

st.sidebar.header("Please Filter Here:") #SIDEBAR TO DISPLAY FILTER

Month = st.sidebar.selectbox("Month", df["Month"].unique()) #DATE FILTER

State = st.sidebar.multiselect(
    "Select the State:",
    options=df["State"].unique(),
    default=df["State"].unique()
) #STATE FILTER

Customer = st.sidebar.multiselect(
    "Select the Customer:",
    options=df["Customer"].unique(),
    default=df["Customer"].unique(),
) #CUSTOMER FILTER
#-----------------------------------

#THIS WILL MAKE THE FILTER WORK
df_selection = df.query(
    "Month == @Month & State == @State & Customer == @Customer" 
) #WE JUST NEED TO REFERENCE DE VARIABLES ABOVE

if df_selection.empty:
    st.warning("No data available based on the current filter settings!") #CHECK IF THE DATAFRAME IS EMPTY
    st.stop() #THIS WILL HALT THE APP FROM FURTHER EXECUTION.
#-----------------------------------

#RUNNING STREAMLIT PAGE, YOU MUST UPLOAD A GITHUB REPO WITH THE FILE AND CREATE A NEW APP ON STREAMLIT
#st.dataframe(df_selection)
#-----------------------------------

#MAIN PAGE
st.title(":bar_chart: Sales Dashboard")
st.markdown("##")

#TOP KPI's
total_sales = int(df_selection["Revenue"].sum()) #THIS IS A SUM TO SHOW THE TOTAL REVENUE IN THE FIRST CARD
average_rating = round(df_selection["Customer Satisfaction Rating"].mean(), 1) #THIS FORMULA CALCULATES THE AVERAGE CSAT
star_rating = ":star:" * int(round(average_rating, 0)) #THIS IS HOW WE CALCULATE THE NUMBER OF STARS SHOWN IN THE THIRD CARD
average_revenue = round(df_selection["Revenue"].mean(), 2) #THIS CALCULATES THE AVERAGE REVENUE OF ALL THE SALES

left_column, middle_column, right_column = st.columns(3)
with left_column:
    st.markdown(f"<p style='font-size: x-large; font-weight: bold;'>Revenue:</p>", unsafe_allow_html=True) #HERE I USED SOME CSS JUST TO MAKE THE TEXT THE SIZE I WANT
    st.subheader(f"US$ {total_sales:,}", anchor=False)
with middle_column:
    st.markdown(f"<p style='font-size: x-large; font-weight: bold;'>Average Revenue:</p>", unsafe_allow_html=True)
    st.subheader(f"US$ {average_revenue:,}", anchor=False)
with right_column:
    st.markdown(f"<p style='font-size: x-large; font-weight: bold;'>Customer Satisfaction Rating:</p>", unsafe_allow_html=True)
    st.subheader(f"{average_rating} {star_rating}", anchor=False)

st.markdown("""---""")
#-----------------------------------

#REVENUE BY DAY OF THE MONTH [BAR CHART]
revenue_by_date = df_selection.groupby(by=["Day"])[["Revenue"]].sum()
fig_daily_sales = px.bar(
    revenue_by_date,
    x=revenue_by_date.index,
    y="Revenue",
    title="<b>Revenue by Day</b>", #HERE I USED SOME HTML TO MAKE THE TITLE BOLD
    color_discrete_sequence=["#086788"] * len(revenue_by_date), #ADDING COLOR TO THE BAR CHART
)
fig_daily_sales.update_layout(
    xaxis=dict(tickmode="linear", title=""),  #REMOVING TITLE FROM X AXIS
    yaxis=dict(title="", showgrid=True, gridcolor="lightgrey", gridwidth=1, griddash="dot"), #ADDIND DOT LINES TO THE Y AXIS
) 
fig_daily_sales.update_xaxes(tickfont_color="black", tickfont_size=9 
) #HERE I DID SOME FORMATTING TO GET BETTER VISUALS FOR THE X AXIS
fig_daily_sales.update_yaxes(tickfont_color="black", tickfont_size=12 
) #HERE I DID SOME FORMATTING TO GET BETTER VISUALS FOR THE Y AXIS
#-----------------------------------

#REVENUE BY STATE [CHOROPLETH MAP]
df_grouped = df_selection.groupby(['id', 'State']).agg({'Revenue': 'sum'}).reset_index()
fig_choropleth_US_map=px.choropleth_mapbox(df_grouped, locations="id", color="Revenue",
                                        center={"lat": 31.15, "lon":-83.42}, zoom=3.7, title="<b>Revenue by State</b>",
                                        geojson=us_states, color_continuous_scale="blues", opacity=0.6,
                                        hover_name= "State", hover_data={"Revenue": True},
)
fig_choropleth_US_map.update_layout(
    autosize= False,
    mapbox_style="open-street-map",
)
#-----------------------------------

#ADDING CHARTS ABOVE TO THE STREAMLIT COLUMNS
left_column, right_column = st.columns(2)
left_column.plotly_chart(fig_daily_sales, use_container_width=True)
right_column.plotly_chart(fig_choropleth_US_map, use_container_width=True)
#-----------------------------------

#REVENUE BY CUSTOMER AQUISITION TYPE [BAR CHART]
revenue_by_caqt= df_selection.groupby(by=["Customer Acquisition Type"])[["Revenue"]].sum().sort_values(by="Customer Acquisition Type") #SORTING VALUES AND GROUPING BY
fig_Revenue_by_CustomerAq1 = px.bar(
    revenue_by_caqt,
    x=revenue_by_caqt.index,
    y="Revenue",
    text=revenue_by_caqt["Revenue"].apply(lambda x: f"US$ {x:,}"),
    title="<b>Revenue by Customer Acquisition Type</b>", #HERE I USED SOME CSS JUST TO MAKE THE TEXT BOLD
    color_discrete_sequence=["#086788"] * len(revenue_by_caqt),
)

fig_Revenue_by_CustomerAq1.update_traces(textposition="outside",texttemplate='%{text}', 
                  textfont_color="#000", textfont_size=11)
fig_Revenue_by_CustomerAq1.update_layout(
    xaxis=dict(tickmode="linear", title="",), 
    yaxis=dict(showgrid=False, title="",showticklabels=False), 
)
fig_Revenue_by_CustomerAq1.update_xaxes(tickfont_color="black", tickfont_size=15)
#------------------------------------------

#REVENUE BY CUSTOMER AQUISITION TYPE [PIE CHART]
sales_by_Customer_Aq = df_selection.groupby(by=["Customer Acquisition Type"])[["Revenue"]].sum().sort_values(by="Customer Acquisition Type") #SORTING VALUES AND GROUPING BY
fig_Revenue_by_CustomerAq2 = px.pie(
    sales_by_Customer_Aq,
    values="Revenue",
    color_discrete_sequence=['#086788', '#DD1C1A', '#F0C808'], #HERE I WROTHE THIS TO CHOOSE THE COLORS OF THE PIE PIECES
    names=sales_by_Customer_Aq.index,
    title="<b>Revenue by Customer Acquisition Type (%) </b>",
)
#-----------------------------------

#ADDING CHARTS ABOVE TO THE STREAMLIT COLUMNS
left_column, right_column = st.columns(2)
left_column.plotly_chart(fig_Revenue_by_CustomerAq1, use_container_width=True)
right_column.plotly_chart(fig_Revenue_by_CustomerAq2, use_container_width=True)
#-----------------------------------

#UNITS SOLD BY PRODUCT [BAR CHART]
sales_by_product = df_selection.groupby(by=["Product"])[["Units"]].sum().sort_values(by="Units") #SORTING VALUES AND GROUPING BY
fig_product_sales = px.bar(
    sales_by_product,
    x="Units",
    y=sales_by_product.index,
    text=sales_by_product["Units"].apply(lambda x: f" {x}"), #ADDING A SPACE BETWEEN LABEL AND BAR
    title="<b>Units Sold by Product</b>", #HERE I USED SOME HTML TO MAKE THE TITLE BOLD
    color_discrete_sequence=["#086788"] * len(sales_by_product), #ADDING COLOR TO THE BAR CHART
)

fig_product_sales.update_traces(textposition="inside",texttemplate='%{text}', 
                  textfont_color="#FFF", textfont_size=12)
fig_product_sales.update_layout(
    xaxis=dict(title="",showgrid=False, showticklabels=False,), #THIS MAKES GRINDLINES DESAPEAR
    yaxis=dict(title="",), #REMOVING TITLE FROM Y AXIS
)
fig_product_sales.update_yaxes(tickfont_color="black", tickfont_size=12)
#-----------------------------------

#ADDING CHARTS ABOVE TO THE STREAMLIT COLUMNS
left_column, middle_column, right_column = st.columns(3)
middle_column.plotly_chart(fig_product_sales, use_container_width=True)

# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)