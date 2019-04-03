import subprocess
import json
import tempfile
import pathlib as pl


class VBSegmenter:

    def __init__(self, *,
                 preprocessing=True,
                 peak_filter_method="n_highest_median",
                 n_peaks=5,
                 scaling_factor=0.4):
        self.preprocessing = preprocessing
        self.peak_filter_method = peak_filter_method
        self.n_peaks = n_peaks
        self.scaling_factor = scaling_factor

    def segment(self, video_path):
        pass


class VideoDataExtractor:

    def __init__(self, *,
                 reencode_video=True,
                 constant_rate_factor=35,
                 encoding_preset="slow"):
        self.reencode_video = reencode_video
        self.constant_rate_factor = str(constant_rate_factor)
        self.encoding_preset = encoding_preset

    def extract_video_data(self, video_file_path):
        """
        Takes a path to an mp4 video.
        Returns a dict with the keys
        :param video_file_path:
        :type video_file_path:
        :return:
        :rtype:
        """
        # Create tempdir always to not duplicate pipeline code
        with tempfile.TemporaryDirectory as temp_dir:
            video_file_path = pl.Path(video_file_path)
            if self.reencode_video:
                temp_file_path = pl.Path(temp_dir) / video_file_path.name
                self.reencode(video_file_path, temp_file_path)
                video_file_path = temp_file_path

            video_meta_data = self.extract_video_meta_data(video_file_path)
            framerate = video_meta_data["framerate"]
            frame_data = self.extract_frame_data(video_file_path)
            bitrate_data = self.extract_bitrate_data(frame_data, framerate)
            return bitrate_data

    def reencode(self, video_file_path, reencoded_video_path):
        video_data_commands = ["ffmpeg", "-y",
                               "-i", str(video_file_path),
                               "-c:v", "libx264",
                               "-preset", self.encoding_preset,
                               "-crf", self.constant_rate_factor,
                               "-c:a", "copy", str(reencoded_video_path)]
        execute_on_commandline(video_data_commands)

    def extract_video_meta_data(self, file_path):
        video_data_commands = ["ffprobe", file_path,
                               "-v", "quiet",
                               "-select_streams", "v",
                               "-show_streams",
                               "-print_format", "json"]
        video_data_string = execute_on_commandline(video_data_commands)
        video_data_json = json.loads(video_data_string)
        frame_rate_string = video_data_json["streams"][0]["r_frame_rate"]
        numerator, denominator = frame_rate_string.split("/")
        framerate = float(numerator) / float(denominator)
        result = {
            "framerate": framerate
        }
        return result

    def extract_frame_data(self, file_path):
        frame_data_commands = ["ffprobe", file_path,
                               "-show_frames",
                               "-select_streams", "v",
                               "-print_format", "json"]

        bit_rate_data = []
        frame_data_string = execute_on_commandline(frame_data_commands)
        frame_data = json.loads(frame_data_string)
        for index, frame in enumerate(frame_data["frames"]):
            # bitrate in bytes
            frame_byterate = float(frame["pkt_size"])
            frame_kbitrate = (frame_byterate * 8) / 1000
            frame_data = {
                "kbitrate": frame_kbitrate,
                "keyframe": frame["key_frame"],
            }
            bit_rate_data.append(frame_data)

        return bit_rate_data

    def extract_bitrate_data(self, frame_data, framerate, keyframes=False):
        """
        Returns a tuple containing k_bitrate sequence
        and corresponding time sequence for raw video data
        :param frame_data:
        :type frame_data:
        :param framerate:
        :type framerate:
        :param keyframes:
        :type keyframes:
        :param normtoseconds:
        :type normtoseconds:
        :return:
        :rtype:
        """
        bitrate_data = []
        time_data = []
        for index, item in enumerate(frame_data):
            if keyframes:
                if item["keyframe"] == 1:
                    item.append(item["kbitrate"])
                else:
                    item.append(0)
            else:
                if item["keyframe"] == 0:
                    bitrate_data.append(item["kbitrate"])
                else:
                    bitrate_data.append(0)
            time = index / framerate
            time_data.append(time)

        normed_bitrate_data = []
        normed_time_data = []
        # may be problematic to use range with integer division. Maybe check for time intevall
        for i in range(int(len(bitrate_data) // framerate)):
            normed_bitrate = sum(bitrate_data[int(i * framerate):int((i + 1) * framerate)])
            normed_bitrate_data.append(normed_bitrate)
            normed_time_data.append(i + 1)

        return normed_bitrate_data


def execute_on_commandline(commands):
    process = subprocess.run(commands, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True)
    return process.stdout.decode()
