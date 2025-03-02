import os.path as osp
from functools import partial
from unittest import TestCase

import numpy as np

from datumaro.components.annotation import AnnotationType, Bbox, LabelCategories
from datumaro.components.dataset import Dataset
from datumaro.components.dataset_base import DatasetItem
from datumaro.components.environment import Environment
from datumaro.components.media import Image
from datumaro.components.task import TaskType
from datumaro.plugins.data_formats.mot import MotSeqGtExporter, MotSeqImporter

from ..requirements import Requirements, mark_requirement

from tests.utils.assets import get_test_asset_path
from tests.utils.test_utils import TestDir, check_save_and_load, compare_datasets


class MotConverterTest(TestCase):
    def _test_save_and_load(
        self, source_dataset, converter, test_dir, target_dataset=None, importer_args=None, **kwargs
    ):
        return check_save_and_load(
            self,
            source_dataset,
            converter,
            test_dir,
            importer="mot_seq",
            target_dataset=target_dataset,
            importer_args=importer_args,
            **kwargs,
        )

    @mark_requirement(Requirements.DATUM_GENERAL_REQ)
    def test_can_save_bboxes(self):
        source_dataset = Dataset.from_iterable(
            [
                DatasetItem(
                    id=1,
                    subset="train",
                    media=Image.from_numpy(data=np.ones((16, 16, 3))),
                    annotations=[
                        Bbox(
                            0,
                            4,
                            4,
                            8,
                            label=2,
                            attributes={
                                "occluded": True,
                            },
                        ),
                        Bbox(
                            0,
                            4,
                            4,
                            4,
                            label=3,
                            attributes={
                                "visibility": 0.4,
                            },
                        ),
                        Bbox(2, 4, 4, 4, attributes={"ignored": True}),
                    ],
                ),
                DatasetItem(
                    id=2,
                    subset="val",
                    media=Image.from_numpy(data=np.ones((8, 8, 3))),
                    annotations=[
                        Bbox(1, 2, 4, 2, label=3),
                    ],
                ),
                DatasetItem(
                    id=3,
                    subset="test",
                    media=Image.from_numpy(data=np.ones((5, 4, 3)) * 3),
                ),
            ],
            categories={
                AnnotationType.label: LabelCategories.from_iterable(
                    "label_" + str(label) for label in range(10)
                ),
            },
            task_type=TaskType.detection,
        )

        target_dataset = Dataset.from_iterable(
            [
                DatasetItem(
                    id=1,
                    media=Image.from_numpy(data=np.ones((16, 16, 3))),
                    annotations=[
                        Bbox(
                            0,
                            4,
                            4,
                            8,
                            label=2,
                            attributes={
                                "occluded": True,
                                "visibility": 0.0,
                                "ignored": False,
                            },
                        ),
                        Bbox(
                            0,
                            4,
                            4,
                            4,
                            label=3,
                            attributes={
                                "occluded": False,
                                "visibility": 0.4,
                                "ignored": False,
                            },
                        ),
                        Bbox(
                            2,
                            4,
                            4,
                            4,
                            attributes={
                                "occluded": False,
                                "visibility": 1.0,
                                "ignored": True,
                            },
                        ),
                    ],
                ),
                DatasetItem(
                    id=2,
                    media=Image.from_numpy(data=np.ones((8, 8, 3))),
                    annotations=[
                        Bbox(
                            1,
                            2,
                            4,
                            2,
                            label=3,
                            attributes={
                                "occluded": False,
                                "visibility": 1.0,
                                "ignored": False,
                            },
                        ),
                    ],
                ),
                DatasetItem(
                    id=3,
                    media=Image.from_numpy(data=np.ones((5, 4, 3)) * 3),
                ),
            ],
            categories={
                AnnotationType.label: LabelCategories.from_iterable(
                    "label_" + str(label) for label in range(10)
                ),
            },
            task_type=TaskType.detection,
        )

        with TestDir() as test_dir:
            self._test_save_and_load(
                source_dataset,
                partial(MotSeqGtExporter.convert, save_media=True),
                test_dir,
                target_dataset=target_dataset,
                require_media=True,
            )

    @mark_requirement(Requirements.DATUM_GENERAL_REQ)
    def test_can_save_and_load_with_no_save_media(self):
        source_dataset = Dataset.from_iterable(
            [
                DatasetItem(
                    id=1,
                    media=Image.from_numpy(data=np.ones((16, 16, 3))),
                    annotations=[
                        Bbox(
                            0,
                            4,
                            4,
                            8,
                            label=0,
                            attributes={
                                "occluded": True,
                                "visibility": 0.0,
                                "ignored": False,
                            },
                        ),
                    ],
                ),
                DatasetItem(
                    id=2,
                    media=Image.from_numpy(data=np.ones((8, 8, 3))),
                    annotations=[
                        Bbox(
                            1,
                            2,
                            4,
                            2,
                            label=1,
                            attributes={
                                "occluded": False,
                                "visibility": 1.0,
                                "ignored": False,
                            },
                        ),
                    ],
                ),
            ],
            categories=["label_0", "label_1"],
            task_type=TaskType.detection,
        )

        with TestDir() as test_dir:
            self._test_save_and_load(
                source_dataset, partial(MotSeqGtExporter.convert, save_media=False), test_dir
            )

    @mark_requirement(Requirements.DATUM_GENERAL_REQ)
    def test_can_save_and_load_image_with_arbitrary_extension(self):
        expected = Dataset.from_iterable(
            [
                DatasetItem(
                    "1",
                    media=Image.from_numpy(data=np.zeros((4, 3, 3)), ext=".JPEG"),
                    annotations=[
                        Bbox(
                            0,
                            4,
                            4,
                            8,
                            label=0,
                            attributes={
                                "occluded": True,
                                "visibility": 0.0,
                                "ignored": False,
                            },
                        ),
                    ],
                ),
                DatasetItem(
                    "2",
                    media=Image.from_numpy(data=np.zeros((3, 4, 3)), ext=".bmp"),
                ),
            ],
            categories=["a"],
            task_type=TaskType.detection,
        )

        with TestDir() as test_dir:
            self._test_save_and_load(
                expected,
                partial(MotSeqGtExporter.convert, save_media=True),
                test_dir,
                require_media=True,
            )

    @mark_requirement(Requirements.DATUM_GENERAL_REQ)
    def test_can_save_and_load_with_meta_file(self):
        source_dataset = Dataset.from_iterable(
            [
                DatasetItem(
                    id=1,
                    media=Image.from_numpy(data=np.ones((16, 16, 3))),
                    annotations=[
                        Bbox(
                            0,
                            4,
                            4,
                            8,
                            label=0,
                            attributes={
                                "occluded": True,
                                "visibility": 0.0,
                                "ignored": False,
                            },
                        ),
                    ],
                ),
                DatasetItem(
                    id=2,
                    media=Image.from_numpy(data=np.ones((8, 8, 3))),
                    annotations=[
                        Bbox(
                            1,
                            2,
                            4,
                            2,
                            label=1,
                            attributes={
                                "occluded": False,
                                "visibility": 1.0,
                                "ignored": False,
                            },
                        ),
                    ],
                ),
            ],
            categories=["label_0", "label_1"],
            task_type=TaskType.detection,
        )

        with TestDir() as test_dir:
            self._test_save_and_load(
                source_dataset,
                partial(MotSeqGtExporter.convert, save_media=True, save_dataset_meta=True),
                test_dir,
                require_media=True,
            )
            self.assertTrue(osp.isfile(osp.join(test_dir, "dataset_meta.json")))


