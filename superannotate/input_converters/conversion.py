"""
Main module for input converters
"""
from argparse import Namespace
from pathlib import Path

from ..exceptions import SABaseException
from .export_from_sa_conversions import export_from_sa
from .import_to_sa_conversions import import_to_sa
from .sa_conversion import (
    sa_convert_platform, sa_convert_project_type, split_coco
)

AVAILABLE_PLATFORMS = ["Desktop", "Web"]

ALLOWED_TASK_TYPES = [
    'panoptic_segmentation', 'instance_segmentation', 'keypoint_detection',
    'object_detection', 'vector_annotation'
]

ALLOWED_PROJECT_TYPES = ['Pixel', 'Vector']

ALLOWED_ANNOTATION_IMPORT_FORMATS = {
    'COCO':
        [
            ('Pixel', 'panoptic_segmentation'),
            ('Pixel', 'instance_segmentation'),
            ('Vector', 'keypoint_detection'),
            ('Vector', 'instance_segmentation'), ('Vector', 'object_detection')
        ],
    'VOC':
        [
            ('Vector', 'object_detection'), ('Vector', 'instance_segmentation'),
            ('Pixel', 'instance_segmentation')
        ],
    'LabelBox':
        [
            ('Vector', 'object_detection'), ('Vector', 'instance_segmentation'),
            ('Vector', 'vector_annotation')
        ],
    'DataLoop':
        [
            ('Vector', 'object_detection'), ('Vector', 'instance_segmentation'),
            ('Vector', 'vector_annotation')
        ],
    'Supervisely':
        [
            ('Vector', 'vector_annotation'), ('Vector', 'object_detection'),
            ('Vector', 'instance_segmentation'),
            ('Pixel', 'instance_segmentation'),
            ('Vector', 'keypoint_detection')
        ],
    'VoTT':
        [
            ('Vector', 'object_detection'), ('Vector', 'instance_segmentation'),
            ('Vector', 'vector_annotation')
        ],
    'SageMaker':
        [('Pixel', 'instance_segmentation'), ('Vector', 'object_detection')],
    'VGG':
        [
            ('Vector', 'object_detection'), ('Vector', 'instance_segmentation'),
            ('Vector', 'vector_annotation')
        ],
    'GoogleCloud': [('Vector', 'object_detection')],
    'YOLO': [('Vector', 'object_detection')]
}

ALLOWED_ANNOTATION_EXPORT_FORMATS = {
    'COCO':
        [
            ('Pixel', 'panoptic_segmentation'),
            ('Pixel', 'instance_segmentation'),
            ('Vector', 'instance_segmentation'),
            ('Vector', 'keypoint_detection'), ('Vector', 'object_detection')
        ]
}


def _passes_sanity_checks(args):
    if not isinstance(args.input_dir, (str, Path)):
        raise SABaseException(
            0, "'input_dir' should be 'str' or 'Path' type, not '%s'" %
            (type(args.input_dir))
        )

    if not isinstance(args.output_dir, (str, Path)):
        raise SABaseException(
            0, "'output_dir' should be 'str' or 'Path' type, not {}".format(
                type(args.output_dir)
            )
        )

    if args.dataset_format not in ALLOWED_ANNOTATION_IMPORT_FORMATS.keys():
        raise SABaseException(
            0, "'%s' converter doesn't exist. Possible candidates are '%s'" %
            (args.dataset_format, ALLOWED_ANNOTATION_IMPORT_FORMATS.keys())
        )

    if not isinstance(args.dataset_name, str):
        raise SABaseException(
            0, "'dataset_name' should be 'str' type, not {}".format(
                type(args.dataset_name)
            )
        )

    if args.project_type not in ALLOWED_PROJECT_TYPES:
        raise SABaseException(
            0, "Please enter valid project type: 'Pixel' or 'Vector'"
        )

    if args.task not in ALLOWED_TASK_TYPES:
        raise SABaseException(
            0, "Please enter valid task '%s'" % (ALLOWED_TASK_TYPES)
        )

    if 'platform' in args:
        if args.platform not in AVAILABLE_PLATFORMS:
            raise SABaseException(
                0, "Please enter valid platform: 'Desktop' or 'Web'"
            )

    if args.project_type == "Pixel" and args.platform == "Desktop":
        raise SABaseException(
            0,
            "Sorry, but Desktop Application doesn't support 'Pixel' projects."
        )


