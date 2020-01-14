"""
SV query from dbSV constructed by ES
Author: suyanan1991@163.com on 11.07, 2019
update:
1.sample index to get sample_num
2.non 5 svtypes process
需求：
DUP类型（标准5类SV）会检索出本地DUP、DUP/INS；（模糊匹配）
DUP/INS会检索出本地DUP/INS、DUP和INS。其他类型：DEL/INV、DUP/INS、INVDUP、INV/INVDUP（匹配多个精确值）
3.Elasticsearch(es_address) -> client just once request
"""

from elasticsearch6 import Elasticsearch # hail 配合的是 elasticsearch6
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch.helpers import bulk

import configparser,sys,os,json,argparse
import time

def get_args():
    parser = argparse.ArgumentParser(description="query SV from ES-dbSV.", usage="usage: %(prog)s [options]")
    parser.add_argument("--input", help="bed(or annotation) file [default: %(default)s]", metavar="FILE")

    parser.add_argument("--outdir",help="output directory [default %(default)s]", metavar="DIR")

    if len(sys.argv) <= 1:
        parser.print_help()
        exit()
    return parser.parse_args()


def get_sample_data(client,es_index,es_doc_type,SIZE):
    """
    function:get sample index's related data (样本个数和列表、健康人样本个数和列表)
    """
    #总样本个数
    response = client.search(
        index = es_index, 
        doc_type = es_doc_type, 
        body = {   
            "_source": "sample_id",
            "size": SIZE
        }    
    )   
    sample_count = response['hits']['total']
    res = response['hits']['hits']
    samples = [i['_source']['sample_id'] for i in res]   # real-time healthy_sample_list

    #健康样本个数
    response = client.search(
        index = es_index,
        doc_type = es_doc_type,
        body = {
            "query": {
                "constant_score": {
                "filter": {
                    "terms" :{
                    "phenotype" : ["healthy"]  # label list in {healthy, genetic, carcinoma, paracarcinoma}
                }
                }
            }
            },
            "_source": "sample_id",
            "size": SIZE
        }
    ) 
    healthy_sample_count = response['hits']['total']
    res = response['hits']['hits']
    healthy_samples = [i['_source']['sample_id'] for i in res]   # real-time healthy_sample_list

    return sample_count,samples,healthy_sample_count,healthy_samples


