
import pandas as pd
import os
import shutil
import yaml
from function import find_max_date
from dataclean import calculate_change_data, format_table_data, generate_merge_chart
from report_main import generate_weekly_report
from mail_main import create_mail_table
from web_main import update_pages

data_path = '../Data/GetData/WeeklyReport'
# create temp folder
os.makedirs("./temp", exist_ok=True)

# read data
df = pd.read_csv('../Data/AllData/WeeklyReport/latest.csv', encoding='utf-8')
df['Date'] = pd.to_datetime(df['Date'])
# using newest data
analysis_date = df['Date'].max()
analysis_YearMonth = analysis_date.strftime("%Y %B")
analysis_MonthYear = analysis_date.strftime("%B %Y")

change_data = calculate_change_data(df, analysis_date)
diseases_order, diseases_order_cn = generate_merge_chart(change_data, original_file=f'{data_path}/{analysis_YearMonth}.csv')
table_data = format_table_data(change_data, analysis_date)
table_data['Diseases'] = pd.Categorical(table_data['Diseases'], categories=diseases_order + ['Total'], ordered=True)
table_data = table_data.sort_values('Diseases')
table_data = table_data.reset_index(drop=True)
diseases = table_data['Diseases'].tolist()
print(diseases_order)

# get environment from model.yml
with open('../model.yml', 'r') as file:
    config_dict = yaml.safe_load(file)
for section, subsections in config_dict.items():
    for key, subvalues in subsections.items():
        for subkey, value in subvalues.items():
            if isinstance(value, str):
                env_var_name = f"{section.upper()}_{key.upper()}_{subkey.upper()}"
                os.environ[env_var_name] = value

# create mail table
create_mail_table(table_data, analysis_YearMonth)

# # generate weekly report, history, mail content and web information
generate_weekly_report(df, table_data, diseases_order, analysis_date, analysis_YearMonth, analysis_MonthYear)

# moving report pages
destination_folder = f"../Report/page/{analysis_YearMonth}/"
os.makedirs(destination_folder, exist_ok=True)
report_files = ['cover_summary', 'cover'] + diseases_order
for disease in diseases_order:
    source_file = f"./temp/{disease}.pdf"
    destination_file = os.path.join(destination_folder, f"{disease}.pdf")
    shutil.move(source_file, destination_file)

# moving report file
shutil.move('./temp/Report.pdf', f'../Report/report {analysis_YearMonth}.pdf')

# remove temp folder
shutil.rmtree('./temp')

# update latest
analysis_date_max = df['Date'].max()
if analysis_date == analysis_date_max:
    shutil.copyfile(f'../Report/report {analysis_YearMonth}.pdf', '../Report/report latest.pdf')
    shutil.copyfile(f'../Report/table/{analysis_YearMonth}.md', '../Report/table/latest.md')
    shutil.copyfile(f'../Report/mail/{analysis_YearMonth}.md', '../Report/mail/latest.md')
    shutil.copytree(f'../Report/page/{analysis_YearMonth}', '../Report/page/latest', dirs_exist_ok=True)
    shutil.copytree(f'../Report/history/{analysis_YearMonth}', '../Report/history/latest', dirs_exist_ok=True)
    # update pages
    print(diseases_order_cn)
    [update_pages(diseases_order, diseases_order_cn, i, df, analysis_MonthYear) for i in range(len(diseases_order))]