CREATE TABLE terminal.terminal(
    ID INTEGER PRIMARY  KEY     AUTOINCREMENT,
    TERMINAL_NAME       TEXT,
    HOSTNAME            TEXT,
    SERVER_IP           TEXT    NOT NULL,
    SERVER_PORT         INT     NOT NULL,
    CONNECTION_MAX      INT     NOT NULL,
    SOCKET_MTU          INT     NOT NULL,
    SOCKET_TIMEOUT      INT     NOT NULL,
    TASK_TIMEOUT        INT     NOT NULL,
    HASH_KEY            TEXT    NOT NULL,
    TAG                 TEXT
);

CREATE TABLE terminal.groups(
    ID INTEGER PRIMARY  KEY     AUTOINCREMENT,
    GROUP_NAME          TEXT    unique  NOT NULL,
    STATUS              TEXT,
    SSH_USER            TEXT,
    SSH_PORT            TEXT    NOT NULL,
    SSH_TIMEOUT         INT     NOT NULL,
    SSH_PASSWORD        TEXT,
    SSH_HOSTKEY         TEXT,
    TAG                 TEXT
);

CREATE TABLE terminal.host(
    ID INTEGER PRIMARY  KEY     AUTOINCREMENT,
    HOSTNAME            TEXT    NOT NULL,
    GROUP_NAME          TEXT    NOT NULL,
    MANAGEMENT_IP       TEXT,
    BOARD_SN            TEXT    unique,
    STATUS              TEXT,
    TAG                 TEXT,
    ASSET_INFO          TEXT,
    LOCATION_INFO       TEXT
);
