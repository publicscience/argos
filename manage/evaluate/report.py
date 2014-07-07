import jinja2
import os

this_dir = os.path.dirname(os.path.realpath(__file__))
templateLoader = jinja2.FileSystemLoader(searchpath=this_dir+'/templates/')
templateEnv = jinja2.Environment(loader=templateLoader)

def build_report(template_name, filename, data):
    template = templateEnv.get_template(template_name +'.jinja')
    html = template.render(data)
    with open(this_dir+'/reports/' + filename + '.html', 'w') as report:
        report.write(html)
