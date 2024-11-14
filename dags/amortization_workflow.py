# dags/amortization_workflow.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import numpy as np
import numpy_financial as npf
from datetime import timedelta

# File paths for input and output
SIMPLE_AMORTIZATION_FILE = "/opt/airflow/dags/SimpleAmortizationTest.xlsx"
MODIFIED_AMORTIZATION_FILE = "/opt/airflow/dags/ModifiedAmortizationTest.xlsx"
OUTPUT_FILE = "/opt/airflow/dags/Consolidated_Amortization_Report.xlsx"


def generate_amortization_report():
    # Load data from Excel files
    loan_data_simple = pd.read_excel(
        SIMPLE_AMORTIZATION_FILE, sheet_name="LoanDataTape", skiprows=1
    )
    loan_data_modified = pd.read_excel(
        MODIFIED_AMORTIZATION_FILE, sheet_name="LoanTape"
    )

    # Rename columns in loan_data_modified for consistency
    loan_data_modified = loan_data_modified.rename(
        columns={
            "original_principal": "loan amount",
            "amortization_term_months": "term",
            "interest_rate": "interest_rate",
            "start_date": "start_date",
        }
    )

    # Amortization calculation function
    def calculate_amortization_schedule(
        principal, rate, term_months, start_date, frequency="Monthly"
    ):
        schedules = []
        monthly_rate = rate / 12 if frequency == "Monthly" else rate
        payment = npf.pmt(monthly_rate, term_months, -principal)
        for period in range(1, term_months + 1):
            interest = principal * monthly_rate
            principal_payment = payment - interest
            principal -= principal_payment
            payment_date = start_date + timedelta(days=30 * period)
            schedules.append(
                {
                    "Payment Date": payment_date,
                    "Payment": payment,
                    "Principal Payment": principal_payment,
                    "Interest Payment": interest,
                    "Remaining Balance": principal,
                }
            )
        return pd.DataFrame(schedules)

    # Generate amortization schedules for each loan
    def generate_schedules(loan_data):
        all_schedules = []
        for _, loan in loan_data.iterrows():
            schedule = calculate_amortization_schedule(
                principal=loan["loan amount"],
                rate=loan["interest_rate"],
                term_months=int(loan["term"]),
                start_date=pd.to_datetime(loan["start_date"]),
            )
            schedule["Loan Number"] = loan.get("loan number", "N/A")
            all_schedules.append(schedule)
        return pd.concat(all_schedules, ignore_index=True)

    # Generate schedules and consolidate report
    monthly_schedules = generate_schedules(loan_data_modified)
    daily_schedules = monthly_schedules.copy()
    expanded_daily = []
    for _, row in daily_schedules.iterrows():
        for day in range(30):
            new_row = row.copy()
            new_row["Payment Date"] += timedelta(days=day)
            expanded_daily.append(new_row)
    daily_schedules = pd.DataFrame(expanded_daily).drop_duplicates(
        subset=["Loan Number", "Payment Date"]
    )
    consolidated_report = pd.merge(
        monthly_schedules,
        daily_schedules,
        on=["Loan Number", "Payment Date"],
        suffixes=("_Monthly", "_Daily"),
        how="outer",
    ).sort_values(by=["Loan Number", "Payment Date"])
    consolidated_report.to_excel(OUTPUT_FILE, index=False)
    print("Amortization report generated:", OUTPUT_FILE)


# Define the DAG
with DAG(
    dag_id="amortization_schedule_workflow",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    # Define the task
    run_report_task = PythonOperator(
        task_id="generate_amortization_report",
        python_callable=generate_amortization_report,
    )

    run_report_task
