import pathlib as pl
from .peak_detection import PeakDetectorKNeighbours
from .bitrate_extraction import BitrateExtractor


class VBSegmenter:

    def __init__(self, *,
                 video_data_extractor=None,
                 peak_detector=None,
                 ):
        """
        Segemnts a mp4 video by its K_bitrate.
        call segment method with filepath to segment video.
        :param video_data_extractor: Extracts the video data. Provide a custom one if
        you want to change how and wether the videos are reencoded before the extraction
        :type video_data_extractor:
        :param peak_detector: Detects peaks in the bitrate data. Provide a custom one
        if you want to change how peaks are detected.
        :type peak_detector:
        """

        if video_data_extractor is None:
            video_data_extractor = BitrateExtractor()
        self.video_data_extractor = video_data_extractor

        if peak_detector is None:
            peak_detector = PeakDetectorKNeighbours()
            self.peak_detector = peak_detector

    def segment(self, video_file_path):
        """
        Takes a path to a video and returns a dict of shape
        {
            "k_bitrate_data": k_bitrate_data,
            "peak_indices": peaks
        }
        :param video_file_path: Path to file
        :type video_file_path:
        :return: dict with k_bitrate data per second and indices of peaks
        :rtype: dict
        """
        video_file_path = pl.Path(video_file_path)
        k_bitrate_data = self.video_data_extractor.extract_bitrate(video_file_path)
        peaks = self.peak_detector.detect_peaks(k_bitrate_data)

        return {
            "k_bitrate_data": k_bitrate_data,
            "peak_indices": peaks
        }
