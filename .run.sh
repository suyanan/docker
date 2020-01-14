华为云登录：
https://auth.huaweicloud.com/authui/login?id=grandomics_bj

#登陆到docker hub
docker login(自己的账户)
docker logout

#查看sha
docker images --digests

#登录到华为云hub


#docker镜像命令
docker run -it --name test alpine:3.9（容器做测试镜像）

docker build -t suyanan/sniffles:1.0.11 .	(.指dockerfile所在的路径)
docker push suyanan/sniffles

docker tag suyanan/sniffles:1.0.11 swr.cn-north-1.myhuaweicloud.com/grandomics_bj/sniffles:v1.0.11
docker push swr.cn-north-1.myhuaweicloud.com/grandomics_bj/sniffles:v1.0.11
