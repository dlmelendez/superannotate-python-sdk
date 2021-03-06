"""
Module which will run converters and convert from
superannotate annotation format to other annotation formats
"""
import copy
import glob
import json
import logging
import os
import shutil
import sys

import numpy as np
from pathlib import Path
from .converters.converters import Converter

from ..exceptions import SABaseException

import tempfile

logger = logging.getLogger("superannotate-python-sdk")


def _split_json(input_dir):
    temp_path = Path(tempfile.mkdtemp()) / 'WebApp'
    temp_path.mkdir()
    json_data = json.load(open(input_dir / "annotations.json"))
    images = json_data.keys()
    for img in images:
        annotations = json_data[img]
        objects = []
        for annot in annotations:
            if annot["type"] != "meta":
                objects.append(annot)
        with open(temp_path / (img + "___objects.json"), "w") as fw:
            json.dump(objects, fw, indent=2)
        shutil.copy(input_dir / "images" / img, temp_path / img)
    (temp_path / "classes").mkdir()
    shutil.copy(
        input_dir / "classes.json", temp_path / "classes" / "classes.json"
    )

    return temp_path


def _load_files(path_to_imgs, task, ptype):
    suffix = None
    if ptype == "Pixel":
        suffix = '___pixel.json'
    else:
        suffix = '___objects.json'

    orig_images = glob.glob(os.path.join(path_to_imgs, '*'))
    orig_images = [
        x for x in orig_images if not os.path.isdir(x) and
        '___' not in x.split('.')[-2] and "mapper.json" not in x
    ]
    all_files = None
    if task == 'keypoint_detection':
        all_files = np.array([(fname, fname + suffix) for fname in orig_images])

    elif ptype == 'Pixel':
        all_files = np.array(
            [
                (fname, fname + suffix, fname + '___save.png')
                for fname in orig_images
            ]
        )
    elif ptype == 'Vector':
        all_files = np.array([(fname, fname + suffix) for fname in orig_images])

    return all_files


def _move_files(data_set, src):
    train_path = src / 'image_set'
    if data_set is not None:
        for tup in data_set:
            for i in tup:
                shutil.copy(i, train_path / Path(i).name)


def _create_classes_mapper(imgs, classes_json):
    classes = {}
    j_data = json.load(open(classes_json))
    for instance in j_data:
        if 'id' not in instance:
            continue
        classes[instance['name']] = instance['id']

    with open(imgs / 'image_set' / 'classes_mapper.json', 'w') as fp:
        json.dump(classes, fp)


def export_from_sa(args):
    """
    :param args: All arguments that will be used during convertion.
    :type args: Namespace
    """
    if args.platform == "Desktop":
        args.input_dir = _split_json(args.input_dir)

    data_set = None

    (args.output_dir / "image_set").mkdir(parents=True, exist_ok=True)

    try:
        _create_classes_mapper(
            args.output_dir, args.input_dir / 'classes' / 'classes.json'
        )
    except Exception as e:
        _create_classes_mapper(args.input_dir, args.output_dir)

    data_set = _load_files(args.input_dir, args.task, args.project_type)
    _move_files(data_set, args.output_dir)

    args.__dict__.update(
        {
            'direction': 'to',
            'export_root': args.output_dir / 'image_set'
        }
    )
    converter = Converter(args)

    if data_set is not None:
        converter.strategy.set_dataset_name(args.dataset_name)
        converter.convert_from_sa()

    if args.platform == "Desktop":
        shutil.rmtree(args.input_dir)
    image_set_failed = copy.deepcopy(converter.strategy.failed_conversion_cnt)

    logger.info('Conversion completed successfully')
    return image_set_failed
