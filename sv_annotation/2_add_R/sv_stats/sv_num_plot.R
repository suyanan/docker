library(ggplot2, quietly = TRUE)

args = commandArgs(trailingOnly = TRUE)

sv_num = read.csv(args[1], sep="\t", comment.char = "#", header = FALSE)
sv_num = sv_num[order(sv_num$V2, decreasing = TRUE), ]
sv_num$V1 = factor(sv_num$V1, levels = sv_num$V1)

p <- ggplot(sv_num, aes(V1, V2, fill = V1))+
  geom_bar(stat = "identity", color = "black", size = 0.5, width = 0.5)+
  xlab("SV Type")+
  ylab("Number")+
  theme_bw()+
  theme(legend.position = "none")+
  theme(text = element_text(size = 20))+
  scale_fill_brewer(palette="Accent",name="")

#args[2] output name for pdf
pdf(args[2], width = 8, height = 6)
p
s <- dev.off() # s is used to collect output of dev.off()
#args[3] output name for png
png(args[3], width = 2400, height = 1800, res = 300)
p
s <- dev.off() # s is used to collect output of dev.off()

