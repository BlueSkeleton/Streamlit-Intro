#!pip install mysqlclient
#!pip install jupytext
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import streamlit as st
#import jupytext

connection = 'mysql://toyscie:WILD4Rdata!@51.178.25.157:23456/toys_and_models'
connection = mysql.connector.connect(user = 'toyscie', password='WILD4Rdata!', host='51.178.25.157',port='23456',database='toys_and_models',use_pure=True)
#sql_engine = sql.create_engine(connection)

query_sales= '''SELECT 
    p.productLine,
    SUM(od.quantityOrdered) AS totalQuantityOrdered,
    previousMonth.totalQuantityOrdered AS previousMonthTotal,
    COALESCE(-(SUM(od.quantityOrdered) - previousMonth.totalQuantityOrdered), 0) AS difference,
    Round((COALESCE(-(SUM(od.quantityOrdered) - previousMonth.totalQuantityOrdered), 0) / previousMonth.totalQuantityOrdered) * 100, 2) AS rateOfChange 
FROM 
    orderdetails AS od
JOIN 
    products AS p ON od.productCode = p.productCode
JOIN 
    orders AS o ON od.orderNumber = o.orderNumber
LEFT JOIN (
    SELECT 
        SUM(od.quantityOrdered) AS totalQuantityOrdered,
        p.productLine
    FROM 
        orderdetails AS od
    JOIN 
        products AS p ON od.productCode = p.productCode
    JOIN 
        orders AS o ON od.orderNumber = o.orderNumber
    WHERE 
        MONTH(o.orderDate) = 12 AND YEAR(o.orderDate) = 2022
    GROUP BY 
        p.productLine
) AS previousMonth ON p.productLine = previousMonth.productLine
WHERE 
    MONTH(o.orderDate) = 1 AND YEAR(o.orderDate) = 2023
GROUP BY 
    p.productLine, previousMonth.totalQuantityOrdered
ORDER BY 
    totalQuantityOrdered DESC;
'''

query_fin1 = '''select cast(sum(priceEach * quantityOrdered) as float) as TotalTurnover, country from orders
join orderdetails on orders.orderNumber = orderdetails.orderNumber
join customers on orders.customerNumber = customers.customerNumber
where month(orderdate) = month(curdate()) or month(orderdate) = month(curdate()) - 1
group by country
order by TotalTurnover desc'''

query_fin2 = '''Select customers.customerNumber, concat(customers.contactFirstName,' ', customers.contactLastName) As complete_name, Total_Order, Total_paied from customers
	join (SELECT payments.customerNumber, Sum(payments.amount) as total_paied from payments group by payments.customerNumber) as totalpaied
		On customers.customerNumber=totalpaied.customerNumber
	join (SELECT orders.customerNumber, SUM(orderdetails.quantityOrdered * orderdetails.priceEach) As Total_Order from orders join orderdetails ON orders.orderNumber=orderdetails.orderNumber
group by orders.customerNumber) AS orderprice
		On  customers.customerNumber=orderprice.customerNumber
where orderprice.Total_Order>totalpaied.Total_paied
Group by customers.customerNumber; '''

query_log = '''SELECT products.productname, Sum(orderdetails.quantityOrdered) AS total_ordered, products.quantityInStock
FROM products
JOIN orderdetails ON products.productCode = orderdetails.productCode
GROUP BY products.productname, products.quantityInStock
ORDER BY total_ordered DESC
LIMIT 5;'''

query_hr = '''Select employeeNumber, concat(firstName,' ' , lastName) AS full_name, YearMonth, Total, RANKING from (
	Select employeeNumber, firstName, lastName, substring(paymentDate,1,7) as YearMonth,
	 sum(amount) AS Total, rank() over(partition by substring(paymentDate,1,7) order by  sum(amount) desc) AS RANKING
	 from employees
	join customers on employees.employeeNumber = customers.salesRepEmployeeNumber
	join payments on payments.customerNumber = customers.customerNumber
	Group by employeeNumber,  firstName, lastName,  substring(paymentDate,1,7)
	Order by YearMonth asc) AS Table_Rank
Where RANKING <3
Order by YearMonth, RANKING; '''

#Variables
df_fin1 = pd.read_sql_query(query_fin1, connection)
df_sales = pd.read_sql_query(query_sales, connection)
df_fin2 = pd.read_sql_query(query_fin2, connection)
df_log = pd.read_sql_query(query_log, connection)
df_hr = pd.read_sql_query(query_hr, connection)

plines_ms = [] #Initializing Multiselect jobbies
df_sales_filt = df_sales 
countries_ms = []
df_fin1_filt = df_fin1 

def drawFin1(df_fin1_filt):
  df_fin1_filt.to_csv("df_fin1_filt.csv")
  fig_fin1 = plt.figure(figsize=(17,10))
  turno = sns.barplot(y=df_fin1_filt['country'], x=df_fin1_filt['TotalTurnover'])
  plt.title("Turnover from last two months by country", size=20)
  turno.set(xlabel=None,ylabel=None)
  turno.grid(axis='x', linestyle=':', color='gray')
  turno.bar_label(turno.containers[0], label_type='center', padding=3)
  return(fig_fin1)