def query_sv(client,es_index,es_doc_type,
    MIN_RE,BREAKPOINT,SIZE,
    target_chrom,target_chr2,target_svtype,target_start,target_end):
    """
    function:1st search from ES , just based on breakpoint
    get all results which can breakpoint at start and end for target_sv
    【模糊匹配】用*svtype*匹配，碰到INS类型（标准5类SV）会检索出本地INS、DUP/INS，但是，碰到DUP/INS会检索出本地DUP/INS且不会查出DUP和INS。
    """
    response = client.search(
        index = es_index, 
        doc_type = es_doc_type, 
        body = {
          "query": {
            "bool": {              
              "must": [
                {
                  "match": {
                    "locus.contig": {
                      "query": target_chrom,
                      "type": "phrase"
                    }
                  }
                }, 
                {
                  "match": {
                    "info.CHR2": {
                      "query": target_chr2,
                      "type": "phrase"
                    }
                  }
                },            
                #{
                #  "match": {
                #    "info.SVTYPE.keyword": {
                #      "query": target_svtype,
                #      "type": "phrase"
                #    }
                #  }
                #},
                {
                  "wildcard": {
                    "info.SVTYPE.keyword": "*%s*" % target_svtype
                  }
                },                
                {
                  "range": {
                    "info.RE": {
                      "gte": MIN_RE
                    }
                  }
                },                
                {
                  "range": {
                    "locus.position": {
                      "gte": target_start-BREAKPOINT,
                      "lte": target_start+BREAKPOINT
                    }
                  }
                },
                {
                  "range": {
                    "info.END": {
                      "gte": target_end-BREAKPOINT,
                      "lte": target_end+BREAKPOINT
                    }
                  }
                }
              ]
            }
          },
          "size": SIZE
        }
    )

    """
    ##SIZE=2 for test
    {
        'took': 31, 
        'timed_out': False, 
        '_shards': {'total': 24, 'successful': 24, 'failed': 0}, 
        'hits': {
            'total': 67, 
            'max_score': 5.7038016, 
            'hits': [
                {
                    '_index': 'mysv', 
                    '_type': 'sv', 
                    '_id': 'AWx-mCJFktKGFwRzadNk', 
                    '_score': 5.7038016, 
                    '_source': {
                        'locus': {'contig': 'X', 'position': 155017581}, 
                        'alleles': ['N', '<DEL>'], 
                        'rsid': '1294014', 
                        'qual': -10.0, 
                        'filters': [], 
                        'info': {
                            'CHR2': 'X', 'END': 155017633, 'RE': 2, 
                            'IMPRECISE': True, 'PRECISE': False, 
                            'SVLEN': 52, 
                            'SVMETHOD': 'Snifflesv1.0.8', 'SVTYPE': 'DEL', 
                            'RNAMES': '0a7adfd6-bb27-41a4-854b-facb6e39539e,c1fb6fe2-2a23-45ff-bf11-582d3394bf28', 
                            'STD_quant_start': [98.501269], 'STD_quant_stop': [98.501269], 'Kurtosis_quant_start': [-1.999897], 'Kurtosis_quant_stop': [-1.999897], 'SUPTYPE': 'AL', 'STRANDS': ['+-'], 
                            'AF': [0.666667]
                        }, 
                        'GT': {'alleles': [0, 1], 'phased': False}, 
                        'DR': 1, 
                        'DV': 2, 
                        'sample': 'DM19A0209-1'
                    }
                }, 
                {
                    '_index': 'mysv', '_type': 'sv', '_id': 'AW0rHtxvW0oo8Iwrkqco', 
                    '_score': 5.7038016, 
                    '_source': {'locus': {'contig': 'X', 'position': 155017127}, 'alleles': ['N', '<DEL>'], 'rsid': '766698', 'qual': -10.0, 'filters': [], 'info': {'CHR2': 'X', 'END': 155017281, 'RE': 2, 'IMPRECISE': True, 'PRECISE': False, 'SVLEN': 154, 'SVMETHOD': 'Snifflesv1.0.8', 'SVTYPE': 'DEL', 'RNAMES': '8b0344fb-82f5-4237-822a-261453364dfb,d825336d-ac6c-4caf-ba4f-1813e7985946', 'STD_quant_start': [122.50102], 'STD_quant_stop': [102.50122], 'Kurtosis_quant_start': [-1.999933], 'Kurtosis_quant_stop': [-1.999905], 'SUPTYPE': 'AL', 'STRANDS': ['+-'], 'AF': [1.0]}, 'GT': {'alleles': [1, 1], 'phased': False}, 'DR': 0, 'DV': 2, 'sample': 'DM19A0805-1', 'timestamp': 1568385518983}
                }
             ]
                
        }
    }
    """
    hits_total_num = response["hits"]["total"] #hits num on all dbSV
    hit_sv_record_list = response["hits"]["hits"]
    return hits_total_num,hit_sv_record_list

def query_sv_nonStandardSVtype(client,es_index,es_doc_type,
    MIN_RE,BREAKPOINT,SIZE,
    target_chrom,target_chr2,target_svtype,target_start,target_end,
    target_svtype_search_region):
    """
    【匹配多个精确值】用terms匹配，碰到DUP/INS会检索出本地DUP/INS、DUP和INS，但是，碰到DUP类型（标准5类SV）会检索出本地DUP且不会查出DUP/INS。
    nonStandardSVtype = ["DEL/INV", "DUP/INS", "INVDUP", "INV/INVDUP"]
    """
    response = client.search(
        index = es_index, 
        doc_type = es_doc_type, 
        body = {
          "query": {
            "bool": {              
              "must": [
                {
                  "match": {
                    "locus.contig": {
                      "query": target_chrom,
                      "type": "phrase"
                    }
                  }
                }, 
                {
                  "match": {
                    "info.CHR2": {
                      "query": target_chr2,
                      "type": "phrase"
                    }
                  }
                },
                #{
                #  "match": {
                #    "info.SVTYPE.keyword": {
                #      "query": target_svtype,
                #      "type": "phrase"
                #    }
                #  }
                #},
                # {
                  # "terms": {
                    # "info.SVTYPE.keyword": target_svtype_search_region                   
                  # }
                # },
                {
                  "range": {
                    "info.RE": {
                      "gte": MIN_RE
                    }
                  }
                },
                {
                  "range": {
                    "locus.position": {
                      "gte": target_start-BREAKPOINT,
                      "lte": target_start+BREAKPOINT
                    }
                  }
                },
                {
                  "range": {
                    "info.END": {
                      "gte": target_end-BREAKPOINT,
                      "lte": target_end+BREAKPOINT
                    }
                  }
                }
              ],
              "filter": {
                "terms": {
                  "info.SVTYPE.keyword": target_svtype_search_region
                }
              }              
            }
          },
          "size": SIZE
        }
    )

    hits_total_num = response["hits"]["total"] #hits num on all dbSV
    hit_sv_record_list = response["hits"]["hits"]
    return hits_total_num,hit_sv_record_list

