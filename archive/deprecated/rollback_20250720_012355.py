import shutil, os
BACKUP_DIR = 'backup_20250720_012355'
for root, dirs, files in os.walk(BACKUP_DIR):
    for file in files:
        src = os.path.join(root, file)
        dst = os.path.relpath(src, BACKUP_DIR)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
print('Rollback completed.')