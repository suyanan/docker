library(ggplot2, quietly = TRUE)
library(dplyr, quietly = TRUE)
args = commandArgs(trailingOnly = TRUE)

sv_len = read.csv(args[1], sep="\t", header=FALSE)
sv_len = filter(sv_len,V2<=1000000)

#alu peak
h = 300

p <- ggplot(sv_len, aes(V2, fill = V1))+
#  geom_jitter(width=.25)+
  geom_density(alpha=0.65)+
  xlab("SV Length(bp)")+
  scale_x_continuous(breaks = c(100,1000,10000,100000,1000000),
                     labels = c("0.1k","1k","10k","100k","1M"),trans = "log10")+
  ylab("Density")+
  theme_bw()+
  theme(legend.justification=c(.9,.9),legend.position=c(.9,.9))+
  theme(text = element_text(size = 20),legend.text=element_text(size=rel(0.6)))+
  # ggtitle(paste("SV Length Density Plot(",args[2],")"))+ # remove title
  # theme(plot.title = element_text(hjust = 0.5))+
  scale_fill_brewer(palette="Accent",name="")

p <- p + geom_vline(xintercept=300, colour="#C0C0C0", linetype="dashed")+
 annotate("text", x = 300, y = Inf, label = "300bp Alu Peak", vjust=2)

#args[2] output name for svg
pdf(args[2], width = 8, height = 6)
p
s <- dev.off() # s is used to collect output of dev.off
#args[3] output name for png
png(args[3], width = 2400, height = 1800, res=300)
p
s <- dev.off() # s is used to collect output of dev.off
