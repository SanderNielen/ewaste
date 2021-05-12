# -----------------------------------------------------------------------------------------------------------
#
#   Name:             04_WEEE_calculations.R
#
#   Description:      This script reads the CSV file with the altered POM data.
#                     Then the WEEE arrising will be calculated using the Weibull function.
#
#
#   Authors:          dr C.P. Balde - Statistics Netherlands,
#                     H. Meeuwissen - Statistics Netherlands,  
#                     dr. F. Wang - United Nations University
#
#   Revised version:  V.M. van Straalen - Statistics Netherlands
#	Second revision:  S.S. van Nielen - Leiden University
# -----------------------------------------------------------------------------------------------------------

setwd(DATA_PATH)
options(stringsAsFactors=FALSE, warn=0, scipen=999, digits=4)

require(plyr)
require(reshape2)



# ----------------------------------------------------------
# tbl_POM: Read POM data
# ----------------------------------------------------------
tbl_POM <- read.csv("POM_Nd.csv", quote = "\"",
                    colClasses = c("character", "character", "numeric", "character", rep("numeric", 3)))


# ----------------------------------------------------------
# tbl_Weibull_parameters: Read scale and shape parameters for Weibull function
# ----------------------------------------------------------
tbl_Weibull_parameters <- read.csv("htbl_Weibull.csv", quote = "\"",
                                   colClasses = c("character", "numeric", "numeric"))

# ----------------------------------------------------------
# tbl_POM: Merge Weibull parameters with POM data
# ----------------------------------------------------------
tbl_POM <- merge(tbl_POM, tbl_Weibull_parameters,  by=c("UNU_Key"),  all.x = TRUE)


# ----------------------------------------------------------
# tbl_POM: Add variables for WEEE calculation per year
# ----------------------------------------------------------

# Create columns for all years in Weibull range
year_first <- min(as.integer(tbl_POM$Year))
year_last <- max(as.integer(tbl_POM$Year)) + 7

years <- c(year_first:year_last)
empty <- as.data.frame(matrix(NA, ncol = length(years), nrow = nrow(tbl_POM)))
colnames(empty) <- years

# Add them to tbl_POM dataset
tbl_POM <- cbind(tbl_POM, empty)
rm(empty)

  
# ----------------------------------------------------------
# tbl_POM: Perform Weibull function
# ----------------------------------------------------------

for (i in year_first:year_last){
  tbl_POM$WEEE_POM_dif <- i - ( as.integer(tbl_POM[, "Year"]) )
  wb <- dweibull(tbl_POM[(tbl_POM$WEEE_POM_dif >= 0),"WEEE_POM_dif"] + 0.5,
                  shape = tbl_POM[(tbl_POM$WEEE_POM_dif >= 0), "shape"],
                  scale = tbl_POM[(tbl_POM$WEEE_POM_dif >= 0), "scale"],
                  log = FALSE)
  weee <-  wb * tbl_POM[(tbl_POM$WEEE_POM_dif >= 0), "Nd_t"]
  tbl_POM[(tbl_POM$WEEE_POM_dif >= 0), as.character(i)] <- weee
}  
  
# Clean-up
tbl_POM$WEEE_POM_dif <- NULL
tbl_POM$scale <- NULL
tbl_POM$shape <- NULL
rm(tbl_Weibull_parameters)
rm(wb)
rm(weee)


# ----------------------------------------------------------
# tbl_POM: Summing the waste arising from all past years
# ----------------------------------------------------------

# Calculate WEEE-generated for all years as the sum of all past years per UNU_Key and Country

# First melt all years into long form. Other variables excluding the years and the classifications are removed.
mylong <- melt(tbl_POM[-(5:7)], id = c("UNU_Key", "Country", "Component", "Year"))

# Remove empty rows to reduce memory burden
# They are records for WEEE years that are earlier than the POM year.
# Therefore they are always empty and not needed.
mylong <- mylong[!is.na(mylong$value), ]
rm(tbl_POM)

mylong <- plyr::rename(mylong,c("variable"="WEEE_Year", "value"="Waste_Nd_t"))
mylong$Year <- NULL

# Then cast into wide form while calculating the sum of every group.
mywide_Nd <- dcast(mylong, UNU_Key + Country + Component ~ WEEE_Year, value.var = "Waste_Nd_t", sum, na.rm=TRUE)

# Finally melt again to long form for merge with POM dataset.
Nd_waste <- melt(mywide_Nd, id = c("UNU_Key", "Country", "Component"))
Nd_waste <- plyr::rename(Nd_waste,c("variable"="Year", "value"="Waste_Nd_t"))

# Attach population to calculate Nd gpi.
Nd_waste <- merge(Nd_waste, Population,  by=c("Country", "Year"),  all.x = TRUE)
Nd_waste$gpi <- Nd_waste$Waste_Nd_t / Nd_waste$Inhabitants * 1e6


# Sort order for columns
sortorder_c <- c("Component", "Country", "UNU_Key", "Year", "Waste_Nd_t",
                 "Inhabitants", "gpi")

# Sort dataframe rows by Country, Component, UNU_Key and Year
sortorder <- order(Nd_waste$Country, Nd_waste$Component, Nd_waste$UNU_Key, Nd_waste$Year)
Nd_waste <- Nd_waste[sortorder, sortorder_c]


# Combine with waste flow data and save into tbl_Waste.csv
Nd_waste <- merge(Nd_waste, tbl_WEEE, all.x = TRUE)
write.csv(Nd_waste, file = "tbl_Waste.csv", quote = TRUE, row.names = FALSE)


# Clean-up
rm(Nd_waste, mylong, mywide_Nd)

