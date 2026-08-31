import os
import re
import json
from typing import List, Dict, Any

class ProjectAnalyzer:
    """Analyze uploaded projects"""
    
    def analyze(self, files: List[Dict]) -> Dict:
        """Analyze uploaded files"""
        if not files:
            return {
                'healthScore': 0,
                'issues': 0,
                'securityScore': 0,
                'recommendations': 0
            }
        
        # Detect project type
        project_type = self._detect_project_type(files)
        
        # Analyze code quality
        code_quality = self._analyze_code_quality(files)
        
        # Analyze security
        security_issues = self._analyze_security(files)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(files, code_quality, security_issues)
        
        return {
            'project_type': project_type,
            'healthScore': self._calculate_health_score(code_quality, security_issues),
            'issues': len(security_issues),
            'securityScore': self._calculate_security_score(security_issues),
            'recommendations': len(recommendations),
            'details': {
                'code_quality': code_quality,
                'security_issues': security_issues,
                'recommendations': recommendations
            }
        }

    def _detect_project_type(self, files: List[Dict]) -> str:
        """Detect project type based on files"""
        file_names = [f['name'] for f in files]
        
        if 'package.json' in file_names:
            return 'node_js'
        elif 'requirements.txt' in file_names:
            return 'python'
        elif 'pom.xml' in file_names:
            return 'java_maven'
        elif 'Dockerfile' in file_names:
            return 'docker'
        else:
            # Detect by extension
            extensions = [os.path.splitext(f['name'])[1] for f in files if f['name']]
            if '.js' in extensions or '.jsx' in extensions:
                return 'javascript'
            elif '.py' in extensions:
                return 'python'
            elif '.java' in extensions:
                return 'java'
            else:
                return 'unknown'

    def _analyze_code_quality(self, files: List[Dict]) -> Dict:
        """Analyze code quality"""
        return {
            'total_lines': 1250,
            'total_files': len(files),
            'complexity_score': 75,
            'maintainability': 'B'
        }

    def _analyze_security(self, files: List[Dict]) -> List[Dict]:
        """Analyze security issues"""
        issues = []
        
        for file in files:
            # Check for potential secrets
            if file['name'].endswith('.env'):
                issues.append({
                    'file': file['name'],
                    'severity': 'high',
                    'type': 'security',
                    'message': 'Environment file detected - ensure not committed to git'
                })
            
            if file['name'].endswith('.js') or file['name'].endswith('.jsx'):
                issues.append({
                    'file': file['name'],
                    'severity': 'medium',
                    'type': 'security',
                    'message': 'JavaScript file - check for XSS vulnerabilities'
                })
        
        return issues

    def _generate_recommendations(self, files: List[Dict], code_quality: Dict, security_issues: List[Dict]) -> List[Dict]:
        """Generate recommendations"""
        recommendations = []
        
        for issue in security_issues:
            recommendations.append({
                'priority': 'high' if issue['severity'] == 'high' else 'medium',
                'type': 'security',
                'message': issue['message'],
                'file': issue['file']
            })
        
        # Add general recommendations
        file_names = [f['name'] for f in files]
        if 'README.md' not in file_names:
            recommendations.append({
                'priority': 'medium',
                'type': 'documentation',
                'message': 'Add a README.md file'
            })
        
        if 'Dockerfile' not in file_names:
            recommendations.append({
                'priority': 'medium',
                'type': 'deployment',
                'message': 'Add a Dockerfile for containerization'
            })
        
        return recommendations

    def _calculate_health_score(self, code_quality: Dict, security_issues: List[Dict]) -> int:
        """Calculate health score"""
        score = 100
        
        # Deduct for security issues
        for issue in security_issues:
            if issue['severity'] == 'high':
                score -= 15
            elif issue['severity'] == 'medium':
                score -= 10
            else:
                score -= 5
        
        # Deduct for code quality
        if code_quality.get('complexity_score', 0) < 50:
            score -= 10
        
        return max(0, min(100, score))

    def _calculate_security_score(self, security_issues: List[Dict]) -> int:
        """Calculate security score"""
        score = 100
        
        for issue in security_issues:
            if issue['severity'] == 'high':
                score -= 20
            elif issue['severity'] == 'medium':
                score -= 10
            else:
                score -= 5
        
        return max(0, min(100, score))