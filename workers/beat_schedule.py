from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'sync-tickers-every-5s': {
        'task': 'workers.tasks.sync_all_tickers',
        'schedule': 5.0,
    },
    'sync-open-orders-every-10s': {
        'task': 'workers.tasks.sync_open_orders',
        'schedule': 10.0,
    },
    'sync-markets-daily': {
        'task': 'workers.tasks.sync_markets',
        'schedule': crontab(hour=0, minute=0),
    },
}
