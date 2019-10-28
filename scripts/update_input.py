# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 09:09:47 2019

Author: Sander van Nielen - CML - Leiden University
"""

import pandas as pd
from os import listdir, getcwd

def update_CN_match(years, source, dest):
    """Function to add match data for recent years
    to the list in `htbl_CN_Match_Key.csv`.
    """
    # Read original table from ewaste-master
    orig = pd.read_csv(source+"htbl_CN_Match_Key.csv", dtype=str)
    # Read correspondence tables one by one
    for y in years:
        py = str(y-1)
        file = "CN%s-CN%d.csv" % (py, y)
        link = pd.read_csv(dest+"new_codes\\"+file, dtype=str)
        link.rename(columns = {'CN'+py:'CN'}, inplace = True)
        # Select previous year from original
        prev = orig.loc[orig.Year == py] #.set_index('CN')
        # left join with correspondence table
        new = pd.merge(prev, link, how='left', on='CN')
        new.Year = str(y)
        new.loc[new['CN'+str(y)].isnull(), 'CN'+str(y)] = new.CN
        new.CN = new['CN'+str(y)]
        # Append to create new table
        orig = pd.concat([orig, new[['Year','CN', 'UNU_Key']]], 
                            ignore_index=True, sort=False)
        print("Conversion for CN in %d added." % y)
    # Save new table in ewaste-xtended
    orig.to_csv(dest+"htbl_CN_Match_Key.csv", index=False, quoting=2)

def update_PCC_match(home):
    # Read two original tables
    CN_match = pd.read_csv(home+"htbl_CN_Match_Key.csv", dtype=str)
    PCC_CN = pd.read_csv(home+"htbl_PCC_CN.csv", dtype=str)
    # Left join tables and save the result
    new = pd.merge(CN_match, PCC_CN, how='left')
    new[['PCC','UNU_Key','Year']].to_csv(home+"htbl_PCC_Match_Key.csv", 
       index=False, quoting=2)
    print("Conversion for PCC added.")

def weight_table(folder, dest):
    """Takes directory containing Intrastat net mass tables as input.
    Make table for CN-code to weight conversion.
    """
    tables = [f for f in listdir(folder) if ("FINAL" in f) | ("final" in f)]
    cols = ["Year", "CN", "Unit", "AverageWeight", "Price"] # Referring to unit weight & unit price.
    all_data = pd.DataFrame(columns=cols)
    for t in tables:
        # Determine year
        year = [int(s) for s in t.replace('_', ' ').split() if s.isdigit()][0]
        # Read and process excel sheet
        if year < 2012:
            conv = pd.read_excel(folder+t, usecols=[0,1,3,5], names=cols[1:], 
                                 na_values='.', dtype={"CN":str})
            conv = conv.replace({"Unit": {"NUMBER OF ITEMS": "p/st", "NUMBER OF CELLS": "p/st"}})
        elif year == 2012:
            conv = pd.read_excel(folder+t, names=cols[1:], 
                                 na_values='.', dtype={"CN":str})
        else:
           conv = pd.read_excel(folder+t, usecols=[0,1,2,4], names=cols[1:], 
                                 dtype={"CN":str})
        if len(conv) == 0:
            print("Skipped %d" % year)
            continue
        conv.CN = conv.CN.str.replace(' ', '')
        conv["Year"] = year
        all_data = pd.concat([all_data, conv], ignore_index=True, sort=False)
    weights = all_data[all_data.Unit == "p/st"]
    weights = weights.drop(columns=["Price", "Unit"])
    weights.to_csv(dest+"CN_Weight.csv", index=False)
    return all_data

def add_lines(table_name, extension):
    """Add the text from extension to the original table (from master version).
    Save as new table in the xtended model.
    """
    orig = open(table_name.replace("xtended", "master"), 'r')
    dest = open(table_name, 'w')
    # Copy original file to destination
    dest.write(orig.read())
    orig.close()
    # Write all lines in CSV-style
    for L in extension:
        dest.write(','.join(L))
        dest.write("\n")
    dest.close()
    
def add_my_cat(tbl_name, years, path):
    LL = []
    # Load categories
    if "PCC" in tbl_name:
        data = pd.read_csv(path+"new_codes\\my_categories_PCC.csv", dtype=str)
        categories = data[["PCC","Key"]].values.tolist()
        for cat in categories:
            for year in years:
                LL.append([cat[0], cat[1], str(year)])
        # Add list to exiting table
        add_lines(path+tbl_name, LL)
    elif "CN" in tbl_name:
        data = pd.read_csv(path+"new_codes\\my_categories_CN.csv", dtype=str)
        categories = data[["CN","Key"]].values.tolist()
        for cat in categories:
            for year in years:
                LL.append([cat[0], str(year), cat[1]])
        # Add list to exiting table
        add_lines(path+tbl_name, LL)

def add_my_cat2(path):
    """Read category names and codes from file, then combine with years
    and add to help tables (input for e-waste script).
    """
    # Read my categories
    PCC_cats = pd.read_csv(path+"new_codes\my_categories_PCC.csv", dtype=str,
                           usecols=["Key", "PCC"])
    CN_cats  = pd.read_csv(path+"new_codes\my_categories_CN.csv", dtype=str)
    nace_rev = pd.read_csv(path+"new_codes\PRC2007-PRC2008.csv", dtype=str, 
                           names=["PCC","PCC2008"])
    
    # Conversion table to translate PCC to CN and vice versa
    PCC_CN = pd.read_csv(path+"htbl_PCC_CN.csv", dtype={"PCC": str, "CN": str})
    PCC_CN["CN6"] = PCC_CN.CN.str[:6]
    # Lookup Prodcom code (PCC) from before 2008, when NACE 1.1 was used.
    old_PCC = pd.merge(PCC_cats.rename(columns={"PCC": "PCC2008"}), nace_rev) # inner join
    nace1 = pd.merge(old_PCC,  PCC_CN[PCC_CN.Year < 2008]) # inner join
    nace2 = pd.merge(PCC_cats, PCC_CN[PCC_CN.Year > 2007], how='left')
    # Two dataframes based on two source files
    from_PCC = pd.concat([nace1, nace2], ignore_index=True, sort=False)
    from_CN = pd.merge(CN_cats, PCC_CN, how='left')
    
    # Append the new dataframes to CSV files
    new_cat = pd.concat([from_PCC, from_CN], ignore_index=True, sort=False)
    new_cat.rename(columns={"Key": "UNU_Key"}, inplace=True)
    for c1, c2 in ("CN", "PCC"), ("PCC", "CN"): # For both codes
        table = pd.read_csv(path+"htbl_%s_Match_Key.csv" % c1, 
                            dtype={c1: str, "UNU_Key": str})
        new = pd.concat([table, new_cat.drop(columns=["PCC2008", "CN6", c2])],  
                        ignore_index=True, sort=False)
        # Drop rows with UNU-Key overlapping my category (same code)
        new.drop_duplicates(subset=[c1, "Year"], keep='last', inplace=True)
        new.to_csv(path+"htbl_%s_Match_Key.csv" % c1, index=False)

#TODO: method for expanding weight list to all years
#for y in years:
#    new = my_weights.copy()
#    new["Year"] = y
#    df = pd.concat([df, new], ignore_index=True, sort=False)

def weight(df):
    """Calculate the weight per row of a DataFrame with import & export
    columns.
    """
    return (df.Imp_kg + df.Exp_kg) / (df.Imp_sup + df.Exp_sup)

def calc_median_weight(key, root):
    """Calculates the median of weight for trade flows in `tbl_CN.csv`.
    Retuns a table with median product weight grouped by `key`.
    """
    # Load tables
    all_CN = pd.read_csv(root+"tbl_CN.csv", dtype={"CN":str})
    htbl = pd.read_csv(root+"htbl_CN_Match_Key.csv", dtype={"CN":str, "UNU_Key":str})
    units = pd.read_csv(root+"htbl_supplementary_units.csv", dtype=str)
    all_CN = pd.merge(all_CN, htbl, how='left')
    all_CN = pd.merge(all_CN, units, how='left')
    all_CN = all_CN.rename(columns={"Import_Quantity_Sup": "Imp_sup", 
                                    "Import_Quantity_kg": "Imp_kg", 
                                    "Export_Quantity_Sup": "Exp_sup", 
                                    "Export_Quantity_kg": "Exp_kg"})
    # Determine average weight per country, CN-code, year for relevant entries
    tbl_CN = all_CN.copy()[all_CN.Unit.isin(["p/st", "ce/el"]) & (all_CN.Country != "EU")]
    tbl_CN.loc[(tbl_CN.Imp_sup<=0) | (tbl_CN.Imp_kg<=0), ["Imp_sup", "Imp_kg"]] = 0
    tbl_CN.loc[(tbl_CN.Exp_sup<=0) | (tbl_CN.Exp_kg<=0), ["Exp_sup", "Exp_kg"]] = 0
    tbl_CN.loc[(tbl_CN.Imp_kg > 0) | (tbl_CN.Exp_kg >0), "Average"] = weight(tbl_CN)
    # Calculate median and return result
    result = pd.pivot_table(tbl_CN, aggfunc='median', values="Average",
                           index=key)
    result.rename(columns={"Average": "Median"}, inplace=True)
    result.to_csv(root+"%s_Weight.csv" % key)
    return result

def calc_avg_weight(max_dev, root):
    """Calculates the average weight of trade flows in `tbl_CN.csv`.
    Retuns a table with product weight per HS-code, year, and country
    """
    # Load tables
    all_CN = pd.read_csv(root+"tbl_CN.csv", dtype={"CN":str})
    htbl = pd.read_csv(root+"htbl_CN_Match_Key.csv", dtype={"CN":str, "UNU_Key":str})
    units = pd.read_csv(root+"htbl_supplementary_units.csv", dtype=str)
    all_CN = pd.merge(all_CN, htbl, how='left')
    all_CN = pd.merge(all_CN, units, how='left')
    all_CN = all_CN.rename(columns={"Import_Quantity_Sup": "Imp_sup", 
                                    "Import_Quantity_kg": "Imp_kg", 
                                    "Export_Quantity_Sup": "Exp_sup", 
                                    "Export_Quantity_kg": "Exp_kg"})
    # Determine average weight per country, CN-code, year for relevant entries
    tbl_CN = all_CN.copy()[all_CN.Unit.isin(["p/st", "ce/el"]) & (all_CN.Country != "EU")]
    tbl_CN.loc[(tbl_CN.Imp_sup<=0) | (tbl_CN.Imp_kg<=0), ["Imp_sup", "Imp_kg"]] = 0
    tbl_CN.loc[(tbl_CN.Exp_sup<=0) | (tbl_CN.Exp_kg<=0), ["Exp_sup", "Exp_kg"]] = 0
    tbl_CN.loc[(tbl_CN.Imp_kg > 0) | (tbl_CN.Exp_kg >0), "Average"] = weight(tbl_CN)
    # Calculate Median, MAD and nonzeros per CN-code and year
    key = ["CN", "UNU_Key", "Year"]
    trade_col = ["Imp_sup", "Imp_kg", "Exp_sup", "Exp_kg"]
    total = pd.pivot_table(tbl_CN, aggfunc='count', values=["Unit"],
                           index=key) #NB: just to create relevant index
    total["Median"] = pd.pivot_table(tbl_CN, aggfunc='median', values=["Average"],
                                     index=key)
    total["MAD"] = pd.pivot_table(tbl_CN, aggfunc='mad', values=["Average"],
                                  index=key)
    total["Group"] = pd.pivot_table(tbl_CN[tbl_CN.Average.notna()], aggfunc=len,
                                    values=["Country"], index=key)
    total = total.reset_index().drop(columns="Unit")
    
    # Remove outliers: value more than max_dev away from Median
    tbl_CN = pd.merge(tbl_CN, total, how='left')
    tbl_CN.loc[tbl_CN.Average - tbl_CN.Median > max_dev*tbl_CN.MAD, "Average"] = 0
    tbl_CN.loc[tbl_CN.Median - tbl_CN.Average > max_dev*tbl_CN.MAD, "Average"] = 0
    # Calculate average weight per CN-code and year using numeric data only
    valid = tbl_CN.Average.notnull() & (tbl_CN.Average > 0) & (tbl_CN.Average != float("inf"))
    per_yr = pd.pivot_table(tbl_CN[valid], aggfunc='sum', values=trade_col, index=key)
    per_yr["Y_Avg"] = weight(per_yr)
    per_yr = per_yr.reset_index().drop(columns=trade_col)
    # Replace outliers by the averaged weight. >4 data points: use Y_Avg
    tbl_CN = pd.merge(tbl_CN, per_yr, how='left')
    tbl_CN.loc[~valid & (tbl_CN.Group >4), "Average"] = tbl_CN.Y_Avg
    
    # Repeat procedure, now for groups of products (different years)
    per_prod = pd.pivot_table(tbl_CN[valid], aggfunc='sum', values=trade_col,
                              index=key[:2])
    per_prod["P_Avg"] = weight(per_prod)
    per_prod = per_prod.reset_index().drop(columns=trade_col)
    tbl_CN = pd.merge(tbl_CN, per_prod, how='left')
    tbl_CN.loc[~valid & ((tbl_CN.Group < 5) | tbl_CN.Group.isna()), 
               "Average"] = tbl_CN.P_Avg
    # Calc avg weight per UNU_Key per year
    #per_key = pd.pivot_table(tbl_CN[valid], aggfunc='sum', values=trade_col, index=key[1:])
#    per_key = pd.pivot_table(tbl_CN, aggfunc='median', values="Average", index="UNU_Key")
#    per_key.to_csv(root+"Key_Weight.csv")
    result = tbl_CN[["UNU_Key", "CN", "Year", "Country", "Average"]]
    result.to_csv(root+"Average_weights.csv", index=False)
    return result

def update_weight(root, update, with_yr, restore=True):
    """Adds more data to the average weight table of classification `update`.
    Calculates these averages using `calc_avg_weight` or a `restore`d result.
    For UNU-keys in `with_yr`, detailed weights per year are yielded.
    """
    code = update.split('_')[-1]
    # Load tables
    old = pd.read_csv(root.replace("xtended", "master") + 
                      "htbl_%s_Weight.csv" % code, dtype={update: str})
    file = "Average_weights.csv"
    if restore and file in listdir(root):
        avg = pd.read_csv(root+file, dtype={"CN": str})
    else:
        avg = calc_avg_weight(3, root)
    if code == "PCC": #FIXME: merge later, to account for PCC change after 2007
        match = pd.read_csv(root+"htbl_PCC_CN.csv", dtype={"PCC": str,
                                                           "CN": str})
        avg = pd.merge(avg, match)
    # Calculate median values per code, and per year when applicable
    with_yrs = avg.UNU_Key.isin(with_yr)
    median = pd.pivot_table(avg[~with_yrs], aggfunc='median', values="Average", index=update)
    detail = pd.pivot_table(avg[ with_yrs], aggfunc='median', values="Average", index=[update, "Year"])
    median = pd.concat([median.reset_index(), detail.reset_index()], ignore_index=True, sort=False)
    median.to_csv(root + code + "_Weight.csv", index=False)
    
    new = median.rename(columns={"Average": "AverageWeight"})
    mykey = set(new[update].unique()) - set(old[update].unique()) # new keys
    new = old.append(new[new[update].isin(mykey)], True, sort=False)
#    for k in mykey:
#        if type(k) != str: mykey.remove(k)
#    # Add new categories to existing (`old`) file, with entry for all years
#    for k in mykey:
#        start_year = avg[avg[update]==k].Year.min()
#        row = new[new[update]==k].assign(key=1)
#        years = pd.DataFrame({"Year": [ y for y in range(start_year, 2022)]})
#        rows = years.assign(key=1).merge(row).drop('key', 1) # equal to columns="key"
#        old = old.append(rows, ignore_index=True, sort=False)
    if update == "UNU_Key": # Add some  weights manual (not used yet)
        manual = pd.DataFrame({"UNU_Key": ["Headphones + earphones", "Laptops", 
                                           "MRIs", "Tablets"],
                               "AverageWeight": [0.0855, 1.81, 16000, 0.5]})
        new = new.append(manual, ignore_index=True, sort=False)
    new.to_csv(root+"htbl_%s_Weight.csv" % code, index=False)
    return new

def update_car_weight(data_path, source):
    # TODO: IMPLEMENT
    # Load ICCT data table, extract gross weight data
    # Remove car data from htbl_Key_Weight.csv
    # Append new data and save
    raise NotImplementedError("Work in progress for car weight update.")

def column_stats(col):
    stats = (col.median(), col.mean(), col.std(), min(col), max(col))
    print("Median: %f, Average: %f, Std. deviation: %f (%f - %f)" % stats)

def update_input(data_path):
    source = data_path + "..\\..\\ewaste-master\\data\\"
    update_CN_match([2016,2017,2018], source, data_path)
    update_PCC_match(data_path)
    add_my_cat2(data_path)

# Calls to functions
data_path = getcwd() + "\\..\\data\\"
# Export user-defined categories to my_categories_#.csv, add supplementary units
# Run R script 00a
#update_input(data_path)
# Now run R scripts 00b & 01
#all_weights = weight_table("C:\\Users\\nielenssvan\\surfdrive\\MFA\\data\\Net mass conversion factors\\", data_path)
#    res = calc_avg_weight(3, data_path)
#    med =pd.pivot_table(res, aggfunc='median', values="Average", index="CN")
#    med.to_csv(data_path+"CN_Weight.csv")
#    res = calc_median_weight("CN", data_path)
with_yr = ["Fans", "Shavers", "Cars", "Motorhomes", "NiMH batteries", "Nickel batteries"]
#new = update_weight(data_path, "UNU_Key", with_yr, 0)
#new = update_weight(data_path, "CN", with_yr)
#new = update_weight(data_path, "PCC", with_yr)
# Now run R script 02 & 03

#years = range(1995,2019)
#add_my_cat("htbl_PCC_Match_Key.csv", years, data_path)
#add_my_cat("htbl_CN_Match_Key.csv",  years, data_path)
