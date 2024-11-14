# Airflow with Docker and PostgreSQL Setup

This guide walks you through deploying Apache Airflow with Docker and PostgreSQL. This setup includes initializing the Airflow database, running the Airflow webserver, and accessing the Airflow UI.

## Prerequisites

- Docker and Docker Compose should be installed on your machine.
- Recommended Docker Compose version: `1.27.0` or higher.

## Folder Structure

```plaintext
project_folder/
├── dags/
│   ├── SimpleAmortizationTest.xlsx
│   ├── ModifiedAmortizationTest.xlsx
│   └── amortization_workflow.py
├── docker-compose.yml
├── logs/
└── plugins/
```

## Steps to Set Up Airflow

### 1. Define `docker-compose.yml`

Create a `docker-compose.yml` file in the `project_folder` directory. This file sets up the PostgreSQL database, Airflow webserver, and scheduler.

```yaml
version: '3'
services:
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_USER=airflow
      - POSTGRES_PASSWORD=airflow
      - POSTGRES_DB=airflow
    ports:
      - "5432:5432"

  webserver:
    image: apache/airflow:2.5.0
    environment:
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
      - AIRFLOW__API__AUTH_BACKENDS=airflow.api.auth.backend.basic_auth
    depends_on:
      - postgres
    ports:
      - "8080:8080"

  scheduler:
    image: apache/airflow:2.5.0
    environment:
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    depends_on:
      - postgres

  airflow-init:
    image: apache/airflow:2.5.0
    environment:
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
    depends_on:
      - postgres
    entrypoint: ["airflow", "db", "init"]
```

### 2. Initialize the Airflow Database

Run the following commands to initialize the Airflow metadata database.

```bash
# Bring down any existing containers and volumes
docker-compose down -v

# Initialize the database
docker-compose up airflow-init
```

After the initialization is complete, you should see a message indicating successful database setup.

### 3. Start the Airflow Services

Start Airflow services in detached mode:

```bash
docker-compose up -d
```

This command starts all necessary services (`postgres`, `webserver`, and `scheduler`). You can check the status of the services with:

```bash
docker-compose ps
```

### 4. Access the Airflow UI

Open your web browser and go to:

```plaintext
http://localhost:8080
```

The default login credentials are:
- **Username:** `airflow`
- **Password:** `airflow`

### 5. Running Your DAGs

- Place any DAG files (e.g., `amortization_workflow.py`) in the `dags/` folder. The DAGs will be automatically picked up by the Airflow webserver.

### 6. Stopping Services

To stop and remove all services, run:

```bash
docker-compose down
```

## Sample Output

After successfully running the DAG for amortization calculations, a consolidated report will be generated and saved as an Excel file in the following location within the Airflow container:

```plaintext
/opt/airflow/dags/Consolidated_Amortization_Report.xlsx
```

This report includes a detailed amortization schedule, with columns such as:
- **Payment Date**: The date of each payment.
- **Payment**: The total payment amount for the period.
- **Principal Payment**: The portion of the payment applied to the loan principal.
- **Interest Payment**: The portion of the payment applied to interest.
- **Remaining Balance**: The remaining loan balance after each payment.

To download the file, you can use Docker commands to copy it from the container to your local system:

```bash
docker cp <container_id>:/opt/airflow/dags/Consolidated_Amortization_Report.xlsx ./Consolidated_Amortization_Report.xlsx
```


## Troubleshooting

- **Database Connection Issues**: Ensure PostgreSQL is running and accessible at `localhost:5432`.
- **Airflow UI Not Accessible**: Confirm that the webserver is up by checking logs (`docker-compose logs webserver`).
- **Executor Compatibility**: Ensure that `LocalExecutor` is used with a compatible database like PostgreSQL (SQLite is incompatible with `LocalExecutor`).
