import boto3
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


def get_date_input(message):
    """
    Ask the user to enter a date in YYYY-MM-DD format.
    """

    while True:
        date_string = input(message)

        try:
            date_value = datetime.strptime(date_string, "%Y-%m-%d").date()
            return date_value

        except ValueError:
            print("Invalid date format.")
            print("Please enter the date in YYYY-MM-DD format.")


def get_billing_data(start_date, end_date):
    """
    Retrieve AWS billing information using AWS Cost Explorer.
    """

    # AWS Cost Explorer is a global service.
    ce_client = boto3.client("ce", region_name="us-east-1")

    # Cost Explorer's End date is exclusive.
    end_date_exclusive = end_date + timedelta(days=1)

    start = start_date.strftime("%Y-%m-%d")
    end = end_date_exclusive.strftime("%Y-%m-%d")

    print("\nRetrieving AWS billing information...")
    print(f"Billing period: {start_date} to {end_date}")

    # ---------------------------------------------------------
    # 1. TOTAL COST
    # ---------------------------------------------------------

    total_response = ce_client.get_cost_and_usage(
        TimePeriod={
            "Start": start,
            "End": end
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"]
    )

    total_cost = 0
    currency = "USD"

    for result in total_response["ResultsByTime"]:

        amount = float(
            result["Total"]["UnblendedCost"]["Amount"]
        )

        total_cost += amount

        currency = result["Total"]["UnblendedCost"]["Unit"]

    # ---------------------------------------------------------
    # 2. SERVICE-WISE COST
    # ---------------------------------------------------------

    service_response = ce_client.get_cost_and_usage(
        TimePeriod={
            "Start": start,
            "End": end
        },
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[
            {
                "Type": "DIMENSION",
                "Key": "SERVICE"
            }
        ]
    )

    service_costs = {}

    for result in service_response["ResultsByTime"]:

        for group in result["Groups"]:

            service_name = group["Keys"][0]

            amount = float(
                group["Metrics"]["UnblendedCost"]["Amount"]
            )

            if service_name in service_costs:
                service_costs[service_name] += amount
            else:
                service_costs[service_name] = amount

    # ---------------------------------------------------------
    # 3. DAILY COST
    # ---------------------------------------------------------

    daily_costs = []

    for result in total_response["ResultsByTime"]:

        date = result["TimePeriod"]["Start"]

        amount = float(
            result["Total"]["UnblendedCost"]["Amount"]
        )

        daily_costs.append(
            {
                "date": date,
                "cost": amount
            }
        )

    return total_cost, currency, service_costs, daily_costs


def generate_pdf(
    start_date,
    end_date,
    total_cost,
    currency,
    service_costs,
    daily_costs
):
    """
    Generate PDF billing report.
    """

    filename = (
        f"AWS_Billing_Report_"
        f"{start_date}_{end_date}.pdf"
    )

    document = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["Normal"]

    story = []

    # ---------------------------------------------------------
    # TITLE
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "AWS Billing Report",
            title_style
        )
    )

    story.append(Spacer(1, 20))

    # ---------------------------------------------------------
    # BILLING PERIOD
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Billing Information",
            heading_style
        )
    )

    billing_period = (
        f"{start_date} to {end_date}"
    )

    information_table = Table(
        [
            ["Billing Period", billing_period],
            ["Currency", currency],
            ["Total AWS Cost", f"{total_cost:.2f} {currency}"]
        ],
        colWidths=[150, 330]
    )

    information_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("PADDING", (0, 0), (-1, -1), 8)
            ]
        )
    )

    story.append(information_table)

    story.append(Spacer(1, 25))

    # ---------------------------------------------------------
    # SERVICE-WISE COST
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Service-wise Cost Breakdown",
            heading_style
        )
    )

    service_table_data = [
        ["Service", f"Cost ({currency})"]
    ]

    # Sort services from highest cost to lowest cost
    sorted_services = sorted(
        service_costs.items(),
        key=lambda item: item[1],
        reverse=True
    )

    for service, cost in sorted_services:

        service_table_data.append(
            [
                service,
                f"{cost:.2f}"
            ]
        )

    service_table = Table(
        service_table_data,
        colWidths=[350, 130],
        repeatRows=1
    )

    service_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.grey
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (1, -1),
                    "RIGHT"
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ]
        )
    )

    story.append(service_table)

    story.append(Spacer(1, 25))

    # ---------------------------------------------------------
    # DAILY COST
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Daily Cost Breakdown",
            heading_style
        )
    )

    daily_table_data = [
        ["Date", f"Cost ({currency})"]
    ]

    for daily in daily_costs:

        daily_table_data.append(
            [
                daily["date"],
                f"{daily['cost']:.2f}"
            ]
        )

    daily_table = Table(
        daily_table_data,
        colWidths=[350, 130],
        repeatRows=1
    )

    daily_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.grey
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (1, -1),
                    "RIGHT"
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ]
        )
    )

    story.append(daily_table)

    story.append(Spacer(1, 20))

    # ---------------------------------------------------------
    # FOOTER
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Report generated using AWS Cost Explorer API "
            "and Python Boto3.",
            normal_style
        )
    )

    document.build(story)

    return filename


def main():

    print("=" * 50)
    print("       AWS BILLING REPORT GENERATOR")
    print("=" * 50)

    # ---------------------------------------------------------
    # GET START DATE
    # ---------------------------------------------------------

    start_date = get_date_input(
        "\nEnter start date (YYYY-MM-DD): "
    )

    # ---------------------------------------------------------
    # GET END DATE
    # ---------------------------------------------------------

    while True:

        end_date = get_date_input(
            "Enter end date (YYYY-MM-DD): "
        )

        if end_date >= start_date:
            break

        print(
            "End date cannot be earlier than start date."
        )

    try:

        (
            total_cost,
            currency,
            service_costs,
            daily_costs
        ) = get_billing_data(
            start_date,
            end_date
        )

        # -----------------------------------------------------
        # DISPLAY TOTAL COST
        # -----------------------------------------------------

        print("\n" + "=" * 50)
        print("AWS BILLING SUMMARY")
        print("=" * 50)

        print(
            f"Billing Period : {start_date} to {end_date}"
        )

        print(
            f"Total AWS Cost : {total_cost:.2f} {currency}"
        )

        # -----------------------------------------------------
        # DISPLAY SERVICE COST
        # -----------------------------------------------------

        print("\nSERVICE-WISE COST")
        print("-" * 50)

        sorted_services = sorted(
            service_costs.items(),
            key=lambda item: item[1],
            reverse=True
        )

        for service, cost in sorted_services:

            print(
                f"{service:<40} "
                f"{cost:>10.2f} {currency}"
            )

        # -----------------------------------------------------
        # DISPLAY DAILY COST
        # -----------------------------------------------------

        print("\nDAILY COST")
        print("-" * 50)

        for daily in daily_costs:

            print(
                f"{daily['date']} : "
                f"{daily['cost']:.2f} {currency}"
            )

        # -----------------------------------------------------
        # GENERATE PDF
        # -----------------------------------------------------

        pdf_file = generate_pdf(
            start_date,
            end_date,
            total_cost,
            currency,
            service_costs,
            daily_costs
        )

        print("\n" + "=" * 50)
        print("PDF REPORT GENERATED SUCCESSFULLY")
        print("=" * 50)

        print(f"File: {pdf_file}")

    except Exception as error:

        print("\nERROR:")
        print(error)


if __name__ == "__main__":
    main()