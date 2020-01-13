# ----------------------------------------------------------
#  UNU_countries: Add data for some product groups to use instead of the statistics
# ----------------------------------------------------------

# At Eurostat there is data available about the Net maximum capacity of Solar Photovoltaic in Megawatt.
# It can be found on the Eurostat website http://ec.europa.eu/eurostat/data/database
# Search for [nrg_113a]
# Or look in the navigation tree under:
# Environment and energy -> Energy (nrg) -> Energy statistics - Infrastructure (nrg_11) ->
# Infrastructure - electricity - annual data [nrg_113a]
# Look for the indicator "Net maximum capacity - Solar Photovoltaic".

# The file that is going to be read after this is already restructured in Excel and multiplied with factors
# for number of panels and kg per megawatt.

# Data for wind turbines, MRIs, cars and bikes were obtained and processed analogously


EXT_PATH <- "C:\\Users\\nielenssvan\\surfdrive\\MFA\\data\\"

# ----------------------------------------------------------
# Additional data: Read and prepare tables
# ----------------------------------------------------------

# Read additional product data from CSVs and add UNU_Keys
cols <- c("Year", "Country", "Sales")
mri <- fread(paste(EXT_PATH,"MRI\\MRI-MFA.csv", sep=""), sel=cols)
mri$UNU_Key <- "0802b"
cars <- fread(paste(EXT_PATH,"Vehicles\\All-Cars.csv", sep=""))
bikes <- fread(paste(EXT_PATH,"E-bikes\\All-Bikes-EU.csv", sep=""), sel=cols)
bikes$UNU_Key <- "1108"
wind <- fread(paste(EXT_PATH,"Wind\\Wind-Sales.csv", sep=""), sel=c(cols, "Type"))
wind[which(wind$Type == "Onshore" ), "UNU_Key"] <- "1205a"
wind[which(wind$Type == "Offshore"), "UNU_Key"] <- "1205b"
wind$Type <- NULL
# Combine extra product sales data in POM table
new <- rbind(mri, cars, bikes, wind)
new <- rename(new, c("Sales"= "units"))

# Read product weight data
weight <- read.csv("htbl_Key_Weight.csv")
weight_cou <- weight[which(weight$Country != ""), ]
weight <- weight[-which(weight$Country != ""), ]
weight$Country <- NULL
weight_yr <- weight[which(weight$Year != ""), ]
weight <- weight[-which(weight$Year != ""), ]
weight$Year <- NULL
# Three times the same: merge and select available weights. For-loop to difficult for R.
new <- merge(new, weight)
new[which( !is.na(new$AverageWeight)), Weight] <- new[which( !is.na(new$AverageWeight)), AverageWeight]
new$AverageWeight <- NULL
new <- merge(new, weight_yr)
new[which( !is.na(new$AverageWeight)), Weight] <- new[which( !is.na(new$AverageWeight)), AverageWeight]
new$AverageWeight <- NULL
new <- merge(new, weight_cou)
new[which( !is.na(new$AverageWeight)), Weight] <- new[which( !is.na(new$AverageWeight)), AverageWeight]
new$AverageWeight <- NULL
# Create additional column for total weight: kg
new$kg <- new$Weight * new$units

# PVpanels: Read raw version of POM data
PVpanels <- read.csv("solar_panel_data.csv", quote = "\"",
                     colClasses = c(rep("character", 3), "numeric", "numeric"))

new <- rbind(new, PVpanels)

# ----------------------------------------------------------
# Add all loaded tables to UNU_countries
# ----------------------------------------------------------
# Remove existing entries if present
new_keys <- unique(new$UNU_Key)
UNU_countries <- UNU_countries[-UNU_countries$UNU_Key %in% new_keys, ]

# merge with UNU_countries
UNU_countries <- merge(UNU_countries, new,  by=c("UNU_Key", "Year", "Country"),  all.x = TRUE)

# Take over data
selection <- UNU_countries$UNU_Key %in% new_keys
UNU_countries[selection, "kpi"] <- UNU_countries[selection, "kg"] / UNU_countries[selection, "Inhabitants"]
UNU_countries[selection, "ppi"] <- UNU_countries[selection, "units"] / UNU_countries[selection, "Inhabitants"]
UNU_countries[selection, "flag"] <- 53


# clean-up
UNU_countries$kg <- NULL
UNU_countries$units <- NULL

rm (cols, mri, cars, bikes, wind, PVpanels, weight, weight_yr, weight_cou, new, selection)

