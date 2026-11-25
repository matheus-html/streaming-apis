import os

import gevent
from locust import events

TIMEOUT = float(os.environ.get("TIMEOUT", "5"))
WARMUP = int(os.environ.get("WARMUP", "0"))
TOTAL_USUARIOS = 5000
TOTAL_PLAYLISTS = 15000
TOTAL_MUSICAS = 20000


@events.test_start.add_listener
def zerar_apos_aquecimento(environment, **kwargs):
    if WARMUP > 0 and environment.runner is not None:
        gevent.spawn_later(WARMUP, environment.runner.stats.reset_all)