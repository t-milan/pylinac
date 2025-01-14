from unittest import TestCase

import numpy as np

from pylinac.core import contrast
from pylinac.core.contrast import Contrast, power_spectrum_1d


class TestContrastAlgorithms(TestCase):
    def test_ratio(self):
        self.assertEqual(contrast.ratio(1, 0.5), 2)
        self.assertEqual(contrast.ratio(0.5, 1), 0.5)

    def test_weber(self):
        self.assertEqual(contrast.weber(1, 0.5), 1)
        self.assertEqual(contrast.weber(0.5, 1), 0.5)

    def test_weber_symmetric(self):
        self.assertEqual(contrast.weber(1.5, 1), 0.5)

    def test_weber_against_old_definition(self):
        """Match previous algorithm =(
        https://github.com/jrkerns/pylinac/blob/release-v3.11/pylinac/core/roi.py#L192-L195
        """

        def old_weber(pixel, contrast):
            return abs(pixel - contrast) / contrast

        self.assertEqual(old_weber(0.5, 1), contrast.weber(0.5, 1))
        self.assertEqual(old_weber(1.5, 1), contrast.weber(1.5, 1))

    def test_michelson(self):
        arr = np.array((0, 1, 3))
        self.assertEqual(contrast.michelson(arr), 1)
        arr2 = np.array((15, 20, 18))
        self.assertEqual(contrast.michelson(arr2), 5 / 35)
        arr3 = np.array((3, 3, 3))
        self.assertEqual(contrast.michelson(arr3), 0)

    def test_difference(self):
        self.assertEqual(10, contrast.difference(20, 10))
        self.assertEqual(10, contrast.difference(10, 20))
        self.assertEqual(1, contrast.difference(-2, -1))

    def test_rms_normal(self):
        arr = np.array((0, 0.5, 1)).astype(float)
        self.assertAlmostEqual(contrast.rms(arr), 0.40825, places=5)
        arr = np.array((0.3, 0.4, 0.5)).astype(float)
        self.assertAlmostEqual(contrast.rms(arr), 0.08165, places=5)

    def test_rms_out_of_range(self):
        arr = np.array((3, 4, 5)).astype(float)
        with self.assertRaises(ValueError):
            contrast.rms(arr)
        arr = np.array((-1, 0, 1)).astype(float)
        with self.assertRaises(ValueError):
            contrast.rms(arr)

    def test_contrast_michelson(self):
        arr2 = np.array((15, 20, 18))
        self.assertEqual(
            contrast.michelson(arr2), contrast.contrast(arr2, Contrast.MICHELSON)
        )

    def test_contrast_difference(self):
        arr = np.array((0.5, 1))
        self.assertEqual(
            contrast.difference(arr[0], arr[1]),
            contrast.contrast(arr, Contrast.DIFFERENCE),
        )

    def test_contrast_difference_bad_array(self):
        arr = np.array((0.5, 1, 1.5))
        with self.assertRaises(ValueError):
            contrast.contrast(arr, Contrast.DIFFERENCE)

    def test_contrast_rms(self):
        arr = np.array((0, 0.5, 1)).astype(float)
        self.assertEqual(contrast.rms(arr), contrast.contrast(arr, Contrast.RMS))

    def test_contrast_weber(self):
        arr = np.array((0.5, 1))
        self.assertEqual(
            contrast.weber(arr[0], arr[1]), contrast.contrast(arr, Contrast.WEBER)
        )

    def test_contrast_weber_bad_array(self):
        arr = np.array((0.5, 1, 1.5))
        with self.assertRaises(ValueError):
            contrast.contrast(arr, Contrast.WEBER)

    def test_contrast_ratio(self):
        arr = np.array((0.5, 1))
        self.assertEqual(
            contrast.ratio(arr[0], arr[1]), contrast.contrast(arr, Contrast.RATIO)
        )

    def test_contrast_ratio_bad_array(self):
        arr = np.array((0.5, 1, 1.5))
        with self.assertRaises(ValueError):
            contrast.contrast(arr, Contrast.RATIO)


class TestCalculate1DPowerSpectrum(TestCase):
    def test_random_noise(self):
        # Test with a random noise image
        test_image = np.random.rand(256, 256)  # noqa: NPY002
        output = power_spectrum_1d(test_image)
        self.assertEqual(output.ndim, 1)
        self.assertTrue(len(output) > 0)
        self.assertEqual(np.argmax(output), 0)

    def test_average_power_uniform_image(self):
        # Test with an image with a constant value
        test_image = np.ones((256, 256))
        output = power_spectrum_1d(test_image)
        self.assertEqual(output.ndim, 1)
        self.assertTrue(len(output) > 0)
        self.assertEqual(np.argmax(output), 0)
        frequencies = np.arange(len(output))
        avg_power = np.sum(frequencies * output) / np.sum(output)
        self.assertAlmostEqual(avg_power, 0, places=5)

    def test_average_power_sinusoidal_image(self):
        # Test with an image with a sinusoidal pattern
        # this oscillates in the y-direction
        test_image = np.ones((256, 256))
        test_image = test_image * np.sin(np.arange(256) * 2 * np.pi / 16)[:, np.newaxis]
        output = power_spectrum_1d(test_image)
        self.assertEqual(output.ndim, 1)
        self.assertEqual(np.argmax(output), 15)
        frequencies = np.arange(len(output))
        avg_power = np.sum(frequencies * output) / np.sum(output)
        self.assertAlmostEqual(avg_power, 15, delta=1)

    def test_edge_cases(self):
        # Test with an empty array
        test_image = np.array([])
        with self.assertRaises(ValueError):
            power_spectrum_1d(test_image)

        # Test with a very small array
        test_image = np.random.rand(2, 2)  # noqa: NPY002
        output = power_spectrum_1d(test_image)
        self.assertEqual(output.ndim, 1)
        self.assertTrue(len(output) > 0)
