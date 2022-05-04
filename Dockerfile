FROM continuumio/miniconda3 AS build

COPY environment.yml .
RUN conda create --file environment.yml
RUN conda install -c conda-forge conda-pack

# Use conda-pack to create a standalone enviornmen in /venv:
RUN conda-pack -n example -o /tmp/env.tar && \
  mkdir /venv && cd /venv && tar xf /tmp/env.tar && \
  rm /tmp/env.tar

RUN /venv/bin/conda-unpack


FROM debian:buster AS runtime
COPY /src /code
COPY --from=build /venv /venv

# When image is run, run the code with the environment
# activated:
SHELL ["/bin/bash", "-c"]
ENTRYPOINT source /venv/bin/activate && python code/launcher.py
