import uvicorn

from core import config

if __name__ == "__main__":
    uvicorn.run(
        "gql.app:app",
        host="0.0.0.0",
        port=config.PORT,
        workers=config.WORKERS,
        access_log=False,
        log_level="warning",
    )