def filter_sv(hit_sv_record_list,SVTYPE_REGION_LIST,OVERLAP,
    target_start,target_end,target_svlen):
    """
    2nd filter : filter es query results
    SVTYPE_REGION_LIST by overlap, INS ok, TRA with two chroms to compare        
    """
    filter_num = 0
    filter_sample_tmp_list = [] #去重处理：一个样本中不会出现两个SV都算在计数内    
    filter_sample_list = []
    for sv_record in hit_sv_record_list:
        source = sv_record["_source"] #sv_record and source ,both dict type
        #print(source)
        #only chrom and start , based on two cols
        svid = source["rsid"] #str
        contig = source["locus"]["contig"]
        position = source["locus"]["position"]
        
        #based on info
        info = source["info"]
        chr2 = info["CHR2"]
        end = info["END"]
        re = info["RE"]
        svlen = abs(info["SVLEN"]) #some svlen in es was negative
        svtype = info["SVTYPE"]
        rnames = info["RNAMES"]
        af = info["AF"]
        
        genotype = "/".join([str(i) for i in source["GT"]["alleles"]])
        sample = source["sample"]        
        
        if svtype in SVTYPE_REGION_LIST:
            #filter logic：overlap > max(len(targetsv),len(sourcesv))*50%
            #default: no certain whether position > end (except TRA) in source sv
            overlap_between_targetsv_and_sourcesv = min(max(position,end),target_end)-max(min(position,end),target_start) #目标sv和库里sv比较overlap的定义：两个右端点的最小值与两个左端点的最大值，做差
            #overlap_between_targetsv_and_sourcesv = min(end,target_end)-max(position,target_start) #certain : position > end (except TRA) in source sv 
            if overlap_between_targetsv_and_sourcesv >= max(svlen,target_svlen)*OVERLAP:                
                #print("\t".join([contig,str(position),str(end),chr2,svtype,str(svlen),sample]))
                if sample not in filter_sample_tmp_list:
                    filter_num += 1
                    filter_sample_tmp_list.append(sample)
                    filter_sample_list.append(sample+":"+svid)
                #else:
                    #print(sample)
                    #print("one sample has more than one SV, just count one.")            
        else:#INS/TRA
            if sample not in filter_sample_tmp_list:
                filter_num += 1
                filter_sample_tmp_list.append(sample)
                filter_sample_list.append(sample+":"+svid)
           
    return filter_num,filter_sample_list
    
    

def get_sv_freq(client,es_index,es_doc_type,MIN_RE,BREAKPOINT,OVERLAP,SVTYPE_REGION_LIST,SIZE,target_chrom,target_chr2,target_svtype,target_start,target_end,target_svlen, nonStandardSVtype_list):
    if target_svtype in ["INS","TRA","INV","DEL","DUP"]:    
        #1st: hits_total_num:ES查询后的样本个数（只包含breakpoint过滤）
        hits_total_num,hit_sv_record_list = query_sv(client,es_index,es_doc_type,MIN_RE,BREAKPOINT,SIZE,target_chrom,target_chr2,target_svtype,target_start,target_end)    
        #2nd: filter_num:FILTER过滤后的样本个数（基于es查询结果，进一步overlap过滤）
        filter_num,filter_sample_list = filter_sv(hit_sv_record_list,SVTYPE_REGION_LIST,OVERLAP,target_start,target_end,target_svlen)
    elif target_svtype in nonStandardSVtype_list:
        """#target_svtype_search_region is diff:
        DEL/INV:["DEL/INV","DEL","INV"]
        DUP/INS:["DUP/INS","DUP","INS"]
        INVDUP:["INVDUP","INV","DUP"]
        INV/INVDUP:["INV/INVDUP","INV","INVDUP","DUP"]"""        
        target_svtype_search_region = []#inital        
        if target_svtype == "DEL/INV":
            target_svtype_search_region = ["DEL/INV","DEL","INV"]
        if target_svtype == "DUP/INS":
            target_svtype_search_region = ["DUP/INS","DUP","INS"]
        if target_svtype == "INVDUP":
            target_svtype_search_region = ["INVDUP","INV","DUP"]
        if target_svtype == "INV/INVDUP":
            target_svtype_search_region = ["INV/INVDUP","INV","INVDUP","DUP"]
        hits_total_num,hit_sv_record_list = query_sv_nonStandardSVtype(client,es_index,es_doc_type,MIN_RE,BREAKPOINT,SIZE,target_chrom,target_chr2,target_svtype,target_start,target_end,target_svtype_search_region)    
        filter_num,filter_sample_list = filter_sv(hit_sv_record_list,SVTYPE_REGION_LIST,OVERLAP,target_start,target_end,target_svlen)
    else:
        print("this sv's svtype is not INS,TRA,INV,DEL,DUP or DEL/INV,DUP/INS,INVDUP,INV/INVDUP.")
    return filter_num,filter_sample_list

    
