import unittest
from unittest.mock import MagicMock
from datetime import datetime
import sys
import os

# Add the project root to sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controller.healers.memory_leak import MemoryLeakHealer

class TestMemoryHealer(unittest.TestCase):
    def setUp(self):
        self.prom = MagicMock()
        self.k8s = MagicMock()
        self.notify = MagicMock()
        self.cfg = {
            'healers': {
                'memory_leak': {
                    'enabled': True,
                    'threshold_percent': 80,
                    'trend_window_minutes': 5,
                    'slope_threshold_percent_per_min': 5,
                    'cooldown_minutes': 5
                }
            }
        }
        self.healer = MemoryLeakHealer(self.prom, self.k8s, self.notify, self.cfg)

    def test_memory_leak_detection_and_heal(self):
        # Scenario: Memory > threshold AND slope > threshold
        self.prom.bulk_pod_memory_trend.return_value = {
            'test-pod-abc-123': {
                'current_percent': 85.0,
                'slope_percent_per_min': 10.0,
                'limit_mb': 512,
                'current_mb': 435
            }
        }
        
        self.k8s.get_deployment_for_pod.return_value = 'test-deploy'
        
        self.healer.run('default')
        
        # Verify healing actions
        self.k8s.rolling_restart.assert_called_once_with('default', 'test-deploy')
        self.notify.send.assert_called_once()

    def test_memory_leak_no_action_below_threshold(self):
        # Scenario: Memory < threshold
        self.prom.bulk_pod_memory_trend.return_value = {
            'test-pod-abc-123': {
                'current_percent': 50.0,
                'slope_percent_per_min': 10.0,
                'limit_mb': 512,
                'current_mb': 256
            }
        }
        
        self.healer.run('default')
        
        self.k8s.rolling_restart.assert_not_called()

    def test_memory_leak_no_action_low_slope(self):
        # Scenario: Memory > threshold BUT slope is stable
        self.prom.bulk_pod_memory_trend.return_value = {
            'test-pod-abc-123': {
                'current_percent': 85.0,
                'slope_percent_per_min': 2.0,
                'limit_mb': 512,
                'current_mb': 435
            }
        }
        
        self.healer.run('default')
        
        self.k8s.rolling_restart.assert_not_called()

    def test_memory_leak_cooldown(self):
        self.prom.bulk_pod_memory_trend.return_value = {
            'test-pod-abc-123': {
                'current_mb': 150,
                'slope_mb_per_min': 25
            }
        }
        self.k8s.get_deployment_for_pod.return_value = 'test-deploy'
        
        # First run triggers heal
        self.healer.run('default')
        self.assertEqual(self.k8s.rolling_restart.call_count, 1)
        
        # Second run immediately after should skip due to cooldown
        self.healer.run('default')
        self.assertEqual(self.k8s.rolling_restart.call_count, 1)

if __name__ == '__main__':
    unittest.main()
