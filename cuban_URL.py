import requests
import csv
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys
import glob

class CubanURLDiscovery:
    def __init__(self, domains_file=None):
        self.domains_file = domains_file
        self.discovered_urls = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Common paths for government websites
        self.paths = [
            '/',
            '/index.html',
            '/index.php',
            '/home',
            '/inicio',
            '/portal',
            '/admin',
            '/login',
            '/acceso',
            '/tramites',
            '/servicios',
            '/ciudadano',
            '/consulta',
            '/noticias',
            '/prensa',
            '/transparencia',
            '/estadisticas',
            '/contacto',
            '/acerca',
            '/sobre',
            '/directorio',
            '/enlaces',
            '/documentos',
            '/normativas',
            '/leyes',
            '/resoluciones',
            '/downloads',
            '/descargas',
            '/buscar',
            '/search',
            '/sitemap.xml',
            '/robots.txt',
            '/api',
            '/servicios-web',
            '/webservices',
            '/css/style.css',
            '/images',
            '/media',
            '/uploads',
            '/files',
            '/archivos'
        ]
        
        # Ensure output directory exists
        self.output_dir = "discovery_results"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def find_csv_files(self):
        """Find CSV files in current directory"""
        csv_files = glob.glob("*.csv")
        if not csv_files:
            csv_files = glob.glob("./*.csv")
        return csv_files
    
    def select_csv_file(self):
        """Prompt user to select a CSV file"""
        csv_files = self.find_csv_files()
        
        if not csv_files:
            print("\n❌ No CSV files found in current directory.")
            print("Please ensure you have a CSV file in the same folder as this script.")
            print("Example CSV format:")
            print("Domain")
            print("example1.cu")
            print("example2.gov.cu")
            print("example3.cub")
            return None
        
        print("\n📁 Available CSV files:")
        for i, file in enumerate(csv_files, 1):
            print(f"  {i}. {file}")
        
        try:
            choice = input(f"\nSelect a CSV file (1-{len(csv_files)}) or press Enter to use first file: ").strip()
            if choice == "":
                choice = "1"
            
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(csv_files):
                return csv_files[selected_index]
            else:
                print("❌ Invalid selection.")
                return None
        except ValueError:
            print("❌ Please enter a valid number.")
            return None
    
    def validate_csv_file(self, filepath):
        """Validate that the input file is a CSV"""
        if not filepath.lower().endswith('.csv'):
            print(f"❌ Error: Input file must be a CSV file. Got: {filepath}")
            return False
        
        if not os.path.exists(filepath):
            print(f"❌ Error: File not found: {filepath}")
            return False
        
        # Check if file has valid content
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sample = f.read(1024)
                if len(sample.strip()) == 0:
                    print(f"❌ Error: CSV file is empty: {filepath}")
                    return False
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
            return False
        
        return True
    
    def load_domains(self):
        """Load domains from CSV file with validation"""
        if not self.validate_csv_file(self.domains_file):
            return []
        
        domains = []
        try:
            with open(self.domains_file, 'r', encoding='utf-8') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                
                # Common CSV delimiters
                delimiters = [',', ';', '\t']
                delimiter = ','
                
                # Try to guess delimiter
                for d in delimiters:
                    if d in sample:
                        delimiter = d
                        break
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                if not reader.fieldnames:
                    print("❌ Error: CSV file has no headers")
                    return []
                
                # Try different column names
                domain_columns = ['Domain', 'domain', 'URL', 'url', 'hostname', 'Hostname', 'site', 'Site', 'website', 'Website']
                
                for row in reader:
                    domain = None
                    for col in domain_columns:
                        if col in row and row[col] and str(row[col]).strip():
                            domain = str(row[col]).strip()
                            break
                    
                    if domain:
                        # Clean up domain (remove protocol if present)
                        cleaned_domain = self.clean_domain(domain)
                        if cleaned_domain and cleaned_domain not in domains:  # Avoid duplicates
                            domains.append(cleaned_domain)
                    else:
                        # Try to find domain in any column
                        for key, value in row.items():
                            if value and str(value).strip():
                                potential_domain = self.clean_domain(str(value).strip())
                                if '.' in potential_domain and ' ' not in potential_domain:
                                    if potential_domain not in domains:
                                        domains.append(potential_domain)
                                    break
                
                print(f"📊 Loaded {len(domains)} unique domains from {self.domains_file}")
                
                if len(domains) == 0:
                    print("❌ No valid domains found in CSV file.")
                    print("Please ensure your CSV has a column with domain names.")
                    print("Accepted column names: Domain, domain, URL, url, hostname, Hostname, site, website")
                
                # Save cleaned domains to a new CSV for reference
                self.save_cleaned_domains(domains)
                
        except Exception as e:
            print(f"❌ Error loading domains: {e}")
            return []
        
        return domains
    
    def clean_domain(self, domain):
        """Remove protocol and paths from domain"""
        domain = domain.strip()
        
        # Remove protocol if present
        if domain.startswith('http://'):
            domain = domain[7:]
        elif domain.startswith('https://'):
            domain = domain[8:]
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Remove trailing slash and paths
        domain = domain.split('/')[0].split('?')[0].split('#')[0]
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        return domain.lower()
    
    def save_cleaned_domains(self, domains):
        """Save cleaned domains to CSV for reference"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.output_dir, f'cleaned_domains_{timestamp}.csv')
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Domain'])
            for domain in sorted(domains):
                writer.writerow([domain])
        
        print(f"📝 Cleaned domains saved to: {filename}")
        return filename
    
    def check_url(self, url):
        """Check if a URL is accessible"""
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10,
                allow_redirects=True,
                verify=False
            )
            
            return {
                'url': url,
                'status_code': response.status_code,
                'final_url': response.url,
                'title': self.extract_title(response.text),
                'content_length': len(response.content),
                'server': response.headers.get('Server', 'Unknown'),
                'content_type': response.headers.get('Content-Type', 'Unknown'),
                'discovery_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'domain': urlparse(response.url).netloc
            }
        except requests.exceptions.SSLError:
            # Try HTTP if HTTPS fails
            if url.startswith('https://'):
                http_url = url.replace('https://', 'http://')
                return self.check_url(http_url)
            return None
        except Exception as e:
            return None
    
    def extract_title(self, html):
        """Extract title from HTML"""
        try:
            start = html.lower().find('<title>')
            if start != -1:
                end = html.lower().find('</title>', start)
                if end != -1:
                    title = html[start+7:end].strip()
                    return title[:200]  # Limit length
        except:
            pass
        return ''
    
    def probe_domain(self, domain):
        """Probe all paths for a domain"""
        found_urls = []
        
        # Try both HTTP and HTTPS
        for protocol in ['https', 'http']:
            base_url = f"{protocol}://{domain}"
            
            for path in self.paths:
                url = urljoin(base_url, path)
                result = self.check_url(url)
                
                if result and result['status_code'] < 500:
                    found_urls.append(result)
                    
                    # Don't check HTTP if HTTPS works
                    if protocol == 'https' and result['status_code'] == 200:
                        break
                
                time.sleep(0.1)  # Rate limiting
            
            # If HTTPS worked, skip HTTP
            if found_urls and protocol == 'https':
                break
        
        if found_urls:
            print(f"✅ Found {len(found_urls)} URLs on {domain}")
        else:
            print(f"❌ No accessible URLs found on {domain}")
        
        return found_urls
    
    def probe_all_domains(self, domains, max_workers=10):
        """Probe all domains with threading"""
        print(f"\n{'='*60}")
        print(f"Starting URL discovery on {len(domains)} domains")
        print(f"Using {max_workers} concurrent workers")
        print(f"{'='*60}\n")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_domain = {
                executor.submit(self.probe_domain, domain): domain 
                for domain in domains
            }
            
            for future in as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    results = future.result()
                    if results:
                        self.discovered_urls.extend(results)
                except Exception as e:
                    print(f"  ❌ Error probing {domain}: {e}")
    
    def save_results(self):
        """Save discovered URLs to CSV with comprehensive reporting"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.output_dir, f'discovered_urls_{timestamp}.csv')
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if self.discovered_urls:
                fieldnames = [
                    'domain',
                    'url',
                    'status_code',
                    'final_url',
                    'title',
                    'content_length',
                    'server',
                    'content_type',
                    'discovery_time'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.discovered_urls)
        
        print(f"\n{'='*60}")
        print(f"📊 RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Total URLs discovered: {len(self.discovered_urls)}")
        print(f"💾 Main results saved to: {filename}")
        
        # Generate additional CSV reports
        self.generate_summary_report(filename)
        
        print(f"{'='*60}")
        return filename
    
    def generate_summary_report(self, main_csv_path):
        """Generate summary statistics CSV"""
        if not self.discovered_urls:
            return
        
        # Read the main CSV for summary
        domains_dict = {}
        status_summary = {}
        
        for url_data in self.discovered_urls:
            domain = url_data['domain']
            status = url_data['status_code']
            
            # Count by domain
            if domain not in domains_dict:
                domains_dict[domain] = 0
            domains_dict[domain] += 1
            
            # Count by status code
            if status not in status_summary:
                status_summary[status] = 0
            status_summary[status] += 1
        
        # Save domain summary CSV
        domain_summary_file = main_csv_path.replace('.csv', '_domain_summary.csv')
        with open(domain_summary_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Domain', 'URLs_Discovered'])
            for domain, count in sorted(domains_dict.items(), key=lambda x: x[1], reverse=True):
                writer.writerow([domain, count])
        
        # Save status code summary CSV
        status_summary_file = main_csv_path.replace('.csv', '_status_summary.csv')
        with open(status_summary_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Status_Code', 'Count'])
            for status, count in sorted(status_summary.items()):
                writer.writerow([status, count])
        
        print(f"📈 Domain summary saved to: {domain_summary_file}")
        print(f"📈 Status code summary saved to: {status_summary_file}")
        
        # Display quick summary
        print(f"\n📋 Quick Summary:")
        print(f"  Domains with URLs found: {len(domains_dict)}")
        print(f"  Most productive domain: {max(domains_dict.items(), key=lambda x: x[1])[0]} ({max(domains_dict.values())} URLs)")
        
        successful_codes = [code for code in status_summary.keys() if 200 <= code < 400]
        if successful_codes:
            successful_count = sum(status_summary[code] for code in successful_codes)
            print(f"  Successful responses (2xx/3xx): {successful_count}")
    
    def create_example_csv(self):
        """Create an example CSV file if none exists"""
        example_file = "example_domains.csv"
        example_data = [
            ["Domain"],
            ["example1.cu"],
            ["example2.gov.cu"],
            ["example3.cub"],
            ["mitrans.gob.cu"],
            ["www.cubagob.cu"],
            ["portal.cubatel.cu"]
        ]
        
        with open(example_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(example_data)
        
        print(f"📝 Created example CSV file: {example_file}")
        print("You can edit this file with your own domains and run the script again.")
        return example_file
    
    def run(self):
        """Main execution"""
        print("="*60)
        print("CUBAN GOVERNMENT URL DISCOVERY TOOL")
        print("="*60)
        print("All results will be saved as CSV files only\n")
        
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # If no CSV file provided, prompt user
        if not self.domains_file:
            print("No CSV file specified. Looking for CSV files in current directory...")
            self.domains_file = self.select_csv_file()
            
            if not self.domains_file:
                # No CSV files found, offer to create example
                print("\nWould you like to create an example CSV file? (y/n): ", end='')
                choice = input().strip().lower()
                if choice in ['y', 'yes']:
                    self.domains_file = self.create_example_csv()
                    print("\nPlease edit the example CSV with your domains and run the script again.")
                    return
                else:
                    print("\n❌ Please provide a CSV file with domains.")
                    print("Usage: python cuban_url.py domains.csv")
                    return
        
        # Validate input file
        if not self.validate_csv_file(self.domains_file):
            print("Please provide a valid CSV file containing domains.")
            return
        
        domains = self.load_domains()
        
        if not domains:
            print("No domains to probe!")
            return
        
        # Ask for confirmation
        print(f"\nReady to probe {len(domains)} domains.")
        print("This may take some time depending on the number of domains.")
        response = input("Continue? (y/n): ").lower()
        if response not in ['y', 'yes']:
            print("Operation cancelled.")
            return
        
        # Ask if user wants to test with fewer domains first
        if len(domains) > 10:
            print(f"\nYou have {len(domains)} domains. Would you like to test with just 5 first? (y/n): ", end='')
            test_choice = input().strip().lower()
            if test_choice in ['y', 'yes']:
                domains = domains[:5]
                print("Testing with first 5 domains only...")
        
        start_time = time.time()
        self.probe_all_domains(domains)
        elapsed_time = time.time() - start_time
        
        if self.discovered_urls:
            results_file = self.save_results()
            print(f"\n⏱️  Total execution time: {elapsed_time:.2f} seconds")
            print(f"📊 Average time per domain: {elapsed_time/len(domains):.2f} seconds")
            print(f"\n📁 All results saved in: {self.output_dir}/")
            
            # Show location of results
            results_path = os.path.abspath(results_file)
            print(f"📄 Main results file: {results_path}")
        else:
            print("\n❌ No URLs discovered. Check your domains list and network connectivity.")
            print("Possible issues:")
            print("  1. Domains may not exist or be accessible")
            print("  2. Network/firewall restrictions")
            print("  3. All sites might be down")
        
        print("\n✅ Discovery complete!")


def main():
    """Main entry point with command line handling"""
    print("="*60)
    print("CSV-BASED URL DISCOVERY TOOL")
    print("="*60)
    
    if len(sys.argv) > 1:
        # Use provided CSV file
        domains_file = sys.argv[1]
        finder = CubanURLDiscovery(domains_file)
    else:
        # No arguments, use interactive mode
        print("\nℹ️  No CSV file specified.")
        print("You can:")
        print("  1. Drag and drop a CSV file onto this script")
        print("  2. Run: python cuban_url.py your_file.csv")
        print("  3. Press Enter to select from available CSV files\n")
        
        # Check if there are CSV files
        finder = CubanURLDiscovery()
    
    finder.run()


if __name__ == "__main__":
    main()
