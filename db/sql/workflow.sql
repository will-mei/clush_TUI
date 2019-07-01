CREATE TABLE workflow.workflow(
    ID INTEGER PRIMARY  KEY     AUTOINCREMENT,
    WORKFLOW_NAME       TEXT    NOT NULL,
    EXEC_MODE           TEXT    NOT NULL,
    WORKFLOW_TASK_MAP   TEXT    NOT NULL,
    AUTH_LEVEL          INT,
    NOTIFY_LEVEL        INT,
    EXEC_COUNT          INT,
    STATUS              TEXT,
    CTIME               INT,
    MTIME               INT
);

CREATE TABLE workflow.task(
    ID INTEGER PRIMARY      KEY     AUTOINCREMENT,
    TASK_NAME               TEXT    NOT NULL,
    ROLLBACKABLE            INT     NOT NULL,
    TRANSPORT_LOCAL_SOURDE  TEXT,
    TRANSPORT_LOCAL_TARGET  TEXT,
    TRANSPORT_REMOTE_SOURCE TEXT,
    TRANSPORT_REMOTE_TARGET TEXT,
    EXEC_TYPE               TEXT    NOT NULL,
    TASK_CONTENT_TYPE       TEXT,
    EXEC_SOURCE_TYPE        TEXT,
    EXEC_STARTUP_FILE       TEXT,
    EXEC_FILE_TYPE          TEXT,
    SHELL_COMMAND_TEXT      TEXT,
    TASK_TAG                TEXT,
    TASK_NOTE               TEXT,
    AUTH_LEVEL              INT,
    NOTIFY_LEVEL            INT,
    CTIME                   INT,
    MTIME                   INT
);

CREATE TABLE workflow.sessions(
    ID INTEGER PRIMARY  KEY     AUTOINCREMENT,
    WORKFLOW_ID         INT     NOT NULL,
    TASK_ID             INT     NOT NULL,
    TARGET_HOST         INT     NOT NULL,
    STATUS              TEXT    NOT NULL,
    START_TIME          TEXT    NOT NULL,
    END_TIME            TEXT,
    CTIME               INT     NOT NULL,
    MTIME               INT
);
