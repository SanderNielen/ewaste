# -----------------------------------------------------------------------------------------------------------
#
#   Name:           02Apparent_Consumption_Method.R
#
#   Description:    This script will read CSV file's of Prodcom data, and International trade data and 
#                   convert everything to weight (kg) with the use of average weights data.
#                   Then the apparent consumption can be calculated with the formula:
#                   Apparent consumption = Production + Imports- Exports
#
#
#   Author:         dr C.P. Balde - Statistics Netherlands
#   Revised version:V.M. van Straalen - Statistics Netherlands
#
# -----------------------------------------------------------------------------------------------------------



setwd(DATA_PATH)

require(plyr)

options(stringsAsFactors=FALSE, warn=0, scipen=999, digits=4)

# ----------------------------------------------------------
# tbl_PCC: Read prodcom data
# ----------------------------------------------------------
tbl_PCC <- read.csv("tbl_PCC.csv", quote = "\"", 
                      colClasses = c("character", "character", "character", "numeric", "numeric",
                                     "character", "NULL"))


# ----------------------------------------------------------
# htbl_PCC_Weight: Read average weights per prodcom code #NEW
# ----------------------------------------------------------
htbl_PCC_Weight <- read.csv("htbl_PCC_Weight.csv", quote = "\"",
                            colClasses = c("character", "numeric", "character"))

# rename AverageWeight to PCC_Av_W
names(htbl_PCC_Weight)[2] <- "PCC_Av_W"

# Split table into one for general average weights and one for year specific weights
selection <- which( htbl_PCC_Weight$Year != "" )
if (length(selection) > 0){
  htbl_PCC_Weight_yr <- htbl_PCC_Weight[selection, ]
  htbl_PCC_Weight_yr <- plyr::rename(htbl_PCC_Weight_yr, c("PCC_Av_W"="PCC_Year_Av_W"))
}

# and remove the same rows from the original
htbl_PCC_Weight <- htbl_PCC_Weight[-selection,]
htbl_PCC_Weight$Year <- NULL


# ----------------------------------------------------------
# htbl_Key_Weight: Read average weights per UNU_Key
# ----------------------------------------------------------
htbl_Key_Weight <- read.csv("htbl_Key_Weight.csv", quote = "\"",
                              colClasses = c("character", "character", "numeric", "character"))

# rename AverageWeight to Key_Av_W
htbl_Key_Weight <- plyr::rename(htbl_Key_Weight, c("AverageWeight"="Key_Av_W"))

# Split table into one for general EU average weights and one for country specific weights

selection <- which( htbl_Key_Weight$Country != "" )
if (length(selection) > 0){
  htbl_Key_Weight_country <- htbl_Key_Weight[selection, ]
  htbl_Key_Weight_country <- plyr::rename(htbl_Key_Weight_country, c("Key_Av_W"="Key_Country_Av_W"))
}

# and remove the same rows from the original
htbl_Key_Weight <- htbl_Key_Weight[-selection,]
htbl_Key_Weight$Country <- NULL

# Repeat for year specific weights #NEW
selection <- which( htbl_Key_Weight$Year != "" )
if (length(selection) > 0){
  htbl_Key_Weight_year <- htbl_Key_Weight[selection, ]
  htbl_Key_Weight_year <- plyr::rename(htbl_Key_Weight_year, c("Key_Av_W"="Key_Year_Av_W"))
}

htbl_Key_Weight <- htbl_Key_Weight[-selection,]
htbl_Key_Weight$Year <- NULL
  

# ----------------------------------------------------------
# htbl_PCC_Match_Key: Read conversion table PCC to UNU_Keys
# ----------------------------------------------------------
htbl_PCC_Match_Key <- read.csv("htbl_PCC_Match_Key.csv", quote = "\"",
                               colClasses = c("character", "character", "character"))


# ----------------------------------------------------------
# htbl_PCC_Match_Key: Merge average weights per UNU_Key with PCC to UNU_Keys conversion table
# ----------------------------------------------------------
htbl_PCC_Match_Key <- merge(htbl_PCC_Match_Key, htbl_Key_Weight,
                            by=c("UNU_Key"), all.x = TRUE)
htbl_PCC_Match_Key <- merge(htbl_PCC_Match_Key, htbl_Key_Weight_year,
                            by=c("UNU_Key", "Year"), all.x = TRUE)


# ----------------------------------------------------------
# tbl_PCC: Merge PCC & UNU_Key average weights with prodcom data #NEW
# ----------------------------------------------------------
tbl_PCC <- merge(tbl_PCC, htbl_PCC_Weight, by=c("PCC"), all.x = TRUE)
tbl_PCC <- merge(tbl_PCC, htbl_PCC_Weight_yr, by=c("PCC", "Year"), all.x = TRUE)
tbl_PCC <- merge(tbl_PCC, htbl_PCC_Match_Key, by=c("PCC", "Year"), all.x = TRUE)
tbl_PCC <- merge(tbl_PCC, htbl_Key_Weight_country, by=c("UNU_Key", "Country", "Year"), all.x = TRUE)

