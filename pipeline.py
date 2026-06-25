#!/usr/bin/env python3
import os
import re
import json
import argparse
import html
from pathlib import Path

# ==========================================
# CONSTANTS & SANITIZATION CONFIGURATION
# ==========================================

# Pattern replacements (regex, replacement, description)
SANITIZATION_RULES = [
    # API Keys and Passwords (hardcoded tokens)
    (
        r'LUFRPT1ZUjVTaWtUcGxiNXptQXZOUTk2N3FRV3ZBelU9bWEvSW96S2dHbjdFclB1TXJWQm5Yc3Q2T0lBSXk5Qzdxanhid0FKSUpKOXZqckFuR2F3YW02cXRVcVpyMTVXalRMZTdkT2tZS3B5WjhVenRWMnRKRWc9PQ==',
        '<PANORAMA_API_KEY_SCRUBBED>',
        'Panorama API Key'
    ),
    (
        r'NDXsnZGS6!7fL\$ZTr!N%vvp',
        '<SERVICENOW_PASSWORD_SCRUBBED>',
        'ServiceNow Password'
    ),
    (
        r'(?i)(api_key|password|secret|token|pass|auth)\s*=\s*["\'][a-zA-Z0-9!@#$%^&*()_+=-]{12,}["\']',
        r'\1 = "<SECRET_SCRUBBED>"',
        'Generic Config Secret Assignment'
    ),
    
    # Specific IP Addresses
    (r'10\.209\.90\.120', '<PROD_PANORAMA_IP>', 'Production Panorama IP'),
    (r'10\.208\.136\.189', '<LAB_PANORAMA_IP>', 'Lab Panorama IP'),
    (r'192\.168\.30\.62', '<N8N_SERVER_IP>', 'N8n Automation Server IP'),
    (r'192\.168\.30\.68', '<DISCORD_BOT_IP>', 'Discord Review Bot IP'),
    (r'192\.168\.10\.111', '<DNS_PRIMARY_IP>', 'Primary Internal DNS IP'),
    (r'192\.168\.10\.112', '<DNS_SECONDARY_IP>', 'Secondary Internal DNS IP'),
    
    # Generic Private IPs (10.x.x.x, 192.168.x.x, 172.16.x.x to 172.31.x.x)
    (r'\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<INTERNAL_IP_10_X>', 'Generic 10.x.x.x Private IP'),
    (r'\b192\.168\.\d{1,3}\.\d{1,3}\b', '<INTERNAL_IP_192_X>', 'Generic 192.168.x.x Private IP'),
    (r'\b172\.(?:1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}\b', '<INTERNAL_IP_172_X>', 'Generic 172.16-31.x.x Private IP'),

    # Emails and Domain Names
    (r'(?i)xc619@cummins\.com', 'security-ops@enterprise.com', 'Primary Operator Email'),
    (r'(?i)ops\.internet@cummins\.com', 'network-hygiene@enterprise.com', 'Team Distribution Email'),
    (r'(?i)[\w\.-]+@cummins\.com', 'user@enterprise.com', 'Generic Cummins Email'),
    (r'(?i)mailrelay\.cummins\.com', 'smtp.enterprise.com', 'SMTP Server Domain'),
    (r'(?i)cummins\.service-now\.com', 'enterprise.service-now.com', 'ServiceNow Enterprise Instance'),
    (r'(?i)cummins', 'Enterprise Network', 'Company Name'),
    (r'(?i)mareoxlan\.local', '<YOUR_DOMAIN>.local', 'Internal AD Domain'),
    (r'(?i)mareoxlan\.com', '<YOUR_DOMAIN>.com', 'Internal Root Domain'),
]

# ==========================================
# PURE PYTHON MARKDOWN TO HTML CONVERTER
# ==========================================

