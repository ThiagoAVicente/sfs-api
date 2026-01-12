#!/bin/bash

# Semantic File Search API - Setup Script

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Semantic File Search API - Setup${NC}"
echo "===================================="
echo ""

# Check dependencies
echo -e "${GREEN}Checking dependencies...${NC}"

if ! command -v openssl &> /dev/null; then
    echo -e "${RED}Error: openssl is not installed${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker is not installed${NC}"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: docker compose is not available${NC}"
    exit 1
fi

echo -e "${GREEN} All dependencies found${NC}"
echo ""


# Copy .env.example to .env
echo -e "${GREEN}1. Creating .env file...${NC}"
if [ ! -f .env.example ]; then
    echo -e "${RED}Error: .env.example not found!${NC}"
    exit 1
fi
cp .env.example .env

# Ask about domain
echo ""
read -p "Do you have a domain? (press Enter for localhost): " USER_DOMAIN

if [ -n "$USER_DOMAIN" ]; then
    echo -e "${YELLOW}Configuring for domain: $USER_DOMAIN${NC}"
    sed -i "s|^DOMAIN=.*|DOMAIN=$USER_DOMAIN|" .env
else
    echo -e "${YELLOW}Configuring for localhost${NC}"
fi

# Generate API key
echo -e "${GREEN}2. Generating API key...${NC}"
API_KEY=$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '=')
sed -i "s/^API_KEY=.*/API_KEY=$API_KEY/" .env

# Generate MinIO KMS key
echo -e "${GREEN}3. Generating MinIO encryption key...${NC}"
MINIO_KMS_KEY=$(openssl rand -base64 32)
MINIO_KMS_FULL="minio-kms:$MINIO_KMS_KEY"
sed -i "s|^MINIO_KMS_SECRET_KEY=.*|MINIO_KMS_SECRET_KEY=$MINIO_KMS_FULL|" .env

# Generate MinIO credentials
echo -e "${GREEN}4. Generating MinIO credentials...${NC}"
MINIO_USER="sfs_$(openssl rand -hex 4)"
MINIO_PASS=$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)
sed -i "s/^MINIO_ROOT_USER=.*/MINIO_ROOT_USER=$MINIO_USER/" .env
sed -i "s/^MINIO_ROOT_PASSWORD=.*/MINIO_ROOT_PASSWORD=$MINIO_PASS/" .env

# Generate Redis password
echo -e "${GREEN}5. Generating Redis password...${NC}"
REDIS_PASS=$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)
sed -i "s/^REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASS/" .env

# Set secure permissions on .env                                                                                                        │
echo -e "${GREEN}6. Setting secure permissions...${NC}"                                                                                 │
chmod 600 .env

echo ""
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}Setup complete${NC}"
echo ""
echo -e "${GREEN}Starting containers${NC}"

docker compose up --build -d

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker compose build failed!${NC}"
    exit 1
fi
echo ""
echo -e "${YELLOW}Generated credentials saved to .env${NC}"
echo -e "${YELLOW}IMPORTANT: Save your credentials somewhere safe!${NC}"
