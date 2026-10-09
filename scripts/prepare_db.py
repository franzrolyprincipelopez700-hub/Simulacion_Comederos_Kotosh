from database_tools import connection, prepare

if __name__ == '__main__':
    prepare(connection())
    print('Conexión PostgreSQL correcta; base de datos preparada.')
