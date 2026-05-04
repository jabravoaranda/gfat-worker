# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html

from .lidar import scheduled as scheduled_lidar
# from .radar import scheduled as scheduled_radar ej de añadir

all_scheduled = {}
all_scheduled |= scheduled_lidar
# all_scheduled |= scheduled_radar ej de añadir


__all__ = ["all_scheduled"]

