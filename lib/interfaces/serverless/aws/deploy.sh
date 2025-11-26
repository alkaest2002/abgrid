#!/usr/bin/env bash

set -e  # Exit on any error

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Configuration
REGION=${AWS_REGION}
REPO=${AWS_REPO}
FUNCTION=${AWS_FUNCTION}
ROLE_ARN=${AWS_ROLE_ARN}

# Environment variables to set (add more as needed)
ENV_VARS="AUTH_SECRET=${AUTH_SECRET:-},AWS_API_KEY=${AWS_API_KEY:-},MPLCONFIGDIR=${MPLCONFIGDIR:-/tmp/matplotlib}"

echo "Creating ECR repository..."
aws ecr create-repository --repository-name $REPO --region $REGION >/dev/null 2>&1 || true

echo "Getting account ID..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE_URI=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO:latest

echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Better buildx handling
echo "Setting up Docker buildx..."
if ! docker buildx inspect lambda-builder >/dev/null 2>&1; then
    echo "Creating new buildx builder..."
    docker buildx create --name lambda-builder --use --bootstrap
else
    echo "Using existing buildx builder..."
    docker buildx use lambda-builder
fi

# Add this after ECR login for extra verification
echo "Testing ECR connectivity..."
aws ecr describe-repositories --repository-names $REPO --region $REGION

# Add retry logic for the push
echo "Building and pushing image (with retries)..."
for i in {1..3}; do
    if docker buildx build \
        --platform linux/arm64 \
        --provenance=false \
        --tag $IMAGE_URI \
        --push \
        --progress=plain \
        --no-cache \
        .; then
        echo "✅ Push succeeded on attempt $i"
        break
    else
        echo "❌ Push failed on attempt $i"
        if [ $i -eq 3 ]; then
            echo "ERROR: All push attempts failed"
            exit 1
        fi
        sleep 5
    fi
done

# Additional verification that the push succeeded
echo "Verifying image push to ECR..."
if ! aws ecr describe-images --repository-name $REPO --region $REGION --image-ids imageTag=latest >/dev/null 2>&1; then
    echo "ERROR: Image not found in ECR after push. Attempting manual push..."
    
    # Fallback: Build locally then push
    docker buildx build \
        --platform linux/arm64 \
        --provenance=false \
        --tag $IMAGE_URI \
        --load \
        --progress=plain \
        .
    
    echo "Manually pushing image to ECR..."
    docker push $IMAGE_URI
    
    # Verify again
    if ! aws ecr describe-images --repository-name $REPO --region $REGION --image-ids imageTag=latest >/dev/null 2>&1; then
        echo "ERROR: Failed to push image to ECR"
        exit 1
    fi
fi

echo "✅ Image successfully pushed to ECR"
aws ecr describe-images --repository-name $REPO --region $REGION --image-ids imageTag=latest --query 'imageDetails[0].{Digest:imageDigest,Size:imageSizeInBytes,PushedAt:imagePushedAt}'

# Check if Lambda function exists
echo "Checking if Lambda function exists..."
FUNCTION_EXISTS=$(aws lambda get-function --function-name $FUNCTION --region $REGION >/dev/null 2>&1 && echo "true" || echo "false")

if [ "$FUNCTION_EXISTS" = "false" ]; then
    echo "Creating new Lambda function..."
    aws lambda create-function \
      --region $REGION \
      --function-name $FUNCTION \
      --package-type Image \
      --code ImageUri=$IMAGE_URI \
      --role $ROLE_ARN \
      --timeout 60 \
      --memory-size 256 \
      --architecture arm64 \
      --environment Variables="{$ENV_VARS}"
else
    echo "Updating Lambda function code..."
    aws lambda update-function-code \
      --region $REGION \
      --function-name $FUNCTION \
      --image-uri $IMAGE_URI
    
    echo "Waiting for function update to complete..."
    aws lambda wait function-updated --function-name $FUNCTION --region $REGION
    
    # Update environment variables
    echo "Updating environment variables..."
    aws lambda update-function-configuration \
      --region $REGION \
      --function-name $FUNCTION \
      --environment Variables="{$ENV_VARS}"
fi

echo "✅ Deployment complete!"
