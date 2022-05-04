FROM continuumio/miniconda3 AS builder
COPY environment.yml .
RUN conda env create --file environment.yml

COPY /src /code
WORKDIR /code

ENTRYPOINT ["python", "launcher.py"]
