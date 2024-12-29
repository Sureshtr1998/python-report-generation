from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from flask import Flask, send_file
import subprocess
import tempfile
from assets.data.data_module import data
# import mysql.connector

# config = {
#     'user': 'saas_root',
#     'password': 'bh57FR!2&jkil',
#     'host': 'saas-development.ckmfwzzuuxwx.ap-south-1.rds.amazonaws.com',
#     'database': 'sc_saas',
# }


# connection = mysql.connector.connect(**config)


# if connection.is_connected():
#     print("Connected to MySQL database")
#     cursor = connection.cursor()
#     query = "SELECT * FROM reporting_report_template"
#     query1 = """
#                 SELECT * FROM reporting_report_template
#                 JOIN FETCH reporting_question_template
#                 WHERE template_id = BRSR_cefj39
#             """
#     query2 = """
#                 SELECT * FROM reporting_report_instance
#                 JOIN FETCH reporting_report_answers
#                 WHERE report_id = GRI_ya21ka_87_1695299959266
#             """
#     cursor.execute(query)

#     print(cursor.fetchall())
#     for row in cursor.fetchall():
#         print(row)
#     connection.close()
# cursor.close()

# Perform database operations here

# Close the connection when done
# connection.close()

app = Flask(__name__)

env = Environment(loader=FileSystemLoader("templates"))

template = env.get_template("template.html")

output_data = {"answers": []}
rows_per_item = 5

# For splitting table
for answer in data["answers"]:
    if answer["type"] == "STATIC_TABLE" or answer["type"] == "DYNAMIC_TABLE":
        for i in range(0, len(answer["details"]["rows"][0]), rows_per_item):
            new_item = {
                "id": f"new-table-{len(output_data['answers']) + 1}",
                "type": "STATIC_TABLE",
                "details": {
                    "title": answer["details"]["title"],
                    "header": answer["details"]["header"],
                    "rows": [
                        answer["details"]["rows"][j][i:i + rows_per_item]
                        for j in range(len(answer["details"]["rows"]))
                    ]
                }
            }
            output_data["answers"].append(new_item)
    else:
        output_data["answers"].append(answer)

data["answers"] = output_data["answers"]

property_data = {"answers": []}
for answer in data["answers"]:
    if answer["type"] == "STATIC_TABLE" or answer["type"] == "DYNAMIC_TABLE":
        if "details" in answer and "rows" in answer["details"]:
            span_data = 0
            start_span = 0
            for row_index, row in enumerate(answer["details"]["rows"]):
                for i, cell in enumerate(row):
                    cell_details = cell["details"]
                    cell_type = cell_details.get("type")
                    if cell_type == "HEADER":
                        cell_details["isBold"] = True
                    if "value" in cell_details and "Current Financial Year" in cell_details["value"]:
                        cell_details["color"] = "#243c8d"
                        cell_details["isBold"] = True
                        if cell_details["colSpan"] == 1:
                            cell_details["borderB"] = "5px solid #243c8d"
                            span_data = 1
                            start_span = 1
                        else:
                            span_data = cell_details["colSpan"]
                            start_span = i
                    if span_data > 1 and 0 <= i - start_span < span_data and row_index == 1:
                        cell_details["color"] = "#243c8d"
                        cell_details["isBold"] = True
                        cell_details["borderB"] = "5px solid #243c8d"
                    if 0 <= i - start_span < span_data:
                        cell_details["bgndColor"] = "#e9e8f6"

    property_data["answers"].append(answer)

data["answers"] = property_data["answers"]

# Get the current date
current_date = datetime.now()

# Define a function to get the ordinal suffix (e.g., "st", "nd", "rd", "th")


def ordinal(number):
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return suffix

# Function to generate the Table of Contents with page numbers


# Format the date as "Day Month, Year"
formatted_date = current_date.strftime(f"%d{ordinal(current_date.day)} %B, %Y")


data["currentDate"] = formatted_date
rendered_template = template.render(data)

html_filename = "output/my_report.html"
with open(html_filename, "w", encoding="utf-8") as html_file:
    html_file.write(rendered_template)

pdf_filename = "output/my_pdf.pdf"

# subprocess.run(['wkhtmltopdf', '--footer-center',
#                'Page [page]', html_filename, pdf_filename])

header_template = env.get_template("header.html")
header_template = header_template.render(data)

footer_template = env.get_template("footer.html")
footer_template = footer_template.render(data)

# Create temporary files for header and footer
with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".html") as header_tempfile:
    header_tempfile.write(header_template)

with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".html") as footer_tempfile:
    footer_tempfile.write(footer_template)


xslfile = "C:/Users/Suresh/Desktop/Report Python/custom-toc.xsl"
subprocess.run([
    'wkhtmltopdf',
    '--header-html', header_tempfile.name,
    '--footer-html', footer_tempfile.name,
    '--footer-spacing', '5',
    '--header-spacing', '5',
    '--page-offset', '0',
    'toc',
    '--xsl-style-sheet', "custom-toc.xsl",
    html_filename,
    pdf_filename
])


@ app.route('/download_pdf')
def download_pdf():
    return send_file(pdf_filename, as_attachment=True)


if __name__ == '__main__':
    app.run()