def markdown_to_html(md_text):
    """
    Converts basic Markdown formatting to clean HTML.
    Handles headers, lists, code blocks, tables, bold, italics, links, and paragraphs.
    """
    lines = md_text.split('\n')
    html_out = []
    in_list = False
    in_ordered_list = False
    in_code_block = False
    code_lang = ""
    code_lines = []
    in_table = False
    table_headers = []
    
    for line in lines:
        stripped = line.strip()
        
        # 1. Handle Code Blocks
        if stripped.startswith('```'):
            if in_code_block:
                # Close code block
                code_content = '\n'.join(code_lines)
                # Escape html inside code blocks
                code_content = html.escape(code_content)
                html_out.append(f'<pre><code class="language-{code_lang}">{code_content}</code></pre>')
                in_code_block = False
                code_lines = []
                code_lang = ""
            else:
                # Open code block
                in_code_block = True
                code_lang = stripped[3:].strip().lower()
            continue
            
        if in_code_block:
            code_lines.append(line)
            continue

        # 2. Handle Tables
        if stripped.startswith('|') and not in_code_block:
            # Table line
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            
            # Check for separator line (e.g. |---|---|)
            if all(re.match(r'^:?-+:?$', c) for c in cells) and len(cells) > 0:
                continue
                
            if not in_table:
                in_table = True
                html_out.append('<table>')
                # The first row is headers
                html_out.append('<thead><tr>')
                for cell in cells:
                    # Apply inline styles to cell text
                    cell_html = parse_inline_markdown(cell)
                    html_out.append(f'<th>{cell_html}</th>')
                html_out.append('</tr></thead><tbody>')
            else:
                html_out.append('<tr>')
                for cell in cells:
                    cell_html = parse_inline_markdown(cell)
                    html_out.append(f'<td>{cell_html}</td>')
                html_out.append('</tr>')
            continue
        elif in_table:
            html_out.append('</tbody></table>')
            in_table = False

        # 3. Handle Lists (Unordered)
        if stripped.startswith('- ') or stripped.startswith('* '):
            if in_ordered_list:
                html_out.append('</ol>')
                in_ordered_list = False
            if not in_list:
                html_out.append('<ul>')
                in_list = True
            item_text = parse_inline_markdown(stripped[2:])
            html_out.append(f'<li>{item_text}</li>')
            continue
            
        # Handle Lists (Ordered)
        match_ol = re.match(r'^\d+\.\s+(.*)$', stripped)
        if match_ol:
            if in_list:
                html_out.append('</ul>')
                in_list = False
            if not in_ordered_list:
                html_out.append('<ol>')
                in_ordered_list = True
            item_text = parse_inline_markdown(match_ol.group(1))
            html_out.append(f'<li>{item_text}</li>')
            continue
            
        # Close lists if line is not a list item
        if in_list and stripped == "":
            html_out.append('</ul>')
            in_list = False
        if in_ordered_list and stripped == "":
            html_out.append('</ol>')
            in_ordered_list = False

        # 4. Handle Headers
        if stripped.startswith('#') and not in_code_block:
            # Count hashes
            hash_count = 0
            for char in stripped:
                if char == '#':
                    hash_count += 1
                else:
                    break
            header_text = stripped[hash_count:].strip()
            header_html = parse_inline_markdown(header_text)
            html_out.append(f'<h{hash_count}>{header_html}</h{hash_count}>')
            continue

        # 5. Handle Blockquotes
        if stripped.startswith('>') and not in_code_block:
            quote_text = stripped[1:].strip()
            quote_html = parse_inline_markdown(quote_text)
            html_out.append(f'<blockquote><p>{quote_html}</p></blockquote>')
            continue

        # 6. Handle Blank Lines
        if stripped == "":
            continue

        # 7. Handle Regular Paragraphs
        paragraph_html = parse_inline_markdown(stripped)
        html_out.append(f'<p>{paragraph_html}</p>')

    # Close any unclosed tables or lists
    if in_table:
        html_out.append('</tbody></table>')
    if in_list:
        html_out.append('</ul>')
    if in_ordered_list:
        html_out.append('</ol>')

    return '\n'.join(html_out)

def parse_inline_markdown(text):
    """Parses inline bold, italics, code, and link tags."""
    # Escape standard HTML characters first to avoid injection
    t = html.escape(text)
    
    # 1. Inline Code: `code`
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    
    # 2. Bold: **text** or __text__
    t = re.sub(r'\*\*([^*]+)\*\*|__([^_]+)__', r'<strong>\1\2</strong>', t)
    
    # 3. Italics: *text* or _text_
    t = re.sub(r'\*([^*]+)\*|_([^_]+)_', r'<em>\1\2</em>', t)
    
    # 4. Links: [text](url)
    # We must be careful to handle escaped quotes or ampersands in URLs
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', t)
    
    # 5. Highlight tags: <tag> (which would be escaped as &lt;tag&gt; now)
    # Re-enable specific safe custom tags if any, like <PANORAMA_IP>
    t = re.sub(r'&lt;([A-Z0-9_]+_IP|[A-Z0-9_]+_SCRUBBED|[A-Z0-9_]+)&gt;', r'<span class="tag-highlight">&lt;\1&gt;</span>', t)
    
    return t

# ==========================================
# SANITIZATION ENGINE
# ==========================================

def sanitize_text(text):
    """Applies all regex sanitization rules to the input text."""
    sanitized = text
    replaced_details = []
    
    for pattern, replacement, desc in SANITIZATION_RULES:
        # Count matches
        matches = len(re.findall(pattern, sanitized))
        if matches > 0:
            sanitized = re.sub(pattern, replacement, sanitized)
            replaced_details.append(f"Scrubbed {matches} instances of {desc} -> '{replacement}'")
            
    return sanitized, replaced_details