#df_sales = pd.read_sql_query(query_sales, connection)
#df_sales.to_csv("df_sales.csv")

def drawSales(df_sales_filt):
    df_sales_filt.to_csv("df_sales_filt.csv")
    fig_sales= plt.figure(figsize=(17, 10))
    gspec = fig_sales.add_gridspec(ncols=3,nrows=2)
    palette = sns.color_palette('Purples_r')

    ax0 = fig_sales.add_subplot(gspec[0:2,0:2])
    ax1 = fig_sales.add_subplot(gspec[0,2])
    ax2 = fig_sales.add_subplot(gspec[1,2])

    ax0.set_xlabel("Product Line", labelpad=10)
    ax0.set_title("Orders this months vs. Previous month",size = 20)
    ax0.bar(df_sales_filt.productLine,df_sales_filt.totalQuantityOrdered, color = palette[0])
    ax0.bar(df_sales_filt.productLine,df_sales_filt.previousMonthTotal,bottom = df_sales_filt.totalQuantityOrdered ,color = palette[1])
    ax0.legend(["Ordered this month","Ordered previous month"])
    ax0.grid(axis='y', linestyle=':', color='gray')
    ax0.yaxis.set_major_locator(ticker.MultipleLocator(2700/9)) #2700 is a multiple of 9 so don't fuck with it
    ax0.bar_label(ax0.containers[0], label_type='center', padding=3)
    ax0.bar_label(ax0.containers[1], label_type='center', padding=3)

    ax1.pie(df_sales_filt.totalQuantityOrdered, labels = df_sales_filt.productLine.values, autopct='%1.1f%%',colors = palette)
    ax1.set_title("Sales volume percentage/Product line this month",size = 18)

    ax2.pie(df_sales_filt.previousMonthTotal,labels = df_sales_filt.productLine.values, autopct='%1.1f%%',colors = palette)
    ax2.set_title("Previous Month",size = 20)
    return(fig_sales)

def drawFin2():

    df_fin2.to_csv("df_fin2.csv")
    fig, ax=plt.subplots(figsize=(17,10))
    ax.bar(df_fin2["complete_name"], df_fin2["Total_Order"], label="Total_Order")
    ax.bar(df_fin2["complete_name"], df_fin2["Total_paied"], label="Total_paied")
    width=7
    ax.set_title('Clients that not paid yet')
    ax.set_xlabel('Customer Number')
    plt.xticks(rotation=45)
    ax.set_ylabel('Amount')
    plt.legend()
    return(fig)

def drawLog():

    df_log.to_csv("df_log.csv")
    fig, ax = plt.subplots(figsize=(17, 10))
    ax.bar(df_log['productname'], df_log['total_ordered'], label='Total Ordered')
    ax.set_xticklabels(df_log['productname'], rotation=45, ha='right')
    ax.set_xlabel('Product Name')
    ax.set_ylabel('Total Ordered')
    ax.set_title('Top 5 Product Name by Total Ordered')
    ax = df_log.plot(kind='bar', color=['red', 'blue'])
    ax.set_title('Total Orders vs Quantitity in stock')
    ax.set_xlabel(['productname'], rotation=45, ha='right')
    ax.set_ylabel('Total Ordered')
    return(fig)

def drawHr():

    df_hr.to_csv("df_hr.csv")

#Dashboard Stuff

st.set_page_config(
    page_icon=":smiley:",
    layout="wide",
)

st.markdown("<h1 style='text-align: center; color: #7a0099;'>Toy Shop Bop</h1>", unsafe_allow_html=True)   #<----- title)

options = ['Sales', 'Finances 1', 'Finances 2', 'Logistics', 'Human Resources']
st.sidebar.header("Choose your KPI")
selecto = st.sidebar.radio("KPI List", options)

if selecto == 'Sales':
    plines_ms = st.sidebar.multiselect("Select the Product Lines:", 
    options=df_sales['productLine'].unique(),
    default=df_sales['productLine'].unique())

    mask_sales = df_sales['productLine'].isin(plines_ms)
    df_sales_filt = df_sales[mask_sales]
    
    fig_sales = drawSales(df_sales_filt)
    st.pyplot(fig_sales)
elif selecto == 'Finances 1':
    countries_ms = st.sidebar.multiselect("Select the Product Lines:", 
    options=df_fin1['country'].unique(),
    default=df_fin1['country'].unique())

    mask_fin1 = df_fin1['country'].isin(countries_ms)
    df_fin1_filt = df_fin1[mask_fin1]

    fig_fin1 = drawFin1(df_fin1_filt)
    st.pyplot(fig_fin1)
elif selecto == 'Finances 2':
    fig_fin2 = drawFin2()
    st.pyplot(fig_fin2)
elif selecto == 'Logistics':
    fig_log = drawLog()
    st.pyplot(fig_log)
else:
    fig_hr = drawHr()
    st.pyplot(fig_hr)


