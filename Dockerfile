FROM reosiain/billy:python_base AS build

FROM python:3.8-slim AS runtime
COPY /src /code
COPY --from=build /venv /venv

SHELL ["/bin/bash", "-c"]
ENTRYPOINT source /venv/bin/activate && python code/launcher.py
