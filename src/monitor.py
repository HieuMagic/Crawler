import psutil
import threading
import time
import os


class ResourceMonitor:
    """Resource monitor for RAM, CPU, and disk usage"""
    
    def __init__(self, output_dir='./data'):
        self.process = psutil.Process()
        self.output_dir = output_dir
        self.ram_samples = []
        self.cpu_samples = []
        self.disk_samples = []
        self.timestamps = []
        self.running = False
        self.thread = None
    
    def start(self):
        """Start monitoring in background"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Timestamp
                self.timestamps.append(time.time())
                
                # RAM and CPU
                ram_mb = self.process.memory_info().rss / (1024 * 1024)
                cpu_percent = self.process.cpu_percent(interval=1)
                
                self.ram_samples.append(ram_mb)
                self.cpu_samples.append(cpu_percent)
                
                # Disk usage - get total size of output directory
                if os.path.exists(self.output_dir):
                    total_size = 0
                    for dirpath, dirnames, filenames in os.walk(self.output_dir):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                total_size += os.path.getsize(filepath)
                            except (OSError, FileNotFoundError):
                                pass
                    disk_mb = total_size / (1024 * 1024)
                    self.disk_samples.append(disk_mb)
                else:
                    self.disk_samples.append(0.0)
                    
            except Exception:
                pass
            
            time.sleep(5)  # Sample every 5 seconds
    
    def stop(self):
        """Stop monitoring and take final measurements"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        
        # Take one final sample to capture the true final state
        try:
            # Final timestamp
            self.timestamps.append(time.time())
            
            # Final RAM and CPU
            ram_mb = self.process.memory_info().rss / (1024 * 1024)
            cpu_percent = self.process.cpu_percent(interval=0.1)
            self.ram_samples.append(ram_mb)
            self.cpu_samples.append(cpu_percent)
            
            # Final disk usage
            if os.path.exists(self.output_dir):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(self.output_dir):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            total_size += os.path.getsize(filepath)
                        except (OSError, FileNotFoundError):
                            pass
                disk_mb = total_size / (1024 * 1024)
                self.disk_samples.append(disk_mb)
        except Exception:
            pass
    
    def get_stats(self):
        """Get monitoring statistics"""
        if not self.ram_samples:
            return {
                'max_ram_mb': 0.0,
                'avg_ram_mb': 0.0,
                'max_cpu_percent': 0.0,
                'avg_cpu_percent': 0.0,
                'max_disk_mb': 0.0,
                'timestamps': [],
                'ram_usage_mb': [],
                'cpu_percent': [],
                'disk_usage_mb': []
            }
        
        return {
            'max_ram_mb': max(self.ram_samples),
            'avg_ram_mb': sum(self.ram_samples) / len(self.ram_samples),
            'max_cpu_percent': max(self.cpu_samples) if self.cpu_samples else 0.0,
            'avg_cpu_percent': sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0.0,
            'max_disk_mb': max(self.disk_samples) if self.disk_samples else 0.0,
            'timestamps': self.timestamps,
            'ram_usage_mb': self.ram_samples,
            'cpu_percent': self.cpu_samples,
            'disk_usage_mb': self.disk_samples
        }
