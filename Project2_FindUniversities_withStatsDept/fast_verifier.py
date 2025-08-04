import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urlparse

class FastStatsVerifier:
    def __init__(self):
        self.universities = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def load_universities(self, filename="known_US_universities.txt"):
        """Load universities from text file"""
        print(f"Loading universities from {filename}...")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            self.universities.append({
                                "name": parts[0].strip(),
                                "url": parts[1].strip(),
                                "state": parts[2].strip(),
                                "has_stats_dept": None,
                                "verified": False,
                                "dept_url": None
                            })
            
            print(f"Loaded {len(self.universities)} universities")
            
        except Exception as e:
            print(f"Error loading universities: {str(e)}")
    
    def quick_verify(self, university):
        """Quick verification focusing on most common patterns"""
        # Extract domain for subdomain checking
        parsed_url = urlparse(university['url'])
        domain_parts = parsed_url.netloc.split('.')
        
        if len(domain_parts) >= 2:
            main_domain = '.'.join(domain_parts[-2:])
            
            # Try most common subdomain patterns
            subdomains = [
                f"https://statistics.{main_domain}",
                f"https://stat.{main_domain}",
                f"https://stats.{main_domain}"
            ]
            
            for subdomain in subdomains:
                try:
                    response = self.session.get(subdomain, timeout=3)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        title = soup.find('title')
                        title_text = title.get_text().lower() if title else ""
                        
                        # Quick check for statistics department indicators
                        if any(indicator in title_text for indicator in [
                            'statistics', 'statistical', 'stat'
                        ]):
                            return subdomain
                            
                except Exception:
                    continue
                    
                time.sleep(0.05)
        
        # Quick check of main site + /statistics
        try:
            base_url = university['url'].rstrip('/')
            test_url = base_url + '/statistics'
            response = self.session.get(test_url, timeout=3)
            if response.status_code == 200:
                return test_url
        except Exception:
            pass
            
        return None
    
    def verify_all(self, max_count=None):
        """Verify all universities quickly"""
        results = []
        verified_count = 0
        found_count = 0
        
        universities_to_check = self.universities[:max_count] if max_count else self.universities
        
        print(f"\nQuick verification of {len(universities_to_check)} universities...")
        print("=" * 80)
        
        for i, university in enumerate(universities_to_check):
            print(f"[{i+1:3d}/{len(universities_to_check)}] {university['name'][:50]:<50}", end=" ")
            
            dept_url = self.quick_verify(university)
            
            if dept_url:
                university['has_stats_dept'] = True
                university['dept_url'] = dept_url
                university['verified'] = True
                print("✅ FOUND")
                found_count += 1
            else:
                university['has_stats_dept'] = False
                university['dept_url'] = None
                university['verified'] = True
                print("❌")
            
            verified_count += 1
            results.append(university)
            
            time.sleep(0.1)  # Be respectful
        
        print("=" * 80)
        print(f"SUMMARY: {found_count}/{verified_count} universities have statistics departments")
        print(f"Success rate: {(found_count/verified_count)*100:.1f}%")
        
        return results
    
    def save_results(self, results, filename="verified_statistics_departments.json"):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"All results saved to {filename}")
        
        # Create separate file with only universities that have stats departments
        stats_only = [uni for uni in results if uni.get('has_stats_dept', False)]
        stats_filename = "universities_with_statistics_only.json"
        with open(stats_filename, 'w') as f:
            json.dump(stats_only, f, indent=2)
        print(f"Universities with statistics departments saved to {stats_filename}")
        
        # Also create a simple text list for easy reading
        text_filename = "statistics_departments_list.txt"
        with open(text_filename, 'w') as f:
            f.write("US UNIVERSITIES WITH VERIFIED STATISTICS DEPARTMENTS\n")
            f.write("=" * 60 + "\n\n")
            
            # Group by state
            by_state = {}
            for uni in stats_only:
                state = uni['state']
                if state not in by_state:
                    by_state[state] = []
                by_state[state].append(uni)
            
            for state in sorted(by_state.keys()):
                f.write(f"{state}:\n")
                f.write("-" * len(state) + "\n")
                for uni in by_state[state]:
                    f.write(f"  • {uni['name']}\n")
                    f.write(f"    University: {uni['url']}\n")
                    f.write(f"    Statistics Dept: {uni['dept_url']}\n")
                    f.write("\n")
                f.write("\n")
            
            f.write(f"TOTAL: {len(stats_only)} universities with statistics departments\n")
        
        print(f"Text summary saved to {text_filename}")
    
    def print_detailed_results(self, results):
        """Print detailed results"""
        print("\n" + "="*80)
        print("DETAILED RESULTS - UNIVERSITIES WITH STATISTICS DEPARTMENTS")
        print("="*80)
        
        # Group by state
        by_state = {}
        for uni in results:
            if uni['has_stats_dept']:
                state = uni['state']
                if state not in by_state:
                    by_state[state] = []
                by_state[state].append(uni)
        
        for state in sorted(by_state.keys()):
            print(f"\n{state}:")
            print("-" * len(state))
            for uni in by_state[state]:
                print(f"  • {uni['name']}")
                print(f"    University: {uni['url']}")
                print(f"    Statistics Dept: {uni['dept_url']}")
                print()

if __name__ == "__main__":
    verifier = FastStatsVerifier()
    verifier.load_universities()
    results = verifier.verify_all()  # Check ALL universities
    verifier.print_detailed_results(results)
    verifier.save_results(results)