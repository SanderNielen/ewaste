# ----------------------------------------------------------
#  UNU_countries: Add data for some product groups to use instead of the statistics
# ----------------------------------------------------------

# Data for wind turbines, MRIs, cars, bikes and catalysts were obtained and processed 
# analogous with the 03h script for PV panels.

require(data.table)
EXT_PATH <- "C:\\Users\\nielenssvan\\surfdrive\\MFA\\data\\"

# ----------------------------------------------------------
# Additional data: Read and prepare tables
# ----------------------------------------------------------

# Read additional product data from CSVs and add UNU_Keys
cols <- c("Year", "Country", "Sales")
mri <- fread(paste(EXT_PATH,"MRI\\MRI-MFA.csv", sep=""), sel=cols)
mri$UNU_Key <- "0802b"
cars <- fread(paste(EXT_PATH,"Vehicles\\All-Cars.csv", sep=""))
cars <- cars[cars$UNU_Key != "1102", ]
bikes <- fread(paste(EXT_PATH,"E-bikes\\All-Bikes-EU.csv", sep=""), sel=cols)
bikes$UNU_Key <- "1108"
wind <- fread(paste(EXT_PATH,"Wind\\Wind-Sales.csv", sep=""), sel=c(cols, "Type"))
wind[which(wind$Type == "Onshore" ), "UNU_Key"] <- "1205a"
wind[which(wind$Type == "Offshore"), "UNU_Key"] <- "1205b"
wind$Sales <- wind$Sales * 1000 # MW to kW
wind$Type <- NULL
fcc <- read.csv(paste(EXT_PATH, "EuroStat\\FCC-demand.csv", sep=""))
fcc$UNU_Key <- "1301"
# Combine extra product sales data in POM table
new <- rbind(mri, cars, bikes, wind, fcc)
new <- rename(new, c("Sales"= "units"))

# Read product weight data
weight <- read.csv("htbl_Key_Weight.csv")
weight$Year <- as.integer(weight$Year)
weight_cou <- weight[which(weight$Country != ""), ]
weight <- weight[-which(weight$Country != ""), ]
weight$Country <- NULL
weight_yr <- weight[which(weight$Year != ""), ]
weight <- weight[-which(weight$Year != ""), ]
weight$Year <- NULL
# Three times the same: merge and select available weights. For-loop to difficult for R.
new$Weight <- as.numeric(NA)
new <- merge(new, weight, all.x = TRUE)
new[which( !is.na(new$AverageWeight)), "Weight"] <- new[which( !is.na(new$AverageWeight)), "AverageWeight"]
new$AverageWeight <- NULL
new <- merge(new, weight_yr, by=c("UNU_Key", "Year"), all.x = TRUE)
new[which( !is.na(new$AverageWeight)), "Weight"] <- new[which( !is.na(new$AverageWeight)), "AverageWeight"]
new$AverageWeight <- NULL
new <- merge(new, weight_cou, by=c("UNU_Key", "Year", "Country"), all.x = TRUE)
new[which( !is.na(new$AverageWeight)), "Weight"] <- new[which( !is.na(new$AverageWeight)), "AverageWeight"]
new$AverageWeight <- NULL
# Create additional column for total weight: kg
new$kg <- new$Weight * new$units
new$Weight <- NULL

# Attach number of inhabitants for each country
new <- merge(new, Population,  by=c("Country", "Year"),  all.x = TRUE)
new <- merge(new, Stratum,  by="Country",  all.x = TRUE)
rm(Stratum)  # Population is needed in 05 for the estimation of past and future values

# ----------------------------------------------------------
# Add all loaded tables to UNU_countries
# ----------------------------------------------------------
# Remove existing entries if present
new_keys <- unique(new$UNU_Key)
UNU_countries <- UNU_countries[!(UNU_countries$UNU_Key %in% new_keys), ]

# merge with UNU_countries
UNU_countries <- merge(UNU_countries, new, all = TRUE)

# Take over data
selection <- UNU_countries$UNU_Key %in% new_keys
UNU_countries[selection, "kpi"] <- UNU_countries[selection, "kg"] / UNU_countries[selection, "Inhabitants"]
UNU_countries[selection, "ppi"] <- UNU_countries[selection, "units"] / UNU_countries[selection, "Inhabitants"]
UNU_countries[selection, "flag"] <- 53


# clean-up
UNU_countries$kg <- NULL
UNU_countries$units <- NULL

rm (cols, mri, cars, bikes, wind, weight, weight_yr, weight_cou, new, selection)

