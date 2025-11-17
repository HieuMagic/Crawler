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
    Create 10 focused visualization charts for the scraper statistics
    
    Args:
        stats: Statistics dict containing resource_history and per_paper_data
        output_prefix: Prefix for output files
    
    Returns:
        List of created file paths
    """
    # Create charts directory if it doesn't exist
    charts_dir = 'charts'
    os.makedirs(charts_dir, exist_ok=True)
    
    created_files = []
    
    # Get data
    history = stats.get('resource_history', {})
    per_paper_data = stats.get('per_paper_data', [])
    error_breakdown = stats.get('error_breakdown', {})
    
    # === CHART 1: CPU Usage Over Time ===
    if history and 'timestamps' in history and history.get('cpu_percent'):
        timestamps = history['timestamps']
        cpu_usage = history['cpu_percent']
        
        if timestamps:
            start_time = timestamps[0]
            time_minutes = [(t - start_time) / 60 for t in timestamps]
            
            plt.figure(figsize=(14, 6))
            plt.plot(time_minutes, cpu_usage, 'r-', linewidth=2, alpha=0.8)
            plt.fill_between(time_minutes, cpu_usage, alpha=0.3, color='red')
            
            # Add mean line
            mean_cpu = np.mean(cpu_usage)
            plt.axhline(y=mean_cpu, color='darkred', linestyle='--', linewidth=1.5, 
                       label=f'Mean: {mean_cpu:.1f}%', alpha=0.7)
            
            plt.xlabel('Time (minutes)', fontsize=13, fontweight='bold')
            plt.ylabel('CPU Usage (%)', fontsize=13, fontweight='bold')
            plt.title('CPU Usage Over Time', fontsize=15, fontweight='bold', pad=15)
            plt.grid(True, alpha=0.3, linestyle='--')
            plt.legend(loc='upper right', fontsize=11)
            
            # Annotate max
            max_cpu = max(cpu_usage)
            max_idx = cpu_usage.index(max_cpu)
            plt.annotate(f'Peak: {max_cpu:.1f}%', 
                        xy=(time_minutes[max_idx], max_cpu),
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='red'),
                        fontsize=10)
            
            plt.tight_layout()
            cpu_file = os.path.join(charts_dir, f'{output_prefix}_cpu.png')
            plt.savefig(cpu_file, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(cpu_file)
    
    # === CHART 2: RAM Usage Over Time ===
    if history and 'timestamps' in history and history.get('ram_usage_mb'):
        timestamps = history['timestamps']
        ram_usage = history['ram_usage_mb']
        
        if timestamps:
            start_time = timestamps[0]
            time_minutes = [(t - start_time) / 60 for t in timestamps]
            
            plt.figure(figsize=(14, 6))
            plt.plot(time_minutes, ram_usage, 'b-', linewidth=2, alpha=0.8)
            plt.fill_between(time_minutes, ram_usage, alpha=0.3, color='blue')
            
            # Add mean line
            mean_ram = np.mean(ram_usage)
            plt.axhline(y=mean_ram, color='darkblue', linestyle='--', linewidth=1.5,
                       label=f'Mean: {mean_ram:.1f} MB', alpha=0.7)
            
            plt.xlabel('Time (minutes)', fontsize=13, fontweight='bold')
            plt.ylabel('RAM Usage (MB)', fontsize=13, fontweight='bold')
            plt.title('Memory Usage Over Time', fontsize=15, fontweight='bold', pad=15)
            plt.grid(True, alpha=0.3, linestyle='--')
            plt.legend(loc='upper right', fontsize=11)
            
            # Annotate max
            max_ram = max(ram_usage)
            max_idx = ram_usage.index(max_ram)
            plt.annotate(f'Peak: {max_ram:.1f} MB', 
                        xy=(time_minutes[max_idx], max_ram),
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='blue'),
                        fontsize=10)
            
            plt.tight_layout()
            ram_file = os.path.join(charts_dir, f'{output_prefix}_ram.png')
            plt.savefig(ram_file, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(ram_file)
    
    # === CHART 3: Disk Usage Over Time ===
    if history and 'timestamps' in history and history.get('disk_usage_mb'):
        timestamps = history['timestamps']
        disk_usage = history['disk_usage_mb']
        
        if timestamps:
            start_time = timestamps[0]
            time_minutes = [(t - start_time) / 60 for t in timestamps]
            
            plt.figure(figsize=(14, 6))
            plt.plot(time_minutes, disk_usage, 'g-', linewidth=2, alpha=0.8)
            plt.fill_between(time_minutes, disk_usage, alpha=0.3, color='green')
            
            plt.xlabel('Time (minutes)', fontsize=13, fontweight='bold')
            plt.ylabel('Disk Usage (MB)', fontsize=13, fontweight='bold')
            plt.title('Disk Space Usage Over Time', fontsize=15, fontweight='bold', pad=15)
            plt.grid(True, alpha=0.3, linestyle='--')
            
            # Annotate final size
            final_size = disk_usage[-1]
            plt.annotate(f'Final: {final_size:.1f} MB', 
                        xy=(time_minutes[-1], final_size),
                        xytext=(-80, -30), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='green'),
                        fontsize=10)
            
            plt.tight_layout()
            disk_file = os.path.join(charts_dir, f'{output_prefix}_disk.png')
            plt.savefig(disk_file, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(disk_file)
    
    # === CHART 4: Scraping Speed (Papers Over Time) ===
    # Prefer using per-paper success timestamps (wall-clock). Fall back to resource_history interpolation.
    if per_paper_data and any('success_timestamp' in p for p in per_paper_data):
        # Use actual success timestamps
        times = sorted([p['success_timestamp'] for p in per_paper_data if 'success_timestamp' in p])
        start_time = times[0]
        elapsed_minutes = [(t - start_time) / 60 for t in times]
        cumulative_papers = np.arange(1, len(times) + 1)

        plt.figure(figsize=(14, 6))
        plt.plot(elapsed_minutes, cumulative_papers, 'purple', linewidth=2.5, alpha=0.9)
        plt.scatter(elapsed_minutes, cumulative_papers, s=10, color='purple', alpha=0.6)
        plt.fill_between(elapsed_minutes, cumulative_papers, alpha=0.15, color='purple')

        plt.xlabel('Time (minutes)', fontsize=13, fontweight='bold')
        plt.ylabel('Papers Successfully Scraped', fontsize=13, fontweight='bold')
        plt.title('Scraping Progress Over Time (by success timestamps)', fontsize=15, fontweight='bold', pad=15)
        plt.grid(True, alpha=0.3, linestyle='--')

        total_papers = len(times)
        total_time_hours = (times[-1] - start_time) / 3600 if times[-1] > start_time else 0
        papers_per_hour = total_papers / total_time_hours if total_time_hours > 0 else 0

        plt.text(0.98, 0.05, f'Rate: {papers_per_hour:.1f} papers/hour\nTotal: {total_papers} papers in {total_time_hours:.2f}h',
                 transform=plt.gca().transAxes,
                 fontsize=11, verticalalignment='bottom', horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        plt.tight_layout()
        speed_file = os.path.join(charts_dir, f'{output_prefix}_scraping_speed.png')
        plt.savefig(speed_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(speed_file)
    elif history and 'timestamps' in history and per_paper_data:
        # Fallback: use resource_history interpolation
        timestamps = history['timestamps']
        if timestamps and len(timestamps) > 0:
            start_time = timestamps[0]
            time_minutes = [(t - start_time) / 60 for t in timestamps]
            total_runtime = stats.get('total_runtime_seconds', timestamps[-1] - timestamps[0])
            total_papers = len(per_paper_data)

            papers_at_time = []
            for t in timestamps:
                elapsed = t - start_time
                papers_done = int((elapsed / total_runtime) * total_papers)
                papers_at_time.append(min(papers_done, total_papers))

            plt.figure(figsize=(14, 6))
            plt.plot(time_minutes, papers_at_time, 'purple', linewidth=2.5, alpha=0.8)
            plt.fill_between(time_minutes, papers_at_time, alpha=0.2, color='purple')

            plt.xlabel('Time (minutes)', fontsize=13, fontweight='bold')
            plt.ylabel('Papers Successfully Scraped', fontsize=13, fontweight='bold')
            plt.title('Scraping Progress Over Time', fontsize=15, fontweight='bold', pad=15)
            plt.grid(True, alpha=0.3, linestyle='--')

            total_time_hours = total_runtime / 3600
            papers_per_hour = total_papers / total_time_hours if total_time_hours > 0 else 0

            plt.text(0.98, 0.05, f'Rate: {papers_per_hour:.1f} papers/hour\nTotal: {total_papers} papers in {total_time_hours:.2f}h',
                    transform=plt.gca().transAxes,
                    fontsize=11, verticalalignment='bottom', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

            plt.tight_layout()
            speed_file = os.path.join(charts_dir, f'{output_prefix}_scraping_speed.png')
            plt.savefig(speed_file, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(speed_file)
    
    # === CHART 5: Paper Size Before vs After (Box Plot Comparison) ===
    if per_paper_data:
        sizes_before_mb = [p['size_before_bytes'] / (1024 * 1024) for p in per_paper_data]
        sizes_after_mb = [p['size_after_bytes'] / (1024 * 1024) for p in per_paper_data]
        
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Create box plots
        bp = ax.boxplot([sizes_before_mb, sizes_after_mb], 
                        labels=['Before Extraction', 'After Extraction'],
                        patch_artist=True, widths=0.6, showmeans=True,
                        meanprops=dict(marker='D', markerfacecolor='red', markersize=8))
        
        # Color boxes
        colors = ['#ff7f0e', '#2ca02c']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_ylabel('Size (MB)', fontsize=13, fontweight='bold')
        ax.set_title(f'Paper Size Comparison: Before vs After Extraction (n={len(per_paper_data)})', 
                    fontsize=15, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')
        
        # Add statistics annotations
        mean_before = np.mean(sizes_before_mb)
        mean_after = np.mean(sizes_after_mb)
        median_before = np.median(sizes_before_mb)
        median_after = np.median(sizes_after_mb)
        reduction = (1 - mean_after / mean_before) * 100 if mean_before > 0 else 0
        
        stats_text = (f'Before: Mean={mean_before:.2f} MB, Median={median_before:.2f} MB\n'
                     f'After: Mean={mean_after:.2f} MB, Median={median_after:.2f} MB\n'
                     f'Size Reduction: {reduction:.1f}%')
        ax.text(0.5, 0.98, stats_text, transform=ax.transAxes,
               fontsize=11, verticalalignment='top', horizontalalignment='center',
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
        
        plt.tight_layout()
        size_file = os.path.join(charts_dir, f'{output_prefix}_paper_sizes.png')
        plt.savefig(size_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(size_file)
    
    # === CHART 6: Number of References Distribution (Histogram) ===
    if per_paper_data:
        references = [p['references'] for p in per_paper_data]
        
        plt.figure(figsize=(12, 7))
        n, bins, patches = plt.hist(references, bins=30, color='#8c564b', alpha=0.75, edgecolor='black')
        
        plt.xlabel('Number of References (with arXiv IDs)', fontsize=13, fontweight='bold')
        plt.ylabel('Frequency (Number of Papers)', fontsize=13, fontweight='bold')
        plt.title(f'Distribution of References per Paper (n={len(per_paper_data)})', 
                 fontsize=15, fontweight='bold', pad=15)
        plt.grid(True, alpha=0.3, axis='y', linestyle='--')
        
        # Add statistics
        mean_refs = np.mean(references)
        median_refs = np.median(references)
        max_refs = max(references)
        papers_with_refs = sum(1 for r in references if r > 0)
        pct_with_refs = (papers_with_refs / len(references)) * 100
        
        stats_text = (f'Mean: {mean_refs:.1f} | Median: {median_refs:.0f} | Max: {max_refs}\n'
                     f'Papers with refs: {papers_with_refs} ({pct_with_refs:.1f}%)')
        plt.text(0.98, 0.97, stats_text, transform=plt.gca().transAxes,
                fontsize=11, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        refs_file = os.path.join(charts_dir, f'{output_prefix}_references.png')
        plt.savefig(refs_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(refs_file)
    
    # === CHART 7: File Types Distribution (Pie Chart) ===
    tex_percent = stats.get('tex_file_percent', 0)
    bib_percent = stats.get('bib_file_percent', 0)
    json_percent = stats.get('json_file_percent', 0)
    
    if tex_percent > 0 or bib_percent > 0 or json_percent > 0:
        plt.figure(figsize=(10, 8))
        
        labels = []
        sizes = []
        colors = []
        
        if tex_percent > 0:
            labels.append(f'TeX Files\n({tex_percent:.1f}%)')
            sizes.append(tex_percent)
            colors.append('#ff9999')
        if bib_percent > 0:
            labels.append(f'BIB Files\n({bib_percent:.1f}%)')
            sizes.append(bib_percent)
            colors.append('#66b3ff')
        if json_percent > 0:
            labels.append(f'JSON Files\n({json_percent:.1f}%)')
            sizes.append(json_percent)
            colors.append('#99ff99')
        
        wedges, texts, autotexts = plt.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                            startangle=90, colors=colors,
                                            textprops={'fontsize': 12, 'fontweight': 'bold'},
                                            pctdistance=0.85, explode=[0.05] * len(sizes))
        
        # Make percentage text bold and larger
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(13)
            autotext.set_fontweight('bold')
        
        plt.title('File Type Distribution by Size', fontsize=15, fontweight='bold', pad=20)
        plt.axis('equal')
        plt.tight_layout()
        
        filetype_file = os.path.join(charts_dir, f'{output_prefix}_filetypes.png')
        plt.savefig(filetype_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(filetype_file)
    
    # === CHART 8: Error Types Distribution (Pie Chart) ===
    if error_breakdown:
        errors = {k: v for k, v in error_breakdown.items() if v > 0}
        
        if errors:
            plt.figure(figsize=(10, 8))
            
            labels = [f'{k.replace("_", " ").title()}\n({v} papers)' for k, v in errors.items()]
            sizes = list(errors.values())
            colors = plt.cm.Set3(range(len(labels)))
            
            wedges, texts, autotexts = plt.pie(sizes, labels=labels, autopct='%1.1f%%',
                                                startangle=90, colors=colors,
                                                textprops={'fontsize': 11, 'fontweight': 'bold'},
                                                pctdistance=0.85, explode=[0.05] * len(sizes))
            
            # Make percentage text bold
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_fontweight('bold')
            
            total_errors = sum(sizes)
            plt.title(f'Error Type Distribution (Total Errors: {total_errors})', 
                     fontsize=15, fontweight='bold', pad=20)
            plt.axis('equal')
            plt.tight_layout()
            
            error_file = os.path.join(charts_dir, f'{output_prefix}_errors.png')
            plt.savefig(error_file, dpi=300, bbox_inches='tight')
            plt.close()
            created_files.append(error_file)
    
    # === CHART 9: Entry Discovery Time Distribution (Histogram + Stats) ===
    if per_paper_data:
        entry_times = [p['entry_discovery_time_seconds'] for p in per_paper_data]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Histogram
        ax1.hist(entry_times, bins=40, color='#1f77b4', alpha=0.75, edgecolor='black')
        ax1.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Frequency (Number of Papers)', fontsize=12, fontweight='bold')
        ax1.set_title('Entry Discovery Time Distribution', fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y', linestyle='--')
        
        # Add statistics
        mean_val = np.mean(entry_times)
        median_val = np.median(entry_times)
        p95_val = np.percentile(entry_times, 95)
        stats_text = f'Mean: {mean_val:.2f}s\nMedian: {median_val:.2f}s\n95th: {p95_val:.2f}s'
        ax1.text(0.98, 0.97, stats_text, transform=ax1.transAxes,
                fontsize=11, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Box plot
        bp = ax2.boxplot(entry_times, vert=True, patch_artist=True, widths=0.5,
                        showmeans=True, meanprops=dict(marker='D', markerfacecolor='red', markersize=8))
        bp['boxes'][0].set_facecolor('#1f77b4')
        bp['boxes'][0].set_alpha(0.7)
        ax2.set_ylabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax2.set_title('Entry Discovery Time Box Plot', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y', linestyle='--')
        ax2.set_xticklabels(['API Call Time'])
        
        fig.suptitle(f'Entry Discovery Time Analysis (arXiv API) - n={len(per_paper_data)}', 
                    fontsize=15, fontweight='bold', y=1.00)
        plt.tight_layout()
        
        entry_file = os.path.join(charts_dir, f'{output_prefix}_entry_times.png')
        plt.savefig(entry_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(entry_file)
    
    # === CHART 10: Processing Time per Paper Distribution (Histogram + Stats) ===
    if per_paper_data:
        processing_times = [p['processing_time_seconds'] for p in per_paper_data]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Histogram
        ax1.hist(processing_times, bins=40, color='#d62728', alpha=0.75, edgecolor='black')
        ax1.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Frequency (Number of Papers)', fontsize=12, fontweight='bold')
        ax1.set_title('Processing Time Distribution', fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y', linestyle='--')
        
        # Add statistics
        mean_val = np.mean(processing_times)
        median_val = np.median(processing_times)
        p95_val = np.percentile(processing_times, 95)
        stats_text = f'Mean: {mean_val:.2f}s\nMedian: {median_val:.2f}s\n95th: {p95_val:.2f}s'
        ax1.text(0.98, 0.97, stats_text, transform=ax1.transAxes,
                fontsize=11, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Box plot
        bp = ax2.boxplot(processing_times, vert=True, patch_artist=True, widths=0.5,
                        showmeans=True, meanprops=dict(marker='D', markerfacecolor='red', markersize=8))
        bp['boxes'][0].set_facecolor('#d62728')
        bp['boxes'][0].set_alpha(0.7)
        ax2.set_ylabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax2.set_title('Processing Time Box Plot', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y', linestyle='--')
        ax2.set_xticklabels(['Total Processing'])
        
        fig.suptitle(f'Total Processing Time per Paper Analysis - n={len(per_paper_data)}', 
                    fontsize=15, fontweight='bold', y=1.00)
        plt.tight_layout()
        
        process_file = os.path.join(charts_dir, f'{output_prefix}_process_times.png')
        plt.savefig(process_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(process_file)
    
    return created_files
