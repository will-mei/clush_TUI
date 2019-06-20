CREATE TABLE task.task(
    ID INTEGER PRIMARY  KEY     NOT NULL AUTOINCREMENT,
    TASK_NAME           TEXT    NOT NULL,
    TASK_TYPE           TEXT    NOT NULL,
    EXEC_TYPE           TEXT    NOT NULL,
    LAUNCHER_ID         INT     NOT NULL,
    STATUS              TEXT    NOT NULL,
    WITH_OUTPUT         INT     NOT NULL,   # 0=false, 1=true 
    OUTPUT_ID           INT,
    CMD_LIST            TEXT    NOT NULL,
    RETURN_VALUE        TEXT    NOT NULL,
    SCRIPT_FILE         TEXT,
    SCRIPT_TYPE         TEXT,               # bash_script, ansible_playbook, other_executable
    SOURCE_FILE         TEXT,
    TARGET_DIR          TEXT,
    TARGET_FILE         TEXT,
    UNTIL_CHECK_OK      INT,
    WHILE_CHECK_OK      INT,
    PARALLEL_WITH_TASK  INT,
    PARALLEL_WAIT_TASK  INT,
    SUCCESS_GOTO        INT,
    FAILED_GOTO         INT,
    CONFIRM_BY          INT,
    ROLLBACK_BY         INT,
    TIMEOUT             INT,
    RETRY_MAX           INT,
    AUTH_LEVEL          INT,
    NOTIFY_LEVEL        INT 
);

CREATE TABLE task.sessions(
    ID INTEGER PRIMARY  KEY     NOT NULL AUTOINCREMENT,
    TARGET_HOST         INT     NOT NULL,
    STATUS              TEXT    NOT NULL,
    PARENT_TASK         INT     NOT NULL,
    CONNECTION_TYPE     TEXT    NOT NULL,
    START_TIME          TEXT    NOT NULL,
    END_TIME            TEXT
);
