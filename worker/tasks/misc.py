from celery import shared_task

@shared_task
def test_sum(x, y):
    return x + y