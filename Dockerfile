FROM python:3.8-slim AS runtime
COPY /src /code

SHELL ["/bin/bash", "-c"]
ENTRYPOINT source /venv/bin/activate && python code/launcher.py
