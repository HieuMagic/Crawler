"""
Simple resource usage visualization for reports
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os


def create_resource_graphs(stats, output_prefix='resource'):
    """
    Create 3 separate graphs: RAM, CPU, and Disk usage
    
    Args:
        stats: Statistics dict containing resource_history
        output_prefix: Prefix for output files (creates prefix_ram.png, etc.)
    
    Returns:
        List of created file paths
    """
    # Create charts directory if it doesn't exist
    charts_dir = 'charts'
    os.makedirs(charts_dir, exist_ok=True)
    
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
    plt.figure(figsize=(12, 6))
    plt.plot(time_minutes, ram_usage, 'b-', linewidth=2)
    plt.fill_between(time_minutes, ram_usage, alpha=0.3, color='blue')
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('RAM Usage (MB)', fontsize=12)
    plt.title('Memory Usage Over Time', fontsize=14, fontweight='bold', pad=20)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    ram_file = os.path.join(charts_dir, f'{output_prefix}_ram.png')
    plt.savefig(ram_file, dpi=300, bbox_inches='tight')
    plt.close()
    created_files.append(ram_file)
    
    # 2. CPU Usage Graph
    plt.figure(figsize=(12, 6))
    plt.plot(time_minutes, cpu_usage, 'r-', linewidth=2)
    plt.fill_between(time_minutes, cpu_usage, alpha=0.3, color='red')
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('CPU Usage (%)', fontsize=12)
    plt.title('CPU Usage Over Time', fontsize=14, fontweight='bold', pad=20)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    cpu_file = os.path.join(charts_dir, f'{output_prefix}_cpu.png')
    plt.savefig(cpu_file, dpi=300, bbox_inches='tight')
    plt.close()
    created_files.append(cpu_file)
    
    # 3. Disk Usage Graph
    plt.figure(figsize=(12, 6))
    plt.plot(time_minutes, disk_usage, 'g-', linewidth=2)
    plt.fill_between(time_minutes, disk_usage, alpha=0.3, color='green')
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('Disk Usage (MB)', fontsize=12)
    plt.title('Disk Usage Over Time', fontsize=14, fontweight='bold', pad=20)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    disk_file = os.path.join(charts_dir, f'{output_prefix}_disk.png')
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
            
            colors = plt.cm.Set3(range(len(labels)))
            
            # Create pie chart 
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=colors, textprops={'fontsize': 10}, pctdistance=0.85)
            plt.title('Error Breakdown', fontsize=14, fontweight='bold', pad=20)
            plt.axis('equal')
            plt.tight_layout()
            
            error_file = os.path.join(charts_dir, f'{output_prefix}_errors.png')
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
               colors=colors, textprops={'fontsize': 11}, pctdistance=0.85)
        plt.title('File Type Distribution', fontsize=14, fontweight='bold', pad=20)
        plt.axis('equal')
        plt.tight_layout()
        
        filetype_file = os.path.join(charts_dir, f'{output_prefix}_filetypes.png')
        plt.savefig(filetype_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(filetype_file)
    
    # Get per-paper data for additional charts
    per_paper_data = stats.get('per_paper_data', [])
    
    if per_paper_data:
        # Extract data
        paper_ids = [p['paper_id'] for p in per_paper_data]
        processing_times = [p['processing_time_seconds'] for p in per_paper_data]
        entry_times = [p['entry_discovery_time_seconds'] for p in per_paper_data]
        sizes_before = [p['size_before_bytes'] / (1024 * 1024) for p in per_paper_data]  # Convert to MB
        sizes_after = [p['size_after_bytes'] / (1024 * 1024) for p in per_paper_data]  # Convert to MB
        versions = [p['versions'] for p in per_paper_data]
        references = [p['references'] for p in per_paper_data]
        
        # 6. Size Before/After Extraction per Paper
        plt.figure(figsize=(14, 6))
        x = np.arange(len(paper_ids))
        width = 0.35
        
        plt.bar(x - width/2, sizes_before, width, label='Before Extraction', color='#ff7f0e', alpha=0.8)
        plt.bar(x + width/2, sizes_after, width, label='After Extraction', color='#2ca02c', alpha=0.8)
        
        plt.xlabel('Paper Index', fontsize=12)
        plt.ylabel('Size (MB)', fontsize=12)
        plt.title('Paper Size Before and After Extraction', fontsize=14, fontweight='bold', pad=20)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Only show some x-axis labels to avoid overlap
        step = max(1, len(paper_ids) // 20)
        plt.xticks(x[::step], [paper_ids[i].split('.')[-1] for i in range(0, len(paper_ids), step)], 
                   rotation=45, ha='right', fontsize=9)
        
        plt.tight_layout()
        size_file = os.path.join(charts_dir, f'{output_prefix}_sizes.png')
        plt.savefig(size_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(size_file)
        
        # 7. Entry Discovery Time per Paper
        plt.figure(figsize=(14, 6))
        plt.bar(x, entry_times, color='#1f77b4', alpha=0.7)
        plt.xlabel('Paper Index', fontsize=12)
        plt.ylabel('Time (seconds)', fontsize=12)
        plt.title('Entry Discovery Time per Paper (arXiv API Call)', fontsize=14, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Add average line
        avg_entry = np.mean(entry_times)
        plt.axhline(y=avg_entry, color='r', linestyle='--', linewidth=2, label=f'Average: {avg_entry:.2f}s')
        plt.legend(fontsize=10)
        
        # Sparse x-axis labels
        plt.xticks(x[::step], [paper_ids[i].split('.')[-1] for i in range(0, len(paper_ids), step)], 
                   rotation=45, ha='right', fontsize=9)
        
        plt.tight_layout()
        entry_file = os.path.join(charts_dir, f'{output_prefix}_entry_times.png')
        plt.savefig(entry_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(entry_file)
        
        # 8. Processing Time per Paper
        plt.figure(figsize=(14, 6))
        plt.bar(x, processing_times, color='#d62728', alpha=0.7)
        plt.xlabel('Paper Index', fontsize=12)
        plt.ylabel('Time (seconds)', fontsize=12)
        plt.title('Total Processing Time per Paper', fontsize=14, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Add average line
        avg_process = np.mean(processing_times)
        plt.axhline(y=avg_process, color='b', linestyle='--', linewidth=2, label=f'Average: {avg_process:.2f}s')
        plt.legend(fontsize=10)
        
        # Sparse x-axis labels
        plt.xticks(x[::step], [paper_ids[i].split('.')[-1] for i in range(0, len(paper_ids), step)], 
                   rotation=45, ha='right', fontsize=9)
        
        plt.tight_layout()
        process_file = os.path.join(charts_dir, f'{output_prefix}_process_times.png')
        plt.savefig(process_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(process_file)
        
        # 9. References per Paper
        plt.figure(figsize=(14, 6))
        plt.bar(x, references, color='#8c564b', alpha=0.7)
        plt.xlabel('Paper Index', fontsize=12)
        plt.ylabel('Number of References', fontsize=12)
        plt.title('Number of References per Paper (with arXiv IDs)', fontsize=14, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Add average line
        avg_refs = np.mean(references)
        plt.axhline(y=avg_refs, color='r', linestyle='--', linewidth=2, label=f'Average: {avg_refs:.2f}')
        plt.legend(fontsize=10)
        
        # Sparse x-axis labels
        plt.xticks(x[::step], [paper_ids[i].split('.')[-1] for i in range(0, len(paper_ids), step)], 
                   rotation=45, ha='right', fontsize=9)
        
        plt.tight_layout()
        refs_file = os.path.join(charts_dir, f'{output_prefix}_references.png')
        plt.savefig(refs_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(refs_file)
    
    return created_files
