"""Print log date and timestamp for run_daily_crawl.bat (one line: YYYY-MM-DD HH:MM:SS)."""
from datetime import datetime

print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