def _passes_converter_sanity(args, direction):
    converter_values = (args.project_type, args.task)
    test_passed = False
    if direction == 'import':
        if converter_values in ALLOWED_ANNOTATION_IMPORT_FORMATS[
            args.dataset_format]:
            test_passed = True
    else:
        if converter_values in ALLOWED_ANNOTATION_EXPORT_FORMATS[
            args.dataset_format]:
            test_passed = True

    if not test_passed:
        raise SABaseException(
            0,
            "Please enter valid converter values. You can check available candidates in the documentation (https://superannotate.readthedocs.io/en/stable/index.html)."
        )


def export_annotation_format(
    input_dir,
    output_dir,
    dataset_format,
    dataset_name,
    project_type="Vector",
    task="object_detection",
    platform="Web",
):
    """Converts SuperAnnotate annotation formate to the other annotation formats. Currently available (project_type, task) combinations for converter
    presented below:

    ==============  ======================
             From SA to COCO
    --------------------------------------
     project_type           task
    ==============  ======================
    Pixel           panoptic_segmentation
    Pixel           instance_segmentation
    Vector          instance_segmentation
    Vector          object_detection
    Vector          keypoint_detection
    ==============  ======================

    :param input_dir: Path to the dataset folder that you want to convert.
    :type input_dir: str
    :param output_dir: Path to the folder, where you want to have converted dataset.
    :type output_dir: str
    :param dataset_format: One of the formats that are possible to convert. Available candidates are: ["COCO"]
    :type dataset_format: str
    :param dataset_name: Will be used to create json file in the output_dir.
    :type dataset_name: str
    :param project_type: SuperAnnotate project type is either 'Vector' or 'Pixel' (Default: 'Vector')
                         'Vector' project creates <image_name>___objects.json for each image.
                         'Pixel' project creates <image_name>___pixel.jsons and <image_name>___save.png annotation mask for each image.
    :type project_type: str
    :param task: Task can be one of the following: ['panoptic_segmentation', 'instance_segmentation',
                 'keypoint_detection', 'object_detection']. (Default: "object_detection").
                 'keypoint_detection' can be used to converts keypoints from/to available annotation format.
                 'panoptic_segmentation' will use panoptic mask for each image to generate bluemask for SuperAnnotate annotation format and use bluemask to generate panoptic mask for invert conversion. Panoptic masks should be in the input folder.
                 'instance_segmentation' 'Pixel' project_type converts instance masks and 'Vector' project_type generates bounding boxes and polygons from instance masks. Masks should be in the input folder if it is 'Pixel' project_type.
                 'object_detection' converts objects from/to available annotation format
    :type task: str
    :param platform: SuperAnnotate has both 'Web' and 'Desktop' platforms. Choose from which one you are converting. (Default: "Web")
    :type platform: str

    """

    if isinstance(input_dir, str):
        input_dir = Path(input_dir)
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    args = Namespace(
        input_dir=input_dir,
        output_dir=output_dir,
        dataset_format=dataset_format,
        dataset_name=dataset_name,
        project_type=project_type,
        task=task,
        platform=platform,
    )

    _passes_sanity_checks(args)
    _passes_converter_sanity(args, 'export')

    export_from_sa(args)


