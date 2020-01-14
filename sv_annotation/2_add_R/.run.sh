bed=$1
prefix=$2
out_dir=$3

annotation=/sfs-grand-med-research/home/suyanan/research/docker/sv_annotation/2_add_R

python3 ${annotation}/sv_stats/sv_stats.py --bed ${bed} --prefix ${prefix} --outdir ${out_dir} 