rm(htbl_PCC_Weight)
rm(htbl_PCC_Weight_yr)
rm(htbl_PCC_Match_Key)

# ----------------------------------------------------------
# tbl_PCC: Select best average weight to use #NEW
# ----------------------------------------------------------

# Determination of the weight. If more specific data is available, it is pasted in place
for (source in list("Key_Av_W", "PCC_Av_W", "Key_Year_Av_W", "PCC_Year_Av_W", "Key_Country_Av_W")){
    selection <- which (!is.na(tbl_PCC[[source]]))
    if (length(selection) > 0){
      tbl_PCC[selection, "Av_Weight"] <- tbl_PCC[selection, source]
    }
    # drop temporary column
    tbl_PCC[[source]] <- NULL
}

# restore column order
sortorder_c <- c("PCC", "Year", "Country", "Value", "prodcom_units", "Unit", 
                 "UNU_Key", "Av_Weight")
tbl_PCC <- tbl_PCC[, sortorder_c ]


# ----------------------------------------------------------
# tbl_PCC: Determination of the production
# ----------------------------------------------------------

# Conversion calculations
# p/st
selection <- tbl_PCC$Unit == "p/st" 
# Track location of TRUE values while removing the NA's.
selection <- which(selection)

tbl_PCC[selection, "PCC_kg"] <- tbl_PCC[selection, "Av_Weight"] * tbl_PCC[selection, "prodcom_units"]
tbl_PCC[selection, "PCC_p"] <- tbl_PCC[selection, "prodcom_units"]


# kg
selection <- tbl_PCC$Unit == "kg" 
# Track location of TRUE values while removing the NA's.
selection <- which(selection)

tbl_PCC[selection, "PCC_kg"] <- tbl_PCC[selection, "prodcom_units"]
tbl_PCC[selection, "PCC_p"] <- tbl_PCC[selection, "prodcom_units"] /
  tbl_PCC[selection, "Av_Weight"] 



# ----------------------------------------------------------
# tbl_PCC: Aggregate PCC per UNU_Key and Year for each Country
# ----------------------------------------------------------
# Convert empty UNU_Keys in NA so they will be removed by the aggregate function.
tbl_PCC[which (tbl_PCC$UNU_Key == ""), "UNU_Key"] <- NA

# Aggregate results per UNU_Key, Year and Country
UNU_countries <- ddply( tbl_PCC[!is.na(tbl_PCC$UNU_Key), ], c("UNU_Key", "Year", "Country"), summarise,
                        PCC_kg = sum(PCC_kg, na.rm=TRUE),
                        PCC_p = sum(PCC_p, na.rm=TRUE) )
rm(tbl_PCC)




### Now the CN code calculations.


# ----------------------------------------------------------
# tbl_CN: Read CN (International Trade) data
# ----------------------------------------------------------
tbl_CN <- read.csv("tbl_CN.csv", quote = "\"",
                   colClasses = c("character", "character", "character", "numeric", "numeric",
                                  "numeric", "numeric", "character", "numeric", "numeric"))

# Convert country codes to uppercase.
tbl_CN$Country <- toupper(tbl_CN$Country)


######################## TIJDELIJKE AANPASSING. BETER DIRECT INVOEREN BIJ JUISTE CN DATA IMPORT
tbl_CN[tbl_CN$CN %in% c("84512110",
                         "84512190",
                         "85171990",
                         "85173000",
                         "85175010",
                         "85175090",
                         "85181010",
                         "85181020",
                         "85181080",
                         "85183010",
                         "85183080",
                         "85183090",
                         "85185010",
                         "94051010",
                         "94051028",
                         "94051029",
                         "94051030",
                         "94051099",
                         "94052019",
                         "94052030",
                         "95031010",
                         "95031090",
                         "95035000",
                         "84151000",
                         "84158110",
                         "84158210",
                         "84158280",
                         "84158310",
                         "84158390",
                         "84181010",
                         "84183010",
                         "84184010",
                         "84186110",
                         "84186190",
                         "84186920",
                         "84186991",
                         "84672910",
                         "85088010",
                         "85152910",
                         "85174000",
                         "85178010",
                         "85178090",
                         "85152990",
                         "85172200",
                         "85178110",
                         "85178190",
                         "85178290",
                         "85181090",
                         "85182110",
                         "85182210",
                         "85318010",
                         "85318030",
                         "85318080",
                         "85318090",
                         "85434000",
                         "85438915",
                         "90181900",
                         "90241010",
                         "90258091",
                         "90268091",
                         "90278015",
                         "90278016",
                         "90278018",
                         "90303930",
                         "90304010",
                         "90304090",
                         "90308110",
                         "90308120",
                         "90308181",
                         "90308183",
                         "90308185",
                         "90308189",
                         "90308920",
                         "90308981",
                         "90308983",
                         "90308985",
                         "90308989",
                         "90308992",
                         "90318031",
                         "90318039",
                         "95041000",
                         "84158190",
                         "85272191",
                         "85272199",
                         "90248010"), "Unit"] <- "-"

