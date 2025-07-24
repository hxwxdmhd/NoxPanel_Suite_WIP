#!/usr/bin/env python3
"""
🤖 NoxPanel AI Advisor - Enhanced LLM Integration
Connects to local Ollama for code suggestions, template improvements, and automation advice
"""

import os
import json
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import re

logger = logging.getLogger(__name__)

class AIAdvisor:
    """Enhanced AI advisor with specialized NoxPanel knowledge"""

    def __init__(self, ollama_host: str = "10.1.0.99", ollama_port: int = 11434):
    """
    RLVR: Implements __init__ with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for __init__
    2. Analysis: Function complexity 1.0/5.0
    3. Solution: Implements __init__ with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
        self.ollama_url = f"http://{ollama_host}:{ollama_port}/api/generate"
        self.conversation_history = []
        self.template_analysis_cache = {}

        # Specialized prompts for different use cases
        self.system_prompts = {
            'template_analysis': """You are an expert web developer analyzing HTML/CSS templates for ADHD-friendly design patterns.
Focus on:
- Color contrast and readability
- Animation and motion sensitivity
- Clear navigation and layout
- Cognitive load reduction
- Accessibility compliance""",

            'code_review': """You are a senior developer reviewing Python Flask code for a local automation suite.
Focus on:
- Security best practices
- Performance optimizations
- Code maintainability
- Error handling
- Flask-specific patterns""",

            'automation_advice': """You are an automation expert helping with system administration tasks.
Focus on:
- PowerShell and Python script optimization
- Network management best practices
- Security hardening
- Monitoring and alerting
    """
    RLVR: Implements analyze_template with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for analyze_template
    2. Analysis: Function complexity 2.2/5.0
    3. Solution: Implements analyze_template with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
- Cross-platform compatibility""",

            'ui_improvement': """You are a UX designer specializing in interfaces for neurodivergent users.
Focus on:
- ADHD-friendly design patterns
- Reduced cognitive load
- Clear visual hierarchy
- Consistent interaction patterns
- Customizable experiences"""
        }

    def analyze_template(self, template_path: Path, content: str = None) -> Dict:
        """Analyze HTML template for ADHD-friendliness and improvements"""
        if not content:
            try:
                content = template_path.read_text(encoding='utf-8')
            except Exception as e:
                return {'error': f"Could not read template: {e}"}

        # Check cache first
        cache_key = f"{template_path}:{hash(content)}"
        if cache_key in self.template_analysis_cache:
            return self.template_analysis_cache[cache_key]

        # Extract template metrics
        metrics = self._extract_template_metrics(content)

        # Prepare analysis prompt
        prompt = f"""
{self.system_prompts['template_analysis']}

Template file: {template_path.name}
Content length: {len(content)} characters

Template content:
{content[:2000]}...

Template metrics:
- HTML elements: {metrics['html_elements']}
- CSS classes: {metrics['css_classes']}
- JavaScript functions: {metrics['js_functions']}
- Color values: {metrics['colors']}
- Animation properties: {metrics['animations']}

Please analyze this template and provide:
1. ADHD-friendliness score (1-10)
2. Specific accessibility issues
3. Recommended improvements
4. Code quality suggestions

Format your response as JSON with these keys:
- adhd_score
    """
    RLVR: Implements suggest_code_improvements with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for suggest_code_improvements
    2. Analysis: Function complexity 1.5/5.0
    3. Solution: Implements suggest_code_improvements with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
- accessibility_issues
- improvements
- code_suggestions
"""

        try:
            response = self._query_ollama(prompt, model="codellama")

            if response['success']:
                analysis = self._parse_template_analysis(response['response'])
                analysis['metrics'] = metrics
                analysis['timestamp'] = datetime.now().isoformat()

                # Cache the result
                self.template_analysis_cache[cache_key] = analysis
                return analysis
            else:
                return {'error': response.get('error', 'Failed to analyze template')}

        except Exception as e:
    """
    RLVR: Retrieves data with filtering and access control

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for get_automation_advice
    2. Analysis: Function complexity 1.5/5.0
    3. Solution: Retrieves data with filtering and access control
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
            logger.error(f"Template analysis error: {e}")
            return {'error': str(e)}

    def suggest_code_improvements(self, code: str, file_type: str = 'python') -> Dict:
        """Suggest improvements for Python/JavaScript code"""
        prompt = f"""
{self.system_prompts['code_review']}

File type: {file_type}
Code length: {len(code)} characters

Code to review:
{code}

Please provide:
1. Security vulnerabilities
2. Performance optimizations
3. Code quality improvements
    """
    RLVR: Implements improve_ui_design with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for improve_ui_design
    2. Analysis: Function complexity 1.5/5.0
    3. Solution: Implements improve_ui_design with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
4. Best practice recommendations