# ==========================================
# MAIN COMMAND LINE PIPELINE
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="Automated Blog Pipeline Sanitizer & Compiler")
    parser.add_argument("--draft", help="Path to the draft markdown file", required=True)
    parser.add_argument("--title", help="Override title of the post")
    parser.add_argument("--category", default="Security Automation", help="Category of the post")
    parser.add_argument("--tags", default="Automation,Firewall,Palo Alto", help="Comma-separated tags")
    parser.add_argument("--cover", default="./assets/firewall_hygiene.png", help="Path to cover image")
    parser.add_argument("--read_time", default="8 min read", help="Estimated reading time")
    
    args = parser.parse_args()
    
    draft_path = Path(args.draft)
    if not draft_path.exists():
        print(f"Error: Draft file '{draft_path}' does not exist.")
        return
        
    with open(draft_path, "r", encoding="utf-8") as f:
        draft_content = f.read()
        
    print(f"=== Loaded draft: {draft_path.name} ({len(draft_content)} bytes) ===")
    
    # 1. Extract metadata from draft frontmatter if it exists
    # Simple frontmatter parser
    title = args.title
    category = args.category
    tags_list = [t.strip() for t in args.tags.split(",")]
    cover_image = args.cover
    read_time = args.read_time
    
    body_content = draft_content
    
    if draft_content.startswith('---'):
        parts = draft_content.split('---', 2)
        if len(parts) >= 3:
            frontmatter_text = parts[1]
            body_content = parts[2].strip()
            
            # Parse frontmatter yaml-like structure
            for line in frontmatter_text.split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    k = k.strip().lower()
                    v = v.strip().strip('"').strip("'")
                    if k == 'title' and not args.title:
                        title = v
                    elif k == 'category':
                        category = v
                    elif k == 'tags':
                        tags_list = [t.strip() for t in v.split(',')]
                    elif k == 'cover':
                        cover_image = v
                    elif k == 'read_time':
                        read_time = v
                        
    if not title:
        # Fallback to draft filename as title
        title = draft_path.stem.replace('-', ' ').title()
        
    # Generate slug
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    
    # 2. Run Sanitization Engine
    print("\nRunning sanitization engine...")
    sanitized_body, scrub_log = sanitize_text(body_content)
    sanitized_title, _ = sanitize_text(title)
    sanitized_category, _ = sanitize_text(category)
    sanitized_tags = [sanitize_text(t)[0] for t in tags_list]
    
    for log in scrub_log:
        print(f"  [SCRUBBED] {log}")
    
    # 3. Convert Markdown to HTML
    print("\nCompiling Markdown to luxury HTML...")
    html_body = markdown_to_html(sanitized_body)
    
    # 4. Generate Post JSON Object
    import datetime
    today_str = datetime.date.today().strftime("%B %d, %Y")
    
    post_data = {
        "title": sanitized_title,
        "slug": slug,
        "date": today_str,
        "category": sanitized_category,
        "tags": sanitized_tags,
        "cover_image": cover_image,
        "read_time": read_time,
        "description": sanitized_body[:200].replace('\n', ' ').strip() + "...",
        "content": html_body
    }
    
    # Create projects/posts/ directory if needed
    posts_dir = Path("projects/posts")
    posts_dir.mkdir(parents=True, exist_ok=True)
    
    post_file_path = posts_dir / f"{slug}.json"
    with open(post_file_path, "w", encoding="utf-8") as f:
        json.dump(post_data, f, indent=4)
    print(f"  [COMPILED] Written detailed post to: {post_file_path}")
    
    # 5. Update projects/posts.json Database Index
    db_path = Path("projects/posts.json")
    db_data = []
    
    if db_path.exists():
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                db_data = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to parse existing posts.json, resetting. Error: {e}")
            
    # Check if post already exists in index and update it, else append
    existing_idx = -1
    for idx, item in enumerate(db_data):
        if item["slug"] == slug:
            existing_idx = idx
            break
            
    # Keep index slim - remove full content field in the main index to save bandwidth
    index_entry = {
        "title": sanitized_title,
        "slug": slug,
        "date": today_str,
        "category": sanitized_category,
        "tags": sanitized_tags,
        "cover_image": cover_image,
        "read_time": read_time,
        "description": post_data["description"]
    }
    
    if existing_idx >= 0:
        db_data[existing_idx] = index_entry
        print(f"  [INDEX] Updated existing entry for slug '{slug}' in index.")
    else:
        # Insert at the beginning of the list (newest first)
        db_data.insert(0, index_entry)
        print(f"  [INDEX] Added new entry for slug '{slug}' to index.")
        
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db_data, f, indent=4)
    print(f"  [INDEX] Successfully updated index database: {db_path}")
    print("\n=== Pipeline Execution Completed Successfully! ===")

if __name__ == "__main__":
    main()
