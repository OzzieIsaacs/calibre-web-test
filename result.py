import os
from test.config_test import CALIBRE_WEB_PATH
from jinja2 import Template


DEFAULT_TEMPLATE = os.path.join(os.path.dirname(__file__), "report_template.html")


def load_template(template):
    """ Try to read a file from a given path, if file
        does not exist, load default one. """
    file = None
    try:
        if template:
            with open(template, "r") as f:
                file = f.read()
    except Exception as err:
        print("Error: Your Template wasn't loaded", err, "Loading Default Template", sep="\n")
    finally:
        if not file:
            with open(DEFAULT_TEMPLATE, "r") as f:
                file = f.read()
        return file


def render_html(template, **kwargs):
    template_file = load_template(template)
    if template_file:
        template = Template(template_file)
        return template.render(**kwargs)


def generate_reports(all_results):
    status_tags = ('success', 'danger', 'warning', 'info')
    header_info = all_results[2]
    html_file = render_html(
        DEFAULT_TEMPLATE,
        title=all_results[1],
        header_info=header_info,
        results=all_results[4],
        status_tags=status_tags,
        summaries=all_results[4],
        environ=all_results[5]
    )
    report_name_body = "Calibre-Web TestSummary_Linux.html"
    return generate_file(report_name_body, html_file)

def generate_file(report_name, report):
    """ Generate the report file in the given path. """

    path_file = os.path.abspath(os.path.join(CALIBRE_WEB_PATH, "test", report_name))
    with open(path_file, 'w') as report_file:
        report_file.write(report)
    return path_file


def generate_html(all_results):
    return generate_reports(all_results)