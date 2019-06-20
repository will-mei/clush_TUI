PRAGMA database_list
CREATE TABLE terminal.terminal(
    ID INT PRIMARY  KEY     NOT NULL,
    NODE_NAME       TEXT    NOT NULL,
    HOSTNAME        TEXT    NOT NULL,
    SERVER_IP       TEXT    NOT NULL,
    SERVER_PORT     INT     NOT NULL,
    CONN_MAX        INT     NOT NULL,
    SOCKET_MTU      INT     NOT NULL,
    SOCKET_TIMEOUT  INT     NOT NULL,
    TASK_TIMEOUT    INT     NOT NULL,
    HASH_KEY        TEXT    NOT NULL
);
PRAGMA database_list
PRAGMA database_list
PRAGMA database_list
select * from terminal.terminal
;
select * from sqlite_master where type="table";
PRAGMA database_list;
