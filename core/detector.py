# core/detector.py
"""
Detects when websites change their structure.
This is crucial for maintaining scrapers.
"""

import hashlib
from difflib import SequenceMatcher
from typing import Dict, Any, List, Tuple
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime

class StructureDetector:
    """
    Compares current HTML with baseline to detect changes.
    """
    
    def __init__(self, site_name: str):
        self.site_name = site_name
        self.baseline_dir = Path("data/baselines")
        self.baseline_dir.mkdir(exist_ok=True)
        self.baseline_file = self.baseline_dir / f"{site_name}_baseline.json"
    
    def save_baseline(self, html: str, important_selectors: List[str] = None):
        """
        Save HTML structure as baseline for future comparison.
        """
        # Parse HTML and extract structure
        soup = BeautifulSoup(html, 'html.parser')
        
        # Create structural fingerprint
        structure = {
            'timestamp': datetime.now().isoformat(),
            'site_name': self.site_name,
            'elements': self._extract_structure(soup),
            'important_sections': {}
        }
        
        # If specific selectors provided, save their HTML too
        if important_selectors:
            for selector in important_selectors:
                elements = soup.select(selector)
                structure['important_sections'][selector] = [
                    str(el) for el in elements
                ]
        
        # Save to file
        with open(self.baseline_file, 'w') as f:
            json.dump(structure, f, indent=2)
        
        self.logger.info(f"Saved baseline for {self.site_name}")
    
    def _extract_structure(self, soup) -> Dict:
        """
        Extract structural elements from HTML.
        Looks at tags, classes, IDs - not content.
        """
        structure = {
            'tags': {},
            'classes': set(),
            'ids': set(),
            'depth': 0
        }
        
        # Find all elements
        for tag in soup.find_all(True):
            tag_name = tag.name
            structure['tags'][tag_name] = structure['tags'].get(tag_name, 0) + 1
            
            # Collect classes
            if tag.get('class'):
                structure['classes'].update(tag.get('class'))
            
            # Collect IDs
            if tag.get('id'):
                structure['ids'].add(tag.get('id'))
        
        # Convert sets to lists for JSON
        structure['classes'] = list(structure['classes'])
        structure['ids'] = list(structure['ids'])
        
        return structure
    
    def compare_with_baseline(self, current_html: str) -> Dict[str, Any]:
        """
        Compare current HTML with baseline.
        Returns change report.
        """
        if not self.baseline_file.exists():
            return {'error': 'No baseline found'}
        
        # Load baseline
        with open(self.baseline_file) as f:
            baseline = json.load(f)
        
        # Parse current HTML
        current_soup = BeautifulSoup(current_html, 'html.parser')
        current_structure = self._extract_structure(current_soup)
        
        # Compare
        changes = {
            'site_name': self.site_name,
            'timestamp': datetime.now().isoformat(),
            'changes_detected': False,
            'tag_changes': {},
            'new_classes': [],
            'missing_classes': [],
            'new_ids': [],
            'missing_ids': [],
            'similarity_score': 0,
            'affected_selectors': []
        }
        
        # Compare tag counts
        baseline_tags = baseline['elements']['tags']
        current_tags = current_structure['tags']
        
        all_tags = set(baseline_tags.keys()) | set(current_tags.keys())
        for tag in all_tags:
            baseline_count = baseline_tags.get(tag, 0)
            current_count = current_tags.get(tag, 0)
            
            if baseline_count != current_count:
                changes['tag_changes'][tag] = {
                    'baseline': baseline_count,
                    'current': current_count,
                    'difference': current_count - baseline_count
                }
                changes['changes_detected'] = True
        
        # Compare classes
        baseline_classes = set(baseline['elements']['classes'])
        current_classes = set(current_structure['classes'])
        
        changes['new_classes'] = list(current_classes - baseline_classes)
        changes['missing_classes'] = list(baseline_classes - current_classes)
        
        if changes['new_classes'] or changes['missing_classes']:
            changes['changes_detected'] = True
        
        # Compare IDs
        baseline_ids = set(baseline['elements']['ids'])
        current_ids = set(current_structure['ids'])
        
        changes['new_ids'] = list(current_ids - baseline_ids)
        changes['missing_ids'] = list(baseline_ids - current_ids)
        
        if changes['new_ids'] or changes['missing_ids']:
            changes['changes_detected'] = True
        
        # Calculate overall similarity score
        # (0 = completely different, 1 = identical)
        changes['similarity_score'] = self._calculate_similarity(
            baseline['elements'],
            current_structure
        )
        
        # Identify which of our important selectors might be affected
        if 'important_sections' in baseline:
            for selector in baseline['important_sections'].keys():
                elements = current_soup.select(selector)
                if not elements:
                    changes['affected_selectors'].append(selector)
        
        return changes
    
    def _calculate_similarity(self, baseline, current) -> float:
        """Calculate how similar two structures are (0-1)."""
        scores = []
        
        # Compare tag distributions
        baseline_tags = baseline.get('tags', {})
        current_tags = current.get('tags', {})
        
        all_tags = set(baseline_tags.keys()) | set(current_tags.keys())
        if all_tags:
            tag_score = sum(
                min(baseline_tags.get(t, 0), current_tags.get(t, 0)) 
                for t in all_tags
            ) / max(sum(baseline_tags.values()), sum(current_tags.values()), 1)
            scores.append(tag_score)
        
        # Compare class sets
        baseline_classes = set(baseline.get('classes', []))
        current_classes = set(current.get('classes', []))
        
        if baseline_classes or current_classes:
            class_intersection = baseline_classes & current_classes
            class_union = baseline_classes | current_classes
            if class_union:
                class_score = len(class_intersection) / len(class_union)
                scores.append(class_score)
        
        # Average scores
        return sum(scores) / len(scores) if scores else 1.0
    
    def suggest_fixes(self, changes: Dict) -> List[str]:
        """
        Suggest how to fix scrapers based on detected changes.
        """
        suggestions = []
        
        if changes.get('similarity_score', 1) < 0.5:
            suggestions.append("Major structure change - entire page may be redesigned")
        
        for selector in changes.get('affected_selectors', []):
            suggestions.append(f"Selector '{selector}' no longer finds elements")
            
            # Suggest alternative based on new classes/IDs
            if changes['new_classes']:
                suggestions.append(f"Try using new class: {changes['new_classes'][0]}")
            if changes['new_ids']:
                suggestions.append(f"Try using new ID: {changes['new_ids'][0]}")
        
        if changes.get('tag_changes'):
            tags = list(changes['tag_changes'].keys())[:3]
            suggestions.append(f"Tag counts changed for: {', '.join(tags)}")
        
        return suggestions if suggestions else ["No automatic fixes available"]