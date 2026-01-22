#!/bin/bash
# =============================================================================
# Docker Restart Script - Rebuild Database từ đầu
# =============================================================================
# Purpose: Stop, remove containers và volumes, sau đó start lại với schema mới
# WARNING: Script này sẽ XÓA TẤT CẢ DATA hiện tại!
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Docker Database Restart Script${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "${RED}[WARNING] Script này sẽ XÓA TẤT CẢ DATA hiện tại!${NC}"
echo ""
read -p "Bạn có chắc chắn muốn tiếp tục? (y/n): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Hủy bỏ."
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/5]${NC} Stopping containers..."
docker-compose down
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

echo -e "${YELLOW}[2/5]${NC} Removing volumes (deleting all data)..."
docker volume rm dropout_prediction_mysql_data 2>/dev/null || true
echo -e "${GREEN}✓ Volumes removed${NC}"
echo ""

echo -e "${YELLOW}[3/5]${NC} Starting containers with new schema..."
docker-compose up -d
echo -e "${GREEN}✓ Containers started${NC}"
echo ""

echo -e "${YELLOW}[4/5]${NC} Waiting for MySQL to be ready..."
sleep 15
echo -e "${GREEN}✓ MySQL should be ready${NC}"
echo ""

echo -e "${YELLOW}[5/5]${NC} Verifying database schema..."
echo "Checking tables..."
docker exec -i dropout_prediction_mysql mysql -uroot -proot_password_123 dropout_prediction_db -e "SHOW TABLES;"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database restart completed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "New tables created:"
echo "  - enrollments"
echo "  - h5p_scores, h5p_scores_summary"
echo "  - video_progress, video_progress_summary"
echo "  - dashboard_summary"
echo "  - mooc_progress (updated with new columns)"
echo "  - mooc_grades (NEW)"
echo "  - mooc_discussions (NEW)"
echo "  - raw_data (updated with new columns)"
echo ""
echo "Access phpMyAdmin: http://localhost:8081"
echo "  Username: dropout_user"
echo "  Password: dropout_pass_123"
echo ""
echo "Next steps:"
echo "  1. Verify schema in phpMyAdmin"
echo "  2. Run fetch_mooc_h5p_data.py to populate data"
echo ""
