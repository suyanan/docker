# docker

# dockerfiles 

These dockerfiles are related to bioinformatics software and basic environments, and most images are based on alpine:3.9.

## R

from r-base , create some libraries.

## Python

- python
- python-pip
- python-pip-libs

## mapper

- minimap2
- ngmlr

## svcaller

- sniffles

## methylationcaller

- nanopolish(todo)

## tools

- samtools
- bedtools

## useful pipeline

- fastq_stat
- sv_annotation
- sv_report

---

Tricks:
1. When installing some packages in docker container, you can check the related libs whether exits in [alpinelinux](https://pkgs.alpinelinux.org/packages).
2. docekr build -t image_name .
3. retry the software installation, by "docker run -it --name container_name image_name"
4. check the container, by "docker cp", to debug the target project.

---
end
