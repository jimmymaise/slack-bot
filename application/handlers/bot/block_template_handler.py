from pathlib import Path

from jinja2 import Template

from application.utils.common import Dict2Obj


class BlockTemplateHandler:
    def __init__(self, template_folder_path):
        self.template_folder_path = template_folder_path

    def get_object_templates(self):
        file_paths = Path(self.template_folder_path).glob('*')
        template_dict = {}
        for file_path in file_paths:
            with open(file_path) as file:
                file_name_without_ext = file_path.with_suffix('').name
                template_dict[file_name_without_ext] = Template(file.read()).render

        return Dict2Obj(template_dict)
