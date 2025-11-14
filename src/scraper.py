import os
import time
import tarfile
import gzip
import shutil
import logging
import requests
import arxiv
import threading
import re
from datetime import datetime
from src.utils import arxiv_id_to_folder_name, get_directory_size, save_json


class RateLimiter:
    """Simple rate limiter ensuring minimum wait time between API calls"""
    
    def __init__(self, seconds_between_calls=1.0):
        self.wait_time = seconds_between_calls
        self.last_call_time = 0
        self.lock = threading.Lock()
    
    def execute(self, func):
        """Execute function with rate limiting"""
        with self.lock:
            now = time.time()
            time_since_last = now - self.last_call_time
            if time_since_last < self.wait_time:
                time.sleep(self.wait_time - time_since_last)
            
            result = func()
            self.last_call_time = time.time()
            
            return result


class ArxivScraper:
    """Main scraper for arXiv papers"""
    
    def __init__(self, config):
        self.config = config
        self.client = arxiv.Client()
        
        # Get API key and set up rate limiter and headers
        api_key = config.get('ss_api_key')
        # API key can be None, empty string, or a valid key
        has_api_key = api_key and api_key.strip()
        
        # With API key: 1s between calls, without: 3s to be respectful
        wait_time = 1 if has_api_key else 3
        self.ss_limiter = RateLimiter(wait_time)
        
        # Only add x-api-key header if we have a valid key
        self.ss_headers = {'x-api-key': api_key} if has_api_key else {}
    
    def process_paper(self, paper_id):
        """Process a single paper, returns dict with results"""
        start_time = time.time()
        folder_name = arxiv_id_to_folder_name(paper_id)
        
        logging.info(f"Processing paper {paper_id}")
        
        try:
            # Time the arXiv API call (entry discovery)
            api_start = time.time()
            paper = self._get_paper_metadata(paper_id)
            api_time = time.time() - api_start
            
            if not paper:
                logging.error(f"Failed to get metadata for {paper_id}")
                return {'error': 'download_timeout'}
            
            entry_id = paper.entry_id
            if 'v' in entry_id:
                latest_version = int(entry_id.split('v')[-1])
            else:
                latest_version = 1
            
            versions = list(range(1, latest_version + 1))
            total_versions = len(versions)
            logging.info(f"  Found {total_versions} version(s)")
            
            version_dates = self._get_version_dates(paper_id, total_versions)
            if not version_dates:
                version_dates = [datetime.now().strftime('%Y-%m-%d')] * total_versions
            
            paper_dir = os.path.join(
                self.config['output_dir'],
                self.config['student_id'],
                folder_name
            )
            os.makedirs(paper_dir, exist_ok=True)
            
            tex_dir = os.path.join(paper_dir, 'tex')
            os.makedirs(tex_dir, exist_ok=True)
            
            size_before = 0
            size_after = 0
            all_dates = []
            successful_downloads = 0
            
            for idx, version_num in enumerate(versions):
                version_id = f"{paper_id}v{version_num}"
                version_date = version_dates[idx] if idx < len(version_dates) else datetime.now().strftime('%Y-%m-%d')
                logging.info(f"  [{paper_id}] Downloading version v{version_num}")
                
                try:
                    size_b, size_a, v_date = self._download_and_extract_version(
                        version_id, folder_name, tex_dir, version_date, paper_id
                    )
                    size_before += size_b
                    size_after += size_a
                    all_dates.append(v_date)
                    successful_downloads += 1
                except requests.exceptions.Timeout:
                    logging.warning(f"  [{paper_id}] Timeout downloading v{version_num}")
                except Exception as e:
                    logging.warning(f"  [{paper_id}] Failed to download v{version_num}: {e}")
            
            if size_after == 0:
                return {'error': 'no_tex_source_pdf_only'}
            
            if successful_downloads < total_versions:
                return {
                    'error': 'missing_versions',
                    'expected': total_versions,
                    'downloaded': successful_downloads
                }
            
            references, venue, ss_status = self._get_references(paper_id)
            
            if ss_status == 'rate_limit':
                return {'error': 'api_rate_limit'}
            
            self._save_metadata(paper, all_dates, venue, paper_dir)
            
            arxiv_ref_count = self._save_references(references, paper_dir)
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'versions': successful_downloads,
                'size_before': size_before,
                'size_after': size_after,
                'references': arxiv_ref_count,
                'time': processing_time,
                'api_time': api_time
            }
            
        except requests.exceptions.Timeout:
            logging.error(f"Timeout processing {paper_id}")
            return {'error': 'download_timeout'}
        except Exception as e:
            logging.error(f"Error processing {paper_id}: {e}")
            return {'error': 'download_timeout'}
    
    def _get_paper_metadata(self, paper_id):
        """Get paper metadata from arXiv"""
        try:
            search = arxiv.Search(id_list=[paper_id])
            paper = next(self.client.results(search))
            return paper
        except Exception as e:
            logging.error(f"Failed to get metadata for {paper_id}: {e}")
            return None
    
    def _get_version_dates(self, paper_id, num_versions):
        """Get submission dates for all versions by scraping arXiv HTML page"""
        try:
            url = f"https://arxiv.org/abs/{paper_id}"
            response = requests.get(url, timeout=10)
            
            pattern = r'\[v\d+\](?:</a>)?</strong>\s+([A-Za-z]+,\s+\d+\s+[A-Za-z]+\s+\d{4})'
            dates_str = re.findall(pattern, response.text)
            
            dates = []
            for date_str in dates_str:
                dt = datetime.strptime(date_str, '%a, %d %b %Y')
                dates.append(dt.strftime('%Y-%m-%d'))
            
            if len(dates) == num_versions:
                return dates
            
            logging.warning(f"Expected {num_versions} dates, got {len(dates)}")
            return []
            
        except Exception as e:
            logging.warning(f"Failed to get version dates: {e}")
            return []
    
    def _download_and_extract_version(self, version_id, folder_name, tex_dir, version_date=None, paper_id=None):
        """Download and extract a specific version"""
        try:
            if 'v' in version_id:
                base_paper_id = version_id.rsplit('v', 1)[0]
                version_num = version_id.split('v')[-1]
            else:
                base_paper_id = version_id
                version_num = '1'
            
            if not paper_id:
                paper_id = base_paper_id
            
            download_url = f"https://arxiv.org/e-print/{base_paper_id}v{version_num}"
            response = requests.get(download_url, timeout=self.config.get('timeout', 30))
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            if not version_date:
                version_date = datetime.now().strftime('%Y-%m-%d')
            
            temp_file = f"/tmp/{version_id}.tar.gz"
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            size_before = len(response.content)
            
            version_folder = f"{folder_name}v{version_num}"
            version_dir = os.path.join(tex_dir, version_folder)
            os.makedirs(version_dir, exist_ok=True)
            
            self._extract_filtered(temp_file, version_dir, paper_id)
            
            size_after = get_directory_size(version_dir)
            
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return size_before, size_after, version_date
            
        except Exception as e:
            raise e
    
    def _extract_filtered(self, tar_path, output_dir, paper_id=None):
        """Extract only .tex and .bib files, keep folder structure"""
        paper_prefix = f"[{paper_id}] " if paper_id else ""
        try:
            try:
                with tarfile.open(tar_path, 'r:gz') as tar:
                    for member in tar.getmembers():
                        if member.isdir():
                            member_path = os.path.join(output_dir, member.name)
                            os.makedirs(member_path, exist_ok=True)
                        elif member.name.endswith(('.tex', '.bib')):
                            tar.extract(member, output_dir)
            except tarfile.ReadError:
                logging.info(f"  {paper_prefix}Not a tarball, trying as single gzipped file")
                with gzip.open(tar_path, 'rb') as gz:
                    content = gz.read()
                    
                    if b'\\documentclass' in content or b'\\begin{document}' in content:
                        output_file = os.path.join(output_dir, 'main.tex')
                        with open(output_file, 'wb') as f:
                            f.write(content)
                        logging.info(f"  {paper_prefix}Extracted single .tex file as main.tex")
                    else:
                        output_file = os.path.join(output_dir, 'source')
                        with open(output_file, 'wb') as f:
                            f.write(content)
                        logging.warning(f"  {paper_prefix}Extracted unknown format as 'source'")
                        
        except Exception as e:
            logging.error(f"{paper_prefix}Extraction error: {e}")
            raise
    
    def _save_metadata(self, paper, all_version_dates, venue, paper_dir):
        """Save paper metadata to JSON"""
        submission_date = all_version_dates[0] if all_version_dates else paper.published.strftime('%Y-%m-%d')
        revised_dates = all_version_dates if all_version_dates else [submission_date]
        
        publication_venue = venue if venue else (paper.journal_ref if paper.journal_ref else '')
        
        metadata = {
            'paper_title': paper.title,
            'authors': [author.name for author in paper.authors],
            'submission_date': submission_date,
            'revised_dates': revised_dates,
            'publication_venue': publication_venue
        }
        
        metadata_path = os.path.join(paper_dir, 'metadata.json')
        save_json(metadata, metadata_path)
        
        paper_id = paper_dir.split('/')[-1].replace('-', '.')
        logging.info(f"  [{paper_id}] Saved metadata")
    
    def _get_references(self, paper_id):
        """Get references and publication venue from Semantic Scholar"""
        url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{paper_id}"
        params = {
            'fields': 'references,references.externalIds,references.title,references.authors,references.publicationDate,references.paperId,venue'
        }
        
        max_retries = self.config.get('max_retries', 3)
        
        def make_api_call():
            try:
                response = requests.get(url, params=params, headers=self.ss_headers, timeout=10)
                return response, None
            except Exception as e:
                return None, e
        
        for attempt in range(max_retries):
            response, error = self.ss_limiter.execute(make_api_call)
            
            if error:
                logging.warning(f"  [{paper_id}] Error getting references: {error} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    continue
                return [], '', 'success'
            
            if response.status_code == 200:
                data = response.json()
                references = data.get('references', [])
                venue = data.get('venue', '')
                logging.info(f"  [{paper_id}] Found {len(references)} references")
                
                return references, venue, 'success'
                
            elif response.status_code == 429:
                # Progressive wait times: 5s, 10s, 20s
                wait_times = [5, 10, 20]
                wait_time = wait_times[min(attempt, len(wait_times) - 1)]
                logging.warning(f"  [{paper_id}] Semantic Scholar rate limit (429), waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                if attempt == max_retries - 1:
                    logging.error(f"  [{paper_id}] Failed to get references after {max_retries} attempts due to rate limit")
                    return [], '', 'rate_limit'
                continue
                
            elif response.status_code == 404:
                logging.info(f"  [{paper_id}] Paper not found in Semantic Scholar")
                return [], '', 'success'
                
            else:
                logging.warning(f"  [{paper_id}] Semantic Scholar returned {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return [], '', 'success'
        
        logging.error(f"  [{paper_id}] Failed to get references after {max_retries} attempts")
        return [], '', 'success'
    
    def _save_references(self, references, paper_dir):
        """Save references to JSON (only those with arXiv IDs)"""
        ref_dict = {}
        
        for ref in references:
            external_ids = ref.get('externalIds', {})
            if external_ids and 'ArXiv' in external_ids:
                arxiv_id = external_ids['ArXiv']
                folder_name = arxiv_id_to_folder_name(arxiv_id)
                
                authors = [a.get('name', '') for a in ref.get('authors', [])]
                
                ref_dict[folder_name] = {
                    'paper_title': ref.get('title', ''),
                    'authors': authors,
                    'submission_date': ref.get('publicationDate', ''),
                    'semantic_scholar_id': ref.get('paperId', '')
                }
        
        references_path = os.path.join(paper_dir, 'references.json')
        save_json(ref_dict, references_path)
        
        return len(ref_dict)
