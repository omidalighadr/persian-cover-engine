FROM python:3.12-slim AS base

# libraqm + fribidi give Pillow real RTL/Persian shaping
RUN apt-get update \
    && apt-get install -y --no-install-recommends libraqm0 libfribidi0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

RUN useradd --create-home app && mkdir /out && chown app /out
USER app
WORKDIR /out
ENTRYPOINT ["persian-cover"]
CMD ["--help"]