def get_batch_svs(bed,query_dict):
    """
    #SV paras
    target_chr2 = "" #init
    target_svlen = 0 #init,INS/TRA is no use
    
    #default:target_start<target_end (except TRA)
    target_chrom = "X"
    target_start = 155017090
    target_end = 155017163
    target_svtype = "DEL"  
    target_svlen = 72 #used on 2nd filter based on overlap
        
    #[('1', 66174, 66423, 248, 'INS')]    
    target_chrom = "1"
    target_start = 66075
    target_end = target_start+1
    target_svtype = "INS"    
    
    #[('1', 202594234, '15', 30465037, 2135170521, 'TRA')]
    target_chrom = "1"
    target_start = 202594834
    target_chr2 = "15" #sniffles的vcf结果里面，chrom<chr2
    target_end = 30465437
    target_svtype = "TRA" 
    
    #target_chr2:default is target_chrom, otherwise supply it for TRA
    #target_svlen:for INS/TRA, svlen is no use.
    if target_svtype in ["INS","DEL","DUP","INV"]:
        target_chr2 = target_chrom
    """
    with open(bed,"r") as bed_io:
        query_sv_list = bed_io.readlines()
        target_svs_list = []  #all svs, each element is dict(include chrom/start/end/chr2/svtype/svlen)
        for query_sv in query_sv_list:
            query_sv = query_sv.strip().split("\t")
            target_sv_dict = {}                       
            
            target_sv_dict["target_chrom"] = query_sv[int(query_dict['chrom_col'])]
            target_sv_dict["target_start"] = int(query_sv[int(query_dict['start_col'])])
                        
            target_sv_dict["target_svid"] = query_sv[int(query_dict['svid_col'])]
            
            #target_info,may used later
            target_sv_dict["target_info"] = query_sv[int(query_dict['info_col'])].split(";") #target_info_list            
            target_info_dict = {}
            for i in target_sv_dict["target_info"]:
                if "=" in i:
                    info_id,info_value = i.split("=")
                    target_info_dict[info_id] = info_value
                else:
                    target_info_dict[i] = i            

            target_sv_dict["target_end"] = int(target_info_dict['END'])            
            target_sv_dict["target_svtype"] = target_info_dict['SVTYPE']
            target_sv_dict["target_svlen"] = abs(int(target_info_dict['SVLEN'])) #some DEL is negetive,target_svlen = 0 #init,TRA is no use, INS has svlen
            
            #target_chr2:default is target_chrom, otherwise supply it for TRA
            #target_svlen:for INS/TRA, svlen is no use.
            target_chr2 = "" #init 
            if target_sv_dict["target_svtype"] == "TRA":
                target_sv_dict["target_chr2"] = target_info_dict["CHR2"]                
            else:
                target_sv_dict["target_chr2"] = target_sv_dict["target_chrom"]
            target_sv_dict.pop("target_info") #induce memory delivery
            target_svs_list.append(target_sv_dict) #[{'target_chrom': 'Y', 'target_start': 10043942, 'target_end': 10043943, 'target_svtype': 'TRA', 'target_svlen': 0, 'target_chr2': 'Y'},{},,,...
        return target_svs_list

    
