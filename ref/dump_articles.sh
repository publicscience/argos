pg_dump -U argos_user -h localhost -d argos_dev -t article > article_dump.sql

# to import:
# pg_restore -d dbname filename
