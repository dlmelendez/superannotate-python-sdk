import os
import json

from .supervisely_converter import SuperviselyConverter
from .supervisely_to_sa_vector import (
    supervisely_to_sa, supervisely_instance_segmentation_to_sa_vector,
    supervisely_object_detection_to_sa_vector,
    supervisely_keypoint_detection_to_sa_vector
)
from .supervisely_to_sa_pixel import supervisely_instance_segmentation_to_sa_pixel


class SuperviselyObjectDetectionStrategy(SuperviselyConverter):
    name = "ObjectDetection converter"

    def __init__(self, args):
        super().__init__(args)
        self.__setup_conversion_algorithm()

    def __setup_conversion_algorithm(self):
        if self.direction == "to":
            raise NotImplementedError("Doesn't support yet")
        else:
            if self.project_type == "Vector":
                if self.task == 'vector_annotation':
                    self.conversion_algorithm = supervisely_to_sa
                elif self.task == 'object_detection':
                    self.conversion_algorithm = supervisely_object_detection_to_sa_vector
                elif self.task == 'instance_segmentation':
                    self.conversion_algorithm = supervisely_instance_segmentation_to_sa_vector
                elif self.task == 'keypoint_detection':
                    self.conversion_algorithm = supervisely_keypoint_detection_to_sa_vector
            elif self.project_type == "Pixel":
                if self.task == 'instance_segmentation':
                    self.conversion_algorithm = supervisely_instance_segmentation_to_sa_pixel

    def __str__(self):
        return '{} object'.format(self.name)

    def to_sa_format(self):
        id_generator = self._make_id_generator()
        sa_classes, classes_id_map = self._create_sa_classes(
            self.export_root, id_generator
        )
        json_files = []
        if self.dataset_name != '':
            json_files.append(
                self.export_root / 'ds' / 'ann' / (self.dataset_name + '.json')
            )
        else:
            files_gen = (self.export_root / 'ds' / 'ann').glob('*')
            json_files = [file for file in files_gen]

        if self.conversion_algorithm.__name__ == 'supervisely_keypoint_detection_to_sa_vector':
            meta_json = json.load(open(self.export_root / 'meta.json'))
            sa_jsons = self.conversion_algorithm(
                json_files, classes_id_map, meta_json
            )
        elif self.conversion_algorithm.__name__ == 'supervisely_instance_segmentation_to_sa_pixel':
            sa_jsons = self.conversion_algorithm(
                json_files, classes_id_map, self.output_dir
            )
        else:
            sa_jsons = self.conversion_algorithm(json_files, classes_id_map)
        self.dump_output(sa_classes, sa_jsons)

    def _make_id_generator(self):
        cur_id = 0
        while True:
            cur_id += 1
            yield cur_id

    def _create_sa_classes(self, input_dir, id_generator):
        classes_json = json.load(open(self.export_root / 'meta.json'))

        attributes = []
        for tag in classes_json['tags']:
            id_ = next(id_generator)
            attributes.append({'id': id_, 'name': tag['name']})

        classes_id_map = {}
        classes_loader = []
        for class_ in classes_json['classes']:
            id_ = next(id_generator)
            group_id = next(id_generator)
            group_name = 'attribute_group_' + str(group_id)
            classes_id_map[class_['title']] = {
                'id': id_,
                'attr_group':
                    {
                        'id': group_id,
                        'group_name': group_name,
                        'attributes': {}
                    }
            }
            for attribute in attributes:
                attribute['group_id'] = group_id
                attribute['groupName'] = group_name
                classes_id_map[class_['title']]['attr_group']['attributes'][
                    attribute['name']] = attribute['id']

            attr_group = {
                'id':
                    id_,
                'name':
                    class_['title'],
                'color':
                    class_['color'],
                'attribute_groups':
                    [
                        {
                            'id': group_id,
                            'class_id': id_,
                            'name': group_name,
                            'is_multiselect': 1,
                            'attributes': attributes
                        }
                    ]
            }
            classes_loader.append(attr_group)
        return classes_loader, classes_id_map
