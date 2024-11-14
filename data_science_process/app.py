import pandas as pd
import numpy_financial as npf
from datetime import timedelta


# Define a function to generate the amortization schedule
def calculate_amortization_schedule(
    principal, rate, term_months, start_date, frequency, prepayment=0
):
    frequency_mapping = {
        "Monthly": 1,
        "Bi-Weekly": 2,
        "Weekly": 4,
        "Semi-Monthly": 24,  # Semi-monthly: 24 periods per year
        "Quarterly": 4,  # Quarterly: 4 periods per year
        "Semi-Annually": 2,  # Semi-annually: 2 periods per year
    }

    periods_per_year = 12 * frequency_mapping[frequency]
    periodic_rate = rate / periods_per_year
    num_periods = term_months * frequency_mapping[frequency]

    # Calculate regular payment amount based on frequency
    payment = npf.pmt(periodic_rate, num_periods, -principal)

    schedule = []
    balance = principal

    for period in range(1, num_periods + 1):
        opening_balance = balance
        interest_payment = opening_balance * periodic_rate
        principal_payment = payment - interest_payment
        total_principal_payment = principal_payment + prepayment
        balance -= total_principal_payment
        payment_date = start_date + timedelta(days=(365 / periods_per_year) * period)

        schedule.append(
            {
                "Payment Date": payment_date,
                "Opening Balance": opening_balance,
                "Payment": payment,
                "Principal Repayment": principal_payment,
                "Interest": interest_payment,
                "Prepayment": prepayment,
                "Closing Balance": balance,
            }
        )

        if balance <= 0:
            break

    return pd.DataFrame(schedule)


# Function to generate schedules for all loans
def generate_all_schedules(loan_data):

    all_schedules = []
    for _, loan in loan_data.iterrows():
        schedule = calculate_amortization_schedule(
            principal=loan["loan amount"],
            rate=loan["interest_rate"],
            term_months=int(loan["term"]),
            start_date=pd.to_datetime(loan["start_date"]),
            frequency=loan.get("payment_frequency", "Monthly"),
            prepayment=loan.get("prepayment", 0),
        )
        schedule["Loan Number"] = loan.get("loan number", "N/A")
        all_schedules.append(schedule)
    return pd.concat(all_schedules, ignore_index=True)


# Consolidate all schedules into a summary
def consolidate_schedules(schedules):
    return schedules.groupby(["Payment Date"]).sum().reset_index()


# Load data and generate schedules
loan_data = pd.read_excel(
    "data_science_process/ModifiedAmortization Test.xlsx", sheet_name="LoanTape"
)
loan_data = loan_data.rename(
    columns={
        "original_principal": "loan amount",  # Adjust if column name is different
        "amortization_term_months": "term",
        "interest_rate": "interest_rate",
        "start_date": "start_date",
        "loan_number": "loan number",  # Adjust if column name is different
    }
)
consolidated_schedules = consolidate_schedules(generate_all_schedules(loan_data))

# Export consolidated report
consolidated_schedules.to_excel("Consolidated_Cash_Flow_Report.xlsx", index=False)
print("Cash flow report generated: Consolidated_Cash_Flow_Report.xlsx")
