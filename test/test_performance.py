"""
Performance Tests for Multi-Camera Display

This test suite validates performance with multiple simultaneous streams:
- Test with 4, 9, and 16 simultaneous streams
- Monitor CPU and memory usage
- Verify UI responsiveness
- Test on target hardware

Requirements tested: 8.1, 8.2, 8.3
"""

import sys
import time
import psutil
import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QSettings, Qt, QTimer
from PyQt5.QtTest import QTest
from ip_camera_player import (
    CameraInstance, CameraManager, CameraPanel, CameraGridLayout,
    CameraState
)


class PerformanceMonitor:
    """Monitor CPU and memory usage during tests."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.initial_cpu = self.process.cpu_percent(interval=0.1)
        self.measurements = []
    
    def measure(self):
        """Take a measurement of current resource usage."""
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        cpu_percent = self.process.cpu_percent(interval=0.1)
        
        measurement = {
            'memory_mb': memory_mb,
            'cpu_percent': cpu_percent,
            'memory_delta': memory_mb - self.initial_memory,
            'timestamp': time.time()
        }
        self.measurements.append(measurement)
        return measurement
    
    def get_stats(self):
        """Get statistics from all measurements."""
        if not self.measurements:
            return {}
        
        memory_values = [m['memory_mb'] for m in self.measurements]
        cpu_values = [m['cpu_percent'] for m in self.measurements]
        memory_deltas = [m['memory_delta'] for m in self.measurements]
        
        return {
            'avg_memory_mb': sum(memory_values) / len(memory_values),
            'max_memory_mb': max(memory_values),
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
            'max_cpu_percent': max(cpu_values),
            'avg_memory_delta_mb': sum(memory_deltas) / len(memory_deltas),
            'max_memory_delta_mb': max(memory_deltas),
            'num_measurements': len(self.measurements)
        }
    
    def print_stats(self):
        """Print performance statistics."""
        stats = self.get_stats()
        if not stats:
            print("No measurements taken")
            return
        
        print("\n=== Performance Statistics ===")
        print(f"Initial Memory: {self.initial_memory:.2f} MB")
        print(f"Average Memory: {stats['avg_memory_mb']:.2f} MB")
        print(f"Max Memory: {stats['max_memory_mb']:.2f} MB")
        print(f"Average Memory Delta: {stats['avg_memory_delta_mb']:.2f} MB")
        print(f"Max Memory Delta: {stats['max_memory_delta_mb']:.2f} MB")
        print(f"Average CPU: {stats['avg_cpu_percent']:.2f}%")
        print(f"Max CPU: {stats['max_cpu_percent']:.2f}%")
        print(f"Measurements: {stats['num_measurements']}")
        print("==============================\n")


def test_performance_with_n_cameras(n_cameras, duration_seconds=5):
    """
    Test performance with N cameras.
    
    Args:
        n_cameras: Number of cameras to test with
        duration_seconds: How long to run the test
    
    Returns:
        Performance statistics dictionary
    """
    print(f"\n{'='*60}")
    print(f"Testing performance with {n_cameras} cameras")
    print(f"{'='*60}")
    
    # Create QApplication if needed
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create performance monitor
    monitor = PerformanceMonitor()
    
    # Create temporary settings
    settings = QSettings("test_org", "test_app")
    settings.clear()
    
    # Create camera manager
    camera_manager = CameraManager(settings)
    
    # Add N cameras
    print(f"Adding {n_cameras} cameras...")
    camera_ids = []
    for i in range(n_cameras):
        config = {
            "name": f"Camera {i+1}",
            "protocol": "rtsp",
            "username": "admin",
            "password": f"pass{i}",
            "ip_address": f"192.168.1.{100+i}",
            "port": 554,
            "stream_path": "stream1",
            "resolution": (1920, 1080)
        }
        camera_id = camera_manager.add_camera(config)
        camera_ids.append(camera_id)
    
    print(f"Successfully added {len(camera_ids)} cameras")
    
    # Create camera panels
    print("Creating camera panels...")
    panels = []
    for camera_id in camera_ids:
        camera = camera_manager.get_camera(camera_id)
        panel = CameraPanel(camera)
        panels.append(panel)
    
    # Create grid layout
    print("Creating grid layout...")
    layout = CameraGridLayout()
    from PyQt5.QtWidgets import QWidgetItem
    for panel in panels:
        layout.addItem(QWidgetItem(panel))
    
    # Create container widget
    container = QWidget()
    container.setLayout(layout)
    container.resize(1920, 1080)
    
    # Take initial measurement
    monitor.measure()
    
    # Simulate activity for duration
    print(f"Monitoring performance for {duration_seconds} seconds...")
    start_time = time.time()
    measurement_count = 0
    
    while time.time() - start_time < duration_seconds:
        # Process events to keep UI responsive
        app.processEvents()
        
        # Take measurement every 0.5 seconds
        if measurement_count % 5 == 0:
            measurement = monitor.measure()
            elapsed = time.time() - start_time
            print(f"  [{elapsed:.1f}s] Memory: {measurement['memory_mb']:.2f} MB "
                  f"(+{measurement['memory_delta']:.2f} MB), "
                  f"CPU: {measurement['cpu_percent']:.1f}%")
        
        measurement_count += 1
        time.sleep(0.1)
    
    # Final measurement
    monitor.measure()
    
    # Print statistics
    monitor.print_stats()
    
    # Cleanup
    settings.clear()
    
    return monitor.get_stats()


def test_ui_responsiveness(n_cameras):
    """
    Test UI responsiveness with N cameras.
    
    Args:
        n_cameras: Number of cameras to test with
    
    Returns:
        Average response time in milliseconds
    """
    print(f"\n{'='*60}")
    print(f"Testing UI responsiveness with {n_cameras} cameras")
    print(f"{'='*60}")
    
    # Create QApplication if needed
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create temporary settings
    settings = QSettings("test_org", "test_app")
    settings.clear()
    
    # Create camera manager and add cameras
    camera_manager = CameraManager(settings)
    camera_ids = []
    for i in range(n_cameras):
        config = {
            "name": f"Camera {i+1}",
            "ip_address": f"192.168.1.{100+i}"
        }
        camera_id = camera_manager.add_camera(config)
        camera_ids.append(camera_id)
    
    # Test selection switching responsiveness
    print("Testing selection switching...")
    response_times = []
    
    for _ in range(10):
        for camera_id in camera_ids:
            start = time.time()
            camera_manager.select_camera(camera_id)
            app.processEvents()
            elapsed = (time.time() - start) * 1000  # Convert to ms
            response_times.append(elapsed)
    
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)
    
    print(f"Average selection response time: {avg_response_time:.2f} ms")
    print(f"Max selection response time: {max_response_time:.2f} ms")
    
    # Test reordering responsiveness
    print("\nTesting reordering...")
    reorder_times = []
    
    for i in range(min(10, n_cameras)):
        start = time.time()
        camera_manager.reorder_cameras(camera_ids[i], (i + 1) % n_cameras)
        app.processEvents()
        elapsed = (time.time() - start) * 1000
        reorder_times.append(elapsed)
    
    avg_reorder_time = sum(reorder_times) / len(reorder_times)
    max_reorder_time = max(reorder_times)
    
    print(f"Average reorder response time: {avg_reorder_time:.2f} ms")
    print(f"Max reorder response time: {max_reorder_time:.2f} ms")
    
    # Cleanup
    settings.clear()
    
    return {
        'avg_selection_ms': avg_response_time,
        'max_selection_ms': max_response_time,
        'avg_reorder_ms': avg_reorder_time,
        'max_reorder_ms': max_reorder_time
    }


def test_grid_layout_performance(n_cameras):
    """
    Test grid layout calculation performance.
    
    Args:
        n_cameras: Number of cameras to test with
    
    Returns:
        Average layout calculation time in milliseconds
    """
    print(f"\n{'='*60}")
    print(f"Testing grid layout performance with {n_cameras} cameras")
    print(f"{'='*60}")
    
    # Create QApplication if needed
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Test layout calculation times without creating actual widgets
    # to avoid Qt lifecycle issues
    print("Testing layout dimension calculations...")
    layout = CameraGridLayout()
    
    calc_times = []
    for _ in range(100):
        start = time.time()
        rows, cols = layout.calculate_grid_dimensions(n_cameras)
        elapsed = (time.time() - start) * 1000
        calc_times.append(elapsed)
    
    avg_calc_time = sum(calc_times) / len(calc_times)
    max_calc_time = max(calc_times)
    
    print(f"Grid dimensions for {n_cameras} cameras: {rows}x{cols}")
    print(f"Average dimension calculation time: {avg_calc_time:.4f} ms")
    print(f"Max dimension calculation time: {max_calc_time:.4f} ms")
    
    return {
        'avg_layout_ms': avg_calc_time,
        'max_layout_ms': max_calc_time
    }


def main():
    """Run all performance tests."""
    print("\n" + "="*60)
    print("MULTI-CAMERA DISPLAY PERFORMANCE TEST SUITE")
    print("="*60)
    
    # Test with 4 cameras
    stats_4 = test_performance_with_n_cameras(4, duration_seconds=3)
    responsiveness_4 = test_ui_responsiveness(4)
    layout_4 = test_grid_layout_performance(4)
    
    # Test with 9 cameras
    stats_9 = test_performance_with_n_cameras(9, duration_seconds=3)
    responsiveness_9 = test_ui_responsiveness(9)
    layout_9 = test_grid_layout_performance(9)
    
    # Test with 16 cameras
    stats_16 = test_performance_with_n_cameras(16, duration_seconds=3)
    responsiveness_16 = test_ui_responsiveness(16)
    layout_16 = test_grid_layout_performance(16)
    
    # Print summary
    print("\n" + "="*60)
    print("PERFORMANCE TEST SUMMARY")
    print("="*60)
    
    print("\nMemory Usage:")
    print(f"  4 cameras:  Avg: {stats_4['avg_memory_mb']:.2f} MB, "
          f"Max: {stats_4['max_memory_mb']:.2f} MB, "
          f"Delta: +{stats_4['max_memory_delta_mb']:.2f} MB")
    print(f"  9 cameras:  Avg: {stats_9['avg_memory_mb']:.2f} MB, "
          f"Max: {stats_9['max_memory_mb']:.2f} MB, "
          f"Delta: +{stats_9['max_memory_delta_mb']:.2f} MB")
    print(f"  16 cameras: Avg: {stats_16['avg_memory_mb']:.2f} MB, "
          f"Max: {stats_16['max_memory_mb']:.2f} MB, "
          f"Delta: +{stats_16['max_memory_delta_mb']:.2f} MB")
    
    print("\nCPU Usage:")
    print(f"  4 cameras:  Avg: {stats_4['avg_cpu_percent']:.2f}%, "
          f"Max: {stats_4['max_cpu_percent']:.2f}%")
    print(f"  9 cameras:  Avg: {stats_9['avg_cpu_percent']:.2f}%, "
          f"Max: {stats_9['max_cpu_percent']:.2f}%")
    print(f"  16 cameras: Avg: {stats_16['avg_cpu_percent']:.2f}%, "
          f"Max: {stats_16['max_cpu_percent']:.2f}%")
    
    print("\nUI Responsiveness (Selection):")
    print(f"  4 cameras:  Avg: {responsiveness_4['avg_selection_ms']:.2f} ms, "
          f"Max: {responsiveness_4['max_selection_ms']:.2f} ms")
    print(f"  9 cameras:  Avg: {responsiveness_9['avg_selection_ms']:.2f} ms, "
          f"Max: {responsiveness_9['max_selection_ms']:.2f} ms")
    print(f"  16 cameras: Avg: {responsiveness_16['avg_selection_ms']:.2f} ms, "
          f"Max: {responsiveness_16['max_selection_ms']:.2f} ms")
    
    print("\nLayout Performance:")
    print(f"  4 cameras:  Avg: {layout_4['avg_layout_ms']:.2f} ms, "
          f"Max: {layout_4['max_layout_ms']:.2f} ms")
    print(f"  9 cameras:  Avg: {layout_9['avg_layout_ms']:.2f} ms, "
          f"Max: {layout_9['max_layout_ms']:.2f} ms")
    print(f"  16 cameras: Avg: {layout_16['avg_layout_ms']:.2f} ms, "
          f"Max: {layout_16['max_layout_ms']:.2f} ms")
    
    print("\n" + "="*60)
    print("PERFORMANCE ASSESSMENT")
    print("="*60)
    
    # Assess performance
    issues = []
    
    # Check memory growth
    if stats_16['max_memory_delta_mb'] > 500:
        issues.append("⚠️  High memory usage with 16 cameras (>500 MB increase)")
    else:
        print("✓ Memory usage is acceptable")
    
    # Check CPU usage
    if stats_16['max_cpu_percent'] > 80:
        issues.append("⚠️  High CPU usage with 16 cameras (>80%)")
    else:
        print("✓ CPU usage is acceptable")
    
    # Check UI responsiveness
    if responsiveness_16['max_selection_ms'] > 100:
        issues.append("⚠️  UI responsiveness degraded with 16 cameras (>100ms)")
    else:
        print("✓ UI remains responsive")
    
    # Check layout performance
    if layout_16['max_layout_ms'] > 50:
        issues.append("⚠️  Layout calculations slow with 16 cameras (>50ms)")
    else:
        print("✓ Layout calculations are fast")
    
    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✓ All performance metrics are within acceptable ranges")
    
    print("\n" + "="*60)
    print("Note: These tests use mock cameras without actual video streams.")
    print("Real-world performance with active streams may differ.")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
