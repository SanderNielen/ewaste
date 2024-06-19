# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 09:01:02 2020

@author: nielenssvan
"""

import pandas as pd
from os import getcwd

# Function
def waste_transfer(data_path, first=1990, last=2021):
    """Calculate the fate of waste after being generated.
    Save these 'waste transfer coefficients' in `tbl_WasteFate.csv`.
    """
    prosum = "C:\\Users\\nielenssvan\\surfdrive\\MFA\\data\\ProSUM\\"
    result = pd.DataFrame()
    
    for group in ["EEE", "Vehicles"]:
        # Read ProSUM data on waste generation and waste fate, then combine both
        fate = pd.read_csv(prosum + "Flow _ %s.csv" % group, '\t', index_col=0)
        waste = pd.read_csv(prosum+"Urban Mine _ %s.csv" % group, '\t', index_col=0)
        waste_fate = pd.merge(waste, fate, on=["category", "country", "year"])
        waste_fate.rename(columns={"country": "Country", "year": "Year"},
                          inplace=True)
        # Some adjustments to the data
        if group == "Vehicles":
            # Aggregate fossil vehicle categories
            waste_fate["category"] = waste_fate.category.replace({"Diesel": "ICE",
                "Other": "ICE", "Petrol": "ICE", "Unknown": "ICE", "LPG": "ICE",
                "NG": "ICE", "BEV/Fuelcell": "BEV"})
            waste_fate = waste_fate.groupby(["category", "Country", "flowtype",
                                        "Year", "population"]).sum().reset_index()
        # Waste must be >0. If there is no total waste, the waste flows are 0 also.
        waste_fate.loc[waste_fate.wastetons < 0, "wastetons"]  = 0
        waste_fate.loc[waste_fate.wastetons ==0, "flowtons_y"] = 0
        # Determine weight fractions per fate (`flowtype`)
        waste_fate["fraction"] = waste_fate.flowtons_y / waste_fate.wastetons
        index = ["category", "Country", "flowtype"]
        pivot = pd.pivot_table(waste_fate, "fraction", index, "Year")
        # Extrapolate forwards and backwards
        for year in range(2016, last):
            pivot[year] = pivot.mean(1)
        for year in range(first, 2010):
            pivot[year] = pivot[2010]
        # Reshape
        wfate = pivot.reset_index().melt(index, None, "Year", "fraction")
        index = ["category", "Country", "Year"]
        wfate = pd.pivot_table(wfate, "fraction", index, "flowtype")
        wfate = wfate.fillna(0)
        if group == "EEE":
        # Assumed that magnets are not scavenged, 3 columns can be summed together.
            wfate["wasteBin"] = wfate.wasteBin + wfate.scavenging \
                                + wfate.recycledAndScavanged
            wfate = wfate.drop(columns=["scavenging", "recycledAndScavanged"])
        elif group == "Vehicles":
            # Export to ETFA is ignored; 
            # it is unknown to which of the ETFA countries it goes.
            wfate["collected"] = wfate.wasteCollection \
                                 + wfate.exportedToEU28AndETFA # + wfate.massFlow
            wfate["exportReuse"] = wfate.exportedToOtherCountries
            wfate = wfate.drop(columns=["wasteCollection", "exportedToEU28AndETFA",
                                        "exportedToOtherCountries"])
        # Determine gap
        wfate["gap"] = 1 - wfate.sum(1)
        wfate.loc[wfate.gap<0, "gap"] = 0
        wfate = wfate.reset_index().melt(index, None, "flowtype", "fraction")
        result = result.append(wfate, sort=True)
    
    result.loc[result.fraction > 1, "fraction"] = 1 #FIXME: Still, the total can be >100%
    result.to_csv(data_path + "tbl_WasteFate.csv", index=False)
    return result

def waste_trt(waste, transf, data_path):
    """Calculate waste treatment quantities based on transfer coefficients.
    """
#    prosum = "C:\\Users\\nielenssvan\\surfdrive\\MFA\\data\\ProSUM\\"
    # Merge with tbl_Waste.csv data table and product categorisation
    waste = pd.read_csv(data_path + waste)
    categ = pd.read_csv(data_path+"categories.csv", usecols=[0,1], dtype='str')
    transf = pd.merge(transf, pd.merge(waste, categ, 'left'))
    #TODO: merge with own list of waste transfer for wind and industrial appl.
    
    # Write relevant columns on waste flows to CSV
    transf["Nd_t"] = transf.Waste_Nd_t * transf.fraction
    transf = transf[transf.Nd_t > 0]
    #NB: "category" left out; can easily be regained by merging with `categories.csv`
    columns = ["UNU_Key", "Component", "Country", "flowtype", "gpi", "Nd_t"]
    transf[columns].to_csv(data_path + "tbl_WasteTrt.csv", index=False)

data_path = getcwd() + "\\..\\data\\"
#transfer = waste_transfer(data_path)
#waste_trt("tbl_Waste.csv", transfer, data_path)

"""
# To determine EU weighted average of collection rates.
EU = ['AUT', 'CZE', 'DNK', 'ESP', 'FIN', 'FRA', 'GBR', 'ITA', 'NLD', 'POL', 'PRT', 'ROU', 'SVN', 'SWE', 'GRC', 'LUX', 'BEL', 'BGR', 'CYP', 'DEU', 'EST', 'HRV', 'HUN', 'IRL', 'LTU', 'LVA', 'MLT', 'SVK']
EU_collection = result[(result.Country.isin(EU)) & (result.flowtype.isin(["collected", "wasteCollection"]))]
EU_coll = pd.pivot_table(EU_collection, ["flowtons_y", "wastetons"], ["category", "Year"], aggfunc=sum)
EU_coll["fraction"] = EU_coll.flowtons_y / EU_coll.wastetons
"""