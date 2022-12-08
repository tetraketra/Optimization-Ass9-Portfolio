# SETUP # ------------------------------------------------------------------------------
rm(list=ls())
if(!require(RMySQL))    {install.packages("RMySQL");    library(RMySQL)}
if(!require(reshape2))  {install.packages("reshape2");  library(reshape2)}
data <- read.csv("M6-NasdaqReturns.csv")


# CREATE DATA # ------------------------------------------------------------------------
#Only returns
data_n <- data.matrix(data[,-c(1:3)])
rownames(data_n) <- data$StockSymbol

#Transpose
n_data_t <- t(data_n)
str(n_data_t)
small <- n_data_t[1:5,1:5] #structure looks good

#Correlation
cor(n_data_t[1:5,1:5])

#Covariance
cov <- cor(n_data_t)
cov

#Mean Returns
r <- colMeans(cov)
r

#Inspection
melt(small)
melt(cov)
colMeans(cov)



# INSERT INTO MySQL # ------------------------------------------------------------------
#Connect to MySQL
pwd <- .rs.askForPassword("DB Password:")
db <- RMySQL::dbConnect(RMySQL::MySQL(),dbname='nasdaq', username='root', password=pwd)

#Metadata
dbListTables(db)
dbReadTable(db,'cov')
dbReadTable(db,'r')

#Insert Setup
dbSendQuery(db, "SET GLOBAL local_infile = true;")

#Insert COV(ariance matrix, melted)
melt_cov <- melt(cov)
names(melt_cov) <- c("stock1", "stock2", "covariance")
dbWriteTable(db, name = 'cov', value = melt_cov, row.names = F, append = F, overwrite = T)

#Insert R(eturns, melted)
melt_r <- melt(r)
melt_r <- cbind(rownames(melt_r), data.frame(melt_r, row.names=NULL))
melt_r$`rownames(melt_r)` <- as.factor(melt_r$`rownames(melt_r)`)
names(melt_r) <- c("stock", "meanReturn")
dbWriteTable(db, name = 'r', value = melt_r, row.names = F, append = F, overwrite = T)