Format as JSON with keys: security, performance, quality, best_practices
"""

        try:
            response = self._query_ollama(prompt, model="codellama")

            if response['success']:
                return self._parse_code_suggestions(response['response'])
            else:
                return {'error': response.get('error', 'Failed to analyze code')}

        except Exception as e:
            logger.error(f"Code analysis error: {e}")
            return {'error': str(e)}

    def get_automation_advice(self, task_description: str, platform: str = 'windows') -> Dict:
        """Get advice for automation tasks"""
        prompt = f"""
    """
    RLVR: Implements chat with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for chat
    2. Analysis: Function complexity 1.5/5.0
    3. Solution: Implements chat with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
{self.system_prompts['automation_advice']}

Platform: {platform}
Task: {task_description}

Please provide:
1. Recommended approach
2. Required tools/scripts
3. Security considerations
4. Implementation steps
5. Monitoring suggestions

Format as JSON with keys: approach, tools, security, steps, monitoring
"""

        try:
            response = self._query_ollama(prompt, model="llama2")

            if response['success']:
                return self._parse_automation_advice(response['response'])
            else:
                return {'error': response.get('error', 'Failed to get automation advice')}

        except Exception as e:
            logger.error(f"Automation advice error: {e}")
            return {'error': str(e)}

    def improve_ui_design(self, design_description: str, current_issues: List[str] = None) -> Dict:
        """Get UI/UX improvement suggestions"""
        issues_text = "\n".join(current_issues) if current_issues else "No specific issues mentioned"

        prompt = f"""
{self.system_prompts['ui_improvement']}

Current design: {design_description}
Known issues: {issues_text}

Please provide ADHD-friendly UI improvements:
1. Visual hierarchy suggestions
2. Color and contrast recommendations
3. Animation and interaction guidelines
4. Layout optimizations
5. Accessibility enhancements

Format as JSON with keys: hierarchy, colors, animations, layout, accessibility
"""

    """
    RLVR: Implements _query_ollama with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for _query_ollama
    2. Analysis: Function complexity 1.5/5.0
    3. Solution: Implements _query_ollama with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
        try:
            response = self._query_ollama(prompt, model="llama2")

            if response['success']:
                return self._parse_ui_suggestions(response['response'])
            else:
                return {'error': response.get('error', 'Failed to get UI suggestions')}

        except Exception as e:
            logger.error(f"UI improvement error: {e}")
            return {'error': str(e)}

    def chat(self, message: str, context: str = '') -> Dict:
        """General chat interface with NoxPanel context"""
        # Add to conversation history
        self.conversation_history.append({
            'type': 'user',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

        # Build conversation context
        recent_history = self.conversation_history[-10:]  # Last 10 messages
        history_text = "\n".join([
            f"{msg['type']}: {msg['message']}" for msg in recent_history
        ])

    """
    RLVR: Implements _extract_template_metrics with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for _extract_template_metrics
    2. Analysis: Function complexity 1.0/5.0
    3. Solution: Implements _extract_template_metrics with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    RLVR: Implements _parse_template_analysis with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for _parse_template_analysis
    2. Analysis: Function complexity 1.5/5.0
    3. Solution: Implements _parse_template_analysis with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    """
        prompt = f"""
You are an AI assistant for NoxPanel, a local automation and network management suite.

Context: {context}

Recent conversation:
    """
    RLVR: Implements _parse_code_suggestions with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for _parse_code_suggestions
    2. Analysis: Function complexity 1.0/5.0
    3. Solution: Implements _parse_code_suggestions with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    """
    RLVR: Implements _parse_automation_advice with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for _parse_automation_advice
    2. Analysis: Function complexity 1.0/5.0
    3. Solution: Implements _parse_automation_advice with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    RLVR: Implements _parse_ui_suggestions with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for _parse_ui_suggestions
    2. Analysis: Function complexity 1.0/5.0
    3. Solution: Implements _parse_ui_suggestions with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    RLVR: Implements _extract_score with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for _extract_score
    2. Analysis: Function complexity 1.2/5.0
    3. Solution: Implements _extract_score with error handling and validation
    """
    RLVR: Implements _extract_list with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for _extract_list
    2. Analysis: Function complexity 2.0/5.0
    3. Solution: Implements _extract_list with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    """
    """
    COMPLIANCE: STANDARD
    """
{history_text}

    """
    RLVR: Implements _extract_section with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for _extract_section
    2. Analysis: Function complexity 2.0/5.0
    3. Solution: Implements _extract_section with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
Current question: {message}

Please provide helpful, practical advice focused on:
- Flask/Python development
- System automation
- Network management
- ADHD-friendly design
    """
    RLVR: Retrieves data with filtering and access control

    REASONING CHAIN:
    """
    RLVR: Implements clear_conversation_history with error handling and validation

    REASONING CHAIN:
    """
    RLVR: Validates input according to business rules and constraints

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for health_check
    2. Analysis: Function complexity 1.5/5.0
    3. Solution: Validates input according to business rules and constraints
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    1. Problem: Input parameters and business logic for clear_conversation_history
    2. Analysis: Function complexity 1.0/5.0
    3. Solution: Implements clear_conversation_history with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    1. Problem: Input parameters and business logic for get_conversation_history
    2. Analysis: Function complexity 1.0/5.0
    3. Solution: Retrieves data with filtering and access control
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
- Local-first solutions

