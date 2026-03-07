CREATE TABLE IF NOT EXISTS etl_run_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  run_timestamp DATETIME NOT NULL,
  strategy VARCHAR(10) NOT NULL,
  products_processed INT NOT NULL,
  products_written INT NOT NULL
);
