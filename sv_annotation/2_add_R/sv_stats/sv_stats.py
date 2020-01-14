#!/usr/bin/env python3
"""
Auchor: yangqi <yangqi2@grandomics.com>
sv num stats and sv len stats
sv distributions on chromosomes will be added in the future
"""
#modified only five main type of SV, DEL,INS,INV,DUP,TRA
import sys
import os
import subprocess
import argparse

class sv_bed(object):
    """docstring for sv_bed"""
    def __init__(self, bed):
        self.bed = bed
        #chr, start, end, name, sv_len, support_reads_num
        fields = self.bed.strip().split()
        (self.chr, self.start, self.end, self.svtype, self.svid,
                self.sv_len, self.support_reads_num) = fields[:-1]
        self.sv_main_id = self.svid
        if self.svtype == "TRA":
            self.sv_main_id  = self.svid.split("_")[0]
            self.sv_tra_id = self.svid.split("_")[1]

def sv_nums(bedfn, outname):
    SVNUMs = {}
    tra_sv_ids = {}
    main_svtype = ["DEL","INS","INV","DUP","TRA"]
    with open(bedfn, "r") as bedfile:
        for line in bedfile:
            sv = sv_bed(line)
            if not sv.svtype in main_svtype:
                continue
            #modified, one sv_id one sv
            if sv.svtype == "TRA":
                if sv.sv_main_id not in tra_sv_ids:
                    tra_sv_ids[sv.sv_main_id] = 1
                    if sv.svtype not in SVNUMs:
                        SVNUMs[sv.svtype] = 1
                    else:
                        SVNUMs[sv.svtype] += 1
                else:
                    continue
            else:
                if sv.svtype not in SVNUMs:
                    SVNUMs[sv.svtype] = 1
                else:
                    SVNUMs[sv.svtype] += 1

    with open(outname, "w") as out:
        #header
        print("#Type\tNumber", file=out)
        for key in sorted(SVNUMs):
            print("%s\t%s" % (key, SVNUMs[key]), file=out)

def sv_lens(bedfn, outname):

    main_svtype = ["DEL","INS","INV","DUP"] # TRA LEN is not valid
    with open(bedfn, "r") as bedfile:
        out = open(outname, "w")
        for line in bedfile:
            sv = sv_bed(line)
            if not sv.svtype in main_svtype:
                continue
            if sv.sv_len == "NA" or int(sv.sv_len) < 0:
                #skip sv without a valid sv_len, eg TRA or other sv
                continue
            print("%s\t%s" % (sv.svtype, sv.sv_len), file=out)
        out.close()


def get_args():
    parser = argparse.ArgumentParser(description="Basic SV stats. "
            "Include SV lenth distribution and SV number of different SV types.",
            usage="usage: %(prog)s [options]")
    parser.add_argument("--bed", help="sv_filter.py output bed file"
            " [default: %(default)s]", metavar="FILE")
    parser.add_argument("--prefix", help="Output file prefix",metavar="STR")
    parser.add_argument("--outdir", help="Output file prefix",metavar="STR")

    if len(sys.argv) <= 1:
        parser.print_help()
        exit()
    return parser.parse_args()

def main():
    args = get_args()

    # make dir
    if not os.path.exists(args.outdir):
        os.path.mkdir(args.outdir)

    #structure variation nums
    bedfilename = args.bed
    outname_svnum = os.path.join(args.outdir, args.prefix+".svnum")
    sv_nums(bedfilename, outname_svnum)
    #plot, make sure sv_num_plot.R are in the same folder
    svnum_Rplot = os.path.join(os.path.dirname(os.path.abspath(__file__)),
            "sv_num_plot.R")
    subprocess.run(["Rscript", svnum_Rplot, outname_svnum, outname_svnum+".pdf",
        outname_svnum+".png"],stdout=None,stderr=None)

    outname_svlen = os.path.join(args.outdir, args.prefix+".svlen")
    sv_lens(bedfilename, outname_svlen)
    #plot, make sure sv_len_plot.R are in the same folder
    svlen_Rplot = os.path.join(os.path.dirname(os.path.abspath(__file__)),
            "sv_len_plot.R")
    subprocess.run(["Rscript",svlen_Rplot, outname_svlen, outname_svlen+".pdf",
        outname_svlen+".png"],stdout=None,stderr=None)

if __name__ == '__main__':
    main()