def import_annotation_format(
    input_dir,
    output_dir,
    dataset_format,
    dataset_name,
    project_type="Vector",
    task="object_detection",
    platform="Web",
    images_root=''
):
    """Converts other annotation formats to SuperAnnotate annotation format. Currently available (project_type, task) combinations for converter
    presented below:

    ==============  ======================
             From COCO to SA
    --------------------------------------
     project_type           task
    ==============  ======================
    Pixel           panoptic_segmentation
    Pixel           instance_segmentation
    Vector          instance_segmentation
    Vector          object_detection
    Vector          keypoint_detection
    ==============  ======================

    ==============  ======================
             From VOC to SA
    --------------------------------------
     project_type           task
    ==============  ======================
    Pixel           instance_segmentation
    Vector          instance_segmentation
    Vector          object_detection
    ==============  ======================

    ==============  ======================
           From LabelBox to SA
    --------------------------------------
     project_type           task
    ==============  ======================
    Vector          object_detection
    Vector          instance_segmentation
    Vector          vector_annotation
    ==============  ======================

    ==============  ======================
           From DataLoop to SA
    --------------------------------------
     project_type           task
    ==============  ======================
    Vector          object_detection
    Vector          instance_segmentation
    Vector          vector_annotation
    ==============  ======================

    ==============  ======================
           From Supervisely to SA
    --------------------------------------
     project_type           task
    ==============  ======================
    Vector          object_detection
    Vector          keypoint_detection
    Vector          vector_annotation
    Vector          instance_segmentation
    Pixel           instance_segmentation
    ==============  ======================

    ==============  ======================
           From VoTT to SA
    --------------------------------------
     project_type           task
    ==============  ======================
    Vector          instance_segmentation
    Vector          object_detection
    Vector          vector_annotation
    ==============  ======================

    ==============  ======================
           From SageMaker to SA
    --------------------------------------
     project_type           task
    ==============  ======================
    Pixel           instance_segmentation
    Vector          objcet_detection
    ==============  ======================

    ==============  ======================
           From VGG to SA
    --------------------------------------
     project_type           task
    ==============  ======================
    Vector          instance_segmentation
    Vector          object_detection
    Vector          vector_annotation
    ==============  ======================

    ==============  ======================
           From GoogleCloud to SA
    --------------------------------------
     project_type           task
    ==============  ======================
    Vector          object_detection
    ==============  ======================

    ==============  ======================
           From YOLO to SA
    --------------------------------------
     project_type           task
    ==============  ======================
    Vector          object_detection
    ==============  ======================

    :param input_dir: Path to the dataset folder that you want to convert.
    :type input_dir: str
    :param output_dir: Path to the folder, where you want to have converted dataset.
    :type output_dir: str
    :param dataset_format: Annotation format to convert SuperAnnotate annotation format. Available candidates are: ["COCO", "VOC", "LabelBox", "DataLoop",
                        "Supervisely", 'VGG', 'YOLO', 'SageMake', 'VoTT', 'GoogleCloud']
    :type dataset_format: str
    :param dataset_name: Name of the json file in the input_dir, which should be converted.
    :type dataset_name: str
    :param project_type: SuperAnnotate project type is either 'Vector' or 'Pixel' (Default: 'Vector')
                         'Vector' project creates <image_name>___objects.json for each image.
                         'Pixel' project creates <image_name>___pixel.jsons and <image_name>___save.png annotation mask for each image.
    :type project_type: str
    :param task: Task can be one of the following: ['panoptic_segmentation', 'instance_segmentation',
                 'keypoint_detection', 'object_detection', 'vector_annotation']. (Default: "object_detection").
                 'keypoint_detection' can be used to converts keypoints from/to available annotation format.
                 'panoptic_segmentation' will use panoptic mask for each image to generate bluemask for SuperAnnotate annotation format and use bluemask to generate panoptic mask for invert conversion. Panoptic masks should be in the input folder.
                 'instance_segmentation' 'Pixel' project_type converts instance masks and 'Vector' project_type generates bounding boxes and polygons from instance masks. Masks should be in the input folder if it is 'Pixel' project_type.
                 'object_detection' converts objects from/to available annotation format
                 'vector_annotation' can be used to convert all annotations (point, ellipse, circule, cuboid and etc) to SuperAnnotate vector project.
    :param platform: SuperAnnotate has both 'Web' and 'Desktop' platforms. Choose to which platform you want convert. (Default: "Web")
    :type platform: str
    :param images_root: Additonal path to images directory in input_dir
    :type platform: str

    """

    if isinstance(input_dir, str):
        input_dir = Path(input_dir)
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    args = Namespace(
        input_dir=input_dir,
        output_dir=output_dir,
        dataset_format=dataset_format,
        dataset_name=dataset_name,
        project_type=project_type,
        task=task,
        platform=platform,
        images_root=images_root
    )

    _passes_sanity_checks(args)
    _passes_converter_sanity(args, 'import')

    import_to_sa(args)


