FROM continuumio/miniconda3 AS builder
COPY requirements.txt .
RUN conda create --name build --file requirements.txt

FROM python:3.8-slim
RUN ls -lh .
WORKDIR /code
COPY --from=builder /root/.local /root/.local
COPY /src /code
ENV PATH=/root/.local:$PATH:/code:/root/.local/bin
RUN ls -lh .
ENTRYPOINT ["python", "code/launcher.py"]
