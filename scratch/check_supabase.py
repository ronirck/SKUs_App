import sys
import os
sys.path.append(os.getcwd())
from updater import AppUpdater
config = AppUpdater.fetch_config()
print(f"APK URL: {config.get('apk_url')}")
print(f"Latest App Version: {config.get('latest_app_version')}")
print(f"Update Message: {config.get('update_message')}")