# ----------------------------------------------------------
# htbl_CN_Weight: Read average weights per CN code #NEW
# ----------------------------------------------------------
htbl_CN_Weight <- read.csv("htbl_CN_Weight.csv",quote = "\"",
                             colClasses = c("character", "numeric", "character"))

# rename AverageWeight to CN_Av_W
htbl_CN_Weight <- plyr::rename(htbl_CN_Weight, c("AverageWeight"="CN_Av_W"))

# Split table into one for general average weights and one for year specific weights
selection <- which( htbl_CN_Weight$Year != "" )
if (length(selection) > 0){
  htbl_CN_Weight_yr <- htbl_CN_Weight[selection, ]
  htbl_CN_Weight_yr <- plyr::rename(htbl_CN_Weight_yr, c("CN_Av_W"="CN_Year_Av_W"))
}

# and remove the same rows from the original
htbl_CN_Weight <- htbl_CN_Weight[-selection,]
htbl_CN_Weight$Year <- NULL



# ----------------------------------------------------------
# htbl_CN_Match_Key: Read conversion table CN to UNU_Keys
# ----------------------------------------------------------
htbl_CN_Match_Key <- read.csv("htbl_CN_Match_Key.csv", quote = "\"",
                              colClasses = c("character", "character", "character"))



# ----------------------------------------------------------
# htbl_CN_Match_Key: Merge average weights per UNUKey with CN to UNU_Keys conversion table
# ----------------------------------------------------------
htbl_CN_Match_Key <- merge(htbl_CN_Match_Key, htbl_Key_Weight, by=c("UNU_Key"), all.x = TRUE)
htbl_CN_Match_Key <- merge(htbl_CN_Match_Key, htbl_Key_Weight_year,
                           by=c("UNU_Key", "Year"), all.x = TRUE)
rm(htbl_Key_Weight)


# ----------------------------------------------------------
# tbl_CN: Merge CN & UNU_Key average weights with CN data #NEW
# ----------------------------------------------------------
tbl_CN <- merge(tbl_CN, htbl_CN_Weight, by=c("CN"), all.x = TRUE)
tbl_CN <- merge(tbl_CN, htbl_CN_Weight_yr, by=c("CN", "Year"), all.x = TRUE)
tbl_CN <- merge(tbl_CN, htbl_CN_Match_Key, by=c("CN", "Year"), all.x = TRUE)
tbl_CN <- merge(tbl_CN, htbl_Key_Weight_country,
                by=c("UNU_Key", "Country", "Year"), all.x = TRUE)

rm(htbl_CN_Weight)
rm(htbl_CN_Weight_yr)
rm(htbl_CN_Match_Key)

# ----------------------------------------------------------
# tbl_CN: Select best average weight to use #NEW
# ----------------------------------------------------------

# Determination of the weight. If more specific data is available, it is pasted in place
for (source in list("Key_Av_W", "CN_Av_W", "Key_Year_Av_W", "CN_Year_Av_W",
                    "Key_Country_Av_W")) {
    selection <- which (!is.na(tbl_CN[[source]]))
    if (length(selection) > 0){
      tbl_CN[selection, "Av_Weight"] <- tbl_CN[selection, source]
    }
    # drop temporary column
    tbl_CN[[source]] <- NULL
}

# restore column order
sortorder_c <- c("CN", "UNU_Key", "Year", "Country", "Unit", "Import_Quantity_Sup",
                 "Import_Value", "Export_Quantity_Sup", "Export_Value", 
				 "Import_Quantity_kg", "Export_Quantity_kg", "Av_Weight")
tbl_CN <- tbl_CN[, sortorder_c ]




# ----------------------------------------------------------
# tbl_CN: Convert CN values to weight
# ----------------------------------------------------------

# Convert missing values to "p/st" and empty to "-".
tbl_CN[which(tbl_CN$Unit == ""), "Unit"] <- "-"
tbl_CN[is.na(tbl_CN$Unit), "Unit"] <- "p/st"

