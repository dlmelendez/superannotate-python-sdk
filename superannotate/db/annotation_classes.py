import io
import json
import logging
from pathlib import Path

import boto3

from ..api import API
from ..exceptions import SABaseException

logger = logging.getLogger("superannotate-python-sdk")

_api = API.get_instance()


def create_annotation_class(project, name, color, attribute_groups=None):
    """Create annotation class in project

    :param project: project metadata
    :type project: dict
    :param name: name for the class
    :type name: str
    :param color: RGB hex color value, e.g, "#FFFFAA"
    :type color: str
    :param attribute_groups: example:
     [ { "name": "tall", "is_multiselect": 0, "attributes": [ { "name": "yes" }, { "name": "no" } ] },
        { "name": "age", "is_multiselect": 0, "attributes": [ { "name": "young" }, { "name": "old" } ] } ]
    :type attribute_groups: list of dicts

    :return: new class metadata
    :rtype: dict
    """
    team_id, project_id = project["team_id"], project["id"]
    logger.info(
        "Creating class in project ID %s with name %s", project_id, name
    )
    params = {
        'team_id': team_id,
        'project_id': project_id,
    }
    data = {
        "classes":
            [
                {
                    "name":
                        name,
                    "color":
                        color,
                    "attribute_groups":
                        attribute_groups if attribute_groups is not None else []
                }
            ]
    }
    response = _api.send_request(
        req_type='POST', path='/classes', params=params, json_req=data
    )
    if not response.ok:
        raise SABaseException(
            response.status_code, "Couldn't create class " + response.text
        )
    res = response.json()
    new_class = res[0]
    return new_class


def create_annotation_classes_from_classes_json(
    project, path_to_classes_json, from_s3_bucket=None
):
    """ Create annotation classes in project from a SuperAnnotate format classes.json

    :param project: project metadata
    :type project: dict
    :param path_to_classes_json: path to the JSON file
    :type path_to_classes_json: Pathlike (str or Path)
    :param from_s3_bucket: AWS S3 bucket to use. If None then path_to_classes_json is in local filesystem
    :type from_s3_bucket: str

    :return: Old classId to new classId translation dict
    :rtype: dict
    """
    project_id = project["id"]
    logger.info(
        "Creating classes in project ID %s from %s.", project_id,
        path_to_classes_json
    )
    old_class_id_to_new_conversion = {}
    if from_s3_bucket is None:
        classes = json.load(open(path_to_classes_json))
    else:
        from_session = boto3.Session()
        from_s3 = from_session.resource('s3')
        file = io.BytesIO()
        from_s3_object = from_s3.Object(from_s3_bucket, path_to_classes_json)
        from_s3_object.download_fileobj(file)
        file.seek(0)
        classes = json.load(file)

    for cl in classes:
        new_class = create_annotation_class(
            project, cl["name"], cl["color"], cl["attribute_groups"]
        )
        old_id = cl["id"]
        new_id = new_class["id"]
        old_class_id_to_new_conversion[old_id] = new_id
    return old_class_id_to_new_conversion


def search_annotation_classes(project, name_prefix=None):
    """Search annotation classes by name_prefix (case-insensitive)

    :param project: project metadata
    :type project: dict
    :param name_prefix: name prefix for search. If None all annotation classes
     will be returned
    :type name_prefix: str

    :return: annotation classes of the project
    :rtype: list of dicts
    """
    result_list = []
    team_id, project_id = project["team_id"], project["id"]
    params = {'team_id': team_id, 'project_id': project_id, 'offset': 0}
    if name_prefix is not None:
        params['name'] = name_prefix
    while True:
        response = _api.send_request(
            req_type='GET', path='/classes', params=params
        )
        if not response.ok:
            raise SABaseException(
                response.status_code, "Couldn't search classes " + response.text
            )
        res = response.json()
        result_list += res["data"]
        new_len = len(result_list)
        # for r in result_list:
        #     print(r)
        if res["count"] <= new_len:
            break
        params["offset"] = new_len
    return result_list


def download_annotation_classes_json(project, folder):
    """Download classes.json to folder

    :param project: project metadata
    :type project: dict
    :param folder: folder to download to
    :type folder: Pathlike (str or Path)

    :return: path of the download file
    :rtype: str
    """
    project_id = project["id"]
    logger.info(
        "Downloading classes.json from project ID %s to folder %s.", project_id,
        folder
    )
    clss = search_annotation_classes(project)
    filepath = Path(folder) / "classes.json"
    json.dump(clss, open(filepath, "w"), indent=2)
    return str(filepath)