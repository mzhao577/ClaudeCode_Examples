import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, urlparse
import re

class UniversityStatsFinder:
    def __init__(self):
        self.universities_with_stats = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def load_universities_from_file(self, filename="known_US_universities.txt"):
        """Load universities from text file"""
        print(f"Loading universities from {filename}...")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            name = parts[0].strip()
                            url = parts[1].strip()
                            state = parts[2].strip()
                            
                            self.universities_with_stats.append({
                                "name": name,
                                "url": url,
                                "state": state,
                                "has_stats_dept": None,  # Unknown until verified
                                "verified": False,
                                "dept_url": None,
                                "verification_method": None
                            })
            
            print(f"Loaded {len(self.universities_with_stats)} universities from file")
            
        except FileNotFoundError:
            print(f"Error: Could not find {filename}")
            print("Please ensure the file exists in the current directory")
        except Exception as e:
            print(f"Error loading universities from file: {str(e)}")
    
    def find_statistics_department_url(self, university):
        """Find the specific statistics department URL for a university"""
        base_url = university['url'].rstrip('/')
        
        # Extract domain for subdomain checking
        from urllib.parse import urlparse
        parsed_url = urlparse(university['url'])
        domain_parts = parsed_url.netloc.split('.')
        
        # Create subdomain patterns for major universities
        subdomain_patterns = []
        if len(domain_parts) >= 2:
            main_domain = '.'.join(domain_parts[-2:])  # e.g., berkeley.edu, uchicago.edu
            subdomain_patterns = [
                f"https://statistics.{main_domain}",
                f"https://stat.{main_domain}",
                f"https://stats.{main_domain}",
                f"https://biostat.{main_domain}",
                f"https://biostatistics.{main_domain}",
                f"https://math.{main_domain}",
                f"https://mathematics.{main_domain}",
                f"https://data.{main_domain}",
                f"https://datascience.{main_domain}"
            ]
        
        # Much more comprehensive URL patterns
        url_patterns = [
            # Direct statistics patterns
            '/statistics', '/stats', '/stat',
            '/department-of-statistics', '/dept-of-statistics',
            '/departments/statistics', '/depts/statistics',
            '/academics/statistics', '/academic/statistics',
            '/schools/statistics', '/school-of-statistics',
            '/colleges/statistics', '/college-of-statistics',
            
            # Math + Statistics combined departments
            '/mathematics-statistics', '/math-statistics', '/math-stat',
            '/mathematical-sciences', '/math-sciences',
            '/departments/mathematics-statistics',
            '/departments/math-stat', '/departments/mathematical-sciences',
            '/math-and-statistics', '/mathematics-and-statistics',
            
            # Statistical Science variations
            '/statistical-science', '/statistical-sciences',
            '/dept-statistical-science', '/department-statistical-science',
            
            # Data Science (often includes statistics)
            '/statistics-data-science', '/data-science-statistics',
            '/statistics-and-data-science',
            
            # Biostatistics
            '/biostatistics', '/biostat', '/biostats',
            '/departments/biostatistics',
            
            # Graduate/Program specific
            '/programs/statistics', '/graduate/statistics',
            '/graduate-programs/statistics',
            '/phd/statistics', '/doctoral/statistics',
            
            # College/School specific patterns
            '/cas/statistics', '/liberal-arts/statistics',
            '/arts-sciences/statistics', '/college-arts-sciences/statistics',
            '/school-of-arts-and-sciences/statistics',
            
            # Common university-specific patterns
            '/academics/departments/statistics',
            '/academic-departments/statistics',
            '/faculty/statistics', '/research/statistics',
            
            # Alternative naming
            '/applied-statistics', '/theoretical-statistics',
            '/computational-statistics'
        ]
        
        print(f"  Searching URL patterns for {university['name']}...")
        
        # First try subdomain patterns (higher success rate)
        print(f"    Trying subdomains...")
        for subdomain_url in subdomain_patterns:
            try:
                response = self.session.get(subdomain_url, timeout=5)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    text_content = soup.get_text().lower()
                    title = soup.find('title')
                    title_text = title.get_text().lower() if title else ""
                    
                    # Enhanced content validation
                    strong_indicators = [
                        'department of statistics',
                        'statistics department',
                        'statistical science department',
                        'phd in statistics',
                        'doctorate in statistics',
                        'graduate program in statistics',
                        'master of statistics',
                        'ms in statistics',
                        'statistics faculty',
                        'statistics research'
                    ]
                    
                    # Check for strong indicators in title or content
                    strong_match = any(indicator in title_text or indicator in text_content 
                                     for indicator in strong_indicators)
                    
                    if strong_match:
                        print(f"    ✓ SUBDOMAIN MATCH found: {subdomain_url}")
                        return subdomain_url
                    
                    # Fallback: check for multiple stats-related terms
                    stats_terms = ['statistics', 'statistical', 'statistician', 'probability', 
                                  'data analysis', 'biostatistics', 'econometrics']
                    academic_terms = ['phd', 'graduate', 'faculty', 'research', 'degree', 
                                    'program', 'course', 'curriculum']
                    
                    stats_count = sum(1 for term in stats_terms if term in text_content)
                    academic_count = sum(1 for term in academic_terms if term in text_content)
                    
                    if stats_count >= 3 and academic_count >= 2:
                        print(f"    ✓ SUBDOMAIN PATTERN MATCH found: {subdomain_url}")
                        return subdomain_url
                
                time.sleep(0.3)
                
            except Exception as e:
                continue
        
        # Then try URL path patterns
        print(f"    Trying URL paths...")
        for pattern in url_patterns:
            try:
                test_url = base_url + pattern
                response = self.session.get(test_url, timeout=5)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    text_content = soup.get_text().lower()
                    title = soup.find('title')
                    title_text = title.get_text().lower() if title else ""
                    
                    # Enhanced content validation
                    strong_indicators = [
                        'department of statistics',
                        'statistics department',
                        'statistical science department',
                        'phd in statistics',
                        'doctorate in statistics',
                        'graduate program in statistics',
                        'master of statistics',
                        'ms in statistics',
                        'statistics faculty',
                        'statistics research'
                    ]
                    
                    # Check for strong indicators in title or content
                    strong_match = any(indicator in title_text or indicator in text_content 
                                     for indicator in strong_indicators)
                    
                    if strong_match:
                        print(f"    ✓ STRONG MATCH found: {test_url}")
                        return test_url
                    
                    # Fallback: check for multiple stats-related terms
                    stats_terms = ['statistics', 'statistical', 'statistician', 'probability', 
                                  'data analysis', 'biostatistics', 'econometrics']
                    academic_terms = ['phd', 'graduate', 'faculty', 'research', 'degree', 
                                    'program', 'course', 'curriculum']
                    
                    stats_count = sum(1 for term in stats_terms if term in text_content)
                    academic_count = sum(1 for term in academic_terms if term in text_content)
                    
                    if stats_count >= 3 and academic_count >= 2:
                        print(f"    ✓ PATTERN MATCH found: {test_url}")
                        return test_url
                
                time.sleep(0.3)
                
            except Exception as e:
                continue
        
        return None
    
    def search_university_site_for_stats(self, university):
        """Search the university's main site for statistics department links"""
        try:
            print(f"  Deep searching main site of {university['name']}...")
            response = self.session.get(university['url'], timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for links with statistics-related keywords
                potential_links = []
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href', '').lower()
                    text = link.get_text().strip().lower()
                    title = link.get('title', '').lower()
                    
                    # Enhanced keyword matching
                    stats_keywords = [
                        'statistic', 'math', 'data science', 'biostat',
                        'probability', 'analytics', 'quantitative',
                        'computational', 'applied math'
                    ]
                    
                    # Prioritize links with strong statistical indicators
                    if any(keyword in text for keyword in ['statistics', 'statistical']):
                        potential_links.insert(0, (href, text, 'high_priority'))
                    elif any(keyword in href for keyword in ['stat', 'math']):
                        potential_links.insert(0, (href, text, 'medium_priority'))  
                    elif any(keyword in href or keyword in text or keyword in title 
                           for keyword in stats_keywords):
                        potential_links.append((href, text, 'low_priority'))
                
                # Test potential links
                tested_count = 0
                for href, link_text, priority in potential_links:
                    if tested_count >= 15:  # Limit to avoid timeout
                        break
                        
                    # Construct full URL
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        full_url = university['url'].rstrip('/') + href
                    else:
                        full_url = university['url'].rstrip('/') + '/' + href
                    
                    # Skip obvious non-department pages
                    skip_patterns = ['news', 'events', 'calendar', 'contact', 'about', 
                                   'admissions', 'library', 'student']
                    if any(pattern in href for pattern in skip_patterns):
                        continue
                    
                    try:
                        print(f"    Testing link: {link_text[:50]}..." if link_text else f"    Testing: {href[:50]}...")
                        test_response = self.session.get(full_url, timeout=8)
                        tested_count += 1
                        
                        if test_response.status_code == 200:
                            test_soup = BeautifulSoup(test_response.content, 'html.parser')
                            test_content = test_soup.get_text().lower()
                            test_title = test_soup.find('title')
                            test_title_text = test_title.get_text().lower() if test_title else ""
                            
                            # Strong indicators of statistics department
                            strong_indicators = [
                                'department of statistics',
                                'statistics department',
                                'statistical science department',
                                'school of statistics',
                                'phd in statistics',
                                'graduate program in statistics',
                                'ms in statistics',
                                'statistics faculty'
                            ]
                            
                            # Check title and content for strong matches
                            if any(indicator in test_title_text or indicator in test_content 
                                 for indicator in strong_indicators):
                                print(f"    ✓ FOUND via site search: {full_url}")
                                return full_url
                            
                            # Medium strength check
                            if ('statistics' in test_content and 
                                any(term in test_content for term in ['graduate', 'phd', 'faculty', 'research', 'program'])):
                                stats_count = test_content.count('statistics') + test_content.count('statistical')
                                if stats_count >= 5:  # Must mention statistics multiple times
                                    print(f"    ✓ FOUND via content analysis: {full_url}")
                                    return full_url
                    
                    except Exception as e:
                        continue
                    
                    time.sleep(0.2)
            
        except Exception as e:
            print(f"    Error in site search: {str(e)}")
        
        return None
    
    def search_with_google_style(self, university):
        """Use targeted search terms to find statistics departments"""
        try:
            print(f"  Trying targeted search for {university['name']}...")
            
            # Try searching specific academic pages
            search_paths = [
                '/academics', '/departments', '/schools', '/colleges',
                '/graduate', '/research', '/faculty'
            ]
            
            base_url = university['url'].rstrip('/')
            
            for path in search_paths:
                try:
                    search_url = base_url + path
                    response = self.session.get(search_url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for any mention of statistics in this academic page
                        links = soup.find_all('a', href=True)
                        text_content = soup.get_text().lower()
                        
                        # If this page mentions statistics, explore it further
                        if 'statistics' in text_content or 'statistical' in text_content:
                            for link in links:
                                link_text = link.get_text().lower()
                                href = link.get('href', '').lower()
                                
                                if ('statistic' in link_text or 'statistic' in href or
                                    'math' in link_text and 'stat' in href):
                                    
                                    # Construct full URL
                                    if href.startswith('http'):
                                        full_url = href
                                    elif href.startswith('/'):
                                        full_url = base_url + href
                                    else:
                                        full_url = base_url + '/' + href
                                    
                                    # Test this potential statistics page
                                    try:
                                        test_response = self.session.get(full_url, timeout=8)
                                        if test_response.status_code == 200:
                                            test_soup = BeautifulSoup(test_response.content, 'html.parser')
                                            test_content = test_soup.get_text().lower()
                                            
                                            # Look for definitive signs of a statistics department
                                            definitive_signs = [
                                                'department of statistics',
                                                'statistics department',
                                                'statistics faculty',
                                                'phd statistics',
                                                'graduate statistics',
                                                'statistics program',
                                                'statistical science'
                                            ]
                                            
                                            if any(sign in test_content for sign in definitive_signs):
                                                print(f"    ✓ FOUND via targeted search: {full_url}")
                                                return full_url
                                    except:
                                        continue
                    
                    time.sleep(0.5)
                        
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"    Error in targeted search: {str(e)}")
        
        return None
    
    def verify_statistics_department(self, university):
        """Comprehensively verify if a university has a statistics department"""
        print(f"Checking {university['name']}...")
        
        # Method 1: Try common URL patterns
        print(f"  Method 1: URL patterns...")
        dept_url = self.find_statistics_department_url(university)
        
        # Method 2: If not found, search the main university site
        if not dept_url:
            print(f"  Method 2: Site search...")
            dept_url = self.search_university_site_for_stats(university)
        
        # Method 3: If still not found, try targeted academic page search
        if not dept_url:
            print(f"  Method 3: Targeted search...")
            dept_url = self.search_with_google_style(university)
        
        if dept_url:
            university['verified'] = True
            university['has_stats_dept'] = True
            university['dept_url'] = dept_url
            university['verification_method'] = 'found'
            print(f"  ✅ SUCCESS: {university['name']} has statistics department")
            print(f"      URL: {dept_url}")
            return True
        else:
            university['verified'] = True
            university['has_stats_dept'] = False
            university['dept_url'] = None
            university['verification_method'] = 'exhaustive_search_failed'
            print(f"  ❌ NOT FOUND: Could not locate statistics department for {university['name']}")
            return False
    
    def save_results(self, filename="us_universities_with_statistics.json"):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.universities_with_stats, f, indent=2)
        print(f"Results saved to {filename}")
    
    def print_results(self):
        """Print formatted results"""
        print("\n" + "="*80)
        print("US UNIVERSITIES - STATISTICS DEPARTMENT VERIFICATION RESULTS")
        print("="*80)
        
        verified_count = 0
        has_stats_count = 0
        total_count = len(self.universities_with_stats)
        
        # Group by state
        by_state = {}
        for uni in self.universities_with_stats:
            state = uni['state']
            if state not in by_state:
                by_state[state] = []
            by_state[state].append(uni)
            if uni.get('verified', False):
                verified_count += 1
            if uni.get('has_stats_dept', False):
                has_stats_count += 1
        
        for state in sorted(by_state.keys()):
            state_has_stats = any(uni.get('has_stats_dept', False) for uni in by_state[state])
            if state_has_stats:  # Only show states with at least one verified stats department
                print(f"\n{state}:")
                print("-" * len(state))
                for uni in by_state[state]:
                    if uni.get('has_stats_dept', False):
                        status = "✅ VERIFIED"
                        print(f"  • {uni['name']} - {status}")
                        print(f"    University: {uni['url']}")
                        print(f"    Statistics Dept: {uni['dept_url']}")
                        print()
        
        # Also show universities where no stats department was found
        print(f"\n{'='*80}")
        print("UNIVERSITIES WHERE NO STATISTICS DEPARTMENT WAS FOUND:")
        print("="*80)
        
        no_stats_count = 0
        for state in sorted(by_state.keys()):
            state_no_stats = [uni for uni in by_state[state] if uni.get('verified', False) and not uni.get('has_stats_dept', False)]
            if state_no_stats:
                print(f"\n{state}:")
                print("-" * len(state))
                for uni in state_no_stats:
                    print(f"  • {uni['name']} - ❌ No Statistics Department Found")
                    no_stats_count += 1
        
        print("\n" + "="*80)
        print("SUMMARY:")
        print(f"Total universities checked: {verified_count}")
        print(f"Universities WITH Statistics Departments: {has_stats_count}")
        print(f"Universities WITHOUT Statistics Departments: {no_stats_count}")
        print(f"Success rate: {(has_stats_count/verified_count)*100:.1f}%" if verified_count > 0 else "0%")
        print("="*80)
    
    def run(self, max_verify=20):
        """Main execution method"""
        print("Starting comprehensive verification of US universities with Statistics departments...")
        
        # Load list of universities from file
        self.load_universities_from_file()
        
        print(f"\nLoaded {len(self.universities_with_stats)} universities")
        print(f"Will verify first {max_verify} universities for demonstration")
        print("=" * 80)
        
        # Verify universities (limit to avoid overwhelming servers during demo)
        verified_count = 0
        for i, university in enumerate(self.universities_with_stats):
            if verified_count >= max_verify:
                break
                
            self.verify_statistics_department(university)
            verified_count += 1
            
            # Add a small delay to be respectful to servers
            time.sleep(0.5)
        
        print("\n" + "=" * 80)
        print("VERIFICATION COMPLETE")
        print("=" * 80)
        
        # Print and save results
        self.print_results()
        self.save_results()

if __name__ == "__main__":
    finder = UniversityStatsFinder()
    finder.run(25)  # Check first 25 universities as demonstration