def convert_platform(input_dir, output_dir, input_platform):
    """ Converts SuperAnnotate input file structure from one platform too another.

    :param input_dir: Path to the dataset folder that you want to convert.
    :type input_dir: str or PathLike
    :param output_dir: Path to the folder where you want to have converted files.
    :type output_dir: str or PathLike
    :param input_platform: Original platform format type
    :type input_platform: str

    """
    param_info = [
        (input_dir, 'input_dir', (str, Path)),
        (output_dir, 'output_dir', (str, Path)),
        (input_platform, 'input_platform', str),
    ]
    for param in param_info:
        type_sanity(param[0], param[1], param[2])

    if input_platform not in AVAILABLE_PLATFORMS:
        raise SABaseException(
            0, "Please enter valid platform: 'Desktop' or 'Web'"
        )

    if isinstance(input_dir, str):
        input_dir = Path(input_dir)
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    sa_convert_platform(input_dir, output_dir, input_platform)


def convert_project_type(input_dir, output_dir):
    """ Converts SuperAnnotate 'Vector' project type to 'Pixel' or reverse.

    :param input_dir: Path to the dataset folder that you want to convert.
    :type input_dir: str or PathLike
    :param output_dir: Path to the folder where you want to have converted files.
    :type output_dir: str or PathLike

    """
    param_info = [
        (input_dir, 'input_dir', (str, Path)),
        (output_dir, 'output_dir', (str, Path)),
    ]
    for param in param_info:
        type_sanity(param[0], param[1], param[2])

    if isinstance(input_dir, str):
        input_dir = Path(input_dir)
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    sa_convert_project_type(input_dir, output_dir)


def coco_split_dataset(
    coco_json_path, image_dir, output_dir, dataset_list_name, ratio_list
):
    """ Splits COCO dataset to few datsets.

    :param coco_json_path: Path to main COCO JSON dataset, which should be splitted.
    :type coco_json_path: str or PathLike
    :param image_dir: Path to all images in the original dataset.
    :type coco_json_path: str or PathLike
    :param coco_json_path: Path to the folder where you want to output splitted COCO JSON files.
    :type coco_json_path: str or PathLike
    :param dataset_list_name: List of dataset names.
    :type dataset_list_name: List
    :param ratio_list: List of ratios for each splitted dataset.
    :type ratio_list: List
    """
    param_info = [
        (coco_json_path, 'coco_json_path', (str, Path)),
        (image_dir, 'image_dir', (str, Path)),
        (output_dir, 'output_dir', (str, Path)),
        (dataset_list_name, 'dataset_list_name', list),
        (ratio_list, 'ratio_list', list)
    ]
    for param in param_info:
        type_sanity(param[0], param[1], param[2])

    for dataset_name in dataset_list_name:
        if not isinstance(dataset_name, (str, Path)):
            raise SABaseException(
                0,
                "'dataset_list_name' member should be 'str' or 'Path' type, not '%s'"
                % (type(dataset_name))
            )

    for ratio in ratio_list:
        if not isinstance(ratio, (int, float)):
            raise SABaseException(
                0,
                "'ratio_list' member should be 'int' or 'float' type, not '%s'"
                % (type(ratio))
            )

    if sum(ratio_list) != 100:
        raise SABaseException(0, "Sum of 'ratio_list' members must be '100'")

    if len(dataset_list_name) != len(ratio_list):
        raise SABaseException(
            0, "'dataset_list_name' and 'ratio_list' should have same lenght"
        )

    if isinstance(image_dir, str):
        image_dir = Path(image_dir)
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    split_coco(
        coco_json_path, image_dir, output_dir, dataset_list_name, ratio_list
    )


def type_sanity(var, var_name, var_type):
    if not isinstance(var, var_type):
        raise SABaseException(
            0, "'{}' should be '{}' type, not '{}'".format(
                var_name, var_type, type(var)
            )
        )
