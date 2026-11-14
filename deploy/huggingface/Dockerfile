# AlertaNexo on a Hugging Face Space: the code comes from the public GitHub repo and the transformer weights
# from a private model repo of the Hub, downloaded when the container starts (see download_weights.py).

FROM python:3.12-slim AS source
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
ARG REPO=https://github.com/JuanTrujilloM/final-project-NN-DL.git
ARG BRANCH=main
# Changes whenever the branch moves, so a rebuild never reuses an old clone from the cache.
ADD https://api.github.com/repos/JuanTrujilloM/final-project-NN-DL/git/refs/heads/${BRANCH} /tmp/version.json
RUN git clone --depth 1 -b ${BRANCH} ${REPO} /repo

FROM node:22-slim AS frontend
COPY --from=source /repo/app/frontend /frontend
WORKDIR /frontend
RUN npm ci && npm run build

FROM python:3.12-slim
RUN useradd -m -u 1000 user
WORKDIR /home/user/app
# CPU-only torch keeps the image under ~1 GB; the Space has no GPU.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY --from=source /repo/app/requirements.txt app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt huggingface_hub

COPY --from=source --chown=user /repo/app app
COPY --from=source --chown=user /repo/src src
COPY --from=source --chown=user /repo/results results
COPY --from=source --chown=user /repo/models models
COPY --from=frontend --chown=user /frontend/dist app/frontend/dist
COPY --chown=user download_weights.py start.sh ./

USER user
ENV HUMAID_WEIGHTS_REPO=tru12jt/alertanexo-modelos \
    HF_HOME=/home/user/.cache/huggingface
EXPOSE 7860
CMD ["sh", "start.sh"]
