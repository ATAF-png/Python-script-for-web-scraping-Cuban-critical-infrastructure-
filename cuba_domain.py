import dns.resolver
import requests
import time
import csv
from datetime import datetime

class CubanInfrastructureMapper:
    def __init__(self):
        self.all_domains = set()
        self.subdomain_results = []
    
    def search_certificates(self):
        """Method 1: Certificate Transparency"""
        print("\n[Method 1] Searching Certificate Transparency Logs...")
        
        tlds = ['gov.cu', 'gob.cu']
        
        for tld in tlds:
            try:
                url = f"https://crt.sh/?q=%.{tld}&output=json"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    for entry in data:
                        name = entry.get('name_value', '')
                        for domain in name.split('\n'):
                            domain = domain.strip().lower()
                            if domain and not domain.startswith('*'):
                                self.all_domains.add(domain)
                
                time.sleep(2)
            except Exception as e:
                print(f"  Error: {e}")
        
        print(f"  ✅ Found {len(self.all_domains)} domains from certificates")
    
    def enumerate_subdomains(self, base_domain, wordlist):
        """Method 2: Subdomain enumeration"""
        found = []
        
        for word in wordlist:
            subdomain = f"{word}.{base_domain}"
            try:
                answers = dns.resolver.resolve(subdomain, 'A')
                for ip in answers:
                    found.append({
                        'domain': subdomain,
                        'ip': str(ip),
                        'method': 'dns_enum'
                    })
                    print(f"    ✅ {subdomain} -> {ip}")
                time.sleep(0.3)
            except:
                pass
        
        return found
    
    def check_all_subdomains(self):
        """Check subdomains for all discovered domains"""
        print("\n[Method 2] Enumerating Subdomains...")
        
        wordlist = [
            'www', 'mail', 'webmail', 'smtp', 'pop', 'imap',
            'ftp', 'sftp', 'admin', 'administrator',
            'portal', 'intranet', 'extranet', 'remote',
            'vpn', 'access', 'secure', 'ssl',
            'api', 'app', 'web', 'servidor',
            'servicios', 'tramites', 'ciudadano', 'consulta',
            'transparencia', 'prensa', 'noticias', 'estadisticas'
        ]
        
        # Get unique base domains
        base_domains = set()
        for domain in self.all_domains:
            parts = domain.split('.')
            if len(parts) >= 2:
                base = '.'.join(parts[-2:])
                base_domains.add(base)
        
        print(f"  Checking {len(base_domains)} base domains...")
        
        for base in sorted(base_domains):
            print(f"\n  Checking: {base}")
            results = self.enumerate_subdomains(base, wordlist)
            self.subdomain_results.extend(results)
            time.sleep(1)
    
    def save_results(self):
        """Save all results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save all domains
        filename1 = f'cuban_domains_{timestamp}.csv'
        with open(filename1, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Domain'])
            for domain in sorted(self.all_domains):
                writer.writerow([domain])
        
        print(f"\n✅ Saved {len(self.all_domains)} domains to {filename1}")
        
        # Save subdomains with IPs
        if self.subdomain_results:
            filename2 = f'cuban_subdomains_{timestamp}.csv'
            with open(filename2, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['domain', 'ip', 'method'])
                writer.writeheader()
                writer.writerows(self.subdomain_results)
            
            print(f"✅ Saved {len(self.subdomain_results)} active subdomains to {filename2}")
    
    def run(self):
        """Run all methods"""
        print("="*60)
        print("CUBAN GOVERNMENT INFRASTRUCTURE MAPPER")
        print("="*60)
        
        self.search_certificates()
        self.check_all_subdomains()
        
        print(f"\n{'='*60}")
        print("FINAL SUMMARY")
        print(f"{'='*60}")
        print(f"Total domains discovered: {len(self.all_domains)}")
        print(f"Active subdomains found: {len(self.subdomain_results)}")
        
        self.save_results()
        
        print("\n✅ Complete!")

if __name__ == "__main__":
    mapper = CubanInfrastructureMapper()
    mapper.run()
