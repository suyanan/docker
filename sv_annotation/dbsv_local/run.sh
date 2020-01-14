#构建镜像
cp /sfs-grand-med-research/home/suyanan/scripts/SV/dbSV/dbsv-es-demos/es.py .
cp /sfs-grand-med-research/home/suyanan/scripts/SV/dbSV/dbsv-es-demos/config.ini .

docker rm dbsv-es-v1
docker rmi swr.cn-north-1.myhuaweicloud.com/grand-med-research/dbsv-es:2.5

docker build -t swr.cn-north-1.myhuaweicloud.com/grand-med-research/dbsv-es:2.5 .

#测试镜像
docker run -it --name dbsv-es-v1 swr.cn-north-1.myhuaweicloud.com/grand-med-research/dbsv-es:2.5
docker cp /sfs-grand-med-research/home/suyanan/research/elasticsearch/demo_data/DBM19A3676-1.re2.filter.100.bed dbsv-es-v1:/dbsv-es-demos
python es.py --input DBM19A3676-1.re2.filter.100.bed

#测试通过后推送镜像
docker push swr.cn-north-1.myhuaweicloud.com/grand-med-research/dbsv-es:2.5

#hanwell test
java -jar wdltool-0.14.jar validate es.wdl 
java -jar wdltool-0.14.jar inputs es.wdl > es_inputs.json

#提交任务
gcs sub wdl es.wdl -i es_inputs.json -o cci.options -n es -s gcs-env-grand-med-research
