"""Robot Framework test library for UC6 LiDAR."""
import numpy as np
from optical_metrology.analysis.lidar import (
    LiDARRangeEquation,
    TimeOfFlightPropagator,
    WaveformAnalyzer,
    generate_point_cloud,
)
from optical_metrology.detector.spad import SPADDetector
from optical_metrology.illumination.scanning import ScanningMechanism
from optical_metrology.scattering import RayleighScattering, MieScattering


class LiDARLibrary:
    def __init__(self):
        self._results = {}

    def create_range_equation(self, power="10", aperture="0.1"):
        self._lre = LiDARRangeEquation(transmitter_power=float(power), receiver_aperture_diameter=float(aperture))

    def compute_received_power(self, range_m="10", backscatter="1e-4"):
        self._received_power = self._lre.compute_range(range_m=float(range_m), backscatter_coeff=float(backscatter))

    def received_power_should_be_positive(self):
        assert self._received_power > 0, f"Expected positive power, got {self._received_power}"

    def create_tof_propagator(self):
        self._tofp = TimeOfFlightPropagator()

    def compute_tof(self, range_m="15"):
        self._tof, self._broadened = self._tofp.compute_tof(range_m=float(range_m), pulse_duration=1e-9)

    def tof_should_be_reasonable(self):
        assert self._tof > 0

    def create_spad(self, dead_time="50e-9", pde="1.0", dcr="0"):
        self._spad = SPADDetector(dead_time=float(dead_time), photon_detection_efficiency=float(pde), dark_count_rate=float(dcr))

    def detect_photons(self):
        timestamps = np.array([1e-9, 2e-9, 3e-9])
        self._events = self._spad.detect(timestamps, pixel=0)

    def events_should_be_detected(self):
        assert len(self._events) > 0, "No SPAD events detected"

    def create_scanner(self, pattern="raster"):
        self._scanner = ScanningMechanism(scan_pattern=pattern, field_of_view_deg=30, resolution=16, scan_rate=10)

    def generate_scan_points(self, duration="0.1"):
        self._scan_points = self._scanner.generate_scan_points(duration=float(duration))

    def scan_points_should_exist(self):
        assert len(self._scan_points) > 0

    def generate_cloud(self):
        ranges = np.ones(len(self._scan_points)) * 50
        az = np.array([p[0] for p in self._scan_points])
        el = np.array([p[1] for p in self._scan_points])
        self._cloud = generate_point_cloud(ranges, az, el)

    def cloud_should_have_points(self):
        assert self._cloud.shape[0] > 0
        assert self._cloud.shape[1] == 4
