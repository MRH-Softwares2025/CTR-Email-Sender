#!/usr/bin/env python3
"""
Template System for Email Automation
Supports dynamic content with HTML formatting (bold, italics, underline)
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime


class EmailTemplate:
    """Template processor for email content with formatting support"""
    
    # Formatting patterns
    BOLD_PATTERN = r'\*\*(.*?)\*\*'
    ITALIC_PATTERN = r'\*(.*?)\*'
    UNDERLINE_PATTERN = r'__(.*?)__'
    
    def __init__(self, template: str):
        self.template = template
        self.variables = {}
    
    def set_variable(self, name: str, value: Any):
        """Set a template variable"""
        self.variables[name] = value
    
    def set_variables(self, variables: Dict[str, Any]):
        """Set multiple template variables"""
        self.variables.update(variables)
    
    def _replace_placeholders(self, text: str) -> str:
        """Replace {{variable}} placeholders with actual values"""
        pattern = r'\{\{(\w+)\}\}'
        
        def replacer(match):
            var_name = match.group(1)
            return str(self.variables.get(var_name, match.group(0)))
        
        return re.sub(pattern, replacer, text)
    
    def _apply_formatting(self, text: str) -> str:
        """Convert markdown-like formatting to HTML"""
        # Bold: **text** -> <strong>text</strong>
        text = re.sub(self.BOLD_PATTERN, r'<strong>\1</strong>', text)
        
        # Italic: *text* -> <em>text</em>
        text = re.sub(self.ITALIC_PATTERN, r'<em>\1</em>', text)
        
        # Underline: __text__ -> <u>text</u>
        text = re.sub(self.UNDERLINE_PATTERN, r'<u>\1</u>', text)
        
        return text
    
    def _convert_line_breaks(self, text: str) -> str:
        """Convert line breaks to <br> tags"""
        return text.replace('\n', '<br>')
    
    def render(self, html: bool = True) -> str:
        """
        Render the template with variables and optional HTML formatting
        
        Args:
            html: If True, apply HTML formatting. If False, return plain text.
        
        Returns:
            Rendered template string
        """
        # First replace placeholders
        rendered = self._replace_placeholders(self.template)
        
        if html:
            # Apply formatting
            rendered = self._apply_formatting(rendered)
            # Convert line breaks
            rendered = self._convert_line_breaks(rendered)
        
        return rendered
    
    def render_plain_text(self) -> str:
        """Render template as plain text (strip HTML formatting)"""
        # Replace placeholders
        rendered = self._replace_placeholders(self.template)
        
        # Remove formatting markers for plain text
        rendered = re.sub(self.BOLD_PATTERN, r'\1', rendered)
        rendered = re.sub(self.ITALIC_PATTERN, r'\1', rendered)
        rendered = re.sub(self.UNDERLINE_PATTERN, r'\1', rendered)
        
        return rendered


class TemplateManager:
    """Manages email templates with preset templates"""
    
    def __init__(self):
        self.templates = {
            'default': EmailTemplate(
                "Dear {{recipient}},\n\n"
                "{{message}}\n\n"
                "Best regards,\n"
                "{{sender}}"
            ),
            'notification': EmailTemplate(
                "**Important Notification**\n\n"
                "{{content}}\n\n"
                "_Sent on {{date}}_"
            ),
            'promotion': EmailTemplate(
                "__Special Offer__\n\n"
                "{{title}}\n\n"
                "{{description}}\n\n"
                "*Valid until: {{expiry_date}}*"
            ),
            'newsletter': EmailTemplate(
                "**Newsletter**\n\n"
                "{{greeting}}\n\n"
                "{{content}}\n\n"
                "---\n"
                "{{footer}}"
            )
        }
    
    def get_template(self, name: str) -> Optional[EmailTemplate]:
        """Get a template by name"""
        return self.templates.get(name)
    
    def create_template(self, name: str, template: str):
        """Create a new template"""
        self.templates[name] = EmailTemplate(template)
    
    def list_templates(self) -> list:
        """List all available template names"""
        return list(self.templates.keys())
    
    def render_template(self, name: str, variables: Dict[str, Any], html: bool = True) -> str:
        """
        Render a template with variables
        
        Args:
            name: Template name
            variables: Dictionary of variables to replace
            html: Whether to apply HTML formatting
        
        Returns:
            Rendered template string
        """
        template = self.get_template(name)
        if not template:
            raise ValueError(f"Template '{name}' not found")
        
        template.set_variables(variables)
        return template.render(html=html)


def create_email_body(subject: str, content: str, variables: Optional[Dict[str, Any]] = None, html: bool = True) -> str:
    """
    Create a complete email body with subject and content
    
    Args:
        subject: Email subject
        content: Email content (can include formatting)
        variables: Optional variables for template replacement
        html: Whether to apply HTML formatting
    
    Returns:
        Complete email body
    """
    template_str = f"**{subject}**\n\n{content}"
    template = EmailTemplate(template_str)
    
    if variables:
        template.set_variables(variables)
    
    # Add common variables
    template.set_variable('date', datetime.now().strftime('%Y-%m-%d'))
    template.set_variable('time', datetime.now().strftime('%H:%M:%S'))
    
    return template.render(html=html)


# Example usage and common variables
COMMON_VARIABLES = {
    'recipient': 'Recipient Name',
    'sender': 'Sender Name',
    'date': datetime.now().strftime('%Y-%m-%d'),
    'time': datetime.now().strftime('%H:%M:%S'),
}
