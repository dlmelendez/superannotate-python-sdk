from pathlib import Path
import superannotate as sa


def test_vott_convert_object(tmpdir):
    input_dir = Path(
        "tests"
    ) / "converter_test" / "VoTT" / "input" / "toSuperAnnotate"
    out_dir = Path(tmpdir) / "object_detection"
    sa.import_annotation_format(
        input_dir, out_dir, "VoTT", "", "Vector", "object_detection", "Web"
    )

    project_name = "vott_object"

    projects = sa.search_projects(project_name, True)
    if projects:
        sa.delete_project(projects[0])
    project = sa.create_project(project_name, "converter vector", "Vector")

    sa.create_annotation_classes_from_classes_json(
        project, out_dir / "classes" / "classes.json"
    )
    sa.upload_images_from_folder_to_project(project, out_dir)
    sa.upload_annotations_from_folder_to_project(project, out_dir)


def test_vott_convert_instance(tmpdir):
    input_dir = Path(
        "tests"
    ) / "converter_test" / "VoTT" / "input" / "toSuperAnnotate"
    out_dir = Path(tmpdir) / "instance_segmentation"
    sa.import_annotation_format(
        input_dir, out_dir, "VoTT", "", "Vector", "instance_segmentation",
        "Desktop"
    )


def test_vott_convert_vector(tmpdir):
    input_dir = Path(
        "tests"
    ) / "converter_test" / "VoTT" / "input" / "toSuperAnnotate"
    out_dir = Path(tmpdir) / "vector_annotation"
    sa.import_annotation_format(
        input_dir, out_dir, "VoTT", "", "Vector", "vector_annotation", "Web"
    )

    project_name = "vott_vector"

    projects = sa.search_projects(project_name, True)
    if projects:
        sa.delete_project(projects[0])
    project = sa.create_project(project_name, "converter vector", "Vector")

    sa.create_annotation_classes_from_classes_json(
        project, out_dir / "classes" / "classes.json"
    )
    sa.upload_images_from_folder_to_project(project, out_dir)
    sa.upload_annotations_from_folder_to_project(project, out_dir)
