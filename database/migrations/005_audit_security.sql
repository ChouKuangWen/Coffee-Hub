-- Batch 6: apply after 001-004; pause writes; single migration runner. No business data deletion.

SET @coffeehub_m005_sql = IF(
 EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='audit_logs' AND column_name='retention_class'),
 'DO 0', 'ALTER TABLE audit_logs ADD COLUMN retention_class VARCHAR(30) NOT NULL DEFAULT ''UNCLASSIFIED''');
PREPARE coffeehub_m005_stmt FROM @coffeehub_m005_sql;
EXECUTE coffeehub_m005_stmt;
DEALLOCATE PREPARE coffeehub_m005_stmt;

SET @coffeehub_m005_sql = IF(
 EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='audit_logs' AND column_name='expires_at'),
 'DO 0', 'ALTER TABLE audit_logs ADD COLUMN expires_at DATETIME NULL');
PREPARE coffeehub_m005_stmt FROM @coffeehub_m005_sql;
EXECUTE coffeehub_m005_stmt;
DEALLOCATE PREPARE coffeehub_m005_stmt;

SET @coffeehub_m005_sql = IF(
 EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='audit_logs' AND column_name='is_held'),
 'DO 0', 'ALTER TABLE audit_logs ADD COLUMN is_held BOOLEAN NOT NULL DEFAULT FALSE');
PREPARE coffeehub_m005_stmt FROM @coffeehub_m005_sql;
EXECUTE coffeehub_m005_stmt;
DEALLOCATE PREPARE coffeehub_m005_stmt;

SET @coffeehub_m005_sql = IF(
 EXISTS (SELECT 1 FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='audit_logs' AND index_name='ix_audit_logs_expires_at'),
 'DO 0', 'CREATE INDEX ix_audit_logs_expires_at ON audit_logs(expires_at)');
PREPARE coffeehub_m005_stmt FROM @coffeehub_m005_sql;
EXECUTE coffeehub_m005_stmt;
DEALLOCATE PREPARE coffeehub_m005_stmt;
INSERT IGNORE INTO schema_migrations(version) VALUES ('005_audit_security');