def main():
    a_time = time.time()
    
    args = get_args()    
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"config.ini")    
    #config_file = "/sfs-grand-med-research/home/suyanan/scripts/SV/dbSV/dbsv-es-demos/config.ini"
    
    #input_file = os.path.join("/sfs-grand-med-research/home/suyanan/research/elasticsearch/demo_data","DBM19A3676-1.af_0.3.minre_0.3.maxre_2.0.filter.bed") #19578SV(814)
    #input_file = os.path.join("/sfs-grand-med-research/home/suyanan/research/elasticsearch/demo_data","demo.bed")
    #input_file = os.path.join("/sfs-grand-med-research/home/suyanan/research/elasticsearch/demo_data","demo.tra.bed")
    #input_file = os.path.join("/sfs-grand-med-research/home/suyanan/research/elasticsearch/demo_data","DBM19A3676-1.re2.filter.bed")     #40746SV（7138TRA）
    input_file = args.input
        
    ##config paras
    config = configparser.ConfigParser()
    config.read(config_file)
    
    #es info
    es = config['es'] 
    es_address = es['address']
    client = Elasticsearch(es_address)
    
    #index mysv
    es_mysv = config['es-mysv']
    es_mysv_index = es_mysv['index']
    es_mysv_doc_type = es_mysv['doc_type']
    MYSV_SIZE = int(es_mysv["SIZE"])
    #index mysample
    es_sample = config['es-sample']
    es_sample_index = es_sample['index']
    es_sample_doc_type = es_sample['doc_type']
    SAMPLE_SIZE = es_sample['SIZE']
    
    #constant vars
    filter = config['filter']
    MIN_RE = int(filter['MIN_RE'])
    BREAKPOINT = int(filter['BREAKPOINT'])
    OVERLAP = float(filter['OVERLAP'])
    SVTYPE_REGION_LIST = filter['SVTYPE_REGION_LIST']
    nonStandardSVtype_list = filter['nonStandardSVtype']
    
    
    #bed culomn of query svs
    query_dict = config['query'] #chrom_col,start_col,info_col            
    
    ##dbSV样本个数和健康人样本个数的查询，一次性的
    sample_num,samples_list,healthy_db_num,healthy_db_list = get_sample_data(client,es_sample_index,es_sample_doc_type,SAMPLE_SIZE)
    print("there are {} samples in dbsv, including {} healthy samples.".format(sample_num,healthy_db_num))
    
    ##SV batch query from ES dbSV    
    target_svs_list = get_batch_svs(input_file,query_dict) 
    #stat_file = os.path.splitext(input_file)[0]+".dbsv.txt"
    stat_file = os.path.join(args.outdir,os.path.basename(input_file).strip("bed")+"dbsv.txt")
    with open(stat_file,"w") as out_io:
        out_list = []
        for target_sv in target_svs_list:
            starter = time.time()
            target_chrom = target_sv["target_chrom"]        
            target_start = target_sv["target_start"]
            target_svid = target_sv["target_svid"]
            
            target_end = target_sv["target_end"]
            target_svtype = target_sv["target_svtype"] #5svs and nonStandardSVtype_list
            target_svlen = target_sv["target_svlen"]
            target_chr2 = target_sv["target_chr2"]
            
            ##1st query and 2nd filter, filter_sample_list is sample:svid
            filter_num,filter_sample_list = get_sv_freq(client,es_mysv_index,es_mysv_doc_type,MIN_RE,BREAKPOINT,OVERLAP,SVTYPE_REGION_LIST,MYSV_SIZE,target_chrom,target_chr2,target_svtype,target_start,target_end,target_svlen, nonStandardSVtype_list)
            
            ##频率：基于dbSV所有样本
            dbsv_freq = filter_num/sample_num
            #print("THE dbsv_freq is {}".format(dbsv_freq))
            #print(filter_sample_list)
            #print(len(filter_sample_list))
            
            ##频率：基于dbSV中正常人样本 
            healthy_sample_list = []  
            healthy_num = 0
            for sample in filter_sample_list:
                #if sample in healthy_db_list:
                if sample.split(":")[0] in healthy_db_list:
                    healthy_num += 1
                    healthy_sample_list.append(sample) #get healthy samples from filter_sample_list           
            dbsv_healthy_freq = healthy_num/healthy_db_num
            #print("The dbsv_healthy_freq is {}".format(dbsv_healthy_freq))
            ender = time.time()    
            timer = ender-starter
            #print(healthy_sample_list)  
            #print(len(healthy_sample_list))
                       
            #out_str = "\t".join([str(dbsv_freq),str(dbsv_healthy_freq),str(timer)])+"\n"
            out_str = ""
            if len(filter_sample_list) != 0:
                out_str = "\t".join([target_svid,str(dbsv_healthy_freq),str(dbsv_freq),";".join(filter_sample_list)])+"\n"            
            else:
                out_str = "\t".join([target_svid,str(dbsv_healthy_freq),str(dbsv_freq),"."])+"\n"            
            out_list.append(out_str)
        
        out_io.write("\t".join(["#SVID","GrandSV_Healthy_Frequency","GrandSV_Frequency","GrandSV_LIST"])+"\n")    
        out_io.writelines(out_list)
    
    b_time = time.time()
    total_time = b_time-a_time
    #print(total_time)
    
if __name__ == "__main__":
    main()