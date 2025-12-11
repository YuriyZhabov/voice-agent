#!/bin/bash
# Deploy Voice Agent to Yandex Cloud Container Registry + Compute VM
# Prerequisites: yc CLI configured, Docker installed

set -e

# Configuration
REGISTRY_ID="${YC_REGISTRY_ID:-}"
FOLDER_ID="${YC_FOLDER_ID:-}"
IMAGE_NAME="voice-agent"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Voice Agent Yandex Cloud Deploy ===${NC}"

# Check prerequisites
if ! command -v yc &> /dev/null; then
    echo -e "${RED}Error: yc CLI not found. Install: https://cloud.yandex.ru/docs/cli/quickstart${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker not found${NC}"
    exit 1
fi

# Get folder ID if not set
if [ -z "$FOLDER_ID" ]; then
    FOLDER_ID=$(yc config get folder-id)
    echo -e "${YELLOW}Using folder: $FOLDER_ID${NC}"
fi

# Create or get Container Registry
if [ -z "$REGISTRY_ID" ]; then
    echo -e "${YELLOW}Creating Container Registry...${NC}"
    REGISTRY_ID=$(yc container registry create --name voice-agent-registry --folder-id $FOLDER_ID --format json | jq -r '.id')
    echo -e "${GREEN}Registry created: $REGISTRY_ID${NC}"
fi

# Configure Docker for Yandex Registry
echo -e "${YELLOW}Configuring Docker auth...${NC}"
yc container registry configure-docker

# Build image
FULL_IMAGE="cr.yandex/${REGISTRY_ID}/${IMAGE_NAME}:${IMAGE_TAG}"
echo -e "${YELLOW}Building image: $FULL_IMAGE${NC}"
docker build -t $FULL_IMAGE .

# Push to registry
echo -e "${YELLOW}Pushing to Yandex Container Registry...${NC}"
docker push $FULL_IMAGE

echo -e "${GREEN}=== Image pushed successfully ===${NC}"
echo -e "Image: $FULL_IMAGE"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Create VM with Container Optimized Image:"
echo "   yc compute instance create-with-container \\"
echo "     --name voice-agent \\"
echo "     --zone ru-central1-a \\"
echo "     --cores 2 --memory 4GB \\"
echo "     --container-image $FULL_IMAGE \\"
echo "     --container-env-file .env.prod \\"
echo "     --ssh-key ~/.ssh/id_rsa.pub"
echo ""
echo "2. Or use docker-compose on existing VM"
