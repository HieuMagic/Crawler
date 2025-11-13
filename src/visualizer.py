"""
Simple resource usage visualization for reports
"""
import matplotlib.pyplot as plt


def create_resource_graphs(stats, output_prefix='resource'):
    """
    Create 3 separate graphs: RAM, CPU, and Disk usage
    
    Args:
        stats: Statistics dict containing resource_history
        output_prefix: Prefix for output files (creates prefix_ram.png, etc.)
    
    Returns:
        List of created file paths
    """
    history = stats.get('resource_history', {})
    
    if not history or 'timestamps' not in history:
        return []
    
    timestamps = history['timestamps']
    ram_usage = history.get('ram_usage_mb', [])
    cpu_usage = history.get('cpu_percent', [])
    disk_usage = history.get('disk_usage_mb', [])
    
    if not timestamps:
        return []
    
    # Convert timestamps to minutes from start
    start_time = timestamps[0]
    time_minutes = [(t - start_time) / 60 for t in timestamps]
    
    created_files = []
    
    # 1. RAM Usage Graph
    plt.figure(figsize=(10, 6))
    plt.plot(time_minutes, ram_usage, 'b-', linewidth=2)
    plt.fill_between(time_minutes, ram_usage, alpha=0.3, color='blue')
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('RAM Usage (MB)', fontsize=12)
    plt.title('Memory Usage Over Time', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    ram_file = f'{output_prefix}_ram.png'
    plt.savefig(ram_file, dpi=300, bbox_inches='tight')
    plt.close()
    created_files.append(ram_file)
    
    # 2. CPU Usage Graph
    plt.figure(figsize=(10, 6))
    plt.plot(time_minutes, cpu_usage, 'r-', linewidth=2)
    plt.fill_between(time_minutes, cpu_usage, alpha=0.3, color='red')
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('CPU Usage (%)', fontsize=12)
    plt.title('CPU Usage Over Time', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    cpu_file = f'{output_prefix}_cpu.png'
    plt.savefig(cpu_file, dpi=300, bbox_inches='tight')
    plt.close()
    created_files.append(cpu_file)
    
    # 3. Disk Usage Graph
    plt.figure(figsize=(10, 6))
    plt.plot(time_minutes, disk_usage, 'g-', linewidth=2)
    plt.fill_between(time_minutes, disk_usage, alpha=0.3, color='green')
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('Disk Usage (MB)', fontsize=12)
    plt.title('Disk Usage Over Time', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    disk_file = f'{output_prefix}_disk.png'
    plt.savefig(disk_file, dpi=300, bbox_inches='tight')
    plt.close()
    created_files.append(disk_file)
    
    # 4. Error Breakdown Pie Chart
    error_breakdown = stats.get('error_breakdown', {})
    if error_breakdown:
        # Filter out zero values
        errors = {k: v for k, v in error_breakdown.items() if v > 0}
        
        if errors:
            plt.figure(figsize=(10, 8))
            labels = list(errors.keys())
            sizes = list(errors.values())
            
            # Use a nice color palette
            colors = plt.cm.Set3(range(len(labels)))
            
            # Create pie chart
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=colors, textprops={'fontsize': 11})
            plt.title('Error Breakdown', fontsize=14, fontweight='bold')
            plt.axis('equal')
            plt.tight_layout()
            
            error_file = f'{output_prefix}_errors.png'
            plt.savefig(error_file, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(error_file)
    
    # 5. File Type Distribution Pie Chart
    tex_percent = stats.get('tex_file_percent', 0)
    bib_percent = stats.get('bib_file_percent', 0)
    json_percent = stats.get('json_file_percent', 0)
    
    if tex_percent > 0 or bib_percent > 0 or json_percent > 0:
        plt.figure(figsize=(10, 8))
        
        labels = []
        sizes = []
        
        if tex_percent > 0:
            labels.append('TeX Files')
            sizes.append(tex_percent)
        if bib_percent > 0:
            labels.append('BIB Files')
            sizes.append(bib_percent)
        if json_percent > 0:
            labels.append('JSON Files')
            sizes.append(json_percent)
        
        colors = ['#ff9999', '#66b3ff', '#99ff99'][:len(labels)]
        
        # Create pie chart
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
               colors=colors, textprops={'fontsize': 12})
        plt.title('File Type Distribution', fontsize=14, fontweight='bold')
        plt.axis('equal')
        plt.tight_layout()
        
        filetype_file = f'{output_prefix}_filetypes.png'
        plt.savefig(filetype_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(filetype_file)
    
    return created_files
