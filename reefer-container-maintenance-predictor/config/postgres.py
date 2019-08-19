import os
import sys


def config():
    host = os.getenv('POSTGRESQL_HOST', False)
    if not host:
        sys.exit('missing POSTGRESQL_HOST env var')
        return

    port = os.getenv('POSTGRESQL_PORT', '5432')
    if not port:
        sys.exit('missing POSTGRESQL_PORT env var')
        return

    user = os.getenv('POSTGRESQL_USER', False)
    if not user:
        sys.exit('missing POSTGRESQL_USER env var')
        return

    password = os.getenv('POSTGRESQL_PASSWORD', False)
    if not password:
        sys.exit('missing POSTGRESQL_PASSWORD env var')
        return

    return {"host": host, "port": port, "user": user, "password": password, "dbname": "postgres"}
