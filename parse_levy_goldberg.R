# This extracts any large dataset WITHOUT a header row, space separated, with verbs
# as the first column and real numbers as the other columns.
# For now, I'm using it only with Levy & Goldberg's dependency-based word embeddings
# https://levyomer.wordpress.com/2014/04/25/dependency-based-word-embeddings/

library(data.table)
cat("Warning: make sure the file for the uncompressed deps.words is available!\n")
cat("(the file is gitignored)\n")

LG = "../BigData/deps.words"

cat("Reading data\n")
words = fread(LG)
colnames(words) = c("member", paste("V", 1:(length(colnames(words)) - 1), sep = ""))
setkey(words, member)

cat("Reading list of verbs\n")
verbs = scan(file = "./parsed/members.txt", what = character(), sep = ',')
# Remove vnclass, remove duplicates
verbs = unique(tstrsplit(verbs, '#')[[1]])

cat("Extracting and writing\n")
vs = words[verbs, ]
# Omit NAs
vs = na.omit(vs)
write.table(vs, file = './parsed/levy_goldberg_words.csv', sep = ',', row.names = FALSE,
            quote = FALSE)
