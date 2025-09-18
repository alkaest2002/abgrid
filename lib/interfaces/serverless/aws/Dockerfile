FROM public.ecr.aws/lambda/python:3.11-arm64

# Ensure non-interactive matplotlib backend and smaller images/logs
ENV MPLBACKEND=Agg \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Copy and install dependencies into Lambda task root
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary=:all: -r requirements.txt --target "${LAMBDA_TASK_ROOT}" && \
    # Optional trimming to reduce size
    find "${LAMBDA_TASK_ROOT}" -type d -name tests -prune -exec rm -rf '{}' + && \
    find "${LAMBDA_TASK_ROOT}" -type d -name __pycache__ -prune -exec rm -rf '{}' + && \
    rm -rf "${LAMBDA_TASK_ROOT}/matplotlib/mpl-data/sample_data" || true

# Add your application code
COPY app.py ${LAMBDA_TASK_ROOT}

# Add the lib directory
COPY lib/ ${LAMBDA_TASK_ROOT}/lib/

# Lambda entry point: module.function
CMD ["app.lambda_handler"]