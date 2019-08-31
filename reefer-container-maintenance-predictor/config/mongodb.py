import os
import sys
import urllib


def mongo_config():
    host = os.getenv('MONGODB_HOST', False)
    if not host:
        sys.exit('missing MONGODB_HOST env var')
        return

    port = os.getenv('MONGODB_PORT', '27017')
    if not port:
        sys.exit('missing POSTGRES_PORT env var')
        return

    user = os.getenv('MONGODB_USER', '')
    if not user:
        sys.exit('missing MONGODB_USER env var')
        return

    password = os.getenv('MONGODB_PASSWORD', '')
    if not password:
        sys.exit('missing MONGODB_PASSWORD env var')
        return

    database = os.getenv('MONGODB_DATABASE', '')
    if not database:
        sys.exit('missing MONGODB_DATABASE env var')
        return


    connection_string = f"mongodb://{user}:{password}@{host}:{port}/{database}"
    return {'connection_string': connection_string, 'database': database}
