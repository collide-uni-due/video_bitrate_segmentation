import pathlib as pl
import subprocess
import json
import tempfile


class BitrateExtractor:

    def __init__(self, *,
                 reencode_video=True,
                 constant_rate_factor=35,
                 encoding_preset="slow"):
        """
        Extracts k_bitrate per second from video.
        Call extract_bitrate method with filepath to extract bitrate.
        :param reencode_video: Wether to reencode the video before extraction
        :type reencode_video:
        :param constant_rate_factor: quality factor from 0 to 51. Lower is better. See ffmpeg doc
        :type constant_rate_factor:
        :param encoding_preset: encoding speed. Slower achieves better compression. See ffmpeg doc
        :type encoding_preset:
        """
        self.reencode_video = reencode_video
        self.constant_rate_factor = str(constant_rate_factor)
        self.encoding_preset = encoding_preset

    def extract_bitrate(self, video_file_path):
        """
        Takes a path to an mp4 video.
        :param video_file_path:
        :type video_file_path:
        :return: a list with the kbitrate per second of the video.
        :rtype:
        """
        video_meta_data = self._extract_video_meta_data(video_file_path)
        framerate = video_meta_data["framerate"]
        frame_data = self._extract_frame_data(video_file_path)
        bitrate_data = self._extract_bitrate_data(frame_data, framerate)
        return bitrate_data

    def _reencode(self, video_file_path, reencoded_video_path):
        video_data_commands = ["ffmpeg", "-y",
                               "-i", str(video_file_path),
                               "-c:v", "libx264",
                               "-preset", self.encoding_preset,
                               "-crf", self.constant_rate_factor,
                               "-c:a", "copy", str(reencoded_video_path)]
        execute_on_commandline(video_data_commands)

    def _extract_video_meta_data(self, file_path):
        print(str(file_path))
        video_data_commands = ["ffprobe", str(file_path),
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

    def _extract_frame_data(self, video_file_path):
        with tempfile.TemporaryDirectory() as temp_dir:
            video_file_path = pl.Path(video_file_path)
            if self.reencode_video:
                temp_file_path = pl.Path(temp_dir) / video_file_path.name
                self._reencode(video_file_path, temp_file_path)
                video_file_path = temp_file_path
            video_file_path = pl.Path(video_file_path)
            frame_data_commands = ["ffprobe", str(video_file_path),
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

    def _extract_bitrate_data(self, frame_data, framerate, keyframes=False):
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
