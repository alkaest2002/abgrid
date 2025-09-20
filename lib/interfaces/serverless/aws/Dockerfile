FROM public.ecr.aws/lambda/python:3.13-arm64

# Ensure non-interactive matplotlib backend and smaller images/logs
ENV MPLBACKEND=Agg \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Copy application code
COPY aws_lambda.py ${LAMBDA_TASK_ROOT}

# Copy lib directory
COPY lib/ ${LAMBDA_TASK_ROOT}/lib/

# Copy templates
COPY lib/core/templates/ ${LAMBDA_TASK_ROOT}/templates/

# Copy requirements
COPY requirements.txt .

# Install only binary packages to avoid build issues in Lambda environment
# and target the Lambda task root for deployment
RUN pip install --no-cache-dir --only-binary=:all: -r requirements.txt --target "${LAMBDA_TASK_ROOT}" && \
    # Optional trimming to reduce size
    find "${LAMBDA_TASK_ROOT}" -type d -name tests -prune -exec rm -rf '{}' + && \
    find "${LAMBDA_TASK_ROOT}" -type d -name __pycache__ -prune -exec rm -rf '{}' + && \
    rm -rf "${LAMBDA_TASK_ROOT}/matplotlib/mpl-data/sample_data" || true

# Set lambda entry point
CMD ["aws_lambda.lambda_handler"]