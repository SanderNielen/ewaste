# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 11:11:44 2019

Script to calculate the flows of neodymium corresponding to goods/waste flows.
Uses tbl_POM.csv to create POM_Nd.csv

Functions to plot the results.

@author: nielenssvan
"""

import pandas as pd
from os import getcwd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def p2f(x):
    """Custom function to convert percentages to float. Taken from
    https://stackoverflow.com/questions/12432663/what-is-a-clean-way-to-convert-a-string-percent-to-a-float
    """
    if '%' in x:
        return float(x.strip('%'))/100
    elif x=='':
        return np.nan
    else:
        return float(x.replace(',',''))

def group_splits(data_path, POM):
    """Divide product categories in two, based on market penetration data.
    Results in entries with `UNU_Key` XXXXa and XXXXb.
    """
    # Read data from CSVs
    penetr = pd.read_csv(data_path+"TechPenetration.csv", dtype={"UNU_Key":str})
    penetr["UNU_Key"] = penetr.New_Key.str[:-1]

    new = pd.merge(POM, penetr)   # Create entries for 'new' technology
    POM = pd.merge(POM, penetr, 'left')    # Modify original entries to represent old technology
    for value in ["POM_pieces", "ppi", "POM_t", "kpi"]:    # Calculate new amounts
        new[value] = new[value] * new.Share
        POM.loc[POM.Share.notna(), value] = POM[value] * (1 - POM.Share)
    new["UNU_Key"] = new.New_Key           # Update keys
    POM.loc[POM.UNU_Key.isin(penetr.UNU_Key), "UNU_Key"] = POM.New_Key.str.replace('b', 'a')
    POM = pd.concat([POM, new], ignore_index=True)
    POM = POM.drop(columns=["New_Key", "Share"])
    return POM

def Nd_flow_calc(data_path, POM):
    """Calculates the quantities of Nd present in the flows.
    Uses data about market share and Nd content of products.
    Results are saved as `POM_Nd.csv`
    """
    # Combine with Nd content and market share data
    content = pd.read_csv(data_path+"MarketShare+Content.csv", '\t', usecols=[0,2,34,36,40])
    #content = content[content.Component == "NdFeB"] #NB: temporary selection
    POM = pd.merge(POM, content.drop_duplicates(ignore_index=True))
    # Multiply by market share of products containing the component
    market = pd.read_csv(data_path+"MarketShare+Content.csv", '\t',
                         usecols=[c for c in range(0, 36)],
                         converters={str(c): p2f for c in range(1990, 2021)})
    market = market.drop(columns=["Product", "Nd_content"])
    for year in range(1980, 1990):
        market[year] = market[str(1990)]
    #market = market[market.Component == "NdFeB"]
    market = market.melt(["UNU_Key", "Component", "Component_weight"], None, "Year", "Share")
    market.Year = market.Year.astype(int)
    POM = pd.merge(POM, market, 'left')
    # Calculate first using Nd_content. Overwrite if better estimate via Component weight
    POM["Nd_t"] = POM.POM_t * POM.Nd_content
    POM.loc[POM.Component_weight.notna(), "Nd_t"] = POM.Component_weight * POM.POM_pieces * POM.Nd_concentration * 1e-6
    #Optional: If product weight differs >10% from category weight: scale Nd accordingly
#    POM["Weight"] = POM.POM_t * 1000 / POM.POM_pieces
#    select = POM.Component_weight.notna() & ((POM.Prod_weight > 1.1*POM.Weight) |
#                                            (POM.Prod_weight < 0.9*POM.Weight))
#    POM.loc[select, "Nd_t"] = POM.Nd_t * POM.Weight / POM.Prod_weight
    # Apply market share correction
    POM.loc[POM.Share.notna(), "Nd_t"] = POM.Nd_t * POM.Share

    # Save the results
    result = POM[POM.Nd_t.notna()]
    columns = ["Country", "UNU_Key", "Year", "Component", "POM_t", "POM_pieces", "Nd_t"]
    result[columns].to_csv(data_path+"POM_Nd.csv", index=False)
    return result

def future_Nd_flow_calc(data_path, POM):
    """Calculates the quantities of Nd present in the flows.
    Uses data about market share and Nd content of products.
    Results are saved as `POM_Nd.csv`
    """
    # Combine with Nd content and market share data
    content = pd.read_csv(data_path+"MarketShare-Future.csv", '\t', usecols=[0,2,64,66,70])
    #content = content[content.Component == "NdFeB"]
    POM = pd.merge(POM, content.drop_duplicates(ignore_index=True))
    # Multiply by market share of products containing the component
    market = pd.read_csv(data_path+"MarketShare-Future.csv", '\t',
                         usecols=[c for c in range(0, 66)],
                         converters={str(c): p2f for c in range(1990, 2051)})
    market = market.drop(columns=["Product", "Nd_content"])
    for year in range(1980, 1990):
        market[year] = market[str(1990)]
    #market = market[market.Component == "NdFeB"]
    market = market.melt(["UNU_Key", "Component", "Component_weight"], None, "Year", "Share")
    market.Year = market.Year.astype(int)
    POM = pd.merge(POM, market, 'left')
    # Calculate first using Nd_content. Overwrite if better estimate via Component weight
    POM["Nd_t"] = POM.POM_t * POM.Nd_content
    POM.loc[POM.Component_weight.notna(), "Nd_t"] = POM.Component_weight * POM.POM_pieces * POM.Nd_concentration * 1e-6
    POM.loc[POM.Share.notna(), "Nd_t"] = POM.Nd_t * POM.Share

    # Save the results
    result = POM[POM.Nd_t.notna()]
    columns = ["Country", "UNU_Key", "Year", "Component", "POM_t", "POM_pieces", "Nd_t"]
    result[columns].to_csv(data_path+"POM_Nd.csv", index=False)
    return result

def plot_quantity(csv, year, flow, element):
    """Produces a resource plot of the flows given in `csv` for `year`.
    `flow` and `element` specify the data columns to use from the `csv`.
    """
#    csv=data_path + "POM_Nd.csv"; year=2018; flow="POM_t"; element="Nd_t"
    # Select data of interest and calculate concentration.
    data = pd.read_csv(csv, usecols=["Country", "UNU_Key", "Year", "Component",
                                     flow, element])
    data = data[(data.Year==year) & (data.Component=="NdFeB")]
    pivot = data.pivot_table([flow, element], ["UNU_Key", "Component"],
                             aggfunc='sum')
    pivot["Concentr"] = pivot[element] / pivot[flow] *1000 # Concentration (kg/t)
    pivot = pivot.sort_values("Concentr", ascending=False).reset_index()
    # Some refinement of the data
    # pivot.loc[pivot.Concentr > 1, "Concentr"] = 0.006
    pivot = pivot[pivot[element] > 0]
    # Construct plot
    x = pivot[element].cumsum()
    fig, ax = plt.subplots()
    fig.set_size_inches(8, 5)
    # Color based on categories
    pivot = pd.merge(pivot, pd.read_csv(data_path+"categories.csv", usecols=[0,2]))
    plot = ax.bar(x, pivot.Concentr, -pivot[element], align='edge', color=pivot.color)
    # Label axis, categories and bars
    ax.set_xlim(0)
    ax.set(ylabel="Nd concentration (kg/t)", xlabel="Nd in waste (t)")
    labels = [mpatches.Patch(color=c, linewidth=1, label=l) for l,c in
              [("Small IT", 'tab:pink'), ("Small appliances", 'tab:green'),
               ("Vehicles", 'tab:red'), ("Cooling & freezing", 'tab:blue'),
               ("Industrial equipment", 'tab:purple'), ("Wind",'tab:cyan'),
               ("Large equipment", 'tab:brown'), ("Screens", 'tab:orange')] ]
    plt.legend(handles=labels)
    for l in range(len(pivot)):
        ax.text(x[l] - pivot[element][l]/2, pivot.Concentr[l] + 2e-4, pivot.UNU_Key[l])
    plt.savefig("WasteConc-%d-Plot.pdf" % year)
#    fig = plt.bar(x, pivot.Concentr, -pivot[element], align='edge')
#    plt.ylabel("Nd concentration (%)"); plt.xlabel("Waste quantity")
    #plt.xticks(x, labels)
    #plt.show()

"""
# Create dataset to investigate economy vs. Nd consumption correlation.
wdir = "C:\Users\nielenssvan\surfdrive\MFA\scripts\ewaste-xtended\data"
stats = pd.read_csv("tbl_Data.csv")
stats = stats.pivot_table("Value", ["Country", "Year"], "Destination")
pom = pd.read_csv("POM_Nd.csv")
pom = pom.pivot_table(['POM_t', 'POM_pieces', 'Nd_t'], ['Country', 'Year'], aggfunc=sum)
demand = pd.merge(stats, pom, left_index=True, right_index=True)
demand.to_clipboard()
"""

# def plot_trend(csv, min_yr, max_yr, flow, element):
    
#TODO: bubble plot. plot = ax.scatter(x, pivot.Concentr, pivot[element], pivot.color)

def treemap(csv, years): #TODO: remove variable definitions
    import matplotlib
    import squarify
    
    data = pd.read_csv(csv, usecols=["Country", "Year", "Component", "gpi",
                                     "Waste_Nd_t"])
    data = data[(data.Year.isin(years)) & (data.Component=="NdFeB")]
    df = data.pivot_table(["gpi", "Waste_Nd_t"], "Country", aggfunc='sum')
    df = df / len(years)
    df = df.reset_index()
     
    # create a color palette, mapped to these values
    cmap = matplotlib.cm.Greens
    # mini=min(my_values)
    norm = matplotlib.colors.Normalize(vmin=0, vmax=max(df.gpi))
    colors = [cmap(norm(value)) for value in df.gpi]
     
    # Change color
    squarify.plot(sizes=df.Waste_Nd_t, label=df.Country, color=colors, alpha=.9)
    # plt.colorbar() #FIXME: not compatible with squarify?
    plt.axis('off')
    plt.show()
    """
    ax = df.plot.scatter("Waste_Nd_t", "gpi")
    for l in range(len(df)):
        ax.text(df.Waste_Nd_t[l] + 5, df.gpi[l] + 0.1, df.Country[l])
    """

def country_trends(csv, trend):
    trend = "gpi"
    csv = data_path + "tbl_Waste.csv"
    data = pd.read_csv(csv, usecols=["Country", "Year", "gpi"])
    df = data.pivot_table("gpi", ["Country", "Year"], aggfunc='sum')
    df = df.reset_index()
    
    # Define colors
    growth = data.pivot_table("gpi", "Country", "Year", aggfunc='sum')
    growth["rate"] = growth["2018"] / growth["2008"]
    growth["color"] = "green"
    growth.loc[growth.rate >0.1, "color"] = "orange"
    #TODO df.loc[df.]

data_path = getcwd() + "\\..\\data\\"
#POM = pd.read_csv(data_path+"tbl_POM.csv")
#POM = group_splits(data_path, POM)
#POM.to_csv(data_path+"tbl_POM.csv", index=False)
#POM_Nd = Nd_flow_calc(data_path, POM)
""" # Plotting functions
plot_quantity(data_path + "POM_Nd.csv", 2018, "POM_t", "Nd_t")
plot_quantity(data_path + "tbl_Waste.csv", 2019, "WEEE_t", "Waste_Nd_t")
pt_POM = POM.pivot_table("POM_t", "Year", "UNU_Key", 'sum')
pt_POM.plot(kind='area', legend=False, ylim=(0,1e8))
treemap(data_path + "tbl_Waste.csv", range(2014, 2019))
"""

""" # These operations have been moved to script 03h
# Read additional product data from CSVs
ext_path = getcwd() + "\\..\\..\\..\\data\\"
cols = ["Year", "Country", "Sales"]
mri = pd.read_csv(ext_path+"MRI\\MRI-MFA.csv", usecols=cols)
mri["UNU_Key"] = "0802b"
cars = pd.read_csv(ext_path+"Vehicles\\All-Cars.csv")
bikes = pd.read_csv(ext_path+"E-bikes\\All-Bikes-EU.csv", usecols=cols)
bikes["UNU_Key"] = "1108"
wind = pd.read_csv(ext_path+"Wind\\Wind-Sales.csv", usecols=cols.append("Type"))
wind.loc[wind.Type == "Onshore", "UNU_Key"] = "1205a"
wind.loc[wind.Type == "Offshore", "UNU_Key"] = "1205b"
wind = wind.drop(columns="Type")
# Read product weight data
weight = pd.read_csv(data_path+"htbl_Key_Weight.csv")
# Add extra product sales data to POM table
for df in [mri, cars, bikes, wind]:
    df = df.rename(columns={"Sales": "POM_pieces"})
    df = pd.merge(df, weight)
    df["POM_t"] = df.POM_pieces * df.AverageWeight * 1e-3
    new = list(df.UNU_Key.unique())
    POM = POM[~ POM.UNU_Key.isin(new)]
    df = df.drop(columns="AverageWeight")
    POM = pd.concat([POM, df], ignore_index=True, sort=False)
"""
