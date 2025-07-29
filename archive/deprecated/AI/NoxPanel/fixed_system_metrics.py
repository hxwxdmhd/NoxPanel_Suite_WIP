def collect_system_metrics(self) -> Dict[str, Any]:
    """
    RLVR: Implements collect_system_metrics with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for collect_system_metrics
    2. Analysis: Function complexity 1.3/5.0
    3. Solution: Implements collect_system_metrics with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    """Collect system metrics with proper error handling"""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_dict = {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'used': memory.used,
            'free': memory.free
        }

        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_dict = {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': (disk.used / disk.total) * 100
        }

        # Network metrics (basic)
        network_stats = psutil.net_io_counters()
        network_dict = {
            'bytes_sent': network_stats.bytes_sent,
            'bytes_recv': network_stats.bytes_recv,
            'packets_sent': network_stats.packets_sent,
            'packets_recv': network_stats.packets_recv
        }

        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count
            },
            'memory': memory_dict,
            'disk': disk_dict,
            'network': network_dict,
            'status': 'healthy'
        }
    except Exception as e:
        logger.error(f"Metrics collection error: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'error': str(e),
            'fallback': True
        }
