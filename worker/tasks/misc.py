from celery import shared_task


@shared_task
def test_sum(x, y):
    return x + y


@shared_task
def lidar_backend_status():
    from lidar_backend import LIDAR_BACKEND, LIDAR_INFO, LidarName

    lidar_names = sorted(LIDAR_INFO.get("metadata", {}).get("name2nick", {}).keys())
    try:
        alhambra_value = LidarName("alhambra").value
    except Exception as exc:
        alhambra_value = None
        alhambra_error = str(exc)
    else:
        alhambra_error = None

    return {
        "backend": LIDAR_BACKEND,
        "has_alhambra": "alhambra" in lidar_names,
        "alhambra_value": alhambra_value,
        "alhambra_error": alhambra_error,
        "lidar_count": len(lidar_names),
        "sample_lidars": lidar_names[:5],
    }
