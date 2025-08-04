import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse

class PhDStatsRequirementsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.universities_with_stats = []
        self.phd_requirements = []
    
    def load_universities_with_stats(self, filename="universities_with_statistics_only.json"):
        """Load universities that have statistics departments"""
        try:
            with open(filename, 'r') as f:
                self.universities_with_stats = json.load(f)
            print(f"Loaded {len(self.universities_with_stats)} universities with statistics departments")
        except FileNotFoundError:
            print(f"Error: Could not find {filename}")
            print("Please run the verification script first to generate this file")
            return False
        return True
    
    def find_phd_pages(self, university):
        """Find PhD program pages for a university's statistics department"""
        dept_url = university['dept_url']
        base_url = dept_url.rstrip('/')
        
        # Common patterns for PhD program pages
        phd_patterns = [
            '/phd',
            '/doctoral',
            '/graduate',
            '/graduate-programs',
            '/phd-program',
            '/doctoral-program',
            '/graduate/phd',
            '/academics/phd',
            '/academics/graduate',
            '/programs/phd',
            '/programs/doctoral',
            '/admissions',
            '/admissions/phd',
            '/graduate-admissions',
            '/prospective-students',
            '/apply'
        ]
        
        phd_urls = []
        
        # Try direct patterns first
        for pattern in phd_patterns:
            try:
                test_url = base_url + pattern
                response = self.session.get(test_url, timeout=5)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    text_content = soup.get_text().lower()
                    title = soup.find('title')
                    title_text = title.get_text().lower() if title else ""
                    
                    # Check if this page is about PhD programs
                    phd_indicators = [
                        'phd program', 'doctoral program', 'ph.d.', 'doctorate',
                        'graduate program', 'phd in statistics', 'doctoral statistics',
                        'admission requirements', 'application requirements'
                    ]
                    
                    if any(indicator in title_text or indicator in text_content for indicator in phd_indicators):
                        phd_urls.append(test_url)
                        print(f"    Found PhD page: {test_url}")
                
                time.sleep(0.2)
                
            except Exception as e:
                continue
        
        # If no direct patterns found, search the main department page for links
        if not phd_urls:
            try:
                response = self.session.get(dept_url, timeout=8)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    links = soup.find_all('a', href=True)
                    
                    for link in links:
                        href = link.get('href', '').lower()
                        text = link.get_text().strip().lower()
                        
                        # Look for PhD-related links
                        if any(keyword in href or keyword in text for keyword in [
                            'phd', 'doctoral', 'graduate', 'admission', 'apply'
                        ]):
                            # Construct full URL
                            if href.startswith('http'):
                                full_url = href
                            elif href.startswith('/'):
                                parsed_base = urlparse(dept_url)
                                full_url = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
                            else:
                                full_url = urljoin(dept_url, href)
                            
                            # Avoid duplicate URLs and non-relevant pages
                            if (full_url not in phd_urls and 
                                not any(skip in full_url.lower() for skip in ['news', 'events', 'faculty', 'contact'])):
                                phd_urls.append(full_url)
                                if len(phd_urls) >= 3:  # Limit to avoid too many requests
                                    break
            except Exception as e:
                pass
        
        return phd_urls[:3]  # Return top 3 most relevant URLs
    
    def extract_requirements(self, url):
        """Extract PhD requirements from a webpage"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text()
            
            requirements = {
                'url': url,
                'gre_required': None,
                'gpa_requirement': None,
                'prerequisites': [],
                'application_deadline': None,
                'research_areas': [],
                'duration': None,
                'funding_info': None,
                'raw_requirements': None
            }
            
            # Extract GRE requirements
            gre_patterns = [
                r'gre.*(?:required|not required|optional)',
                r'graduate record exam.*(?:required|not required|optional)',
                r'(?:requires?|need|must have).*gre',
                r'gre.*(?:waived|waiver)'
            ]
            
            for pattern in gre_patterns:
                matches = re.findall(pattern, text_content.lower())
                if matches:
                    if any(word in matches[0] for word in ['not required', 'optional', 'waived', 'waiver']):
                        requirements['gre_required'] = False
                    else:
                        requirements['gre_required'] = True
                    break
            
            # Extract GPA requirements
            gpa_patterns = [
                r'gpa.*?(\d+\.?\d*)',
                r'grade point average.*?(\d+\.?\d*)',
                r'minimum.*?gpa.*?(\d+\.?\d*)',
                r'(\d+\.?\d*).*?gpa.*?(?:required|minimum)'
            ]
            
            for pattern in gpa_patterns:
                matches = re.findall(pattern, text_content.lower())
                if matches:
                    try:
                        gpa = float(matches[0])
                        if 2.0 <= gpa <= 4.0:  # Reasonable GPA range
                            requirements['gpa_requirement'] = gpa
                            break
                    except:
                        continue
            
            # Extract prerequisites
            prereq_keywords = [
                'prerequisite', 'background', 'preparation', 'coursework',
                'mathematics', 'calculus', 'linear algebra', 'statistics',
                'probability', 'programming', 'computer science'
            ]
            
            prereq_text = []
            for keyword in prereq_keywords:
                pattern = rf'{keyword}[^.]*\.'
                matches = re.findall(pattern, text_content.lower())
                prereq_text.extend(matches[:2])  # Limit to avoid too much text
            
            requirements['prerequisites'] = prereq_text[:5]  # Top 5 most relevant
            
            # Extract application deadlines
            deadline_patterns = [
                r'(?:deadline|due|apply by).*?(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}',
                r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}.*?(?:deadline|due)',
                r'\d{1,2}/\d{1,2}/\d{4}.*?(?:deadline|due)',
                r'(?:deadline|due).*?\d{1,2}/\d{1,2}/\d{4}'
            ]
            
            for pattern in deadline_patterns:
                matches = re.findall(pattern, text_content.lower())
                if matches:
                    requirements['application_deadline'] = matches[0]
                    break
            
            # Extract research areas
            research_keywords = [
                'research areas', 'research interests', 'specializations',
                'biostatistics', 'machine learning', 'data science',
                'bayesian', 'computational', 'theoretical', 'applied statistics'
            ]
            
            research_areas = []
            for keyword in research_keywords:
                if keyword.lower() in text_content.lower():
                    research_areas.append(keyword)
            
            requirements['research_areas'] = research_areas
            
            # Extract program duration
            duration_patterns = [
                r'(\d+)\s*(?:year|yr)s?\s*(?:program|degree)',
                r'(?:program|degree).*?(\d+)\s*(?:year|yr)s?',
                r'typically.*?(\d+)\s*(?:year|yr)s?'
            ]
            
            for pattern in duration_patterns:
                matches = re.findall(pattern, text_content.lower())
                if matches:
                    try:
                        duration = int(matches[0])
                        if 3 <= duration <= 8:  # Reasonable duration range
                            requirements['duration'] = f"{duration} years"
                            break
                    except:
                        continue
            
            # Extract funding information
            funding_keywords = [
                'funding', 'assistantship', 'fellowship', 'scholarship',
                'tuition waiver', 'stipend', 'financial support'
            ]
            
            funding_info = []
            for keyword in funding_keywords:
                if keyword.lower() in text_content.lower():
                    # Extract sentence containing funding info
                    pattern = rf'[^.]*{keyword}[^.]*\.'
                    matches = re.findall(pattern, text_content.lower(), re.IGNORECASE)
                    if matches:
                        funding_info.extend(matches[:2])
            
            requirements['funding_info'] = funding_info[:3]  # Top 3 most relevant
            
            # Store a snippet of raw requirements text
            req_section = self.find_requirements_section(soup)
            if req_section:
                requirements['raw_requirements'] = req_section[:500] + "..." if len(req_section) > 500 else req_section
            
            return requirements
            
        except Exception as e:
            print(f"    Error extracting requirements from {url}: {str(e)}")
            return None
    
    def find_requirements_section(self, soup):
        """Find the requirements section in the HTML"""
        # Look for headings that might contain requirements
        requirement_headings = [
            'admission requirements', 'application requirements', 'prerequisites',
            'requirements', 'how to apply', 'application process'
        ]
        
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            heading_text = heading.get_text().lower()
            if any(req_heading in heading_text for req_heading in requirement_headings):
                # Get the next few paragraphs after this heading
                content = []
                next_element = heading.find_next_sibling()
                while next_element and len(content) < 3:
                    if next_element.name in ['p', 'ul', 'ol', 'div']:
                        text = next_element.get_text().strip()
                        if text:
                            content.append(text)
                    next_element = next_element.find_next_sibling()
                
                if content:
                    return ' '.join(content)
        
        return None
    
    def scrape_university_requirements(self, university):
        """Scrape PhD requirements for a single university"""
        print(f"Scraping requirements for {university['name']}...")
        
        # Find PhD program pages
        phd_urls = self.find_phd_pages(university)
        
        if not phd_urls:
            print(f"  No PhD pages found for {university['name']}")
            return None
        
        # Extract requirements from found pages
        all_requirements = []
        for url in phd_urls:
            print(f"  Checking: {url}")
            requirements = self.extract_requirements(url)
            if requirements:
                all_requirements.append(requirements)
        
        if not all_requirements:
            return None
        
        # Combine requirements from multiple pages
        combined_requirements = self.combine_requirements(all_requirements)
        
        return {
            'university': university['name'],
            'state': university['state'],
            'university_url': university['url'],
            'dept_url': university['dept_url'],
            'requirements': combined_requirements,
            'last_updated': time.strftime('%Y-%m-%d')
        }
    
    def combine_requirements(self, requirements_list):
        """Combine requirements from multiple pages"""
        combined = {
            'gre_required': None,
            'gpa_requirement': None,
            'prerequisites': [],
            'application_deadline': None,
            'research_areas': [],
            'duration': None,
            'funding_info': [],
            'source_urls': [],
            'raw_requirements': []
        }
        
        for req in requirements_list:
            combined['source_urls'].append(req['url'])
            
            # Take the first non-None value for binary fields
            if combined['gre_required'] is None and req['gre_required'] is not None:
                combined['gre_required'] = req['gre_required']
            
            if combined['gpa_requirement'] is None and req['gpa_requirement'] is not None:
                combined['gpa_requirement'] = req['gpa_requirement']
            
            if combined['application_deadline'] is None and req['application_deadline'] is not None:
                combined['application_deadline'] = req['application_deadline']
            
            if combined['duration'] is None and req['duration'] is not None:
                combined['duration'] = req['duration']
            
            # Combine lists, avoiding duplicates
            combined['prerequisites'].extend(req['prerequisites'])
            combined['research_areas'].extend(req['research_areas'])
            combined['funding_info'].extend(req['funding_info'])
            
            if req['raw_requirements']:
                combined['raw_requirements'].append(req['raw_requirements'])
        
        # Remove duplicates from lists
        combined['prerequisites'] = list(set(combined['prerequisites']))[:5]
        combined['research_areas'] = list(set(combined['research_areas']))
        combined['funding_info'] = list(set(combined['funding_info']))[:3]
        
        return combined
    
    def scrape_all_requirements(self, max_universities=None):
        """Scrape PhD requirements for all universities"""
        universities_to_check = self.universities_with_stats[:max_universities] if max_universities else self.universities_with_stats
        
        print(f"Scraping PhD requirements for {len(universities_to_check)} universities...")
        print("=" * 80)
        
        for i, university in enumerate(universities_to_check):
            print(f"[{i+1:2d}/{len(universities_to_check)}] {university['name']}")
            
            requirements = self.scrape_university_requirements(university)
            if requirements:
                self.phd_requirements.append(requirements)
                print(f"  ✅ Requirements extracted")
            else:
                print(f"  ❌ No requirements found")
            
            time.sleep(1)  # Be respectful to servers
            print()
        
        print("=" * 80)
        print(f"Successfully extracted requirements for {len(self.phd_requirements)} universities")
        
        return self.phd_requirements
    
    def save_requirements(self, filename="phd_statistics_requirements.json"):
        """Save requirements to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.phd_requirements, f, indent=2)
        print(f"Requirements saved to {filename}")
    
    def generate_summary_report(self, filename="phd_requirements_summary.txt"):
        """Generate a human-readable summary report"""
        with open(filename, 'w') as f:
            f.write("PhD STATISTICS PROGRAM REQUIREMENTS SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            for req in self.phd_requirements:
                f.write(f"{req['university']} ({req['state']})\n")
                f.write("-" * len(req['university']) + "\n")
                f.write(f"Department URL: {req['dept_url']}\n")
                
                requirements = req['requirements']
                
                # GRE requirement
                if requirements['gre_required'] is not None:
                    gre_status = "Required" if requirements['gre_required'] else "Not Required/Optional"
                    f.write(f"GRE: {gre_status}\n")
                
                # GPA requirement  
                if requirements['gpa_requirement']:
                    f.write(f"Minimum GPA: {requirements['gpa_requirement']}\n")
                
                # Duration
                if requirements['duration']:
                    f.write(f"Program Duration: {requirements['duration']}\n")
                
                # Application deadline
                if requirements['application_deadline']:
                    f.write(f"Application Deadline: {requirements['application_deadline']}\n")
                
                # Prerequisites
                if requirements['prerequisites']:
                    f.write("Prerequisites/Background:\n")
                    for prereq in requirements['prerequisites'][:3]:
                        f.write(f"  • {prereq}\n")
                
                # Research areas
                if requirements['research_areas']:
                    f.write(f"Research Areas: {', '.join(requirements['research_areas'])}\n")
                
                # Funding info
                if requirements['funding_info']:
                    f.write("Funding Information:\n")
                    for funding in requirements['funding_info'][:2]:
                        f.write(f"  • {funding}\n")
                
                f.write(f"\nSource URLs: {', '.join(requirements['source_urls'])}\n")
                f.write("\n" + "="*80 + "\n\n")
        
        print(f"Summary report saved to {filename}")

if __name__ == "__main__":
    scraper = PhDStatsRequirementsScraper()
    
    # Load universities with statistics departments
    if not scraper.load_universities_with_stats():
        exit(1)
    
    # Scrape requirements for first 5 universities as demo
    # Remove the limit (5) to process all universities
    requirements = scraper.scrape_all_requirements(5)
    
    # Save results
    scraper.save_requirements()
    scraper.generate_summary_report()
    
    print("\nScraping complete! Check the output files:")
    print("- phd_statistics_requirements.json (detailed JSON data)")
    print("- phd_requirements_summary.txt (human-readable summary)")