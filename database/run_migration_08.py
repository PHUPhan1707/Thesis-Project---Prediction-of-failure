"""
Script để chạy migration 08: Remove H5P early activity features
"""
import sys
import logging
from pathlib import Path
import mysql.connector
from mysql.connector import Error

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 4000,
    "database": "dropout_prediction_db",
    "user": "dropout_user",
    "password": "dropout_pass_123"
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_migration():
    """Chạy migration 08 để xóa các cột h5p_early"""
    connection = None
    
    try:
        # Kết nối database
        logger.info("Connecting to database...")
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if not connection.is_connected():
            logger.error("Failed to connect to database")
            return False
        
        logger.info("Connected to database successfully")
        
        # Đọc migration file
        migration_file = Path(__file__).parent / "migrations" / "08_remove_h5p_early_features.sql"
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        logger.info(f"Reading migration file: {migration_file}")
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Tách các câu lệnh SQL (dựa vào dấu chấm phẩy)
        # Loại bỏ comments và empty lines trước
        lines = []
        for line in migration_sql.split('\n'):
            line = line.strip()
            # Bỏ qua comments và empty lines
            if line and not line.startswith('--') and not line.startswith('USE'):
                # Loại bỏ inline comments
                if '--' in line:
                    line = line.split('--')[0].strip()
                lines.append(line)
        
        # Ghép lại và tách theo dấu chấm phẩy
        full_sql = ' '.join(lines)
        statements = [s.strip() for s in full_sql.split(';') if s.strip()]
        
        # Chạy từng câu lệnh
        cursor = connection.cursor()
        
        # Chạy USE statement riêng
        cursor.execute("USE dropout_prediction_db")
        
        # Kiểm tra MySQL version để xem có hỗ trợ IF EXISTS không
        cursor.execute("SELECT VERSION()")
        mysql_version = cursor.fetchone()[0]
        logger.info(f"MySQL version: {mysql_version}")
        
        # MySQL 8.0.19+ hỗ trợ DROP COLUMN IF EXISTS
        supports_if_exists = False
        try:
            version_parts = mysql_version.split('.')
            major = int(version_parts[0])
            minor = int(version_parts[1])
            patch = int(version_parts[2].split('-')[0]) if len(version_parts) > 2 else 0
            if major > 8 or (major == 8 and minor > 0) or (major == 8 and minor == 0 and patch >= 19):
                supports_if_exists = True
        except:
            # Nếu không parse được version, thử dùng IF EXISTS
            supports_if_exists = True
        
        # Chạy các ALTER TABLE statements
        logger.info(f"Executing {len(statements)} ALTER TABLE statements...")
        success_count = 0
        skipped_count = 0
        error_count = 0
        
        # Lấy danh sách các cột hiện có
        cursor.execute("SHOW COLUMNS FROM raw_data")
        existing_columns = {row[0] for row in cursor.fetchall()}
        
        for i, statement in enumerate(statements, 1):
            if statement.strip():
                try:
                    # Extract column name
                    if 'DROP COLUMN IF EXISTS' in statement:
                        col_name = statement.split('DROP COLUMN IF EXISTS')[-1].strip().split()[0]
                    elif 'DROP COLUMN' in statement:
                        col_name = statement.split('DROP COLUMN')[-1].strip().split()[0]
                    else:
                        col_name = 'unknown'
                    
                    # Kiểm tra cột có tồn tại không
                    if col_name not in existing_columns:
                        skipped_count += 1
                        logger.info(f"[{i}/{len(statements)}] Column {col_name} does not exist, skipping")
                        continue
                    
                    logger.info(f"[{i}/{len(statements)}] Dropping column: {col_name}")
                    
                    # Bỏ IF EXISTS khỏi statement (MySQL không hỗ trợ)
                    # Chúng ta đã kiểm tra cột tồn tại rồi nên không cần IF EXISTS
                    if 'DROP COLUMN IF EXISTS' in statement:
                        statement = statement.replace('DROP COLUMN IF EXISTS', 'DROP COLUMN')
                    elif 'DROP COLUMN' not in statement:
                        # Nếu không có DROP COLUMN, bỏ qua
                        logger.warning(f"  ⚠ Statement does not contain DROP COLUMN, skipping")
                        continue
                    
                    cursor.execute(statement)
                    success_count += 1
                    existing_columns.discard(col_name)  # Xóa khỏi danh sách
                    logger.info(f"  ✓ Successfully dropped {col_name}")
                    
                except Error as e:
                    error_msg = str(e)
                    # Nếu cột không tồn tại, bỏ qua lỗi
                    if "Unknown column" in error_msg or "doesn't exist" in error_msg or "check that column/key exists" in error_msg:
                        skipped_count += 1
                        logger.warning(f"  ⚠ Column does not exist, skipping: {col_name}")
                        existing_columns.discard(col_name)
                    else:
                        error_count += 1
                        logger.error(f"  ✗ Error: {error_msg}")
                        # Không raise để tiếp tục với các cột khác
                        logger.warning(f"  Continuing with next column...")
        
        logger.info(f"\nSummary: {success_count} dropped, {skipped_count} skipped (not exist), {error_count} errors")
        
        # Commit changes
        connection.commit()
        logger.info("Migration completed successfully!")
        
        # Verify: Kiểm tra các cột còn lại
        logger.info("\n=== Verification ===")
        cursor.execute("SHOW COLUMNS FROM raw_data LIKE 'h5p_early%'")
        remaining_columns = cursor.fetchall()
        
        if remaining_columns:
            logger.warning(f"⚠ Found {len(remaining_columns)} remaining h5p_early columns:")
            for col in remaining_columns:
                logger.warning(f"  - {col[0]}")
        else:
            logger.info("✓ No h5p_early columns found - all removed successfully")
        
        cursor.execute("SHOW COLUMNS FROM raw_data LIKE 'h5p_first%'")
        first_columns = cursor.fetchall()
        
        if first_columns:
            logger.warning(f"⚠ Found {len(first_columns)} remaining h5p_first columns:")
            for col in first_columns:
                logger.warning(f"  - {col[0]}")
        else:
            logger.info("✓ No h5p_first columns found - all removed successfully")
        
        cursor.close()
        return True
        
    except Error as e:
        logger.error(f"Database error: {e}")
        if connection:
            connection.rollback()
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if connection:
            connection.rollback()
        return False
        
    finally:
        if connection and connection.is_connected():
            connection.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run migration 08: Remove H5P early features')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be executed without running')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        # TODO: Implement dry-run mode
        logger.info("Dry-run mode not yet implemented")
    else:
        success = run_migration()
        if success:
            logger.info("\n✅ Migration 08 completed successfully!")
            sys.exit(0)
        else:
            logger.error("\n❌ Migration 08 failed!")
            sys.exit(1)

