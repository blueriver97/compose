#!/bin/sh

docker exec vault vault kv put secret/user/database/local-mysql name="local-mysql" host="mysql.svc.internal" port=3306 user="root" password="mysql"
docker exec vault vault kv put secret/user/database/local-sqlserver name="local-sqlserver" host="sqlserver.svc.internal" port=1433 user="root" password="sqlserver"
