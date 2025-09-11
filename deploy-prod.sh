#!/bin/bash

# Production deployment script for ERP MIF Maroc
# This script builds and deploys the full stack (backend + frontend)

set -e

echo "🚀 Starting production deployment for ERP MIF Maroc..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the backend directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}Error: Please run this script from the backend directory (PFE_ERP_BackEnd_MIF_Maroc)${NC}"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "../VITE-FRONTEND-ERP-MIF-MAROC" ]; then
    echo -e "${RED}Error: Frontend directory not found at ../VITE-FRONTEND-ERP-MIF-MAROC${NC}"
    exit 1
fi

echo -e "${YELLOW}Building frontend for production...${NC}"
cd ../VITE-FRONTEND-ERP-MIF-MAROC
npm ci
npm run build

echo -e "${GREEN}Frontend built successfully!${NC}"

cd ../PFE_ERP_BackEnd_MIF_Maroc

echo -e "${YELLOW}Starting production services...${NC}"
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up --build -d

echo -e "${GREEN}Production deployment completed!${NC}"
echo -e "${GREEN}Services should be available at:${NC}"
echo -e "  - Frontend: http://localhost"
echo -e "  - API: http://localhost/api/v1/"
echo -e "  - API Docs: http://localhost/docs"
echo -e "  - Health Check: http://localhost/health"

echo -e "${YELLOW}To check service status:${NC}"
echo "  docker-compose -f docker-compose.prod.yml ps"
echo "  docker-compose -f docker-compose.prod.yml logs [service_name]"
