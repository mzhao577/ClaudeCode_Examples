#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import re

def extract_students():
    url = "https://www.stat.purdue.edu/people/graduate_students/index.html"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        students = []
        
        # Look for all mailto links first to understand email structure
        email_links = soup.find_all('a', href=re.compile(r'^mailto:'))
        print(f"Found {len(email_links)} email links")
        
        # Find all student entries by looking for patterns
        # Try to find student blocks - look for combinations of h2/h3 tags with following content
        student_sections = []
        
        # Look for h2 or h3 tags that likely contain student names
        name_tags = soup.find_all(['h2', 'h3'])
        
        for name_tag in name_tags:
            name_text = name_tag.get_text(strip=True)
            # Skip if this doesn't look like a student name or is a section header
            if (not name_text or 
                len(name_text.split()) < 2 or 
                name_text.lower() in ['graduate students', 'students', 'current students'] or
                name_text.startswith('Current') or
                name_text.startswith('Graduate')):
                continue
                
            student_data = extract_student_info_improved(name_tag)
            if student_data and student_data['name']:
                students.append(student_data)
        
        return students
        
    except requests.RequestException as e:
        print(f"Error fetching webpage: {e}")
        return []

def extract_student_info_improved(name_tag):
    """Extract student info starting from name tag with improved email detection"""
    name = name_tag.get_text(strip=True)
    
    # Skip if this doesn't look like a student name
    if not name or len(name.split()) < 2:
        return None
    
    program = ""
    office = ""
    email = ""
    
    # Find the parent container that holds all student info
    parent = name_tag.parent
    if not parent:
        parent = name_tag
    
    # Look for email in the current element and all following siblings
    current = name_tag
    search_depth = 0
    
    while current and search_depth < 10:  # Limit search depth
        # Check current element for email
        email_link = current.find('a', href=re.compile(r'^mailto:'))
        if email_link:
            email = email_link.get('href').replace('mailto:', '')
            break
        
        # Check for text patterns that might contain emails
        text = current.get_text() if hasattr(current, 'get_text') else str(current)
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            email = email_match.group()
            break
        
        # Move to next sibling
        current = current.find_next_sibling()
        search_depth += 1
    
    # Reset and look for program and office info
    current = name_tag.find_next_sibling()
    while current and current.name in ['p', 'div', 'span']:
        text = current.get_text(strip=True)
        
        if 'Ph.D.' in text or 'PhD' in text or 'Ph.D' in text:
            program = "PhD"
        elif 'M.S.' in text or 'MS' in text or 'M.S' in text or 'Master' in text:
            program = "MS"
        elif 'Office:' in text or 'Office' in text:
            office = text.replace('Office:', '').strip()
            # Clean up office field if it contains email
            if 'Email:' in office:
                office = office.split('Email:')[0].strip()
        
        current = current.find_next_sibling()
    
    # If still no email found, try searching in parent container
    if not email and parent:
        email_link = parent.find('a', href=re.compile(r'^mailto:'))
        if email_link:
            email = email_link.get('href').replace('mailto:', '')
    
    return {
        'name': name,
        'program': program,
        'office': office,
        'email': email
    }

def extract_student_info_from_entry(entry):
    """Extract student info from a complete entry div"""
    name_tag = entry.find('h2')
    if not name_tag:
        return None
    
    name = name_tag.get_text(strip=True)
    program = ""
    office = ""
    email = ""
    
    # Extract program
    p_tags = entry.find_all('p')
    for p in p_tags:
        text = p.get_text(strip=True)
        if 'Ph.D.' in text or 'PhD' in text:
            program = "PhD"
        elif 'M.S.' in text or 'MS' in text:
            program = "MS"
        elif text.startswith('Office:') or 'Office' in text:
            office = text.replace('Office:', '').strip()
    
    # Extract email
    email_link = entry.find('a', href=re.compile(r'^mailto:'))
    if email_link:
        email = email_link.get('href').replace('mailto:', '')
    
    return {
        'name': name,
        'program': program,
        'office': office,
        'email': email
    }

def save_to_file(students, filename='students.csv'):
    """Save students data to CSV file"""
    import csv
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['Name', 'Program', 'Office', 'Email'])
        
        # Write student data
        for student in students:
            writer.writerow([student['name'], student['program'], student['office'], student['email']])
    
    print(f"Saved {len(students)} students to {filename}")

def main():
    print("Extracting student data from Purdue Statistics website...")
    students = extract_students()
    
    if students:
        save_to_file(students)
        print(f"Successfully extracted {len(students)} students")
        
        # Display first few entries for verification
        print("\nFirst 3 entries:")
        for i, student in enumerate(students[:3]):
            print(f"{i+1}. {student['name']} | {student['program']} | {student['office']} | {student['email']}")
    else:
        print("No student data found")

if __name__ == "__main__":
    main()