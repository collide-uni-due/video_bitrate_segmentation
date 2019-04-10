from video_bitrate_segmentation import VBSegmenter
import unittest
import pathlib as pl

base_path = pl.Path().absolute()
video_path = base_path / "lttt.mp4"


class TestVBS(unittest.TestCase):

    def test_segmentation(self):
        segmenter = VBSegmenter()
        seg_result = segmenter.segment(str(video_path))
        print(seg_result)