DUMMY_DATASET_DIR = get_test_asset_path("mot_dataset", "mot_seq")
DUMMY_SEQINFO_DATASET_DIR = get_test_asset_path("mot_dataset", "mot_seq_with_seqinfo")


class MotImporterTest(TestCase):
    def _define_expected_dataset(self):
        expected_dataset = Dataset.from_iterable(
            [
                DatasetItem(
                    id=1,
                    media=Image.from_numpy(data=np.ones((16, 16, 3))),
                    annotations=[
                        Bbox(
                            0,
                            4,
                            4,
                            8,
                            label=2,
                            attributes={
                                "occluded": False,
                                "visibility": 1.0,
                                "ignored": False,
                            },
                        ),
                    ],
                ),
            ],
            categories=["label_" + str(label) for label in range(10)],
            task_type=TaskType.detection,
        )

        return expected_dataset

    @mark_requirement(Requirements.DATUM_GENERAL_REQ)
    def test_can_detect(self):
        detected_formats = Environment().detect_dataset(DUMMY_DATASET_DIR)
        self.assertEqual([MotSeqImporter.NAME], detected_formats)

    @mark_requirement(Requirements.DATUM_GENERAL_REQ)
    def test_can_import(self):
        expected_dataset = self._define_expected_dataset()

        dataset = Dataset.import_from(DUMMY_DATASET_DIR, "mot_seq")

        compare_datasets(self, expected_dataset, dataset)

    @mark_requirement(Requirements.DATUM_BUG_560)
    def test_can_import_seqinfo(self):
        expected_dataset = self._define_expected_dataset()

        dataset = Dataset.import_from(DUMMY_SEQINFO_DATASET_DIR, "mot_seq")

        compare_datasets(self, expected_dataset, dataset)
