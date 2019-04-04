import numpy as np
import abc


class AbstractPeakDetector(abc.ABC):
    @abc.abstractmethod
    def detect_peaks(self, series_data):
        pass


# Based on https://www.researchgate.net/publication/228853276_Simple_Algorithms_for_Peak_Detection_in_Time-Series
# By Girish Palshikar
class PeakDetectorKNeighbours(AbstractPeakDetector):

    def __init__(self,
                 k_neighbours=5,
                 neighbour_aggregation_function=None,
                 std_dev_threshold_factor=2):
        """
        Detect peaks in a timeseries of data based on the distance
        between the value of a datapoint and the value of its k neighbours
        :param k_neighbours: number of neighbours to consider
        :type k_neighbours: int
        :param neighbour_aggregation_function: function to aggregate the distances of neighbours
        default = average
        :type neighbour_aggregation_function: callable
        :param std_dev_threshold_factor: Filter out all peaks with value that have a
         distane less than (this parameter * std_dev of series) from the men
        :type std_dev_threshold_factor:
        """

        self.k_neighbours = k_neighbours
        if neighbour_aggregation_function is None:
            def neighbour_aggregation_function(x):
                return sum(x) / len(x)
        self.neighbour_aggregation_function = neighbour_aggregation_function
        self.std_dev_threshold_factor = std_dev_threshold_factor

    def detect_peaks(self, series_data):

        spikiness_values = [self.calc_spikiness(i,
                                                series_data,
                                                self.neighbour_aggregation_function)
                            for i in range(len(series_data))]

        mean = np.mean(spikiness_values)
        std_dev = np.std(spikiness_values)
        # Filter based on mean and stddev and everything that is negative
        peaks_filtered_global = []
        for i, sp in enumerate(spikiness_values):
            if sp > 0 and (sp - mean) > (std_dev * self.std_dev_threshold_factor):
                peaks_filtered_global.append(i)

        remove_list = []
        # maybe seperate constant instead of k for larger window?
        for i1, i2 in zip(peaks_filtered_global[:-1], peaks_filtered_global[1:]):
            if i2 - i1 <= self.k_neighbours:
                if (spikiness_values[i1] > spikiness_values[i2]):
                    remove_list.append(i2)
                else:
                    remove_list.append(i1)

        filtered_peaks_local = [i for i in peaks_filtered_global if i not in set(remove_list)]

        return filtered_peaks_local

    # Functions to eval spikiness of point
    # Based on Aggregate of the  left and right neighbours
    def calc_spikiness(self, i, s_data, neighbour_aggregation):

        k_left_neighbours = s_data[i - self.k_neighbours:i]
        k_right_neighbours = s_data[i + 1: i + self.k_neighbours + 1]
        # Return No Peak Value if at edge of series
        if len(k_left_neighbours) < self.k_neighbours or len(k_right_neighbours) < self.k_neighbours:
            return -1

        left_dist_reduction = neighbour_aggregation([s_data[i] - neighbour_value
                                                     for neighbour_value in k_left_neighbours])
        right_dist_reduction = neighbour_aggregation([s_data[i] - neighbour_value for
                                                      neighbour_value in k_right_neighbours])

        spikiness = (left_dist_reduction + right_dist_reduction) / 2
        return spikiness