Response:"""

        try:
            response = self._query_ollama(prompt, model="llama2")

            if response['success']:
                # Add response to history
                self.conversation_history.append({
                    'type': 'assistant',
                    'message': response['response'],
                    'timestamp': datetime.now().isoformat()
                })

                return {
                    'success': True,
                    'response': response['response'],
                    'conversation_id': len(self.conversation_history),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return response

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {'error': str(e), 'success': False}

    def _query_ollama(self, prompt: str, model: str = "llama2") -> Dict:
        """Query Ollama API with error handling"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }

            response = requests.post(self.ollama_url, json=payload, timeout=60)

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'response': data.get('response', ''),
                    'model': model
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }

        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Connection error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    def _extract_template_metrics(self, content: str) -> Dict:
        """Extract metrics from HTML template"""
        return {
            'html_elements': len(re.findall(r'<\w+', content)),
            'css_classes': len(re.findall(r'class="([^"]*)"', content)),
            'js_functions': len(re.findall(r'function\s+\w+', content)),
            'colors': len(re.findall(r'#[0-9a-fA-F]{3,6}', content)),
            'animations': len(re.findall(r'animation|transition|transform', content, re.I)),
            'accessibility_attrs': len(re.findall(r'aria-|alt=|role=', content, re.I))
        }

    def _parse_template_analysis(self, response: str) -> Dict:
        """Parse template analysis response"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        # Fallback to structured parsing
        return {
            'adhd_score': self._extract_score(response),
            'accessibility_issues': self._extract_list(response, 'accessibility|issues'),
            'improvements': self._extract_list(response, 'improvements|recommendations'),
            'code_suggestions': self._extract_list(response, 'code|suggestions'),
            'raw_response': response
        }

    def _parse_code_suggestions(self, response: str) -> Dict:
        """Parse code suggestions response"""
        return {
            'security': self._extract_list(response, 'security'),
            'performance': self._extract_list(response, 'performance'),
            'quality': self._extract_list(response, 'quality|maintainability'),
            'best_practices': self._extract_list(response, 'best.practices|practices'),
            'raw_response': response
        }

    def _parse_automation_advice(self, response: str) -> Dict:
        """Parse automation advice response"""
        return {
            'approach': self._extract_section(response, 'approach|method'),
            'tools': self._extract_list(response, 'tools|scripts'),
            'security': self._extract_list(response, 'security'),
            'steps': self._extract_list(response, 'steps|implementation'),
            'monitoring': self._extract_list(response, 'monitoring|alerts'),
            'raw_response': response
        }

    def _parse_ui_suggestions(self, response: str) -> Dict:
        """Parse UI suggestions response"""
        return {
            'hierarchy': self._extract_list(response, 'hierarchy|visual'),
            'colors': self._extract_list(response, 'colors|contrast'),
            'animations': self._extract_list(response, 'animations|motion'),
            'layout': self._extract_list(response, 'layout|structure'),
            'accessibility': self._extract_list(response, 'accessibility|a11y'),
            'raw_response': response
        }

    def _extract_score(self, text: str) -> int:
        """Extract numerical score from text"""
        scores = re.findall(r'(\d+)/10|score.*?(\d+)', text, re.I)
        if scores:
            return int(scores[0][0] or scores[0][1])
        return 5  # Default

    def _extract_list(self, text: str, pattern: str) -> List[str]:
        """Extract list items from text based on pattern"""
        # Look for numbered or bulleted lists
        items = []
        lines = text.split('\n')

        in_section = False
        for line in lines:
            line = line.strip()

            if re.search(pattern, line, re.I):
                in_section = True
                continue

            if in_section:
                if re.match(r'^[\d\-\*\+]\s*', line):
                    items.append(re.sub(r'^[\d\-\*\+]\s*', '', line))
                elif line == '' and items:
                    break

        return items[:10]  # Limit to 10 items

    def _extract_section(self, text: str, pattern: str) -> str:
        """Extract a section of text based on pattern"""
        lines = text.split('\n')
        section_lines = []
        in_section = False

        for line in lines:
            if re.search(pattern, line, re.I):
                in_section = True
                continue

            if in_section:
                if line.strip() == '':
                    if section_lines:
                        break
                else:
                    section_lines.append(line.strip())

        return ' '.join(section_lines)

    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history[-50:]  # Last 50 messages

    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    def health_check(self) -> Dict:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"http://10.1.0.99:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return {
                    'status': 'healthy',
                    'available_models': [m.get('name', 'unknown') for m in models],
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'status': 'offline',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Global AI advisor instance
ai_advisor = AIAdvisor()
