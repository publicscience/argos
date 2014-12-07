# Dumps the remote database and loads it locally.
ssh user@remote.co 'pg_dump -U argos_user -h localhost -d argos_dev -f ~/argos_dump.sql'
scp user@remote.co:~/argos_dump.sql ~/
dropdb argos_dev
createdb -U argos_user -E utf8 -O argos_user argos_dev -T template0
psql -U argos_user -d argos_dev -f ~/argos_dump.sql
rm ~/argos_dump.sql
