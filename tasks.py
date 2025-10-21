from huey import RedisHuey
from config.settings import CONFIG

# --- Ambil konfigurasi dari YAML ---
worker_conf = CONFIG.get('workers', {}).get('mssql', {})
queue_name = worker_conf.get('queue', 'mssql_queue')

# Ambil URL Redis khusus untuk tasks (Huey)
redis_url = CONFIG.get('tasks', {}).get('redis_url', 'redis://127.0.0.1:6379/1')

# Inisialisasi Huey dengan Redis URL dari config.yaml
huey = RedisHuey(queue_name, url=redis_url)

@huey.task()
def welcome():
    print(f'[INFO] Welcome task on queue={queue_name}, redis={redis_url}')
