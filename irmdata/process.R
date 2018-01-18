# This script converts .mat files to csvs.
MATFILES <- c(
  '50animalbindat.mat',
  # 'alyawarradata.mat',  # Definitely a subset of this that is clusterable, skip for now 'dnations.mat'  # Use the 2D matrix only, i.e. mat$A
  # 'uml.mat'  # UML involves a ternary relation. Doesn't seem like CrossCat can handle those.
)
PWD <- '~/Git/2015_a_dr/Data/irmdata'
setwd(PWD)

# Libraries ====
library(R.matlab)

# 50animalbindat ====
mat <- readMat('50animalbindat.mat')
data.50 <- as.data.frame(mat$data)
# The biggest mess ever to get the standard feature names
features <- sapply(mat$features, FUN = function(el) el[1][[1]][[1]][1])
names <- sapply(mat$names, FUN = function(el) el[1][[1]][[1]][1])

numpy.savetxt(names)
write.table(t(names), file = '../parsed/50animalbindat-members.txt',
            row.names = FALSE, col.names = FALSE, sep = ',', quote = FALSE)
write.table(t(features), file = '../parsed/50animalbindat-columns.txt',
            row.names = FALSE, col.names = FALSE, sep = ',', quote = FALSE)

rownames(data.50) <- names
colnames(data.50) <- features

write.csv(data.50, file = '../parsed/50animalbindat.csv', quote = FALSE)

# dnations ====
mat <- readMat('dnations.mat')
data.dn <- as.data.frame(mat$A)
countrynames <- sapply(mat$countrynames, FUN = function(el) el[1][[1]][[1]][1])
attnames <- sapply(mat$attnames, FUN = function(el) el[1][[1]][[1]][1])

rownames(data.dn) <- countrynames
colnames(data.dn) <- attnames

write.csv(data.dn, file = '../parsed/dnations.csv', quote = FALSE, na='')