# Conversion calculations. Weight is less reliable as the number of pieces.
# Therefore we calculate the weight by multiplying the number of pieces with the average weight.
tbl_CN[tbl_CN$Unit == "p/st", "cn_imp_kg"] <- tbl_CN[tbl_CN$Unit == "p/st", "Av_Weight"] *
  tbl_CN[tbl_CN$Unit == "p/st", "Import_Quantity_Sup"]
tbl_CN[tbl_CN$Unit == "p/st", "cn_exp_kg"] <- tbl_CN[tbl_CN$Unit == "p/st", "Av_Weight"] *
  tbl_CN[tbl_CN$Unit == "p/st", "Export_Quantity_Sup"]
tbl_CN[tbl_CN$Unit == "p/st", "cn_imp_pieces"] <- tbl_CN[tbl_CN$Unit == "p/st", "Import_Quantity_Sup"]
tbl_CN[tbl_CN$Unit == "p/st", "cn_exp_pieces"] <- tbl_CN[tbl_CN$Unit == "p/st", "Export_Quantity_Sup"]


# In case no information about p/st is available, the data on weights is used.
selection <- tbl_CN$Unit != "p/st"

tbl_CN[selection, "cn_imp_kg"] <- tbl_CN[selection, "Import_Quantity_kg"]
tbl_CN[selection, "cn_exp_kg"] <- tbl_CN[selection, "Export_Quantity_kg"]
tbl_CN[selection, "cn_imp_pieces"] <- tbl_CN[selection, "Import_Quantity_kg"] / tbl_CN[selection, "Av_Weight"]
tbl_CN[selection, "cn_exp_pieces"] <- tbl_CN[selection, "Export_Quantity_kg"] / tbl_CN[selection, "Av_Weight"]




# ----------------------------------------------------------
# tbl_CN: Aggregate CN per UNU_Key and Year for each Country
# ----------------------------------------------------------
# Remove empty UNU_Keys.
selection <- !(tbl_CN$UNU_Key == "" | is.na(tbl_CN$UNU_Key))
tbl_CN <- tbl_CN[selection, ]

#Aggregate results per UNU_Key and Year
library(plyr)
tbl_CN_aggr <- ddply( tbl_CN, c("UNU_Key", "Year", "Country"), summarise,
                      imp_kg = sum(cn_imp_kg, na.rm=TRUE),
                      exp_kg = sum(cn_exp_kg, na.rm=TRUE),
                      imp_p = sum(cn_imp_pieces, na.rm=TRUE),
                      exp_p = sum(cn_exp_pieces, na.rm=TRUE) )

rm(tbl_CN)


# ----------------------------------------------------------
# UNU_countries: merge aggregated CN codes with combination table
# ----------------------------------------------------------
UNU_countries <- merge(UNU_countries, tbl_CN_aggr, by=c("UNU_Key", "Year", "Country"), all = TRUE)
rm(tbl_CN_aggr)


# ----------------------------------------------------------
# UNU_countries: Calculate Put On Market
# ----------------------------------------------------------
# Removing NA's.
UNU_countries[is.na(UNU_countries$PCC_kg),"PCC_kg"] <-0
UNU_countries[is.na(UNU_countries$imp_kg),"imp_kg"] <-0
UNU_countries[is.na(UNU_countries$exp_kg),"exp_kg"] <-0
UNU_countries[is.na(UNU_countries$PCC_p),"PCC_p"] <-0
UNU_countries[is.na(UNU_countries$imp_p),"imp_p"] <-0
UNU_countries[is.na(UNU_countries$exp_p),"exp_p"] <-0

# The POM calculation
UNU_countries$POM_kg <- UNU_countries$PCC_kg + UNU_countries$imp_kg - UNU_countries$exp_kg
UNU_countries$POM_pieces <- UNU_countries$PCC_p + UNU_countries$imp_p - UNU_countries$exp_p

# Delete negatives
selection <- which( UNU_countries$POM_kg > 0 & UNU_countries$POM_pieces > 0 )
UNU_countries <- UNU_countries[selection, ]


# ----------------------------------------------------------
#  UNU_countries: Clean up and save result
# ----------------------------------------------------------

# Remove all EU aggregates
selection <- ifelse(substr(UNU_countries$Country,1,2) == "EU",1,0)
UNU_countries <- UNU_countries[selection == 0, ]

# Remove variables that are not needed anymore
# for (col in list("imp_kg", "exp_kg", "imp_p", "exp_p", "PCC_kg", "PCC_p")) {
#     UNU_countries[[col]] <- NULL
# }

# Sort dataframe rows by UNU_Key, Year and Country.
sortorder <- order(UNU_countries$UNU_Key, UNU_countries$Year, UNU_countries$Country)
UNU_countries <- UNU_countries[sortorder, ]

write.csv(UNU_countries, file = "UNU_countries.csv", quote = TRUE, row.names = FALSE)

